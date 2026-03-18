-- ============================================================
-- YIP Full Schema (Local Postgres)
-- ============================================================
-- Run this script inside the yip database in DBeaver or pgAdmin.
-- Notes:
-- - All identifiers are lower-case (recommended for Postgres).
-- - Uses pgcrypto for gen_random_uuid().
-- ============================================================

BEGIN;

-- ----------------------------
-- Extensions
-- ----------------------------
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ----------------------------
-- Core: Studios + Users
-- ----------------------------
CREATE TABLE IF NOT EXISTS studios (
  studioid   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name       TEXT NOT NULL UNIQUE,
  createdat  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updatedat  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS studiousers (
  userid       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  studioid     UUID NOT NULL REFERENCES studios(studioid) ON DELETE CASCADE,
  email        TEXT NOT NULL UNIQUE,
  passwordhash TEXT NOT NULL,
  role         TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('admin','member','read_only')),
  isactive     BOOLEAN NOT NULL DEFAULT true,
  createdat    TIMESTAMPTZ NOT NULL DEFAULT now(),
  prevlogin    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_studiusers_studioid
  ON studiousers (studioid);

-- ----------------------------
-- Movies + Studio Top 5
-- ----------------------------
CREATE TABLE IF NOT EXISTS movies (
  movieid      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  studioid     UUID NOT NULL REFERENCES studios(studioid) ON DELETE CASCADE,
  title        TEXT NOT NULL,
  releasedate  DATE,
  status       TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','archived')),
  createdat    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updatedat    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (studioid, title)
);

CREATE INDEX IF NOT EXISTS idx_movies_studio_status
  ON movies (studioid, status);

CREATE TABLE IF NOT EXISTS studiotopmovies (
  studioid  UUID NOT NULL REFERENCES studios(studioid) ON DELETE CASCADE,
  rank      INT  NOT NULL CHECK (rank BETWEEN 1 AND 5),
  movieid   UUID NOT NULL REFERENCES movies(movieid) ON DELETE CASCADE,
  asof      TIMESTAMPTZ NOT NULL DEFAULT now(),
  method    TEXT NOT NULL DEFAULT 'youtube_views',
  PRIMARY KEY (studioid, rank),
  UNIQUE (studioid, movieid)
);

CREATE INDEX IF NOT EXISTS idx_studiotopmovies_asof
  ON studiotopmovies (studioid, asof DESC);

-- ----------------------------
-- YouTube: Channels + Videos
-- ----------------------------
CREATE TABLE IF NOT EXISTS ytchannels (
  channelid     TEXT PRIMARY KEY,
  channeltitle  TEXT NOT NULL,
  country       TEXT,
  createdat     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updatedat     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ytvideos ( -- what does caption do?
  videoid          TEXT PRIMARY KEY,
  channelid        TEXT NOT NULL REFERENCES ytchannels(channelid) ON DELETE RESTRICT,
  title            TEXT NOT NULL,
  description      TEXT,
  publishedat      TIMESTAMPTZ NOT NULL,
  durationseconds  INT,
  categoryid       TEXT,
  defaultlanguage  TEXT,
  tags             JSONB,
  caption          BOOLEAN,
  createdat        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updatedat        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ytvideos_channelid
  ON ytvideos (channelid);

CREATE INDEX IF NOT EXISTS idx_ytvideos_publishedat
  ON ytvideos (publishedat);

-- ----------------------------
-- Transcripts (must come before segments)
-- ----------------------------
CREATE TABLE IF NOT EXISTS ytvideotranscripts (
  transcriptid  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  videoid       TEXT NOT NULL REFERENCES ytvideos(videoid) ON DELETE CASCADE,
  language      TEXT NOT NULL DEFAULT 'en',
  source        TEXT NOT NULL DEFAULT 'manual' CHECK (source = ANY (ARRAY['manual','auto','other'])),
  fetchedat     TIMESTAMPTZ NOT NULL DEFAULT now(),
  fulltext      TEXT NOT NULL,
  UNIQUE (videoid, language, fetchedat)
);

CREATE TABLE IF NOT EXISTS yttranscriptsegments ( -- do we need this table?
  segmentid       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transcriptid    UUID NOT NULL REFERENCES ytvideotranscripts(transcriptid) ON DELETE CASCADE,
  startseconds    INT NOT NULL,
  durationseconds INT,
  text            TEXT NOT NULL
);

-- ----------------------------
-- Movie <-> YouTube Videos Link
-- ----------------------------
CREATE TABLE IF NOT EXISTS movieytvideos (
  movieid    UUID NOT NULL REFERENCES movies(movieid) ON DELETE CASCADE,
  videoid    TEXT NOT NULL REFERENCES ytvideos(videoid) ON DELETE CASCADE,
  videorole  TEXT NOT NULL DEFAULT 'official_trailer'
    CHECK (videorole IN ('official_trailer','teaser','clip','tv_spot','featurette','review','other')),
  isprimary  BOOLEAN NOT NULL DEFAULT false,
  weight     DOUBLE PRECISION NOT NULL DEFAULT 1.0,
  addedat    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (movieid, videoid)
);

CREATE INDEX IF NOT EXISTS idx_movieytvideos_movie_role_primary
  ON movieytvideos (movieid, videorole, isprimary);

CREATE INDEX IF NOT EXISTS idx_movieytvideos_videoid
  ON movieytvideos (videoid);

CREATE UNIQUE INDEX IF NOT EXISTS uq_movie_one_primary
  ON movieytvideos (movieid)
  WHERE isprimary = true;

-- ----------------------------
-- Video Metric Snapshots
-- ----------------------------
CREATE TABLE IF NOT EXISTS ytvideometricsnapshots (
  videoid      TEXT NOT NULL REFERENCES ytvideos(videoid) ON DELETE CASCADE,
  capturedat   TIMESTAMPTZ NOT NULL,
  viewcount    BIGINT NOT NULL,
  likecount    BIGINT,
  commentcount BIGINT NOT NULL,
  PRIMARY KEY (videoid, capturedat)
);

CREATE INDEX IF NOT EXISTS idx_ytvideometricsnapshots_capturedat
  ON ytvideometricsnapshots (capturedat);

-- ----------------------------
-- Movie Metric Snapshots
-- ----------------------------
CREATE TABLE IF NOT EXISTS moviemetricsnapshots (
  movieid         UUID NOT NULL REFERENCES movies(movieid) ON DELETE CASCADE,
  capturedat      TIMESTAMPTZ NOT NULL,
  viewstotal      BIGINT NOT NULL,
  likestotal      BIGINT,
  commentstotal   BIGINT NOT NULL,
  viewsdelta1d    BIGINT,
  viewsdelta7d    BIGINT,
  engagementrate  DOUBLE PRECISION, -- calculated as (total likes + total comments) / total views, can be null if no views
  PRIMARY KEY (movieid, capturedat)
);

CREATE INDEX IF NOT EXISTS idx_moviemetricsnapshots_movie_time
  ON moviemetricsnapshots (movieid, capturedat DESC);

-- ----------------------------
-- Comments + Threads
-- ----------------------------
CREATE TABLE IF NOT EXISTS ytcommentthreads (
  threadid         TEXT PRIMARY KEY,
  videoid          TEXT NOT NULL REFERENCES ytvideos(videoid) ON DELETE CASCADE,
  totalreplycount  INT NOT NULL DEFAULT 0,
  lastfetchedat    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_ytcommentthreads_videoid
  ON ytcommentthreads (videoid);

CREATE TABLE IF NOT EXISTS ytcomments (
  commentid        TEXT PRIMARY KEY,
  videoid          TEXT NOT NULL REFERENCES ytvideos(videoid) ON DELETE CASCADE,
  threadid         TEXT REFERENCES ytcommentthreads(threadid) ON DELETE SET NULL,
  parentcommentid  TEXT,
  text             TEXT NOT NULL,
  likecount        INT NOT NULL DEFAULT 0,
  authorchannelid  TEXT,
  publishedat      TIMESTAMPTZ NOT NULL,
  updatedat        TIMESTAMPTZ NOT NULL,
  ingestedat       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ytcomments_video_published
  ON ytcomments (videoid, publishedat DESC);

CREATE INDEX IF NOT EXISTS idx_ytcomments_video_updated
  ON ytcomments (videoid, updatedat DESC);

CREATE INDEX IF NOT EXISTS idx_ytcomments_parent
  ON ytcomments (parentcommentid);

-- ----------------------------
-- Insight Runs + Outputs
-- ----------------------------
CREATE TABLE IF NOT EXISTS insightruns (
  runid      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  studioid   UUID NOT NULL REFERENCES studios(studioid) ON DELETE CASCADE,
  runscope   TEXT NOT NULL DEFAULT 'top5',
  status     TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','success','failed')),
  params     JSONB,
  startedat  TIMESTAMPTZ NOT NULL DEFAULT now(),
  finishedat TIMESTAMPTZ,
  error      TEXT
);

CREATE INDEX IF NOT EXISTS idx_insightruns_studio_started
  ON insightruns (studioid, startedat DESC);

CREATE TABLE IF NOT EXISTS movieinsights (
  runid           UUID NOT NULL REFERENCES insightruns(runid) ON DELETE CASCADE,
  movieid         UUID NOT NULL REFERENCES movies(movieid) ON DELETE CASCADE,
  summary         TEXT NOT NULL,
  keytakeaways    JSONB,
  recommendations JSONB,
  createdat       TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (runid, movieid)
);

CREATE INDEX IF NOT EXISTS idx_movieinsights_movie_run
  ON movieinsights (movieid, runid);

CREATE TABLE IF NOT EXISTS movietopics (
  topicid           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  runid             UUID NOT NULL REFERENCES insightruns(runid) ON DELETE CASCADE,
  movieid           UUID NOT NULL REFERENCES movies(movieid) ON DELETE CASCADE,
  label             TEXT NOT NULL,
  summary           TEXT NOT NULL,
  keywords          JSONB,
  sentimentavg      DOUBLE PRECISION,
  volume            INT NOT NULL DEFAULT 0,
  consensusscore    DOUBLE PRECISION,
  controversyscore  DOUBLE PRECISION,
  createdat         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_movietopics_movie_run
  ON movietopics (movieid, runid);

CREATE INDEX IF NOT EXISTS idx_movietopics_run
  ON movietopics (runid);

CREATE TABLE IF NOT EXISTS topicevidencecomments (
  topicid    UUID NOT NULL REFERENCES movietopics(topicid) ON DELETE CASCADE,
  commentid  TEXT NOT NULL REFERENCES ytcomments(commentid) ON DELETE CASCADE,
  relevance  DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  createdat  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (topicid, commentid)
);

CREATE INDEX IF NOT EXISTS idx_topicevidence_topic
  ON topicevidencecomments (topicid, relevance DESC);

CREATE INDEX IF NOT EXISTS idx_topicevidence_comment
  ON topicevidencecomments (commentid);

CREATE TABLE IF NOT EXISTS movietopicaggregates (
  topicid       UUID PRIMARY KEY REFERENCES movietopics(topicid) ON DELETE CASCADE,
  commentcount  INT NOT NULL,
  pospct        DOUBLE PRECISION,
  negpct        DOUBLE PRECISION,
  neupct        DOUBLE PRECISION,
  topkeywords   JSONB,
  updatedat     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS movieinsightpayloads (
  runid                UUID NOT NULL REFERENCES insightruns(runid) ON DELETE CASCADE,
  movieid              UUID NOT NULL REFERENCES movies(movieid) ON DELETE CASCADE,
  movie_title          TEXT,
  key_takeaways        JSONB NOT NULL DEFAULT '[]'::jsonb,
  top_narratives       JSONB NOT NULL DEFAULT '[]'::jsonb,
  sentiment_breakdown  JSONB NOT NULL DEFAULT '{}'::jsonb,
  top_words            JSONB NOT NULL DEFAULT '[]'::jsonb,
  mood_signals         JSONB NOT NULL DEFAULT '[]'::jsonb,
  creator_risk         JSONB NOT NULL DEFAULT '{}'::jsonb,
  createdat            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updatedat            TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (runid, movieid)
);

CREATE INDEX IF NOT EXISTS idx_movieinsightpayloads_movie_run
  ON movieinsightpayloads (movieid, runid);

CREATE INDEX IF NOT EXISTS idx_movieinsightpayloads_run
  ON movieinsightpayloads (runid);

CREATE INDEX IF NOT EXISTS gin_movieinsightpayloads_key_takeaways
  ON movieinsightpayloads USING GIN (key_takeaways);

CREATE INDEX IF NOT EXISTS gin_movieinsightpayloads_top_narratives
  ON movieinsightpayloads USING GIN (top_narratives);

CREATE INDEX IF NOT EXISTS gin_movieinsightpayloads_sentiment_breakdown
  ON movieinsightpayloads USING GIN (sentiment_breakdown);

CREATE INDEX IF NOT EXISTS gin_movieinsightpayloads_creator_risk
  ON movieinsightpayloads USING GIN (creator_risk);

-- ----------------------------
-- Analytics Snapshots
-- ----------------------------
CREATE TABLE IF NOT EXISTS movieanalyticssnapshots (
  snapshotid          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  movieid             UUID NOT NULL REFERENCES movies(movieid) ON DELETE CASCADE,
  computedat          TIMESTAMPTZ NOT NULL DEFAULT now(),
  totalreviewvideos   INT NOT NULL DEFAULT 0,
  averagesentiment    DOUBLE PRECISION,
  totalviews          BIGINT,
  totallikes          BIGINT,
  pospct              DOUBLE PRECISION,
  negpct              DOUBLE PRECISION,
  neupct              DOUBLE PRECISION,
  topsentimentwords   JSONB,
  creatorriskscore    DOUBLE PRECISION CHECK (creatorriskscore >= 0 AND creatorriskscore <= 100),
  moodsignals         JSONB,
  keydiscussiontopics JSONB
);

CREATE TABLE IF NOT EXISTS moviediscussiontopics (
  topicid    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  movieid    UUID NOT NULL REFERENCES movies(movieid) ON DELETE CASCADE,
  computedat TIMESTAMPTZ NOT NULL DEFAULT now(),
  topiclabel TEXT NOT NULL,
  pct        DOUBLE PRECISION NOT NULL CHECK (pct >= 0 AND pct <= 1),
  keywords   JSONB,
  summary    TEXT
);

CREATE TABLE IF NOT EXISTS movieengagedreviewvideos (
  movieid         UUID NOT NULL REFERENCES movies(movieid) ON DELETE CASCADE,
  computedat      TIMESTAMPTZ NOT NULL DEFAULT now(),
  videoid         TEXT NOT NULL REFERENCES ytvideos(videoid) ON DELETE CASCADE,
  rank            INT NOT NULL,
  views           BIGINT,
  likes           BIGINT,
  comments        BIGINT,
  engagementrate  DOUBLE PRECISION,
  PRIMARY KEY (movieid, computedat, rank),
  UNIQUE (movieid, computedat, videoid)
);

CREATE TABLE IF NOT EXISTS moviereviewvelocity (
  movieid            UUID NOT NULL REFERENCES movies(movieid) ON DELETE CASCADE,
  weekstart          DATE NOT NULL,
  computedat         TIMESTAMPTZ NOT NULL DEFAULT now(),
  reviewsthisweek    INT NOT NULL DEFAULT 0,
  cumulativereviews  INT NOT NULL DEFAULT 0,
  PRIMARY KEY (movieid, weekstart, computedat)
);

CREATE TABLE IF NOT EXISTS moviesentimenttimeline (
  movieid           UUID NOT NULL REFERENCES movies(movieid) ON DELETE CASCADE,
  periodstart       DATE NOT NULL,
  periodend         DATE NOT NULL,
  computedat        TIMESTAMPTZ NOT NULL DEFAULT now(),
  avgsentiment      DOUBLE PRECISION,
  pospct            DOUBLE PRECISION,
  negpct            DOUBLE PRECISION,
  neupct            DOUBLE PRECISION,
  reviewvideocount  INT NOT NULL DEFAULT 0,
  PRIMARY KEY (movieid, periodstart, computedat)
);

COMMIT;