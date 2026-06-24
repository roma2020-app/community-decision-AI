-- Migration Script V1: Initialize Community Decision Intelligence Schema
-- Applied on: 2026-06-23

BEGIN;

-- Create community_data table if not exists
CREATE TABLE IF NOT EXISTS community_data (
    id SERIAL PRIMARY KEY,
    area VARCHAR(255) NOT NULL,
    complaints INTEGER DEFAULT 0,
    traffic VARCHAR(50),
    aqi INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create community_insights table if not exists
CREATE TABLE IF NOT EXISTS community_insights (
    id SERIAL PRIMARY KEY,
    area VARCHAR(255) NOT NULL,
    insight TEXT NOT NULL,
    priority_score DOUBLE PRECISION DEFAULT 0.0,
    recommendation TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes on area for performance
CREATE INDEX IF NOT EXISTS idx_community_data_area ON community_data(area);
CREATE INDEX IF NOT EXISTS idx_community_insights_area ON community_insights(area);

COMMIT;
