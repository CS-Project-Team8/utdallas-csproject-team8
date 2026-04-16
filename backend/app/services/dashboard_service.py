from sqlalchemy import text


def format_compact(n: int) -> str:
    abs_n = abs(n)
    if abs_n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if abs_n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if abs_n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def sentiment_label(avg_sentiment):
    if avg_sentiment is None:
        return None
    if avg_sentiment >= 0.35:
        return "Very positive"
    if avg_sentiment >= 0.1:
        return "Positive"
    if avg_sentiment > -0.1:
        return "Neutral"
    if avg_sentiment > -0.35:
        return "Mixed"
    return "Negative"


def engagement_label(total_views, total_likes):
    if not total_views and not total_likes:
        return None
    if total_likes and total_likes >= 1_000_000:
        return "Most likes"
    if total_views and total_views >= 20_000_000:
        return "Top engagement"
    if total_views and total_views >= 10_000_000:
        return "Strong buzz"
    return "Rising interest"


def get_studio_dashboard(db, studio_id: str):
    studio_sql = text("""
                      SELECT
                          s.studioid,
                          s.name,
                          s.brandaccent,
                          s.initials,
                          s.logotextleft,
                          s.logotextright
                      FROM studios s
                      WHERE s.studioid = :studio_id
                      """)

    metrics_sql = text("""
                       WITH latest_snapshots AS (
                           SELECT DISTINCT ON (mas.movieid)
                           mas.movieid,
                           mas.computedat,
                           mas.totalviews,
                           mas.totallikes,
                           mas.creatorriskscore
                       FROM movieanalyticssnapshots mas
                       ORDER BY mas.movieid, mas.computedat DESC
                           )
                       SELECT
                           COUNT(m.movieid) AS total_movies,
                           COALESCE(ROUND(AVG(m.rating)::numeric, 1), 0) AS avg_rating,
                           COALESCE(ROUND(AVG(ls.creatorriskscore)::numeric, 1), 0) AS creator_risk_score,
                           COALESCE(SUM(ls.totalviews), 0) AS total_views
                       FROM movies m
                                LEFT JOIN latest_snapshots ls
                                          ON ls.movieid = m.movieid
                       WHERE m.studioid = :studio_id
                         AND m.status = 'active'
                       """)

    movies_sql = text("""
                      WITH latest_snapshots AS (
                          SELECT DISTINCT ON (mas.movieid)
                          mas.movieid,
                          mas.computedat,
                          mas.averagesentiment,
                          mas.totalviews,
                          mas.totallikes
                      FROM movieanalyticssnapshots mas
                      ORDER BY mas.movieid, mas.computedat DESC
                          ),
                          latest_success_run AS (
                      SELECT ir.runid
                      FROM insightruns ir
                      WHERE ir.studioid = :studio_id
                        AND ir.status = 'success'
                      ORDER BY ir.finishedat DESC NULLS LAST, ir.startedat DESC
                          LIMIT 1
                          )
                      SELECT
                          m.movieid,
                          m.studioid,
                          m.title,
                          m.releasedate,
                          m.posterurl,
                          mi.summary,
                          ls.averagesentiment,
                          ls.totalviews,
                          ls.totallikes
                      FROM movies m
                               LEFT JOIN latest_snapshots ls
                                         ON ls.movieid = m.movieid
                               LEFT JOIN latest_success_run lsr
                                         ON TRUE
                               LEFT JOIN movieinsights mi
                                         ON mi.movieid = m.movieid
                                             AND mi.runid = lsr.runid
                      WHERE m.studioid = :studio_id
                        AND m.status = 'active'
                      ORDER BY m.releasedate DESC NULLS LAST, m.createdat DESC
                          LIMIT 5
                      """)

    studio = db.execute(studio_sql, {"studio_id": studio_id}).mappings().first()
    if not studio:
        return None

    metrics = db.execute(metrics_sql, {"studio_id": studio_id}).mappings().first()
    movies = db.execute(movies_sql, {"studio_id": studio_id}).mappings().all()

    initials = studio["initials"]
    if not initials:
        initials = "".join(word[0] for word in studio["name"].split()[:2]).upper()

    return {
        "studio": {
            "id": str(studio["studioid"]),
            "name": studio["name"],
            "brandAccent": studio["brandaccent"] or "#E23333",
            "initials": initials,
            "logoTextLeft": studio["logotextleft"],
            "logoTextRight": studio["logotextright"],
        },
        "metrics": {
            "totalMovies": metrics["total_movies"] or 0,
            "avgRating": float(metrics["avg_rating"] or 0),
            "creatorRiskScore": float(metrics["creator_risk_score"] or 0),
            "extraLabel": "Total Views",
            "extraValue": format_compact(metrics["total_views"] or 0),
        },
        "recentMovies": [
            {
                "id": str(row["movieid"]),
                "title": row["title"],
                "year": row["releasedate"].year if row["releasedate"] else None,
                "posterUrl": row["posterurl"],
                "summary": row["summary"],
                "sentimentLabel": sentiment_label(row["averagesentiment"]),
                "engagementLabel": engagement_label(row["totalviews"], row["totallikes"]),
            }
            for row in movies
        ],
    }


def get_dashboard_movies(db, studio_id: str):
    movies_sql = text("""
                      WITH latest_snapshots AS (
                          SELECT DISTINCT ON (mas.movieid)
                          mas.movieid,
                          mas.computedat,
                          mas.averagesentiment,
                          mas.totalviews,
                          mas.totallikes
                      FROM movieanalyticssnapshots mas
                      ORDER BY mas.movieid, mas.computedat DESC
                          ),
                          latest_success_run AS (
                      SELECT ir.runid
                      FROM insightruns ir
                      WHERE ir.studioid = :studio_id
                        AND ir.status = 'success'
                      ORDER BY ir.finishedat DESC NULLS LAST, ir.startedat DESC
                          LIMIT 1
                          )
                      SELECT
                          m.movieid,
                          m.studioid,
                          m.title,
                          m.releasedate,
                          m.posterurl,
                          mi.summary,
                          ls.averagesentiment,
                          ls.totalviews,
                          ls.totallikes
                      FROM movies m
                               LEFT JOIN latest_snapshots ls
                                         ON ls.movieid = m.movieid
                               LEFT JOIN latest_success_run lsr
                                         ON TRUE
                               LEFT JOIN movieinsights mi
                                         ON mi.movieid = m.movieid
                                             AND mi.runid = lsr.runid
                      WHERE m.studioid = :studio_id
                        AND m.status = 'active'
                      ORDER BY m.releasedate DESC NULLS LAST, m.createdat DESC
                          LIMIT 5
                      """)

    rows = db.execute(movies_sql, {"studio_id": studio_id}).mappings().all()

    return [
        {
            "id": str(row["movieid"]),
            "title": row["title"],
            "year": row["releasedate"].year if row["releasedate"] else None,
            "posterUrl": row["posterurl"],
            "summary": row["summary"],
            "sentimentLabel": sentiment_label(row["averagesentiment"]),
            "engagementLabel": engagement_label(row["totalviews"], row["totallikes"]),
        }
        for row in rows
    ]


def search_studio_movies(db, studio_id: str, query: str = "", limit: int = 12):
    search_sql = text("""
                      WITH latest_snapshots AS (
                          SELECT DISTINCT ON (mas.movieid)
                          mas.movieid,
                          mas.computedat,
                          mas.averagesentiment,
                          mas.totalviews,
                          mas.totallikes
                      FROM movieanalyticssnapshots mas
                      ORDER BY mas.movieid, mas.computedat DESC
                          ),
                          latest_success_run AS (
                      SELECT ir.runid
                      FROM insightruns ir
                      WHERE ir.studioid = :studio_id
                        AND ir.status = 'success'
                      ORDER BY ir.finishedat DESC NULLS LAST, ir.startedat DESC
                          LIMIT 1
                          )
                      SELECT
                          m.movieid,
                          m.studioid,
                          m.title,
                          m.releasedate,
                          m.posterurl,
                          mi.summary,
                          ls.averagesentiment,
                          ls.totalviews,
                          ls.totallikes
                      FROM movies m
                               LEFT JOIN latest_snapshots ls
                                         ON ls.movieid = m.movieid
                               LEFT JOIN latest_success_run lsr
                                         ON TRUE
                               LEFT JOIN movieinsights mi
                                         ON mi.movieid = m.movieid
                                             AND mi.runid = lsr.runid
                      WHERE m.studioid = :studio_id
                        AND m.status = 'active'
                        AND (
                          :query = ''
                              OR LOWER(m.title) LIKE LOWER(:like_query)
                          )
                      ORDER BY m.releasedate DESC NULLS LAST, m.createdat DESC
                          LIMIT :limit
                      """)

    rows = db.execute(
        search_sql,
        {
            "studio_id": studio_id,
            "query": query,
            "like_query": f"%{query}%",
            "limit": limit,
        },
    ).mappings().all()

    return [
        {
            "id": str(row["movieid"]),
            "title": row["title"],
            "year": row["releasedate"].year if row["releasedate"] else None,
            "posterUrl": row["posterurl"],
            "summary": row["summary"],
            "sentimentLabel": sentiment_label(row["averagesentiment"]),
            "engagementLabel": engagement_label(row["totalviews"], row["totallikes"]),
        }
        for row in rows
    ]