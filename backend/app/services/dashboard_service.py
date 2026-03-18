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
                          s.studioId,
                          s.name,
                          s.brandAccent,
                          s.initials,
                          s.logoTextLeft,
                          s.logoTextRight
                      FROM studios s
                      WHERE s.studioId = :studio_id
                      """)

    metrics_sql = text("""
                       WITH latest_snapshots AS (
                           SELECT DISTINCT ON (mas.movieId)
                           mas.movieId,
                           mas.computedAt,
                           mas.totalViews,
                           mas.totalLikes,
                           mas.creatorRiskScore
                       FROM movieanalyticssnapshots mas
                       ORDER BY mas.movieId, mas.computedAt DESC
                           )
                       SELECT
                           COUNT(m.movieId) AS total_movies,
                           COALESCE(ROUND(AVG(m.rating)::numeric, 1), 0) AS avg_rating,
                           COALESCE(ROUND(AVG(ls.creatorRiskScore)::numeric, 1), 0) AS creator_risk_score,
                           COALESCE(SUM(ls.totalViews), 0) AS total_views
                       FROM movies m
                                LEFT JOIN latest_snapshots ls
                                          ON ls.movieId = m.movieId
                       WHERE m.studioId = :studio_id
                         AND m.status = 'active'
                       """)

    movies_sql = text("""
                      WITH latest_snapshots AS (
                          SELECT DISTINCT ON (mas.movieId)
                          mas.movieId,
                          mas.computedAt,
                          mas.averageSentiment,
                          mas.totalViews,
                          mas.totalLikes
                      FROM movieanalyticssnapshots mas
                      ORDER BY mas.movieId, mas.computedAt DESC
                          ),
                          latest_success_run AS (
                      SELECT ir.runId
                      FROM insightRuns ir
                      WHERE ir.studioId = :studio_id
                        AND ir.status = 'success'
                      ORDER BY ir.finishedAt DESC NULLS LAST, ir.startedAt DESC
                          LIMIT 1
                          )
                      SELECT
                          m.movieId,
                          m.title,
                          m.releaseDate,
                          m.posterUrl,
                          mi.summary,
                          ls.averageSentiment,
                          ls.totalViews,
                          ls.totalLikes,
                          stm.rank
                      FROM studioTopMovies stm
                               JOIN movies m
                                    ON m.movieId = stm.movieId
                               LEFT JOIN latest_snapshots ls
                                         ON ls.movieId = m.movieId
                               LEFT JOIN latest_success_run lsr
                                         ON TRUE
                               LEFT JOIN movieInsights mi
                                         ON mi.movieId = m.movieId
                                             AND mi.runId = lsr.runId
                      WHERE stm.studioId = :studio_id
                      ORDER BY stm.rank ASC
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
                          SELECT DISTINCT ON (mas.movieId)
                          mas.movieId,
                          mas.computedAt,
                          mas.averageSentiment,
                          mas.totalViews,
                          mas.totalLikes
                      FROM movieanalyticssnapshots mas
                      ORDER BY mas.movieId, mas.computedAt DESC
                          ),
                          latest_success_run AS (
                      SELECT ir.runId
                      FROM insightRuns ir
                      WHERE ir.studioId = :studio_id
                        AND ir.status = 'success'
                      ORDER BY ir.finishedAt DESC NULLS LAST, ir.startedAt DESC
                          LIMIT 1
                          )
                      SELECT
                          m.movieId,
                          m.title,
                          m.releaseDate,
                          m.posterUrl,
                          mi.summary,
                          ls.averageSentiment,
                          ls.totalViews,
                          ls.totalLikes,
                          stm.rank
                      FROM studioTopMovies stm
                               JOIN movies m
                                    ON m.movieId = stm.movieId
                               LEFT JOIN latest_snapshots ls
                                         ON ls.movieId = m.movieId
                               LEFT JOIN latest_success_run lsr
                                         ON TRUE
                               LEFT JOIN movieInsights mi
                                         ON mi.movieId = m.movieId
                                             AND mi.runId = lsr.runId
                      WHERE stm.studioId = :studio_id
                      ORDER BY stm.rank ASC
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
                          SELECT DISTINCT ON (mas.movieId)
                          mas.movieId,
                          mas.computedAt,
                          mas.averageSentiment,
                          mas.totalViews,
                          mas.totalLikes
                      FROM movieanalyticssnapshots mas
                      ORDER BY mas.movieId, mas.computedAt DESC
                          ),
                          latest_success_run AS (
                      SELECT ir.runId
                      FROM insightRuns ir
                      WHERE ir.studioId = :studio_id
                        AND ir.status = 'success'
                      ORDER BY ir.finishedAt DESC NULLS LAST, ir.startedAt DESC
                          LIMIT 1
                          )
                      SELECT
                          m.movieId,
                          m.title,
                          m.releaseDate,
                          m.posterUrl,
                          mi.summary,
                          ls.averageSentiment,
                          ls.totalViews,
                          ls.totalLikes
                      FROM movies m
                               LEFT JOIN latest_snapshots ls
                                         ON ls.movieId = m.movieId
                               LEFT JOIN latest_success_run lsr
                                         ON TRUE
                               LEFT JOIN movieInsights mi
                                         ON mi.movieId = m.movieId
                                             AND mi.runId = lsr.runId
                      WHERE m.studioId = :studio_id
                        AND m.status = 'active'
                        AND (
                          :query = ''
                              OR LOWER(m.title) LIKE LOWER(:like_query)
                          )
                      ORDER BY m.releaseDate DESC NULLS LAST, m.createdAt DESC
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