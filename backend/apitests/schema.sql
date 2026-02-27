CREATE EXTENSION IF NOT EXISTS pgcrypto; 

CREATE TABLE IF NOT EXISTS studios (  -- doesn't require YouTube data
  studioId   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL UNIQUE,
  createdAt  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updatedAt  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS studioUsers ( -- doesn't require YouTube data
  userId        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  studioId      UUID NOT NULL REFERENCES studios(studioId) ON DELETE CASCADE,
  email          TEXT NOT NULL UNIQUE,
  passwordHash  TEXT NOT NULL,
  role           TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('admin','member','read_only')),
  isActive      BOOLEAN NOT NULL DEFAULT true,
  createdAt     TIMESTAMPTZ NOT NULL DEFAULT now(),
  prevLogin  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_studio_users_studio_id 
  ON studioUsers (studioId);


CREATE TABLE IF NOT EXISTS movies ( -- requires YouTube data (search for the top 5 most recent movie trailers for each studio)
  movieId      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  studioId     UUID NOT NULL REFERENCES studios(studioId) ON DELETE CASCADE,
  title         TEXT NOT NULL,
  releaseDate  DATE,
  status        TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','archived')),
  createdAt    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updatedAt    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (studioId, title) 
);

CREATE INDEX IF NOT EXISTS idx_movies_studio_status
  ON movies (studioId, status);


CREATE TABLE IF NOT EXISTS studioTopMovies ( -- unsure if this requires YouTube data
  studioId  UUID NOT NULL REFERENCES studios(studioId) ON DELETE CASCADE,
  rank       INT  NOT NULL CHECK (rank BETWEEN 1 AND 5),
  movieId   UUID NOT NULL REFERENCES movies(movieId) ON DELETE CASCADE,
  asOf      TIMESTAMPTZ NOT NULL DEFAULT now(),
  method     TEXT NOT NULL DEFAULT 'youtube_views',
  PRIMARY KEY (studioId, rank),
  UNIQUE (studioId, movieId)
);

CREATE INDEX IF NOT EXISTS idx_studio_top_movies_as_of
  ON studioTopMovies (studioId, asOf DESC);


CREATE TABLE IF NOT EXISTS ytChannels ( -- requires YouTube data (search for the top 5 most viewed movie reviews for each movie & extract channel info)
  channelId     TEXT PRIMARY KEY,         
  channelTitle  TEXT NOT NULL,
  country       TEXT,
  createdAt     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updatedAt     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ytVideos ( -- requires YouTube data (search for the top 5 most viewed movie reviews for each movie & extract ytvideo info)
  videoId          TEXT PRIMARY KEY,      -- YouTube videoId
  channelId        TEXT NOT NULL REFERENCES ytChannels(channelId) ON DELETE RESTRICT,
  title             TEXT NOT NULL,
  description       TEXT,
  publishedAt      TIMESTAMPTZ NOT NULL,
  durationSeconds  INT,
  categoryId       TEXT,
  defaultLanguage  TEXT,
  tags              JSONB,                 
  caption           BOOLEAN,
  createdAt        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updatedAt        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_yt_videos_channel_id
  ON ytVideos (channelId);

CREATE INDEX IF NOT EXISTS idx_yt_videos_published_at
  ON ytVideos (publishedAt);


CREATE TABLE IF NOT EXISTS movieYtVideos (  -- requires YouTube data (search for the top 5 most recent movie trailers for each studio & extract ytvideo info)
  movieId    UUID NOT NULL REFERENCES movies(movieId) ON DELETE CASCADE,
  videoId    TEXT NOT NULL REFERENCES ytVideos(videoId) ON DELETE CASCADE,
  videoRole  TEXT NOT NULL DEFAULT 'official_trailer'
    CHECK (videoRole IN ('official_trailer','teaser','clip','tv_spot','featurette','other')),
  isPrimary  BOOLEAN NOT NULL DEFAULT false,
  weight      DOUBLE PRECISION NOT NULL DEFAULT 1.0,
  addedAt    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (movieId, videoId)
);

CREATE INDEX IF NOT EXISTS idx_movie_yt_videos_movie_role_primary
  ON movieYtVideos (movieId, videoRole, isPrimary);

CREATE INDEX IF NOT EXISTS idx_movie_yt_videos_video_id
  ON movieYtVideos (videoId);


CREATE UNIQUE INDEX IF NOT EXISTS uq_movie_one_primary
  ON movieYtVideos (movieId)
  WHERE isPrimary = true;


CREATE TABLE IF NOT EXISTS ytVideoMetricSnapshots ( -- requires YouTube data (search for the top 5 most viewed movie reviews for each movie & extract ytvideo info)
  videoId       TEXT NOT NULL REFERENCES ytVideos(videoId) ON DELETE CASCADE,
  capturedAt    TIMESTAMPTZ NOT NULL,
  viewCount     BIGINT NOT NULL,
  likeCount     BIGINT,
  commentCount  BIGINT NOT NULL,
  PRIMARY KEY (videoId, capturedAt)
);

CREATE INDEX IF NOT EXISTS idx_yt_video_metric_snapshots_captured_at
  ON ytVideoMetricSnapshots (capturedAt);


CREATE TABLE IF NOT EXISTS movieMetricSnapshots ( -- requires YouTube data (search for the top 5 most recent movie trailers for each studio & extract ytvideo info)
  movieId          UUID NOT NULL REFERENCES movies(movieId) ON DELETE CASCADE,
  capturedAt       TIMESTAMPTZ NOT NULL,
  viewsTotal       BIGINT NOT NULL,
  likesTotal       BIGINT,
  commentsTotal    BIGINT NOT NULL,

  
  viewsDelta1d    BIGINT,
  viewsDelta7d    BIGINT,

  
  engagementRate   DOUBLE PRECISION, 

  PRIMARY KEY (movieId, capturedAt)
);

CREATE INDEX IF NOT EXISTS idx_movie_metric_snapshots_movie_time
  ON movieMetricSnapshots (movieId, capturedAt DESC);


CREATE TABLE IF NOT EXISTS ytCommentThreads ( -- requires YouTube data (search for the top 5 most viewed movie reviews for each movie & extract top 10 comments info)
  threadId          TEXT PRIMARY KEY, 
  videoId           TEXT NOT NULL REFERENCES ytVideos(videoId) ON DELETE CASCADE,
  totalReplyCount  INT NOT NULL DEFAULT 0,
  lastFetchedAt    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_yt_comment_threads_video_id
  ON ytCommentThreads (videoId);


CREATE TABLE IF NOT EXISTS ytComments ( -- requires YouTube data (search for the top 5 most viewed movie reviews for each movie & extract top 10 comments info)
  commentId         TEXT PRIMARY KEY, 
  videoId           TEXT NOT NULL REFERENCES ytVideos(videoId) ON DELETE CASCADE,
  threadId          TEXT REFERENCES ytCommentThreads(threadId) ON DELETE SET NULL,
  parentCommentId  TEXT,             
  text               TEXT NOT NULL,
  likeCount         INT NOT NULL DEFAULT 0,
  authorChannelId  TEXT,
  publishedAt       TIMESTAMPTZ NOT NULL,
  updatedAt         TIMESTAMPTZ NOT NULL,
  ingestedAt        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_yt_comments_video_published
  ON ytComments (videoId, publishedAt DESC);

CREATE INDEX IF NOT EXISTS idx_yt_comments_video_updated
  ON ytComments (videoId, updatedAt DESC);

CREATE INDEX IF NOT EXISTS idx_yt_comments_parent
  ON ytComments (parentCommentId);


CREATE TABLE IF NOT EXISTS insightRuns ( -- does not require YouTube data 
  runId      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  studioId   UUID NOT NULL REFERENCES studios(studioId) ON DELETE CASCADE,
  runScope   TEXT NOT NULL DEFAULT 'top5', 
  status      TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','success','failed')),
  params      JSONB,
  startedAt  TIMESTAMPTZ NOT NULL DEFAULT now(),
  finishedAt TIMESTAMPTZ,
  error       TEXT
);

CREATE INDEX IF NOT EXISTS idx_insight_runs_studio_started
  ON insightRuns (studioId, startedAt DESC);


CREATE TABLE IF NOT EXISTS movieInsights ( -- does not require YouTube data 
  runId          UUID NOT NULL REFERENCES insightRuns(runId) ON DELETE CASCADE,
  movieId        UUID NOT NULL REFERENCES movies(movieId) ON DELETE CASCADE,
  summary         TEXT NOT NULL,
  keyTakeaways   JSONB, 
  recommendations JSONB, 
  createdAt      TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (runId, movieId)
);

CREATE INDEX IF NOT EXISTS idx_movie_insights_movie_run
  ON movieInsights (movieId, runId);


CREATE TABLE IF NOT EXISTS movieTopics ( -- does not require YouTube data 
  topicId         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  runId           UUID NOT NULL REFERENCES insightRuns(runId) ON DELETE CASCADE,
  movieId         UUID NOT NULL REFERENCES movies(movieId) ON DELETE CASCADE,

  label            TEXT NOT NULL, 
  summary          TEXT NOT NULL,  
  keywords         JSONB,          

  sentimentAvg    DOUBLE PRECISION,  
  volume           INT NOT NULL DEFAULT 0, 
  consensusScore  DOUBLE PRECISION,  
  controversyScore DOUBLE PRECISION, 

  createdAt       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_movie_topics_movie_run
  ON movieTopics (movieId, runId);

CREATE INDEX IF NOT EXISTS idx_movie_topics_run
  ON movieTopics (runId);


CREATE TABLE IF NOT EXISTS topicEvidenceComments ( -- unsure if this requires YouTube data
  topicId    UUID NOT NULL REFERENCES movieTopics(topicId) ON DELETE CASCADE,
  commentId  TEXT NOT NULL REFERENCES ytComments(commentId) ON DELETE CASCADE,
  relevance   DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  createdAt  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (topicId, commentId)
);

CREATE INDEX IF NOT EXISTS idx_topic_evidence_topic
  ON topicEvidenceComments (topicId, relevance DESC);

CREATE INDEX IF NOT EXISTS idx_topic_evidence_comment
  ON topicEvidenceComments (commentId);


CREATE TABLE IF NOT EXISTS movieTopicAggregates ( -- unsure if this requires YouTube data
  topicId         UUID PRIMARY KEY REFERENCES movieTopics(topicId) ON DELETE CASCADE,
  commentCount    INT NOT NULL,
  posPct          DOUBLE PRECISION,
  negPct          DOUBLE PRECISION,
  neuPct          DOUBLE PRECISION,
  topKeywords     JSONB,
  updatedAt       TIMESTAMPTZ NOT NULL DEFAULT now()
);