-- Script to create PostgreSQL database and user for Facebook scraper
-- This can be run directly with psql or used as a reference for pgAdmin setup

-- ========================================================================
-- PGADMIN INSTRUCTIONS:
-- ========================================================================
-- 1. Open pgAdmin and connect to your PostgreSQL server
-- 2. Right-click on "Databases" and select "Create" > "Database..."
-- 3. Enter "facebook_scraper_beta" as the database name
-- 4. Set the owner to "postgres" (or your preferred database user)
-- 5. Click "Save" to create the database
-- 6. Right-click the new database and select "Query Tool" 
-- 7. Run any additional commands below (like extensions) if needed
-- ========================================================================

-- Create database if it doesn't exist (when running via psql)
CREATE DATABASE facebook_scraper_beta;

-- Note: The following commands should be run after connecting to the new database
-- For psql, this would be done with: \connect facebook_scraper_beta
-- For pgAdmin, right-click the database and select "Query Tool"

-- Create any extensions if needed (uncomment if needed)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
-- CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- For faster indexing

-- When running with psql, this grants privileges
-- In pgAdmin, do this through the GUI: right-click on database > Properties > Privileges
-- GRANT ALL PRIVILEGES ON DATABASE facebook_scraper_beta TO postgres;
