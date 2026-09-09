-- setup_least_privilege_gateway_role.sql
-- Production Provisioning Script for Secure DB Access Gateway
--
-- PURPOSE:
-- Establishes a strictly contained, read-only database role for the Secure DB Access Gateway.
-- Enforces defense-in-depth: Even if application-layer SQL safety checks were bypassed,
-- the PostgreSQL engine will reject any INSERT, UPDATE, DELETE, TRUNCATE, ALTER, DROP,
-- or dangerous function calls.
--
-- USAGE:
-- Execute as a PostgreSQL superuser (e.g., 'postgres') in the target database:
--   psql -U postgres -d your_database -f setup_least_privilege_gateway_role.sql

\set ON_ERROR_STOP on

BEGIN;

-- 1. Create dedicated gateway role (if not already exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'gateway_readonly_user') THEN
        -- Password should be substituted or managed via IAM / external secret manager
        CREATE ROLE gateway_readonly_user WITH LOGIN PASSWORD 'REPLACE_WITH_SECURE_PASSWORD';
    END IF;
END
$$;

-- 2. Revoke all default permissions
REVOKE ALL ON DATABASE current_database() FROM gateway_readonly_user;
REVOKE ALL ON SCHEMA public FROM gateway_readonly_user;

-- 3. Grant connection and schema usage only
GRANT CONNECT ON DATABASE current_database() TO gateway_readonly_user;
GRANT USAGE ON SCHEMA public TO gateway_readonly_user;

-- 4. Grant strictly SELECT on all existing tables and views
GRANT SELECT ON ALL TABLES IN SCHEMA public TO gateway_readonly_user;

-- 5. Ensure future tables created by migrations also default to SELECT-only
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT ON TABLES TO gateway_readonly_user;

-- 6. Explicitly revoke any write, truncate, or DDL privileges
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM gateway_readonly_user;

-- 7. Block dangerous system and file access functions
-- Revoke execution of dynamic execution and file operations from PUBLIC
REVOKE EXECUTE ON FUNCTION pg_read_file(text) FROM PUBLIC, gateway_readonly_user;
REVOKE EXECUTE ON FUNCTION pg_read_file(text, bigint, bigint) FROM PUBLIC, gateway_readonly_user;
REVOKE EXECUTE ON FUNCTION pg_read_file(text, bigint, bigint, boolean) FROM PUBLIC, gateway_readonly_user;
REVOKE EXECUTE ON FUNCTION pg_read_binary_file(text) FROM PUBLIC, gateway_readonly_user;
REVOKE EXECUTE ON FUNCTION pg_read_binary_file(text, bigint, bigint) FROM PUBLIC, gateway_readonly_user;
REVOKE EXECUTE ON FUNCTION pg_read_binary_file(text, bigint, bigint, boolean) FROM PUBLIC, gateway_readonly_user;

-- 8. Set session-level read-only and statement timeout defaults on the role itself
ALTER ROLE gateway_readonly_user SET default_transaction_read_only = on;
ALTER ROLE gateway_readonly_user SET statement_timeout = '15s';
ALTER ROLE gateway_readonly_user SET idle_in_transaction_session_timeout = '10s';

COMMIT;

-- Verify setup
-- SELECT rolname, rolcanlogin FROM pg_roles WHERE rolname = 'gateway_readonly_user';
