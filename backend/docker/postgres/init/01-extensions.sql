-- Runs once on first container start (empty data volume). Spec §6: extensions pgcrypto, vector.
-- Alembic migrations also issue CREATE EXTENSION IF NOT EXISTS, so this is a convenience only.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
