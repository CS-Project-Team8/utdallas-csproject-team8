import os
import json
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(
    database="Retrospec",
    user="postgres",
    password="postgres",
    host="localhost",
    port=5432
)

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

def load_llm_output(runid, movieid, result):
    try:
        cursor = conn.cursor()
        
        print("Saving movie insights")
        insert_movie_insights(cursor, runid, movieid, result)

        print("Saving movie topics")
        insert_movie_topics(cursor, runid, movieid, result)

        print("Saving insight payload")
        insert_insights_payload(cursor, runid, movieid, result)

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
