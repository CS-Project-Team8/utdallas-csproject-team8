# general imports
import re
import time
from googleapiclient.discovery import build
from datetime import datetime, timezone

# imports for transcript extraction
from groq import Groq
import subprocess
import tempfile
import math

# imports for Gemini 3 Flash
# from google import genai
# from google.genai import types

# imports for TMDB API
import requests

# imports for environment variables
from dotenv import load_dotenv
import os
from pathlib import Path

# imports for DB operations
from db_operationstest import (
    conn,
    insert_yt_channel,
    insert_yt_video,
    insert_yt_video_metric_snapshot,
    insert_yt_comment_thread,
    insert_yt_comment,
    insert_movie,
    insert_movie_metric_snapshot,
    insert_transcript
)

# keys and client setup
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

DEVELOPER_KEY1 = os.getenv("YOUTUBE_API_KEY_1")
DEVELOPER_KEY2 = os.getenv("YOUTUBE_API_KEY_2")
DEVELOPER_KEY3 = os.getenv("YOUTUBE_API_KEY_3")
#GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY")
GROQ_TRANSCRIPT_API_KEY = os.getenv("GROQ_TRANSCRIPT_API_KEY")
TMDB_API_KEY    = os.getenv("TMDB_API_KEY")

youtube_object = build("youtube", "v3", developerKey=DEVELOPER_KEY2)
#client = genai.Client(api_key=GEMINI_API_KEY)
client = Groq(api_key=GROQ_TRANSCRIPT_API_KEY)

TRAILER_KEYWORDS = ["official trailer", "trailer", "official teaser", "teaser"]
QUOTA_LIMIT = 9000  # hard stop before hitting YouTube's 10,000 daily limit
quota_used = 0      # global quota tracker

REVIEW_QUERY_TEMPLATES = [
    "{title} movie review",
    "{title} review",
    "{title} film review",
]
MIN_REVIEW_DURATION_SECONDS = 180  # filter out Shorts (< 3 minutes)

# TRACKING/CALCULATING/FILTEIRNG FUNCTIONS:

# tracking quote so that we don't accidentally go over YouTubeAPI's daily quota limit (just during testing)
def use_quota(units, reason=""):
    global quota_used
    quota_used += units
    print(f"  [Quota: +{units} ({reason}) → total: {quota_used}/{QUOTA_LIMIT}]")
    if quota_used >= QUOTA_LIMIT:
        raise RuntimeError(f"Daily YouTube quota limit reached ({quota_used} units). Stopping.")

# helper function to convert ISO 8601 duration format (e.g. PT2M30S) to total seconds -> easier filtering by vid length
def iso8601_duration_to_seconds(d):
    if not d or not d.startswith("PT"):
        return None
    h = m = s = 0
    mh = re.search(r"(\d+)H", d)
    mm = re.search(r"(\d+)M", d)
    ms = re.search(r"(\d+)S", d)
    if mh:
        h = int(mh.group(1))
    if mm:
        m = int(mm.group(1))
    if ms:
        s = int(ms.group(1))
    return h * 3600 + m * 60 + s

# helper function to calculate engagement rate = (total likes + total comments) / total views -> for movieMetricSnapshots table
def calculate_engagement_rate(views, likes, comments):
    likes = likes or 0
    comments = comments or 0
    return (likes + comments) / views if views and views > 0 else 0.0

# helper function to normalize video titles and extract movie name for common trailer title formats (i.e., "Movie Title | Official Trailer")
def normalize_title(video_title):
    t = video_title.strip()

    TRAILER_SIGNALS = [
        "official trailer", "official teaser trailer", "official teaser",
        "teaser trailer", "trailer"
    ]

    for sep in ["|", "–", "-"]:
        if sep in t:
            parts = [p.strip() for p in t.split(sep, 1)]
            if len(parts) == 2:
                right = parts[1].lower()
                if any(right.startswith(sig) for sig in TRAILER_SIGNALS):
                    candidate = re.sub(r"\s*\(.*?\)\s*$", "", parts[0]).strip()
                    return candidate if len(candidate) > 2 else None

    return None

# helper function to check TMDB for movie release date -> easier filter for latest 5 movies
def get_movie_release_date(movie_title):
    response = requests.get(
        "https://api.themoviedb.org/3/search/movie",
        params={
            "api_key": TMDB_API_KEY,
            "query": movie_title
        }
    ).json()

    results = response.get("results", [])
    if not results:
        return None

    release_date = results[0].get("release_date")
    return release_date if release_date else None
      
    
# TRANSCRIBE FUNCTIONS:   
    
GROQ_MAX_FILE_MB = 24 # limit is 25MB 
GROQ_MAX_SECONDS = 10 * 60  # making it 10 mins max so that way I don't go over limit
TRANSCRIBE_SLEEP = 30 # so I don't overload groq

# getting audio file length
def get_audio_duration_seconds(path):
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ], capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None
    
# trimming audio to GROQ_MAX_SECONDS (≤ 20 mins)
def trim_audio_if_needed(path, max_seconds=GROQ_MAX_SECONDS):
    duration = get_audio_duration_seconds(path)
    if duration is None or duration <= max_seconds:
        return path  # no trim needed

    print(f"  Audio is {duration:.0f}s — trimming to {max_seconds}s...")
    trimmed_path = path.replace(".mp3", "_trimmed.mp3")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", path,
        "-t", str(max_seconds),
        "-acodec", "copy",
        trimmed_path
    ], check=True, capture_output=True)
    os.unlink(path)           # remove the original
    return trimmed_path

# transcribing using a temporary audio file and sending to groq
def transcribe_with_groq_whisper(video_url):
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, "audio.mp3")

    try:
        subprocess.run([
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "3",
            "-o", tmp_path,
            video_url
        ], check=True)

        # Trim if too long before hitting Groq
        tmp_path = trim_audio_if_needed(tmp_path)

        file_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        print(f"  Sending {file_mb:.1f}MB to Whisper...")

        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio_file,
                response_format="text"
            )
        return result

    finally:
        for f in os.listdir(tmp_dir):
            os.unlink(os.path.join(tmp_dir, f))
        os.rmdir(tmp_dir)

# getting transcript from temp audio file and inserting to db
def transcribe_and_insert(cursor, videoid, video_url):
    try:
        fulltext = transcribe_with_groq_whisper(video_url)
        insert_transcript(
            cursor,
            videoid=videoid,
            language="en",
            source="auto",
            fulltext=fulltext,
        )
        print(f"  Transcribed and saved: {videoid}")
        time.sleep(TRANSCRIBE_SLEEP)   # <-- rate limit buffer
    except Exception as e:
        error_str = str(e)
        # If still rate limited despite sleep, wait and retry once
        if "429" in error_str and "Please try again in" in error_str:
            wait = _parse_retry_wait(error_str)
            print(f"  Rate limited — waiting {wait}s then retrying...")
            time.sleep(wait + 5)
            try:
                fulltext = transcribe_with_groq_whisper(video_url)
                insert_transcript(cursor, videoid=videoid, language="en",
                                  source="auto", fulltext=fulltext)
                print(f"  Transcribed and saved on retry: {videoid}")
            except Exception as e2:
                print(f"  Failed on retry: {e2}")
        else:
            print(f"  Error transcribing {video_url}: {e}")

# getting the suggested wait time if running into too many requests
def _parse_retry_wait(error_str):
    # Matches patterns like "3m20s", "11m13s", "2m5.5s", "4m41s"
    m = re.search(r"(\d+)m([\d.]+)s", error_str)
    if m:
        return math.ceil(int(m.group(1)) * 60 + float(m.group(2)))
    # Fallback: match just seconds
    m = re.search(r"in ([\d.]+)s", error_str)
    if m:
        return math.ceil(float(m.group(1)))
    return 240  # conservative fallback: 4 minutes
        
# # prompt for Gemini 3 Flash -> please check over during PR for accuracy/clarity & if output is in right format
# TRANSCRIBE_PROMPT = """
# You are a video content analyst that specializes in extracting structured insights from YouTube videos.
# Your job is to analyze the video and return a structured JSON object with insights. Do not return anything else.
# Do not include any explanation or text outside of the JSON object. If a field cannot be determined, use null.

# You must return the following JSON structure exactly:

# {
#   "overall_sentiment": "<either positive, negative, or mixed>",
#   "key_points": [
#     "<concise string summarizing a main point made by the creator>",
#     ...
#   ],
#   "conclusions": [
#     "<any verdict or conclusion the creator reaches>",
#     ...
#   ],
#   "summary": "<2-3 sentence overview of the video's content and tone>"
# }

# Guidelines:
# - Extract 3-5 key points and 1-3 conclusions.
# - Overall sentiment should reflect the creator's tone, not the subject matter.
# - Key points should be actionable insights, not vague descriptions.
# """

# # prompt for Gemini 3 Flash -> please check over during PR for accuracy/clarity & if output is in right format
# TRANSCRIBE_PROMPT = """
# Extract the transcript from the following youtube video and return the transcript as a JSON object.
# """

# # helper function to get video transcript and extract insights using Gemini 3 Flash 
# def transcribe(video_url):
#     response = client.models.generate_content(
#         model="gemini-3-flash-preview",
#         contents=[
#             types.Content(parts=[
#                 types.Part(text=TRANSCRIBE_PROMPT),  # system instructions
#             ]),
#             types.Content(parts=[
#                 types.Part(file_data=types.FileData(file_uri=video_url)),  # actual video
#                 types.Part(text="Analyze this video and return the JSON object as specified.")
#             ])
#         ]
#     )
#     raw = response.text.strip()
#     # strip markdown code fences if Gemini wraps the response
#     if raw.startswith("```"):
#         raw = re.sub(r"^```[a-z]*\n?", "", raw)
#         raw = re.sub(r"\n?```$", "", raw)
#     return json.loads(raw)

# # helper function to transcribe a video and insert the result into ytvideotranscripts table
# def transcribe_and_insert(cursor, videoid, video_url):
#     try:
#         insights = transcribe(video_url)
#         # store the full JSON insights as the fulltext
#         fulltext = json.dumps(insights)
#         transcript_id = insert_transcript(
#             cursor,
#             videoid=videoid,
#             language="en",
#             source="auto",
#             fulltext=fulltext,
#         )
#         return transcript_id
#     except Exception as e:
#         print(f"  Error transcribing {video_url}: {e}")
#         return None
    
    
# YOUTUBE API DATA FUNCTIONS:   

# helper function to get video statistics (views, likes, comments) -> for ytVideoMetricSnapshots table and movieMetricSnapshots table
def get_video_statistics(video_id):
    try:
        result = youtube_object.videos().list(
            part="snippet,statistics,contentDetails",
            id=video_id
        ).execute()
        use_quota(1, f"videos.list ({video_id})")
        if result['items']:
            item = result['items'][0]
            stats = item['statistics']
            snippet = item['snippet']
            return {
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "commentCount": int(stats.get("commentCount", 0)),
                "publishedAt": snippet.get("publishedAt"),
                "description": snippet.get("description", ""),
                "channelId": snippet.get("channelId"),
                "channelTitle": snippet.get("channelTitle"),
                "title": snippet.get("title"),
                "tags": snippet.get("tags"),
                "defaultLanguage": snippet.get("defaultLanguage"),
                "categoryId": snippet.get("categoryId"),
                "caption": item.get("contentDetails", {}).get("caption") == "true",
            }
    except Exception as e:
        print(f"Could not retrieve statistics for {video_id}: {e}")
        return None

# helper function to get top comments for a video -> for ytCommentThreads and ytComments tables
def get_video_comments(video_id, order="relevance", max_results=100):
    try:
        result = youtube_object.commentThreads().list(
            part="snippet",
            videoId=video_id,
            order=order,
            maxResults=max_results,
            textFormat="plainText"
        ).execute()
        use_quota(1, f"commentThreads.list ({video_id})")

        comments = []
        for item in result['items']:
            top_comment = item['snippet']['topLevelComment']
            snippet = top_comment['snippet']
            comments.append({
                "comment_id": top_comment['id'],
                "thread_id": item['id'],
                "author_channel_id": (snippet.get("authorChannelId") or {}).get("value"),
                "text": snippet.get("textOriginal", ""),
                "likes": int(snippet.get("likeCount", 0)),
                "published_at": snippet.get("publishedAt"),
                "updated_at": snippet.get("updatedAt"),
                "total_reply_count": item['snippet']['totalReplyCount']
            })
        return comments
    except Exception as e:
        print(f"Could not retrieve comments for {video_id}: {e}")
        return []
    
# helper function (for Phase 0) to get uploads playlist ID of studio channel uploads -> more quota-efficient
def get_uploads_playlist_id(channel_id):
    result = youtube_object.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()
    use_quota(1, "channels.list (uploads playlist)")
    items = result.get("items", [])
    if not items:
        raise RuntimeError(f"Channel not found: {channel_id}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

# # helper function (for Phase 0) to get latest trailers from channel uploads playlist
# def get_latest_trailers_from_channel(channel_id, limit=5, max_scan=200): # see if I have to increase max_scan to guarantee 5 trailers
#     print(f"  Fetching uploads playlist for channel {channel_id}...")
#     playlist_id = get_uploads_playlist_id(channel_id)

#     # Step 1: collect video IDs from uploads playlist
#     video_ids = []
#     page_token = None
#     while len(video_ids) < max_scan:
#         result = youtube_object.playlistItems().list(
#             part="contentDetails",
#             playlistId=playlist_id,
#             maxResults=50,
#             pageToken=page_token
#         ).execute()
#         use_quota(1, "playlistItems.list")

#         for item in result.get("items", []):
#             vid = item["contentDetails"].get("videoId")
#             if vid:
#                 video_ids.append(vid)
#         page_token = result.get("nextPageToken")
#         if not page_token:
#             break

#     print(f"  Scanned {len(video_ids)} uploads, fetching details...")

#     # Step 2: fetch video details in batches of 50
#     trailers = []
#     seen_titles = set()
#     today = datetime.today().strftime("%Y-%m-%d")

#     for i in range(0, len(video_ids), 50):
#         if len(trailers) >= limit:
#             break

#         batch = video_ids[i:i + 50]
#         result = youtube_object.videos().list(
#             part="snippet,statistics,contentDetails",
#             id=",".join(batch)
#         ).execute()
#         use_quota(1, f"videos.list (batch {i//50 + 1})")

#         for item in result.get("items", []):
#             title = item["snippet"]["title"]
#             print(f"  Scanning: '{title}'")  # add this
#             title_lower = title.lower()
    
#             # Skip anything that doesn't look like a trailer
#             if not any(kw in title_lower for kw in ["trailer", "teaser"]):
#                 continue
            
#             movie_title = normalize_title(title)
#             if not movie_title or movie_title in seen_titles:
#                 continue

#             # Check TMDB for release date — skip unreleased movies
#             release_date = get_movie_release_date(movie_title)
#             if not release_date:
#                 print(f"  Skipping '{movie_title}' — not found on TMDB")
#                 continue
#             if release_date > today:
#                 print(f"  Skipping '{movie_title}' — releases {release_date} (not yet out)")
#                 continue

#             seen_titles.add(movie_title)
#             trailers.append({
#                 "movie_title": movie_title,
#                 "video_id": item["id"],
#                 "title": title,
#                 "channel_id": item["snippet"]["channelId"],
#                 "channel_title": item["snippet"]["channelTitle"],
#                 "published_at": item["snippet"]["publishedAt"][:10],
#                 "published_at_full": item["snippet"]["publishedAt"],
#                 "description": item["snippet"]["description"],
#                 "views": int(item["statistics"].get("viewCount", 0)),
#                 "likes": int(item["statistics"].get("likeCount", 0)),
#                 "comment_count": int(item["statistics"].get("commentCount", 0)),
#                 "tags": item["snippet"].get("tags"),
#                 "category_id": item["snippet"].get("categoryId"),
#                 "default_language": item["snippet"].get("defaultLanguage"),
#                 "caption": item.get("contentDetails", {}).get("caption") == "true",
#             })

#             if len(trailers) >= limit:
#                 break

#     return trailers

def get_latest_trailers_from_channel(channel_id, limit=5, max_scan=200):
    print(f"  Searching for trailers on channel {channel_id}...")

    # Run two searches — date for recency, relevance for well-known trailers
    candidate_ids = []
    seen = set()

    for order in ["date", "relevance"]:
        result = youtube_object.search().list(
            q="official trailer movie",
            part="id,snippet",
            type="video",
            channelId=channel_id,
            maxResults=25,
            order=order
        ).execute()
        use_quota(100, f"search.list (channel trailers {order})")
        for item in result.get("items", []):
            vid = item["id"]["videoId"]
            if vid not in seen:
                seen.add(vid)
                candidate_ids.append(vid)

    if not candidate_ids:
        print("  No trailer candidates found")
        return []

    # Fetch full details for all candidates in one batch
    result = youtube_object.videos().list(
        part="snippet,statistics,contentDetails",
        id=",".join(candidate_ids)
    ).execute()
    use_quota(1, "videos.list (trailer candidates)")

    trailers = []
    seen_titles = set()
    today = datetime.today().strftime("%Y-%m-%d")

    for item in result.get("items", []):
        if len(trailers) >= limit:
            break

        title = item["snippet"]["title"]
        print(f"  Scanning: '{title}'")

        movie_title = normalize_title(title)
        if not movie_title or movie_title in seen_titles:
            continue

        release_date = get_movie_release_date(movie_title)
        if not release_date:
            print(f"  Skipping '{movie_title}' — not found on TMDB")
            continue
        if release_date > today:
            print(f"  Skipping '{movie_title}' — releases {release_date} (not yet out)")
            continue

        seen_titles.add(movie_title)
        trailers.append({
            "movie_title": movie_title,
            "video_id": item["id"],
            "title": title,
            "channel_id": item["snippet"]["channelId"],
            "channel_title": item["snippet"]["channelTitle"],
            "published_at": item["snippet"]["publishedAt"][:10],
            "published_at_full": item["snippet"]["publishedAt"],
            "description": item["snippet"]["description"],
            "views": int(item["statistics"].get("viewCount", 0)),
            "likes": int(item["statistics"].get("likeCount", 0)),
            "comment_count": int(item["statistics"].get("commentCount", 0)),
            "tags": item["snippet"].get("tags"),
            "category_id": item["snippet"].get("categoryId"),
            "default_language": item["snippet"].get("defaultLanguage"),
            "caption": item.get("contentDetails", {}).get("caption") == "true",
        })

    return trailers


# PHASE 0: Find official YouTube channel for each studio and insert into DB 

def phase0_insert_studio_channels(studio_id, studio_name):
    print(f"\n{'='*60}")
    print(f"PHASE 0: Finding official channel for {studio_name}")
    print(f"{'='*60}")

    search = youtube_object.search().list(
        q=studio_name,
        part="id, snippet",
        type="channel",
        maxResults=1
    ).execute()
    use_quota(100, f"search.list (channel: {studio_name})")

    items = search.get("items", [])
    if not items:
        print(f"  No channel found for {studio_name}")
        return None

    item = items[0]
    channel_id = item["id"]["channelId"]
    channel_title = item["snippet"]["channelTitle"]

    # Fetch full channel details to get country
    channel_details = youtube_object.channels().list(
        part="snippet",
        id=channel_id
    ).execute()
    use_quota(1, "channels.list (country)")

    country = None
    if channel_details["items"]:
        country = channel_details["items"][0]["snippet"].get("country")

    print(f"  Found channel: {channel_title} (ID: {channel_id})")

    try:
        with conn.cursor() as cur:
            insert_yt_channel(cur, channel_id, channel_title, country)
        conn.commit()
        print(f"  Inserted channel: {channel_title}")
    except Exception as e:
        conn.rollback()
        print(f"  Error inserting channel: {e}")
        return None

    return channel_id


# PHASE 1: insert movies + trailers into DB, along with trailer comments

def phase1_insert_movies(studio_id, studio_name, trailers):
    print(f"\n{'='*60}")
    print(f"PHASE 1: Inserting movies for {studio_name}")
    print(f"{'='*60}")

    movie_ids = []

    for trailer in trailers:
        movie_name = trailer["movie_title"]
        published_at = trailer["published_at"]

        print(f"\n  Inserting: {movie_name} ({published_at})")

        # Capture a single timestamp to use for both metric snapshot inserts in this batch
        captured_at = datetime.now(timezone.utc)
        engagement_rate = calculate_engagement_rate(trailer["views"], trailer["likes"], trailer["comment_count"])
        
        # insert trailers into movie table, ytChannel table, ytVideo table, movieYtVideos table, ytVideoMetricSnapshots table, and movieMetricSnapshots table
        try:
            with conn.cursor() as cur:
                movie_id = insert_movie(cur, studio_id, movie_name, published_at)
                insert_yt_channel(cur, trailer["channel_id"], trailer["channel_title"], None)
                insert_yt_video(
                    cur,
                    videoid=trailer["video_id"],
                    channelid=trailer["channel_id"],
                    title=trailer["title"],
                    description=trailer["description"],
                    publishedat=trailer["published_at_full"],
                    movieid=movie_id,
                    videorole="official_trailer",
                )
                # insert_movie_yt_video(cur, movie_id, trailer["video_id"], 'official_trailer', is_primary=True)
                # insert_yt_video_metric_snapshot(
                #     cur,
                #     videoid=trailer["video_id"],
                #     capturedat=captured_at,
                #     viewcount=trailer["views"],
                #     likecount=trailer["likes"],
                #     commentcount=trailer["comment_count"],
                # )
                insert_movie_metric_snapshot(
                    cur,
                    movieid=movie_id,
                    capturedat=captured_at,
                    viewstotal=trailer["views"],
                    likestotal=trailer["likes"],
                    commentstotal=trailer["comment_count"],
                    engagementrate=engagement_rate,
                )

            conn.commit()
            print(f"  Inserted movie: {movie_name} (movieId: {movie_id})")
            movie_ids.append((movie_id, movie_name))

        except Exception as e:
            conn.rollback()
            print(f"  Error inserting movie {movie_name}: {e}")
            continue
        
        # insert review video transcript using Groq and save to ytvideotranscripts table
        video_url = f"https://www.youtube.com/watch?v={trailer['video_id']}"
        try:
            with conn.cursor() as cur:
                transcript_id = transcribe_and_insert(cur, trailer["video_id"], video_url)
            conn.commit()
            if transcript_id:
                print(f"  Saved transcript for {trailer['title']}")
        except Exception as e:
            conn.rollback()
            print(f"  Error saving transcript: {e}")

        # Fetch trailer comments (relevance + recent, deduplicated)
        trailer_comments = get_video_comments(trailer["video_id"], order="relevance", max_results=100)
        recent = get_video_comments(trailer["video_id"], order="time", max_results=50)
        seen_ids = {c["comment_id"] for c in trailer_comments}
        for c in recent:
            if c["comment_id"] not in seen_ids:
                trailer_comments.append(c)

        # insert trailer comments into ytCommentThreads and ytComments tables
        if trailer_comments:
            try:
                with conn.cursor() as cur:
                    for comment in trailer_comments:
                        insert_yt_comment_thread(
                            cur, comment["thread_id"], trailer["video_id"], comment["total_reply_count"]
                        )
                        insert_yt_comment(
                            cur,
                            commentid=comment["comment_id"],
                            videoid=trailer["video_id"],
                            threadid=comment["thread_id"],
                            parentcommentid=None,
                            text=comment["text"],
                            likecount=comment["likes"],
                            authorchannelid=comment["author_channel_id"],
                            publishedat=comment["published_at"],
                            updatedat=comment["updated_at"],
                            ingestedat=datetime.now(timezone.utc),
                        )
                conn.commit()
                print(f"  Saved {len(trailer_comments)} trailer comments for {movie_name}")
            except Exception as e:
                conn.rollback()
                print(f"  Error saving trailer comments: {e}")

    return movie_ids

# PHASE 2: for each movie, find and insert 5 top review videos + comments

def phase2_insert_reviews(movie_id, movie_name, studio_channel_id):
    print(f"\n{'='*60}")
    print(f"PHASE 2: Finding reviews for {movie_name}")
    print(f"{'='*60}")

    # Step 1: collect candidate video IDs from multiple search query templates
    candidate_ids = []
    seen = set()
    for template in REVIEW_QUERY_TEMPLATES:
        query = template.format(title=f"'{movie_name}'")
        result = youtube_object.search().list(
            q=query,
            part="id,snippet",
            type="video",
            maxResults=10
        ).execute()
        use_quota(100, f"search.list (reviews: {query})")
        for item in result.get("items", []):
            vid = item["id"]["videoId"]
            if vid not in seen:
                seen.add(vid)
                candidate_ids.append(vid)

    if not candidate_ids:
        print(f"  No review candidates found for {movie_name}")
        return

    # Step 2: fetch full details for all candidates in batches of 50
    all_records = []
    for i in range(0, len(candidate_ids), 50):
        batch = candidate_ids[i:i + 50]
        result = youtube_object.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(batch)
        ).execute()
        use_quota(1, f"videos.list (review candidates batch {i//50 + 1})")
        for item in result.get("items", []):
            sn = item["snippet"]
            st = item["statistics"]
            cd = item["contentDetails"]
            duration = iso8601_duration_to_seconds(cd.get("duration"))
            all_records.append({
                "video_id": item["id"],
                "channel_id": sn["channelId"],
                "channel_title": sn.get("channelTitle", ""),
                "title": sn.get("title", ""),
                "description": sn.get("description", ""),
                "published_at": sn.get("publishedAt"),
                "duration_seconds": duration,
                "views": int(st.get("viewCount", 0)),
                "likes": int(st["likeCount"]) if "likeCount" in st else None,
                "comment_count": int(st.get("commentCount", 0)),
                "tags": sn.get("tags"),
                "category_id": sn.get("categoryId"),
                "default_language": sn.get("defaultLanguage"),
                "caption": cd.get("caption") == "true",
            })

    # Step 3: filter out studio channel + Shorts, sort by views, pick top 5 unique channels --> changing this to 3 b/c of limit
    filtered = [
        r for r in all_records
        if r["channel_id"] != studio_channel_id
        and (r["duration_seconds"] or 0) >= MIN_REVIEW_DURATION_SECONDS
    ]
    filtered.sort(key=lambda r: r["views"], reverse=True)

    selected = []
    used_channels = set()
    for r in filtered:
        if r["channel_id"] in used_channels:
            continue
        selected.append(r)
        used_channels.add(r["channel_id"])
        if len(selected) >= 3: # changing this to 3 
            break

    print(f"  Selected {len(selected)} reviews from unique channels")

    # Step 4: insert review videos + comments into db
    total_views = total_likes = total_comments = 0
    captured_at = datetime.now(timezone.utc)

    for r in selected:
        print(f"\n  Review: {r['title']} ({r['views']:,} views)")

        # insert review video into ytChannel table, ytVideo table, ytVideoMetricSnapshots table 
        try:
            with conn.cursor() as cur:
                insert_yt_channel(cur, r["channel_id"], r["channel_title"], None)
                insert_yt_video(
                    cur,
                    videoid=r["video_id"],
                    channelid=r["channel_id"],
                    title=r["title"],
                    description=r["description"],
                    publishedat=r["published_at"],
                    movieid=movie_id,       
                    videorole="review",
                    durationseconds=r["duration_seconds"],
                    categoryid=r["category_id"],
                    defaultlanguage=r["default_language"],
                    tags=r["tags"],
                    caption=r["caption"],
                )
                insert_yt_video_metric_snapshot(
                    cur,
                    videoid=r["video_id"],
                    capturedat=captured_at,
                    viewcount=r["views"],
                    likecount=r["likes"],
                    commentcount=r["comment_count"],
                )
                
            conn.commit()
            
            # insert review video transcript using Groq and save to ytvideotranscripts table
            video_url = f"https://www.youtube.com/watch?v={r['video_id']}"
            try:
                with conn.cursor() as cur:
                    transcript_id = transcribe_and_insert(cur, r["video_id"], video_url)
                conn.commit()
                if transcript_id:
                    print(f"  Saved transcript for {r['title']}")
            except Exception as e:
                conn.rollback()
                print(f"  Error saving transcript: {e}")

            total_views += r["views"]
            total_likes += (r["likes"] or 0)
            total_comments += r["comment_count"]

        except Exception as e:
            conn.rollback()
            print(f"  Error inserting review {r['video_id']}: {e}")
            continue

        # Fetch and insert top comments -> by relevance + most recent, deduplicate
        comments = get_video_comments(r["video_id"], order="relevance", max_results=100)
        recent = get_video_comments(r["video_id"], order="time", max_results=50)
        seen_ids = {c["comment_id"] for c in comments}
        for c in recent:
            if c["comment_id"] not in seen_ids:
                comments.append(c)

        # insert review comments into ytCommentThreads and ytComments tables
        if comments:
            try:
                with conn.cursor() as cur:
                    for comment in comments:
                        insert_yt_comment_thread(
                            cur, comment["thread_id"], r["video_id"], comment["total_reply_count"]
                        )
                        insert_yt_comment(
                            cur,
                            commentid=comment["comment_id"],
                            videoid=r["video_id"],
                            threadid=comment["thread_id"],
                            parentcommentid=None,
                            text=comment["text"],
                            likecount=comment["likes"],
                            authorchannelid=comment["author_channel_id"],
                            publishedat=comment["published_at"],
                            updatedat=comment["updated_at"],
                            ingestedat=datetime.now(timezone.utc),
                        )
                conn.commit()
                print(f"  Saved {len(comments)} comments")
            except Exception as e:
                conn.rollback()
                print(f"  Error saving comments: {e}")

        time.sleep(1)

    # Save aggregate movie metric snapshot for reviews
    try:
        with conn.cursor() as cur:
            insert_movie_metric_snapshot(
                cur,
                movieid=movie_id,
                capturedat=captured_at,
                viewstotal=total_views,
                likestotal=total_likes,
                commentstotal=total_comments,
                engagementrate=None,
            )
        conn.commit()
        print(f"\n  Saved movie metric snapshot for {movie_name}")
    except Exception as e:
        conn.rollback()
        print(f"  Error saving movie metric snapshot: {e}")


# RUNNING PIPELINE

# main pipeline function to run all phases end-to-end for a list of studios -> latest 5 trailers + top 5 reviews & comments for each trailer
def run_pipeline(studio):
    global quota_used

    if quota_used >= QUOTA_LIMIT:
        print(f"\nQuota limit reached ({quota_used} units). Stopping pipeline.")
        return

    studio_id = studio["id"]
    studio_name = studio["name"]

    try:
        # Phase 0: find official YouTube channel
        official_channel_id = phase0_insert_studio_channels(studio_id, studio_name)
        if not official_channel_id:
            print(f"Skipping {studio_name} — no channel found")
            return

        # Get latest 5 released trailers from channel uploads (quota-efficient)
        print("\n  Fetching latest trailers from channel uploads...")
        trailers = get_latest_trailers_from_channel(official_channel_id, limit=5)
        if not trailers:
            print(f"Skipping {studio_name} — no released trailers found on channel")
            return

        print(f"\n  Found {len(trailers)} trailers for {studio_name}:")
        for t in trailers:
            print(f"    - {t['movie_title']} ({t['published_at']}) | {t['views']:,} views")

        # Phase 1: insert movies + trailers into DB
        movie_ids = phase1_insert_movies(studio_id, studio_name, trailers)

        # Phase 2: for each movie, find and insert review videos + comments
        for movie_id, movie_name in movie_ids:
            phase2_insert_reviews(movie_id, movie_name, official_channel_id)
            time.sleep(2)

    except RuntimeError as e:
        print(f"\n  STOPPED: {e}")

    print(f"\n{'='*60}")
    print(f"Pipeline complete. Total YouTube quota used: {quota_used} units")
    print(f"{'='*60}")


# MAIN: 

# main function to run the pipeline and test the transcription function with a sample YouTube video URL
if __name__ == "__main__":
    # studio = {"name": "Paramount Pictures", "id": "f5cfdff5-13a5-47a3-a7e9-51416f44ee33"}
    # studio = {"name": "Sony Pictures Entertainment", "id": "aa40a97c-fc5b-40cf-8b36-79719e630b93"}
    # studio = {"name": "A24", "id": "860c981b-4b3a-4e37-b7d9-560da40cfce4"}
    studio = {"name": "Marvel Studios", "id": "11111111-1111-1111-1111-111111111111"}
    run_pipeline(studio)

    # tests the transcription function with a sample YouTube video URL (replace with an actual trailer URL for real testing)
    # result = transcribe("https://www.youtube.com/watch?v=PVEi8KnD56o")
    # print(result)
