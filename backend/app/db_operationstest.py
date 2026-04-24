from anyio import Path
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def insert_yt_channel(cursor, channelid, channeltitle, country):
    cursor.execute("""
        INSERT INTO ytChannels (channelId, channelTitle, country)
        VALUES (%s, %s, %s)
        ON CONFLICT (channelId) DO UPDATE SET
            channelTitle = EXCLUDED.channelTitle,
            updatedAt = now()
    """, (channelid, channeltitle, country))


# update this to have movieid + videorole
def insert_yt_video(cursor, videoid, channelid, title, description, publishedat,
                    movieid=None, videorole=None,
                    durationseconds=None, categoryid=None, defaultlanguage=None,
                    tags=None, caption=None):
    cursor.execute("""
        INSERT INTO ytVideos (videoId, movieId, channelId, title, description, videoRole, publishedAt,
                              durationSeconds, categoryId, defaultLanguage, tags, caption)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (videoId) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            updatedAt = now()
    """, (videoid, movieid, channelid, title, description, videorole, publishedat,
          durationseconds, categoryid, defaultlanguage,
          psycopg2.extras.Json(tags) if tags else None, caption))


def insert_yt_video_metric_snapshot(cursor, videoid, capturedat, viewcount, likecount, commentcount):
    cursor.execute("""
        INSERT INTO ytVideoMetricSnapshots (videoId, capturedAt, viewCount, likeCount, commentCount)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (videoId, capturedAt) DO NOTHING
    """, (videoid, capturedat, viewcount, likecount, commentcount))


def insert_yt_comment_thread(cursor, threadid, videoid, totalreplycount):
    cursor.execute("""
        INSERT INTO ytCommentThreads (threadId, videoId, totalReplyCount, lastFetchedAt)
        VALUES (%s, %s, %s, now())
        ON CONFLICT (threadId) DO UPDATE SET
            totalReplyCount = EXCLUDED.totalReplyCount,
            lastFetchedAt = now()
    """, (threadid, videoid, totalreplycount))


def insert_yt_comment(cursor, commentid, videoid, threadid, parentcommentid, text, likecount,
                      authorchannelid, publishedat, updatedat, ingestedat):
    cursor.execute("""
        INSERT INTO ytComments (commentId, videoId, threadId, parentCommentId, text,
                                likeCount, authorChannelId, publishedAt, updatedAt, ingestedAt)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (commentId) DO NOTHING
    """, (commentid, videoid, threadid, parentcommentid, text,
          likecount, authorchannelid, publishedat, updatedat, ingestedat))


def insert_movie(cursor, studioid, title, releasedate=None):
    cursor.execute("""
        INSERT INTO movies (studioId, title, releaseDate, status)
        VALUES (%s, %s, %s, 'active')
        ON CONFLICT (studioId, title) DO UPDATE SET updatedAt = now()
        RETURNING movieId
    """, (studioid, title, releasedate))
    return cursor.fetchone()[0]


# def insert_movie_yt_video(cursor, movieid, videoid, videorole, is_primary=False):
#     cursor.execute("""
#         INSERT INTO movieYtVideos (movieId, videoId, videoRole, isPrimary)
#         VALUES (%s, %s, %s, %s)
#         ON CONFLICT (movieId, videoId) DO NOTHING
#     """, (movieid, videoid, videorole, is_primary))


def insert_movie_metric_snapshot(cursor, movieid, capturedat, viewstotal, likestotal, commentstotal, engagementrate):
    cursor.execute("""
        INSERT INTO movieMetricSnapshots (movieId, capturedAt, viewsTotal, likesTotal, commentsTotal, engagementRate)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (movieId, capturedAt) DO NOTHING
    """, (movieid, capturedat, viewstotal, likestotal, commentstotal, engagementrate))
    
    
def insert_transcript(cursor, videoid, language, source, fulltext):
    cursor.execute("""
        INSERT INTO ytvideotranscripts (videoid, language, source, fulltext)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (videoid, language, fetchedat) DO NOTHING
    """, (videoid, language, source, fulltext))   
    
def insert_movie_poster(cursor, movie_id, poster_url):
    cursor.execute("""
        UPDATE movies
        SET posterurl = %s, updatedat = now()
        WHERE movieid = %s
    """, (poster_url, movie_id))
    
def insert_movie_rating(cursor, movie_id, rating):
    cursor.execute("""
        UPDATE movies
        SET rating = %s, updatedat = now()
        WHERE movieid = %s
    """, (rating, movie_id))