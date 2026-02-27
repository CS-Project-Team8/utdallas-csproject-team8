from googleapiclient.discovery import build
from google import genai
from google.genai import types
import json 
import requests
from datetime import datetime, timedelta
import time
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

# DEVELOPER_KEY1 = "AIzaSyAsxHBbNUV36SfPDDdwTCVw2xObCuVKXLk"
# DEVELOPER_KEY2 = "AIzaSyCFm6rV8_2DG5UifjWkaeGKvBrDF7Z-EJQ"
DEVELOPER_KEY3 = "AIzaSyDDIfZvRrErbN2PzyilM-6QqzTUzVihoCE"

youtube_object = build("youtube", "v3", developerKey=DEVELOPER_KEY3)
client = genai.Client(api_key="AIzaSyDTnU1EHq6EIuM1e5Xx7rzMff24P_2nbkE")
TMDB_API_KEY = "0c6c85d148f2f66b937d2f8bfb1936a1"

def get_video_statistics(video_id):
    try:
        result = youtube_object.videos().list(
            part="snippet,statistics,contentDetails",
            id=video_id
        ).execute()
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


def get_video_comments(video_id, max_results=20):
    try:
        result = youtube_object.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=max_results,
            textFormat="plainText"
        ).execute()

        comments = []
        for item in result['items']:
            thread_id = item['id']
            top_comment = item['snippet']['topLevelComment']
            snippet = top_comment['snippet']
            comments.append({
                "comment_id": top_comment['id'],
                "thread_id": thread_id,
                "author": snippet["authorDisplayName"],
                "author_channel_id": snippet.get("authorChannelId", {}).get("value"),
                "text": snippet["textDisplay"],
                "likes": snippet["likeCount"],
                "published_at": snippet["publishedAt"],
                "updated_at": snippet["updatedAt"],
                "total_reply_count": item['snippet']['totalReplyCount']
            })
        return comments
    except Exception as e:
        print(f"Could not retrieve comments for {video_id}: {e}")
        return []


def extract_movie_name(title):
    for separator in ["|", "-", "–", ":"]:
        title = title.split(separator)[0]
    remove_words = ["Official Trailer", "Trailer", "Teaser", "Official", "HD", "4K", "2024", "2025"]
    for word in remove_words:
        title = title.replace(word, "")
    return title.strip()


# # Function to send video link to Gemini 3 Flash and get transcript summary/opinions
# def transcribe(video_url):
#     response = client.models.generate_content(
#         model="gemini-3-flash-preview",
#         contents=types.Content(
#             parts=[
#                 types.Part(
#                     file_data=types.FileData(file_uri=video_url)
#                 ),
#                 types.Part(text=f"You are a video content analyst. Given the YouTube video link, extract and summarize the main opinions and points made by the creator. Focus on: overall sentiment, key points, and any conclusions or verdicts mentioned."
#                 )
#             ]
#         )
#     )
#     print(response.text)

# ---------------------------------------------------------------
# PHASE 0: Find studio channels → insert ytChannels (I think we should consider adding another table: studioChannels))
# ---------------------------------------------------------------
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

    country = None
    if channel_details["items"]:
        country = channel_details["items"][0]["snippet"].get("country")  # may still be None if not set
    
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

def get_latest_movies_for_studio(studio_name, limit=5):
    print(f"\n  Searching TMDB for latest movies by {studio_name}")
    
    # Step 1: search for the company ID
    company_search = requests.get(
        "https://api.themoviedb.org/3/search/company",
        params={
            "api_key": TMDB_API_KEY,
            "query": studio_name
        }
    ).json()
    
    companies = company_search.get("results", [])
    if not companies:
        print(f"  No company found for {studio_name}")
        return []
    
    company_id = companies[0]["id"]
    company_name = companies[0]["name"]
    print(f"  Found company: {company_name} (ID: {company_id})")
    
    # Date range: movies released up to today, no earlier than 2 years ago
    today = datetime.today()
    one_month_ago = today - timedelta(days=30)
    two_years_ago = today - timedelta(days=730)
    
    # Step 2: get movies by company, sorted by most recent
    movies_response = requests.get(
        "https://api.themoviedb.org/3/discover/movie",
        params={
            "api_key": TMDB_API_KEY,
            "with_companies": company_id,
            "sort_by": "release_date.desc",
            "include_adult": False,
            "primary_release_date.lte": one_month_ago.strftime("%Y-%m-%d"),  # at least 1 month old
            "page": 1
        }
    ).json()
    
    movies = movies_response.get("results", [])
    if not movies:
        print(f"  No movies found for {studio_name}")
        return []
    
    latest_movies = []
    for movie in movies[:limit]:
        title = movie.get("title")
        release_date = movie.get("release_date", "")
        year = int(release_date[:4]) if release_date else None
        if title and year:
            latest_movies.append({"title": title, "year": year})
            print(f"  Found movie: {title} ({year})")
    
    return latest_movies


# ---------------------------------------------------------------
# PHASE 1: Find trailers → insert movies + movieYtVideos
# ---------------------------------------------------------------
def phase1_insert_movies(studio_id, studio_name, official_channel_id, latest_movies):
    print(f"\n{'='*60}")
    print(f"PHASE 1: Finding trailers for {studio_name}")
    print(f"{'='*60}")

    movie_ids = []

    for movie in latest_movies:
        movie_name = movie["title"]
        year = movie["year"]
        
        print(f"\n  Searching trailer for: {movie_name} ({year})")

        search = youtube_object.search().list(
            q=f'{movie_name} {year} official trailer',
            part="id, snippet",
            # channelId=official_channel_id,
            # order="viewCount",
            type="video",
            maxResults=1
        ).execute()

        items = search.get("items", [])
        if not items:
            print(f"  No trailer found for {movie_name}")
            continue

        item = items[0]
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        channel_id = item["snippet"]["channelId"]
        channel_title = item["snippet"]["channelTitle"]
        published_at = item["snippet"]["publishedAt"][:10]
        
        # Validate that the trailer title contains the movie name
        if movie_name.lower() not in title.lower():
            print(f"  Skipping (wrong movie): {title}")
            continue

        print(f"  Found trailer: {title}")

        try:
            with conn.cursor() as cur:
                movie_id = insert_movie(cur, studio_id, movie_name, published_at)
                insert_yt_channel(cur, channel_id, channel_title, None) 
                insert_yt_video(
                    cur,
                    video_id=video_id,
                    channel_id=channel_id,
                    title=title,
                    description=item["snippet"]["description"],
                    published_at=item["snippet"]["publishedAt"],
                )
                insert_movie_yt_video(cur, movie_id, video_id, 'official_trailer', is_primary=True)
                # stats = get_video_statistics(video_id)
                # if stats:
                #     insert_yt_video_metric_snapshot(
                #         cur, video_id, stats["views"], stats["likes"], stats["commentCount"]
                #     )

            conn.commit()
            print(f"  Inserted movie: {movie_name} (movieId: {movie_id})")
            movie_ids.append((movie_id, movie_name))

        except Exception as e:
            conn.rollback()
            print(f"  Error inserting movie {movie_name}: {e}")

    return movie_ids


# ---------------------------------------------------------------
# PHASE 2: For each movie → find reviews → insert YT data
# ---------------------------------------------------------------
def phase2_insert_reviews(movie_id, movie_name):
    print(f"\n{'='*60}")
    print(f"PHASE 2: Finding reviews for {movie_name}")
    print(f"{'='*60}")

    search = youtube_object.search().list(
        q=f"{movie_name} movie review",
        part="id, snippet",
        order="date",
        type="video",
        maxResults=5
    ).execute()

    total_views = 0
    total_likes = 0
    total_comments = 0

    for item in search.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        channel_id = item["snippet"]["channelId"]
        channel_title = item["snippet"]["channelTitle"]

        print(f"\n  Review: {title} (ID: {video_id})")

        stats = get_video_statistics(video_id)
        if not stats:
            continue

        try:
            with conn.cursor() as cur:
                insert_yt_channel(cur, channel_id, channel_title)

                insert_yt_video(
                    cur,
                    video_id=video_id,
                    channel_id=channel_id,
                    title=title,
                    description=stats["description"],
                    published_at=stats["publishedAt"],
                    category_id=stats["categoryId"],
                    default_language=stats["defaultLanguage"],
                    tags=stats["tags"],
                    caption=stats["caption"],
                )

                insert_yt_video_metric_snapshot(
                    cur, video_id, stats["views"], stats["likes"], stats["commentCount"]
                )

                insert_movie_yt_video(cur, movie_id, video_id, 'other', is_primary=False)

            conn.commit()

            total_views += stats["views"]
            total_likes += stats["likes"]
            total_comments += stats["commentCount"]

        except Exception as e:
            conn.rollback()
            print(f"  Error inserting review {video_id}: {e}")
            continue

        comments = get_video_comments(video_id, max_results=20)
        if comments:
            try:
                with conn.cursor() as cur:
                    for comment in comments:
                        insert_yt_comment_thread(
                            cur, comment["thread_id"], video_id, comment["total_reply_count"]
                        )
                        insert_yt_comment(
                            cur,
                            comment_id=comment["comment_id"],
                            video_id=video_id,
                            thread_id=comment["thread_id"],
                            text=comment["text"],
                            like_count=comment["likes"],
                            author_channel_id=comment["author_channel_id"],
                            published_at=comment["published_at"],
                            updated_at=comment["updated_at"],
                        )
                conn.commit()
                print(f"  Saved {len(comments)} comments for {title}")
            except Exception as e:
                conn.rollback()
                print(f"  Error saving comments: {e}")

        time.sleep(1)

    try:
        with conn.cursor() as cur:
            insert_movie_metric_snapshot(cur, movie_id, total_views, total_likes, total_comments)
        conn.commit()
        print(f"\n  Saved movie metric snapshot for {movie_name}")
    except Exception as e:
        conn.rollback()
        print(f"  Error saving movie metric snapshot: {e}")


# ---------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------
def run_pipeline(studios):
    for studio in studios:
        studio_id = studio["id"]
        studio_name = studio["name"]

        # Phase 0: find official YouTube channel
        official_channel_id = phase0_insert_studio_channels(studio_id, studio_name)
        if not official_channel_id:
            print(f"Skipping {studio_name} — no channel found")
            continue

        # Get latest 5 movies from IMDB
        latest_movies = get_latest_movies_for_studio(studio_name)
        if not latest_movies:
            print(f"Skipping {studio_name} — no movies found on IMDB")
            continue

        # Phase 1: insert movies from trailers
        movie_ids = phase1_insert_movies(studio_id, studio_name, official_channel_id, latest_movies)

        # # Phase 2: for each movie, insert review YT data
        # for movie_id, movie_name in movie_ids:
        #     phase2_insert_reviews(movie_id, movie_name)
        #     time.sleep(2)


if __name__ == "__main__":
    
    studios = [
        # {"name": "Walt Disney Animation Studios", "id": "08bd686f-964d-4621-b7bf-190a154c7947"},
        # {"name": "Sony Pictures Entertainment",   "id": "8da2d831-7051-4831-8afc-3b6e2fa47ee8"},
        # {"name": "Warner Bros.",                   "id": "05864c87-4a02-4dee-ace9-7b1ca8b5b86d"},
        # {"name": "Universal Pictures",             "id": "156ac1c3-71f0-40e2-9a5f-0f1c7a4d96db"},
        {"name": "Paramount Pictures",             "id": "ae377009-5af5-4894-b6e7-f4269f29601c"},
    ]

    run_pipeline(studios)