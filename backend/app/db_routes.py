import json
import os
from pathlib import Path
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")
DB_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DB_URL)

# call after running llm to update its run status
def update_run_status(cursor, runid, status, error = None):
    cursor.execute("""
        UPDATE insightruns
        SET status = %s,
            finishedat = now(),
            error = %s
        WHERE runid = %s
    """, (status, error, runid))

# add key takeaways
def insert_movie_insights(cursor, runid, movieid, result):
    summary = " ".join(result.get("key_takeaways", []))         # refine summary analysis to llm
    key_takeaways = json.dumps(result.get("key_takeaways", []))
    
    cursor.execute("""
        INSERT INTO movieinsights (runid, movieid, summary, keytakeaways)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (runid, movieid) DO UPDATE
            SET summary = EXCLUDED.summary,
                keytakeaways = EXCLUDED.keytakeaways
    """, (runid, movieid, summary, key_takeaways))

# add narratives/topics
def insert_movie_topics(cursor, runid, movieid, result):
    for narrative in result.get("top_narratives", []):
        sentiment_map = {"positive": 1.0, "negative": -1.0, "mixed": 0.0}
        sentiment_avg = sentiment_map.get(narrative.get("sentiment", "mixed"), 0.0)
        cursor.execute("""
            INSERT INTO movietopics (runid, movieid, label, summary, sentimentavg)
            VALUES (%s, %s, %s, %s, %s)
        """, (runid, movieid, narrative.get("title", ""), narrative.get("summary", ""), sentiment_avg))

def insert_insights_payload(cursor, runid, movieid, result):
    cursor.execute("""
        INSERT INTO movieinsightpayloads (runid, movieid, movie_title, key_takeaways, top_narratives, 
                                          sentiment_breakdown, top_words, mood_signals, creator_risk)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (runid, movieid) DO UPDATE SET 
                movie_title = EXCLUDED.movie_title,
                key_takeaways = EXCLUDED.key_takeaways,
                top_narratives = EXCLUDED.top_narratives,
                sentiment_breakdown = EXCLUDED.sentiment_breakdown,
                top_words = EXCLUDED.top_words,
                mood_signals = EXCLUDED.mood_signals,
                creator_risk = EXCLUDED.creator_risk,
                updatedat = now()
    """, (
        runid,
        movieid,
        result.get("movie"),
        json.dumps(result.get("key_takeaways", [])),
        json.dumps(result.get("top_narratives", [])),
        json.dumps(result.get("sentiment_breakdown", {})),
        json.dumps(result.get("top_words", [])),
        json.dumps(result.get("mood_signals", [])),
        json.dumps(result.get("creator_risk", {}))
    ))

def insert_movie_analytics_snapshot(cursor, movieid, result):
    risk_score = result.get("creator_risk", {}).get("risk_score")
    risk_score_scaled = risk_score * 10 if risk_score is not None else None
    sentiment = result.get("sentiment_breakdown", {})

    cursor.execute("""
        INSERT INTO movieanalyticssnapshots (
            movieid, totalreviewvideos, totalviews, totallikes,
            averagesentiment, pospct, negpct, neupct,
            topsentimentwords, creatorriskscore, moodsignals, keydiscussiontopics
        )
        VALUES (
            %s,
            (SELECT COUNT(*) FROM ytvideos WHERE movieid = %s AND videorole = 'review'),
            (SELECT COALESCE(SUM(viewcount), 0) FROM ytvideometricsnapshots
             WHERE videoid IN (SELECT videoid FROM ytvideos WHERE movieid = %s)),
            (SELECT COALESCE(SUM(likecount), 0) FROM ytvideometricsnapshots
             WHERE videoid IN (SELECT videoid FROM ytvideos WHERE movieid = %s)),
            %s, %s, %s, %s, %s, %s, %s, %s
        )
    """, (
        movieid, movieid, movieid, movieid,
        sentiment.get("avg_sentiment_score"),
        sentiment.get("positive_pct", 0) / 100.0,
        sentiment.get("negative_pct", 0) / 100.0,
        sentiment.get("neutral_pct", 0) / 100.0,
        json.dumps(result.get("top_words", [])),
        risk_score_scaled,
        json.dumps(result.get("mood_signals", [])),
        json.dumps(result.get("top_narratives", []))
    ))

def load_llm_output(runid, movieid, result):
    conn = get_conn()  # fresh connection, called AFTER all LLM work is done
    try:
        cursor = conn.cursor()
        
        print("Saving movie insights")
        insert_movie_insights(cursor, runid, movieid, result)

        print("Saving movie topics")
        insert_movie_topics(cursor, runid, movieid, result)

        print("Saving insight payload")
        insert_insights_payload(cursor, runid, movieid, result)
        
        print("Saving analytics snapshot")
        insert_movie_analytics_snapshot(cursor, movieid, result)

        conn.commit()

        print("Updating run status")
        update_run_status(cursor, runid, "success")
        conn.commit()

        print("All data saved successfully")
 
    except Exception as e:          # error with llm run
        conn.rollback()
        update_run_status(cursor, runid, "failed", str(e))
        conn.commit()
        raise
    
# getting transcript, videoid, movieid, comments
def get_movie_data_for_llm(movie_id):
    conn = get_conn()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
            SELECT v.videoid, v.videorole, t.fulltext AS transcript
            FROM ytvideos v
            LEFT JOIN ytvideotranscripts t ON t.videoid = v.videoid
            WHERE v.movieid = %s
              AND v.videorole IN ('official_trailer', 'review')
            ORDER BY
                CASE v.videorole WHEN 'official_trailer' THEN 0 ELSE 1 END,
                v.publishedat ASC
        """, (movie_id,))
        videos = cursor.fetchall()

        if not videos:
            raise ValueError(f"No videos found for movie_id: {movie_id}")

        def get_comments(video_id):
            cursor.execute("""
                SELECT text FROM ytcomments
                WHERE videoid = %s
                ORDER BY likecount DESC, publishedat DESC
                LIMIT 100
            """, (video_id,))
            return [row["text"] for row in cursor.fetchall()]

        trailer = None
        reviews = []
        for video in videos:
            video_id   = video["videoid"]
            video_role = video["videorole"]
            transcript = video["transcript"]
            if not transcript:
                print(f"  Warning: no transcript for video {video_id} ({video_role}), skipping")
                continue
            entry = {"transcript": transcript, "comments": get_comments(video_id)}
            if video_role == "official_trailer" and trailer is None:
                trailer = entry
            elif video_role == "review":
                reviews.append(entry)

        if not trailer:
            raise ValueError(f"No trailer with transcript found for movie_id: {movie_id}")
        if not reviews:
            raise ValueError(f"No review videos with transcripts found for movie_id: {movie_id}")

        return trailer, reviews
    finally:
        conn.close()

# helper method for getting movie_id from movie_title
def get_movie_id_from_title(movie_title):
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT movieid FROM movies
                WHERE title = %s
                ORDER BY releasedate DESC NULLS LAST
                LIMIT 1
            """, (movie_title,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                raise ValueError(f"No movie found with title: {movie_title}")
    finally:
        conn.close()

def insert_insight_run(cursor, studioid):
    cursor.execute("""
        INSERT INTO insightruns (studioid, status)
        VALUES (%s, 'running')
        RETURNING runid
    """, (studioid,))
    result = cursor.fetchone()
    return result[0] if result else None


# helper method for getting studio_id from movie_id
def get_studio_id_from_movie_id(movie_id):
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT studioid FROM movies WHERE movieid = %s
            """, (movie_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                raise ValueError(f"No movie found with id: {movie_id}")
    finally:
        conn.close()
