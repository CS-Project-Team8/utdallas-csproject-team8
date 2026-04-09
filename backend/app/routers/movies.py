from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db.session import engine

router = APIRouter(prefix="/api/v1", tags=["movies"])


@router.get("/studios/{studio_id}/movies/{movie_id}")
def get_movie(studio_id: UUID, movie_id: UUID):
    query = text("""
                 SELECT
                     movieid,
                     studioid,
                     title,
                     rating,
                     releasedate,
                     posterurl
                 FROM movies
                 WHERE studioid = :studio_id
                   AND movieid = :movie_id
                     LIMIT 1
                 """)

    with engine.connect() as conn:
        row = conn.execute(
            query,
            {"studio_id": studio_id, "movie_id": movie_id},
        ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Movie not found")

    return {
        "movieid": str(row["movieid"]),
        "studioid": str(row["studioid"]),
        "title": row["title"],
        "year": row["releasedate"].year if row["releasedate"] else None,
        "posterUrl": row["posterurl"],
        "rating": row["rating"],
    }


@router.get("/studios/{studio_id}/movies/{movie_id}/trends")
def get_movie_trends(studio_id: UUID, movie_id: UUID):
    movie_check_sql = text("""
                           SELECT 1
                           FROM movies
                           WHERE studioid = :studio_id
                             AND movieid = :movie_id
                               LIMIT 1
                           """)

    snapshot_sql = text("""
                        SELECT
                            computedat,
                            totalreviewvideos,
                            averagesentiment,
                            totalviews,
                            totallikes,
                            topsentimentwords,
                            moodsignals,
                            keydiscussiontopics
                        FROM movieanalyticssnapshots
                        WHERE movieid = :movie_id
                        ORDER BY computedat DESC
                            LIMIT 1
                        """)

    sentiment_sql = text("""
                         SELECT
                             periodstart,
                             periodend,
                             avgsentiment,
                             pospct,
                             negpct,
                             neupct,
                             reviewvideocount
                         FROM moviesentimenttimeline
                         WHERE movieid = :movie_id
                         ORDER BY periodstart ASC, computedat ASC
                         """)

    velocity_sql = text("""
                        SELECT
                            weekstart,
                            reviewsthisweek,
                            cumulativereviews
                        FROM moviereviewvelocity
                        WHERE movieid = :movie_id
                        ORDER BY weekstart ASC, computedat ASC
                        """)

    engaged_sql = text("""
                       SELECT
                           videoid,
                           rank,
                           views,
                           likes,
                           comments,
                           engagementrate
                       FROM movieengagedreviewvideos
                       WHERE movieid = :movie_id
                       ORDER BY computedat DESC, rank ASC
                       """)

    topics_sql = text("""
                    SELECT
                        label,
                        summary,
                        sentimentavg,
                        volume,
                        consensusscore,
                        controversyscore
                    FROM movietopics
                    WHERE movieid = :movie_id
                    ORDER BY createdat DESC
                """)

    payload_sql = text("""
                       SELECT
                           top_words,
                           mood_signals,
                           sentiment_breakdown
                       FROM movieinsightpayloads
                       WHERE movieid = :movie_id
                       ORDER BY updatedat DESC, createdat DESC
                           LIMIT 1
                       """)

    with engine.connect() as conn:
        exists = conn.execute(
            movie_check_sql,
            {"studio_id": studio_id, "movie_id": movie_id},
        ).first()

        if not exists:
            raise HTTPException(status_code=404, detail="Movie not found")

        snapshot = conn.execute(snapshot_sql, {"movie_id": movie_id}).mappings().first()
        sentiment_rows = conn.execute(sentiment_sql, {"movie_id": movie_id}).mappings().all()
        velocity_rows = conn.execute(velocity_sql, {"movie_id": movie_id}).mappings().all()
        engaged_rows = conn.execute(engaged_sql, {"movie_id": movie_id}).mappings().all()
        topic_rows = conn.execute(topics_sql, {"movie_id": movie_id}).mappings().all()
        payload = conn.execute(payload_sql, {"movie_id": movie_id}).mappings().first()

    peak_week = None
    if velocity_rows:
        peak = max(velocity_rows, key=lambda r: r["reviewsthisweek"] or 0)
        peak_week = peak["weekstart"].isoformat() if peak["weekstart"] else None

    growth_rate = None
    if len(velocity_rows) >= 2:
        first = velocity_rows[0]["reviewsthisweek"] or 0
        last = velocity_rows[-1]["reviewsthisweek"] or 0
        if first > 0:
            growth_rate = round(((last - first) / first) * 100)

    viral_reviews = sum(1 for r in engaged_rows if (r["views"] or 0) >= 500_000)

    top_words = []
    if payload and payload["top_words"]:
        raw_words = payload["top_words"]
        if isinstance(raw_words, list):
            for item in raw_words:
                if isinstance(item, str):
                    top_words.append(item)
                elif isinstance(item, dict):
                    top_words.append(item.get("word") or item.get("label") or item.get("term"))
    elif snapshot and snapshot["topsentimentwords"]:
        raw_words = snapshot["topsentimentwords"]
        if isinstance(raw_words, list):
            for item in raw_words:
                if isinstance(item, str):
                    top_words.append(item)
                elif isinstance(item, dict):
                    top_words.append(item.get("word") or item.get("label") or item.get("term"))

    rising_signals = []
    if payload and payload["mood_signals"]:
        raw_signals = payload["mood_signals"]
        if isinstance(raw_signals, list):
            for item in raw_signals:
                if isinstance(item, dict):
                    label = item.get("label") or item.get("name") or item.get("signal")
                    value = item.get("value") or item.get("score") or item.get("pct")
                    if label is not None and value is not None:
                        rising_signals.append({"label": label, "value": round(float(value))})
    elif snapshot and snapshot["moodsignals"]:
        raw_signals = snapshot["moodsignals"]
        if isinstance(raw_signals, list):
            for item in raw_signals:
                if isinstance(item, dict):
                    label = item.get("label") or item.get("name") or item.get("signal")
                    value = item.get("value") or item.get("score") or item.get("pct")
                    if label is not None and value is not None:
                        rising_signals.append({"label": label, "value": round(float(value))})

    return {
        "metrics": {
            "trendingTopics": len(topic_rows),
            "peakWeek": peak_week,
            "growthRate": growth_rate,
            "viralReviews": viral_reviews,
        },
        "sentimentTimeline": [
            {
                "periodStart": row["periodstart"].isoformat(),
                "periodEnd": row["periodend"].isoformat(),
                "avgSentiment": row["avgsentiment"],
                "posPct": row["pospct"],
                "negPct": row["negpct"],
                "neuPct": row["neupct"],
                "reviewVideoCount": row["reviewvideocount"],
            }
            for row in sentiment_rows
        ],
        "reviewVolume": [
            {
                "weekStart": row["weekstart"].isoformat(),
                "reviewsThisWeek": row["reviewsthisweek"],
                "cumulativeReviews": row["cumulativereviews"],
            }
            for row in velocity_rows
        ],
        "risingSignals": rising_signals[:8],
        "topWords": [w for w in top_words if w][:12],
    }


@router.get("/studios/{studio_id}/movies/{movie_id}/narratives")
def get_movie_narratives(studio_id: UUID, movie_id: UUID):
    movie_check_sql = text("""
                           SELECT 1
                           FROM movies
                           WHERE studioid = :studio_id
                             AND movieid = :movie_id
                               LIMIT 1
                           """)

    payload_sql = text("""
                       SELECT
                           top_narratives
                       FROM movieinsightpayloads
                       WHERE movieid = :movie_id
                       ORDER BY updatedat DESC, createdat DESC
                           LIMIT 1
                       """)

    fallback_topics_sql = text("""
                               SELECT
                                   topiclabel,
                                   pct,
                                   summary
                               FROM moviediscussiontopics
                               WHERE movieid = :movie_id
                               ORDER BY computedat DESC, pct DESC
                                   LIMIT 10
                               """)

    with engine.connect() as conn:
        exists = conn.execute(
            movie_check_sql,
            {"studio_id": studio_id, "movie_id": movie_id},
        ).first()

        if not exists:
            raise HTTPException(status_code=404, detail="Movie not found")

        payload = conn.execute(payload_sql, {"movie_id": movie_id}).mappings().first()
        fallback_topics = conn.execute(
            fallback_topics_sql, {"movie_id": movie_id}
        ).mappings().all()

    narratives = []

    if payload and payload["top_narratives"]:
        raw = payload["top_narratives"]
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    title = item.get("title") or item.get("label") or item.get("name")
                    description = (
                            item.get("description")
                            or item.get("summary")
                            or item.get("desc")
                    )
                    strength = item.get("strength") or item.get("score") or item.get("pct")
                    review_count = (
                            item.get("reviewCount")
                            or item.get("reviews")
                            or item.get("count")
                            or 0
                    )
                    is_counter = bool(
                        item.get("isCounterNarrative")
                        or item.get("counter")
                        or item.get("is_counter")
                    )

                    if title:
                        narratives.append(
                            {
                                "title": title,
                                "description": description,
                                "strength": round(float(strength) * 100) if strength is not None and float(strength) <= 1 else round(float(strength or 0)),
                                "reviewCount": int(review_count),
                                "isCounterNarrative": is_counter,
                            }
                        )

    if not narratives:
        narratives = [
            {
                "title": row["topiclabel"],
                "description": row["summary"],
                "strength": round(float(row["pct"] or 0) * 100),
                "reviewCount": 0,
                "isCounterNarrative": False,
            }
            for row in fallback_topics
        ]

    dominant = max(narratives, key=lambda n: n["strength"])["title"] if narratives else None
    counter_count = sum(1 for n in narratives if n["isCounterNarrative"])
    coverage = max((n["strength"] for n in narratives), default=0)

    return {
        "metrics": {
            "activeNarratives": len(narratives),
            "dominantNarrative": dominant,
            "counterNarratives": counter_count,
            "reviewCoverage": coverage,
        },
        "narratives": narratives,
    }

@router.get("/studios/{studio_id}/movies/{movie_id}/claims")
def get_movie_claims(studio_id: UUID, movie_id: UUID):
    movie_check_sql = text("""
                           SELECT 1
                           FROM movies
                           WHERE studioid = :studio_id
                             AND movieid = :movie_id
                               LIMIT 1
                           """)

    claims_sql = text("""
                      SELECT
                          claimid,
                          claimtext,
                          mentionpct,
                          mentioncount,
                          verdict,
                          risklevel,
                          createdat,
                          updatedat
                      FROM movieclaims
                      WHERE movieid = :movie_id
                      ORDER BY
                          COALESCE(mentionpct, 0) DESC,
                          COALESCE(mentioncount, 0) DESC,
                          updatedat DESC,
                          createdat DESC
                      """)

    with engine.connect() as conn:
        exists = conn.execute(
            movie_check_sql,
            {"studio_id": studio_id, "movie_id": movie_id},
        ).first()

        if not exists:
            raise HTTPException(status_code=404, detail="Movie not found")

        claim_rows = conn.execute(
            claims_sql, {"movie_id": movie_id}
        ).mappings().all()

    verified_count = sum(1 for row in claim_rows if row["verdict"] == "verified")
    disputed_count = sum(1 for row in claim_rows if row["verdict"] == "disputed")
    misleading_count = sum(1 for row in claim_rows if row["verdict"] == "misleading")

    def normalize_tone(risklevel: str | None, verdict: str) -> str:
        if risklevel in {"low", "mid", "high"}:
            return risklevel
        if verdict == "verified":
            return "low"
        if verdict == "disputed":
            return "mid"
        if verdict == "misleading":
            return "high"
        return "mid"

    claims = []
    for row in claim_rows:
        mention_pct = row["mentionpct"]
        if mention_pct is None:
            freq = 0
        else:
            freq = round(float(mention_pct) * 100) if float(mention_pct) <= 1 else round(float(mention_pct))

        verdict_raw = row["verdict"] or "unverified"
        verdict_label = verdict_raw.capitalize()

        claims.append(
            {
                "id": str(row["claimid"]),
                "claim": row["claimtext"],
                "freq": freq,
                "mentionCount": row["mentioncount"] or 0,
                "verdict": verdict_label,
                "tone": normalize_tone(row["risklevel"], verdict_raw),
            }
        )

    return {
        "metrics": {
            "totalClaims": len(claim_rows),
            "verified": verified_count,
            "disputed": disputed_count,
            "misleading": misleading_count,
        },
        "claims": claims,
    }