# general imports
import re
import time
from googleapiclient.discovery import build
from datetime import datetime, timezone, timedelta

# imports for transcript extraction
from groq import Groq
import subprocess
import tempfile
import math

# imports for TMDB API
import requests

# imports for DB operations
from app.db_operationstest import (
    get_conn,
    insert_yt_channel,
    insert_yt_video,
    insert_yt_video_metric_snapshot,
    insert_yt_comment_thread,
    insert_yt_comment,
    insert_movie,
    insert_movie_metric_snapshot,
    insert_transcript,
    insert_movie_poster,
    insert_movie_rating
)

# imports for environment variables
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# keys (loaded from env, not used at import time)
DEVELOPER_KEY1 = os.getenv("YOUTUBE_API_KEY_1")
DEVELOPER_KEY2 = os.getenv("YOUTUBE_API_KEY_2")
DEVELOPER_KEY3 = os.getenv("YOUTUBE_API_KEY_3")
GROQ_TRANSCRIPT_API_KEY = os.getenv("GROQ_TRANSCRIPT_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# clients are created on demand, not at import time
def get_youtube_client():
    return build("youtube", "v3", developerKey=DEVELOPER_KEY2)

def get_groq_client():
    return Groq(api_key=GROQ_TRANSCRIPT_API_KEY)

TRAILER_KEYWORDS = ["official trailer", "trailer", "official teaser", "teaser"]
QUOTA_LIMIT = 9000  # hard stop before hitting YouTube's 10,000 daily limit
quota_used = 0      # global quota tracker

REVIEW_QUERY_TEMPLATES = [
    "{title} movie review",
    "{title} review",
    "{title} film review",
]
MIN_REVIEW_DURATION_SECONDS = 180  # filter out Shorts (< 3 minutes)

# TRACKING/CALCULATING/FILTERING FUNCTIONS:

def use_quota(units, reason=""):
    global quota_used
    quota_used += units
    print(f"  [Quota: +{units} ({reason}) → total: {quota_used}/{QUOTA_LIMIT}]")
    if quota_used >= QUOTA_LIMIT:
        raise RuntimeError(f"Daily YouTube quota limit reached ({quota_used} units). Stopping.")

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

def calculate_engagement_rate(views, likes, comments):
    likes = likes or 0
    comments = comments or 0
    return (likes + comments) / views if views and views > 0 else 0.0

def normalize_title(video_title):
    t = video_title.strip()
    TRAILER_SIGNALS = [
        "official trailer", "official teaser trailer", "teaser trailer", "trailer"
    ]
    for sep in ["|", "–", "-", ":"]:
        if sep in t:
            parts = [p.strip() for p in t.split(sep, 1)]
            if len(parts) == 2:
                left, right = parts[0], parts[1].lower()
                if any(sig in right for sig in TRAILER_SIGNALS):
                    candidate = re.sub(r"\s*\(\d{4}\)\s*$", "", left).strip()
                    return candidate if len(candidate) > 1 else None
    for phrase in ["trailer for ", "teaser for "]:
        if phrase in t.lower():
            idx = t.lower().find(phrase) + len(phrase)
            candidate = re.split(r'[,.\!]', t[idx:])[0].strip()
            return candidate if len(candidate) > 1 else None
    t_lower = t.lower()
    for signal in TRAILER_SIGNALS:
        if signal in t_lower:
            idx = t_lower.find(signal)
            candidate = t[:idx].strip()
            candidate = re.sub(r"[\!\?\:\-]$", "", candidate).strip()
            candidate = re.sub(r"\s*\(\d{4}\)\s*$", "", candidate).strip()
            if len(candidate) > 1:
                return candidate
    return None

def get_movie_release_date(movie_title):
    response = requests.get(
        "https://api.themoviedb.org/3/search/movie",
        params={"api_key": TMDB_API_KEY, "query": movie_title}
    ).json()
    results = response.get("results", [])
    if not results:
        return None
    release_date = results[0].get("release_date")
    return release_date if release_date else None

def get_tmdb_canonical_title(movie_title):
    try:
        response = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"api_key": TMDB_API_KEY, "query": movie_title}
        ).json()
        results = response.get("results", [])
        if results:
            return results[0].get("title", movie_title)
    except Exception as e:
        print(f"  Could not fetch TMDB title for '{movie_title}': {e}")
    return movie_title

# TRANSCRIBE FUNCTIONS:

GROQ_MAX_FILE_MB = 24
GROQ_MAX_SECONDS = 10 * 60
TRANSCRIBE_SLEEP = 30

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

def trim_audio_if_needed(path, max_seconds=GROQ_MAX_SECONDS):
    duration = get_audio_duration_seconds(path)
    if duration is None or duration <= max_seconds:
        return path
    print(f"  Audio is {duration:.0f}s — trimming to {max_seconds}s...")
    trimmed_path = path.replace(".mp3", "_trimmed.mp3")
    subprocess.run([
        "ffmpeg", "-y", "-i", path, "-t", str(max_seconds), "-acodec", "copy", trimmed_path
    ], check=True, capture_output=True)
    os.unlink(path)
    return trimmed_path

def transcribe_with_groq_whisper(video_url):
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, "audio.mp3")
    try:
        subprocess.run([
            "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "3",
            "-o", tmp_path, video_url
        ], check=True)
        tmp_path = trim_audio_if_needed(tmp_path)
        file_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        print(f"  Sending {file_mb:.1f}MB to Whisper...")
        client = get_groq_client()
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

def transcribe_and_insert(cursor, videoid, video_url):
    try:
        fulltext = transcribe_with_groq_whisper(video_url)
        insert_transcript(cursor, videoid=videoid, language="en", source="auto", fulltext=fulltext)
        print(f"  Transcribed and saved: {videoid}")
        time.sleep(TRANSCRIBE_SLEEP)
    except Exception as e:
        error_str = str(e)
        if "429" in error_str and "Please try again in" in error_str:
            wait = _parse_retry_wait(error_str)
            print(f"  Rate limited — waiting {wait}s then retrying...")
            time.sleep(wait + 5)
            try:
                fulltext = transcribe_with_groq_whisper(video_url)
                insert_transcript(cursor, videoid=videoid, language="en", source="auto", fulltext=fulltext)
                print(f"  Transcribed and saved on retry: {videoid}")
            except Exception as e2:
                print(f"  Failed on retry: {e2}")
        else:
            print(f"  Error transcribing {video_url}: {e}")

def _parse_retry_wait(error_str):
    m = re.search(r"(\d+)m([\d.]+)s", error_str)
    if m:
        return math.ceil(int(m.group(1)) * 60 + float(m.group(2)))
    m = re.search(r"in ([\d.]+)s", error_str)
    if m:
        return math.ceil(float(m.group(1)))
    return 240

# YOUTUBE API DATA FUNCTIONS:

def get_video_statistics(video_id):
    youtube = get_youtube_client()
    try:
        result = youtube.videos().list(
            part="snippet,statistics,contentDetails", id=video_id
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

def get_video_comments(video_id, order="relevance", max_results=100):
    youtube = get_youtube_client()
    try:
        result = youtube.commentThreads().list(
            part="snippet", videoId=video_id, order=order,
            maxResults=max_results, textFormat="plainText"
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

def get_uploads_playlist_id(channel_id):
    youtube = get_youtube_client()
    result = youtube.channels().list(part="contentDetails", id=channel_id).execute()
    use_quota(1, "channels.list (uploads playlist)")
    items = result.get("items", [])
    if not items:
        raise RuntimeError(f"Channel not found: {channel_id}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

def get_latest_trailers_from_channel(channel_id, limit=6, max_scan=200):
    youtube = get_youtube_client()
    print(f"  Searching for trailers on channel {channel_id}...")
    one_year_ago = (datetime.now() - timedelta(days=365)).isoformat() + "Z"
    candidate_ids = []
    seen = set()
    for order in ["date", "relevance"]:
        result = youtube.search().list(
            q="official trailer", part="id,snippet", type="video",
            channelId=channel_id, maxResults=25, order=order, publishedAfter=one_year_ago
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
    result = youtube.videos().list(
        part="snippet,statistics,contentDetails", id=",".join(candidate_ids)
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
        release_year = int(release_date.split("-")[0])
        if release_year < 2024:
            print(f"  Skipping '{movie_title}' — too old (Released {release_date})")
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
    youtube = get_youtube_client()
    print(f"\n{'='*60}")
    print(f"PHASE 0: Finding official channel for {studio_name}")
    print(f"{'='*60}")

    search = youtube.search().list(
        q=studio_name, part="id, snippet", type="channel", maxResults=1
    ).execute()
    use_quota(100, f"search.list (channel: {studio_name})")

    items = search.get("items", [])
    if not items:
        print(f"  No channel found for {studio_name}")
        return None

    item = items[0]
    channel_id = item["id"]["channelId"]
    channel_title = item["snippet"]["channelTitle"]

    channel_details = youtube.channels().list(part="snippet", id=channel_id).execute()
    use_quota(1, "channels.list (country)")

    country = None
    if channel_details["items"]:
        country = channel_details["items"][0]["snippet"].get("country")

    print(f"  Found channel: {channel_title} (ID: {channel_id})")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            insert_yt_channel(cur, channel_id, channel_title, country)
        conn.commit()
        print(f"  Inserted channel: {channel_title}")
    except Exception as e:
        conn.rollback()
        print(f"  Error inserting channel: {e}")
        return None
    finally:
        conn.close()

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
        movie_name = get_tmdb_canonical_title(movie_name)
        print(f"\n  Inserting: {movie_name} ({published_at})")

        captured_at = datetime.now(timezone.utc)
        engagement_rate = calculate_engagement_rate(trailer["views"], trailer["likes"], trailer["comment_count"])

        # Insert movie + trailer metadata
        movie_id = None
        conn = get_conn()
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
        finally:
            conn.close()

        # Transcribe trailer
        video_url = f"https://www.youtube.com/watch?v={trailer['video_id']}"
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                transcribe_and_insert(cur, trailer["video_id"], video_url)
            conn.commit()
            print(f"  Saved transcript for {trailer['title']}")
        except Exception as e:
            conn.rollback()
            print(f"  Error saving transcript: {e}")
        finally:
            conn.close()

        # Fetch trailer comments
        trailer_comments = get_video_comments(trailer["video_id"], order="relevance", max_results=100)
        recent = get_video_comments(trailer["video_id"], order="time", max_results=50)
        seen_ids = {c["comment_id"] for c in trailer_comments}
        for c in recent:
            if c["comment_id"] not in seen_ids:
                trailer_comments.append(c)

        # Insert trailer comments
        if trailer_comments:
            conn = get_conn()
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
            finally:
                conn.close()

    return movie_ids


# PHASE 2: for each movie, find and insert top review videos + comments

def phase2_insert_reviews(movie_id, movie_name, studio_channel_id):
    youtube = get_youtube_client()
    print(f"\n{'='*60}")
    print(f"PHASE 2: Finding reviews for {movie_name}")
    print(f"{'='*60}")

    # Step 1: collect candidate video IDs
    candidate_ids = []
    seen = set()
    for template in REVIEW_QUERY_TEMPLATES:
        query = template.format(title=f"'{movie_name}'")
        result = youtube.search().list(
            q=query, part="id,snippet", type="video", maxResults=10
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

    # Step 2: fetch full details in batches of 50
    all_records = []
    for i in range(0, len(candidate_ids), 50):
        batch = candidate_ids[i:i + 50]
        result = youtube.videos().list(
            part="snippet,statistics,contentDetails", id=",".join(batch)
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

    # Step 3: filter + sort + pick top 3 from unique channels
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
        if len(selected) >= 3:
            break

    print(f"  Selected {len(selected)} reviews from unique channels")

    total_views = total_likes = total_comments = 0
    captured_at = datetime.now(timezone.utc)

    for r in selected:
        print(f"\n  Review: {r['title']} ({r['views']:,} views)")

        # Insert review video metadata
        conn = get_conn()
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
            total_views += r["views"]
            total_likes += (r["likes"] or 0)
            total_comments += r["comment_count"]
        except Exception as e:
            conn.rollback()
            print(f"  Error inserting review {r['video_id']}: {e}")
            continue
        finally:
            conn.close()

        # Transcribe review
        video_url = f"https://www.youtube.com/watch?v={r['video_id']}"
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                transcribe_and_insert(cur, r["video_id"], video_url)
            conn.commit()
            print(f"  Saved transcript for {r['title']}")
        except Exception as e:
            conn.rollback()
            print(f"  Error saving transcript: {e}")
        finally:
            conn.close()

        # Fetch and insert review comments
        comments = get_video_comments(r["video_id"], order="relevance", max_results=100)
        recent = get_video_comments(r["video_id"], order="time", max_results=50)
        seen_ids = {c["comment_id"] for c in comments}
        for c in recent:
            if c["comment_id"] not in seen_ids:
                comments.append(c)

        if comments:
            conn = get_conn()
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
            finally:
                conn.close()

        time.sleep(1)

    # Save aggregate movie metric snapshot for reviews
    conn = get_conn()
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
    finally:
        conn.close()


# PHASE 3: for each movie, find the poster using TMDB API call

def phase3_insert_posters(movie_id, movie_name):
    print(f"\n{'='*60}")
    print(f"PHASE 3: Finding poster for {movie_name}")
    print(f"{'='*60}")

    try:
        response = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"api_key": TMDB_API_KEY, "query": movie_name}
        ).json()

        results = response.get("results", [])
        if not results:
            print(f"  No TMDB entry found for {movie_name}")
            return

        poster_path = results[0].get("poster_path")
        if not poster_path:
            print(f"  No poster found on TMDB for {movie_name}")
            return

        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                insert_movie_poster(cur, movie_id, poster_url)
            conn.commit()
            print(f"  Saved poster for {movie_name}")
        except Exception as e:
            conn.rollback()
            print(f"  Error saving poster: {e}")
        finally:
            conn.close()

    except Exception as e:
        print(f"  Error fetching poster from TMDB: {e}")


# PHASE 4: for each movie, find the movie rating using TMDB API call

def phase4_insert_ratings(movie_id, movie_name):
    print(f"\n{'='*60}")
    print(f"PHASE 4: Finding rating for {movie_name}")
    print(f"{'='*60}")

    try:
        response = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"api_key": TMDB_API_KEY, "query": movie_name}
        ).json()

        results = response.get("results", [])
        if not results:
            print(f"  No TMDB entry found for {movie_name}")
            return

        rating = results[0].get("vote_average")
        if rating is None:
            print(f"  No rating found on TMDB for {movie_name}")
            return

        conn = get_conn()
        try:
            with conn.cursor() as cur:
                insert_movie_rating(cur, movie_id, rating)
            conn.commit()
            print(f"  Saved rating {rating} for {movie_name}")
        except Exception as e:
            conn.rollback()
            print(f"  Error saving rating: {e}")
        finally:
            conn.close()

    except Exception as e:
        print(f"  Error fetching rating from TMDB: {e}")


# RUNNING PIPELINE

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

        # Get latest trailers from channel
        print("\n  Fetching latest trailers from channel uploads...")
        trailers = get_latest_trailers_from_channel(official_channel_id, limit=6)
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

        # Phase 3: for each movie, find the poster
        for movie_id, movie_name in movie_ids:
            phase3_insert_posters(movie_id, movie_name)
            time.sleep(2)

        # Phase 4: for each movie, find the rating
        for movie_id, movie_name in movie_ids:
            phase4_insert_ratings(movie_id, movie_name)
            time.sleep(2)

    except RuntimeError as e:
        print(f"\n  STOPPED: {e}")

    print(f"\n{'='*60}")
    print(f"Pipeline complete. Total YouTube quota used: {quota_used} units")
    print(f"{'='*60}")


def update_all_ratings():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT movieid, title FROM movies")
            movies = cur.fetchall()
    finally:
        conn.close()

    print(f"Found {len(movies)} movies to update")
    for movie_id, movie_name in movies:
        phase4_insert_ratings(movie_id, movie_name)


def run_pipeline_for_studio(studio_id: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM studios WHERE studioid = %s", (studio_id,))
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        raise ValueError(f"Studio not found: {studio_id}")

    studio = {"id": studio_id, "name": row[0]}
    run_pipeline(studio)


# MAIN:
if __name__ == "__main__":
    # studio = {"name": "Marvel Studios", "id": "11111111-1111-1111-1111-111111111111"}
    # studio = {"name": "A24", "id": "860c981b-4b3a-4e37-b7d9-560da40cfce4"}
    # studio = {"name": "Lionsgate Films", "id": "170a1803-718f-4166-93c8-839d6442438c"}
    # studio = {"name": "Universal Pictures", "id": "9fe4726b-fdb3-4640-8066-fbf067e503ce"}
    # studio = {"name": "Sony Pictures Entertainment", "id": "6233e3e4-8bcd-4ca0-adac-1fcc3f6ff623"}
    studio = {"name": "Warner Bros. Pictures", "id": "c9e36e96-5295-4724-8825-9a2db92636e9"}

    run_pipeline(studio)