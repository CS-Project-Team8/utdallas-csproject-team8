# general imports
import re
import time
from googleapiclient.discovery import build
import json

# imports for Gemini 3 Flash
from google import genai
from google.genai import types

# imports for TMDB API
import requests
from datetime import datetime, timedelta

# imports for environment variables
from dotenv import load_dotenv
import os
from pathlib import Path

# imports for DB operations
from testdb_operations import (
    conn,
    insert_yt_channel,
    insert_yt_video,
    insert_yt_video_metric_snapshot,
    insert_yt_comment_thread,
    insert_yt_comment,
    insert_movie,
    insert_movie_yt_video,
    insert_movie_metric_snapshot
)

# keys and client setup
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

DEVELOPER_KEY1 = os.getenv("YOUTUBE_API_KEY_1")
DEVELOPER_KEY2 = os.getenv("YOUTUBE_API_KEY_2")
DEVELOPER_KEY3 = os.getenv("YOUTUBE_API_KEY_3")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY")
TMDB_API_KEY    = os.getenv("TMDB_API_KEY")

youtube_object = build("youtube", "v3", developerKey=DEVELOPER_KEY1)
client = genai.Client(api_key=GEMINI_API_KEY)

TRAILER_KEYWORDS = ["official trailer", "trailer", "official teaser", "teaser"]
QUOTA_LIMIT = 9000  # hard stop before hitting YouTube's 10,000 daily limit
quota_used = 0      # global quota tracker

REVIEW_QUERY_TEMPLATES = [
    "{title} movie review",
    "{title} review",
    "{title} film review",
]
MIN_REVIEW_DURATION_SECONDS = 180  # filter out Shorts (< 3 minutes)


# ---------------------------------------------------------------------------
# Quota tracking
# ---------------------------------------------------------------------------

def use_quota(units, reason=""):
    global quota_used
    quota_used += units
    print(f"  [Quota: +{units} ({reason}) → total: {quota_used}/{QUOTA_LIMIT}]")
    if quota_used >= QUOTA_LIMIT:
        raise RuntimeError(f"Daily YouTube quota limit reached ({quota_used} units). Stopping.")


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def iso8601_duration_to_seconds(d):
    """Parse ISO 8601 duration like PT2M30S to seconds."""
    if not d or not d.startswith("PT"):
        return None
    h = m = s = 0
    mh = re.search(r"(\d+)H", d)
    mm = re.search(r"(\d+)M", d)
    ms = re.search(r"(\d+)S", d)
    if mh: h = int(mh.group(1))
    if mm: m = int(mm.group(1))
    if ms: s = int(ms.group(1))
    return h * 3600 + m * 60 + s


def normalize_title(video_title):
    """Extract movie name only from 'Movie Title | Official Trailer' format."""
    t = video_title.strip()

    if "|" not in t:
        return None

    parts = [p.strip() for p in t.split("|")]

    if len(parts) < 2 or not parts[1].lower().startswith("official trailer"):
        return None

    candidate = parts[0]
    # Remove year in parentheses like (2024)
    candidate = re.sub(r"\s*\(.*?\)\s*$", "", candidate).strip()

    return candidate if len(candidate) > 2 else None


def get_movie_release_date(movie_title):
    """Check TMDB for the movie's release date. Returns 'YYYY-MM-DD' or None."""
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


def transcribe(video_url):
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=types.Content(
            parts=[
                types.Part(
                    file_data=types.FileData(file_uri=video_url)
                ),
                types.Part(text="You are a video content analyst. Given the YouTube video link, extract and summarize the main opinions and points made by the creator. Focus on: overall sentiment, key points, and any conclusions or verdicts mentioned.")
            ]
        )
    )
    print(response.text)


# ---------------------------------------------------------------------------
# Phase 0: find & insert official studio YouTube channel
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Trailer discovery: uploads playlist approach (low quota cost)
# ---------------------------------------------------------------------------

def get_uploads_playlist_id(channel_id):
    """Get the uploads playlist ID for a channel (1 quota unit)."""
    result = youtube_object.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()
    use_quota(1, "channels.list (uploads playlist)")
    items = result.get("items", [])
    if not items:
        raise RuntimeError(f"Channel not found: {channel_id}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_latest_trailers_from_channel(channel_id, limit=5, max_scan=200):
    """
    Get the latest N released trailers from a studio's official YouTube channel uploads.
    Uses uploads playlist instead of search — much cheaper on quota.
    - playlistItems.list: 1 unit per page (vs 100 for search)
    - videos.list: 1 unit per 50 videos batch
    Filters out unreleased movies using TMDB release date.
    """
    print(f"  Fetching uploads playlist for channel {channel_id}...")
    playlist_id = get_uploads_playlist_id(channel_id)

    # Step 1: collect video IDs from uploads playlist
    video_ids = []
    page_token = None
    while len(video_ids) < max_scan:
        result = youtube_object.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=page_token
        ).execute()
        use_quota(1, "playlistItems.list")

        for item in result.get("items", []):
            vid = item["contentDetails"].get("videoId")
            if vid:
                video_ids.append(vid)
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    print(f"  Scanned {len(video_ids)} uploads, fetching details...")

    # Step 2: fetch video details in batches of 50
    trailers = []
    seen_titles = set()
    today = datetime.today().strftime("%Y-%m-%d")

    for i in range(0, len(video_ids), 50):
        if len(trailers) >= limit:
            break

        batch = video_ids[i:i + 50]
        result = youtube_object.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(batch)
        ).execute()
        use_quota(1, f"videos.list (batch {i//50 + 1})")

        for item in result.get("items", []):
            title = item["snippet"]["title"]
            movie_title = normalize_title(title)
            if not movie_title or movie_title in seen_titles:
                continue

            # Check TMDB for release date — skip unreleased movies
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

            if len(trailers) >= limit:
                break

    return trailers


# ---------------------------------------------------------------------------
# Phase 1: insert movies + trailers into DB
# ---------------------------------------------------------------------------

def phase1_insert_movies(studio_id, studio_name, trailers):
    print(f"\n{'='*60}")
    print(f"PHASE 1: Inserting movies for {studio_name}")
    print(f"{'='*60}")

    movie_ids = []

    for trailer in trailers:
        movie_name = trailer["movie_title"]
        published_at = trailer["published_at"]

        print(f"\n  Inserting: {movie_name} ({published_at})")

        # insert trailers into movie table, ytChannel table, ytVideo table,
        # movieYtVideos table, ytVideoMetricSnapshots table, and movieMetricSnapshots table
        try:
            with conn.cursor() as cur:
                movie_id = insert_movie(cur, studio_id, movie_name, published_at)
                insert_yt_channel(cur, trailer["channel_id"], trailer["channel_title"], None)
                insert_yt_video(
                    cur,
                    video_id=trailer["video_id"],
                    channel_id=trailer["channel_id"],
                    title=trailer["title"],
                    description=trailer["description"],
                    published_at=trailer["published_at_full"],
                )
                insert_movie_yt_video(cur, movie_id, trailer["video_id"], 'official_trailer', is_primary=True)
                insert_yt_video_metric_snapshot(cur, trailer["video_id"], trailer["views"], trailer["likes"], trailer["comment_count"])
                insert_movie_metric_snapshot(cur, movie_id, trailer["views"], trailer["likes"], trailer["comment_count"])

            conn.commit()
            print(f"  Inserted movie: {movie_name} (movieId: {movie_id})")
            movie_ids.append((movie_id, movie_name))

        except Exception as e:
            conn.rollback()
            print(f"  Error inserting movie {movie_name}: {e}")
            continue  # add continue so comment fetching is skipped on error too

        # Fetch trailer comments (relevance + recent, deduplicated)
        trailer_comments = get_video_comments(trailer["video_id"], order="relevance", max_results=100)
        recent = get_video_comments(trailer["video_id"], order="time", max_results=50)
        seen_ids = {c["comment_id"] for c in trailer_comments}
        for c in recent:
            if c["comment_id"] not in seen_ids:
                trailer_comments.append(c)

        if trailer_comments:
            try:
                with conn.cursor() as cur:
                    for comment in trailer_comments:
                        insert_yt_comment_thread(
                            cur, comment["thread_id"], trailer["video_id"], comment["total_reply_count"]
                        )
                        insert_yt_comment(
                            cur,
                            comment_id=comment["comment_id"],
                            video_id=trailer["video_id"],
                            thread_id=comment["thread_id"],
                            text=comment["text"],
                            like_count=comment["likes"],
                            author_channel_id=comment["author_channel_id"],
                            published_at=comment["published_at"],
                            updated_at=comment["updated_at"],
                        )
                conn.commit()
                print(f"  Saved {len(trailer_comments)} trailer comments for {movie_name}")
            except Exception as e:
                conn.rollback()
                print(f"  Error saving trailer comments: {e}")

    return movie_ids


# ---------------------------------------------------------------------------
# Phase 2: find reviews for each movie and insert into DB
# ---------------------------------------------------------------------------

def phase2_insert_reviews(movie_id, movie_name, studio_channel_id):
    print(f"\n{'='*60}")
    print(f"PHASE 2: Finding reviews for {movie_name}")
    print(f"{'='*60}")

    # Step 1: collect candidate video IDs from multiple search query templates
    candidate_ids = []
    seen = set()
    for template in REVIEW_QUERY_TEMPLATES:
        query = template.format(title=movie_name)
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

    # Step 3: filter out studio channel + Shorts, sort by views, pick top 5 unique channels
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
        if len(selected) >= 5:
            break

    print(f"  Selected {len(selected)} reviews from unique channels")

    # Step 4: insert review videos into ytChannel table, ytVideo table,
    # ytVideoMetricSnapshots table, movieYtVideos table,
    # ytCommentThreads table, and ytComments table
    total_views = total_likes = total_comments = 0

    for r in selected:
        print(f"\n  Review: {r['title']} ({r['views']:,} views)")

        try:
            with conn.cursor() as cur:
                insert_yt_channel(cur, r["channel_id"], r["channel_title"], None)
                insert_yt_video(
                    cur,
                    video_id=r["video_id"],
                    channel_id=r["channel_id"],
                    title=r["title"],
                    description=r["description"],
                    published_at=r["published_at"],
                    category_id=r["category_id"],
                    default_language=r["default_language"],
                    tags=r["tags"],
                    caption=r["caption"],
                )
                insert_yt_video_metric_snapshot(
                    cur, r["video_id"], r["views"], r["likes"], r["comment_count"]
                )
            conn.commit()

            total_views += r["views"]
            total_likes += (r["likes"] or 0)
            total_comments += r["comment_count"]

        except Exception as e:
            conn.rollback()
            print(f"  Error inserting review {r['video_id']}: {e}")
            continue

        # Fetch and insert comments
        # Get top comments by relevance + most recent, deduplicate
        comments = get_video_comments(r["video_id"], order="relevance", max_results=100)
        recent = get_video_comments(r["video_id"], order="time", max_results=50)
        seen_ids = {c["comment_id"] for c in comments}
        for c in recent:
            if c["comment_id"] not in seen_ids:
                comments.append(c)
                
        if comments:
            try:
                with conn.cursor() as cur:
                    for comment in comments:
                        insert_yt_comment_thread(
                            cur, comment["thread_id"], r["video_id"], comment["total_reply_count"]
                        )
                        insert_yt_comment(
                            cur,
                            comment_id=comment["comment_id"],
                            video_id=r["video_id"],
                            thread_id=comment["thread_id"],
                            text=comment["text"],
                            like_count=comment["likes"],
                            author_channel_id=comment["author_channel_id"],
                            published_at=comment["published_at"],
                            updated_at=comment["updated_at"],
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
            insert_movie_metric_snapshot(cur, movie_id, total_views, total_likes, total_comments)
        conn.commit()
        print(f"\n  Saved movie metric snapshot for {movie_name}")
    except Exception as e:
        conn.rollback()
        print(f"  Error saving movie metric snapshot: {e}")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(studios):
    global quota_used
    for studio in studios:
        if quota_used >= QUOTA_LIMIT:
            print(f"\nQuota limit reached ({quota_used} units). Stopping pipeline.")
            break

        studio_id = studio["id"]
        studio_name = studio["name"]

        try:
            # Phase 0: find official YouTube channel
            official_channel_id = phase0_insert_studio_channels(studio_id, studio_name)
            if not official_channel_id:
                print(f"Skipping {studio_name} — no channel found")
                continue

            # Get latest 5 released trailers from channel uploads (quota-efficient)
            print(f"\n  Fetching latest trailers from channel uploads...")
            trailers = get_latest_trailers_from_channel(official_channel_id, limit=5)
            if not trailers:
                print(f"Skipping {studio_name} — no released trailers found on channel")
                continue

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
            break

    print(f"\n{'='*60}")
    print(f"Pipeline complete. Total YouTube quota used: {quota_used} units")
    print(f"{'='*60}")


if __name__ == "__main__":
    studios = [
        # {"name": "Walt Disney Animation Studios", "id": "08bd686f-964d-4621-b7bf-190a154c7947"},
        # {"name": "Sony Pictures Entertainment",   "id": "8da2d831-7051-4831-8afc-3b6e2fa47ee8"},
        # {"name": "Warner Bros.",                   "id": "05864c87-4a02-4dee-ace9-7b1ca8b5b86d"},
        # {"name": "Universal Pictures",             "id": "156ac1c3-71f0-40e2-9a5f-0f1c7a4d96db"},
        {"name": "Paramount Pictures",             "id": "ae377009-5af5-4894-b6e7-f4269f29601c"},
    ]

    run_pipeline(studios)
    # transcribe("https://www.youtube.com/watch?v=tSx8ubSBFN8")
