import psycopg2
import psycopg2.extras

conn = psycopg2.connect(
    host="localhost",
    database="youtubetestdb",
    user="zora",
    password=""
)

def insert_yt_channel(cursor, channel_id, channel_title, country):
    cursor.execute("""
        INSERT INTO ytChannels (channelId, channelTitle, country)
        VALUES (%s, %s, %s)
        ON CONFLICT (channelId) DO UPDATE SET
            channelTitle = EXCLUDED.channelTitle,
            updatedAt = now()
    """, (channel_id, channel_title, country))

def insert_yt_video(cursor, video_id, channel_id, title, description, published_at,
                     duration_seconds=None, category_id=None, default_language=None,
                     tags=None, caption=None):
    cursor.execute("""
        INSERT INTO ytVideos (videoId, channelId, title, description, publishedAt,
                              durationSeconds, categoryId, defaultLanguage, tags, caption)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (videoId) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            updatedAt = now()
    """, (video_id, channel_id, title, description, published_at,
          duration_seconds, category_id, default_language,
          psycopg2.extras.Json(tags) if tags else None, caption))

def insert_yt_video_metric_snapshot(cursor, video_id, view_count, like_count, comment_count):
    cursor.execute("""
        INSERT INTO ytVideoMetricSnapshots (videoId, capturedAt, viewCount, likeCount, commentCount)
        VALUES (%s, now(), %s, %s, %s)
        ON CONFLICT (videoId, capturedAt) DO NOTHING
    """, (video_id, view_count, like_count, comment_count))

def insert_yt_comment_thread(cursor, thread_id, video_id, total_reply_count=0):
    cursor.execute("""
        INSERT INTO ytCommentThreads (threadId, videoId, totalReplyCount, lastFetchedAt)
        VALUES (%s, %s, %s, now())
        ON CONFLICT (threadId) DO UPDATE SET
            totalReplyCount = EXCLUDED.totalReplyCount,
            lastFetchedAt = now()
    """, (thread_id, video_id, total_reply_count))

def insert_yt_comment(cursor, comment_id, video_id, thread_id, text, like_count,
                       author_channel_id, published_at, updated_at, parent_comment_id=None):
    cursor.execute("""
        INSERT INTO ytComments (commentId, videoId, threadId, parentCommentId, text,
                                likeCount, authorChannelId, publishedAt, updatedAt)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (commentId) DO NOTHING
    """, (comment_id, video_id, thread_id, parent_comment_id, text,
          like_count, author_channel_id, published_at, updated_at))

def insert_movie(cursor, studio_id, title, release_date=None):
    cursor.execute("""
        INSERT INTO movies (studioId, title, releaseDate, status)
        VALUES (%s, %s, %s, 'active')
        ON CONFLICT (studioId, title) DO UPDATE SET updatedAt = now()
        RETURNING movieId
    """, (studio_id, title, release_date))
    return cursor.fetchone()[0]

def insert_movie_yt_video(cursor, movie_id, video_id, video_role='official_trailer', is_primary=False):
    cursor.execute("""
        INSERT INTO movieYtVideos (movieId, videoId, videoRole, isPrimary)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (movieId, videoId) DO NOTHING
    """, (movie_id, video_id, video_role, is_primary))

def insert_movie_metric_snapshot(cursor, movie_id, views_total, likes_total, comments_total):
    cursor.execute("""
        INSERT INTO movieMetricSnapshots (movieId, capturedAt, viewsTotal, likesTotal, commentsTotal)
        VALUES (%s, now(), %s, %s, %s)
        ON CONFLICT (movieId, capturedAt) DO NOTHING
    """, (movie_id, views_total, likes_total, comments_total))