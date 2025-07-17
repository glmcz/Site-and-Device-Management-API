CREATE EXTENSION IF NOT EXISTS pg_cron;

DROP TABLE users;
CREATE TABLE users (
    id UUID PRIMARY KEY,
    name VARCHAR(100),
    access_level VARCHAR(50)
);

-- drop table etl_jobs;
CREATE TABLE sites (
    id UUID PRIMARY KEY,
    name VARCHAR(100),
    user_id UUID
);

DROP TABLE devices;
CREATE TABLE if not exists devices (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    site_id UUID,
    type VARCHAR(100)
);

DROP TABLE IF EXISTS device_metrics;
CREATE TABLE if not exists device_metrics (
    time TIMESTAMPTZ NOT NULL,
    device_id UUID,
    metric_type VARCHAR(100),
    value DOUBLE PRECISION,
    PRIMARY KEY (time, device_id, metric_type)
);

SELECT create_hypertable('device_metrics', by_range('time', INTERVAL '1 day'));


CREATE SCHEMA dev_stats;
GRANT ALL ON SCHEMA dev_stats TO szn;

-- redirect to new schema
SET search_path TO dev_stats, public;

-- reset to default schema
RESET search_path;
SET TIME ZONE 'Europe/Prague';
