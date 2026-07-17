-- === ОБНОВЛЁННАЯ СХЕМА ===
-- Накатить: psql "$DATABASE_URL" -f db/schema.sql

CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);
INSERT INTO sources (name) VALUES ('hh.kz') ON CONFLICT DO NOTHING;
INSERT INTO sources (name) VALUES ('olx.kz') ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS vacancies (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES sources(id),
    external_id VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    salary_from INT,
    salary_to INT,
    currency VARCHAR(10) DEFAULT 'KZT',
    city VARCHAR(100),
    category VARCHAR(150),
    description_raw TEXT,
    description_clean TEXT,
    url TEXT UNIQUE NOT NULL,
    embedding REAL[],
    is_active BOOLEAN DEFAULT TRUE,
    last_checked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, external_id)
);

CREATE INDEX IF NOT EXISTS idx_vacancies_active_created ON vacancies (is_active, created_at);
CREATE INDEX IF NOT EXISTS idx_vacancies_city ON vacancies (city);

CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    username VARCHAR(100),
    city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION cosine_similarity(a REAL[], b FLOAT8[])
RETURNS FLOAT8 AS $$
DECLARE
    dot FLOAT8 := 0;
    norm_a FLOAT8 := 0;
    norm_b FLOAT8 := 0;
    i INT;
BEGIN
    FOR i IN 1..array_length(a, 1) LOOP
        dot := dot + a[i] * b[i];
        norm_a := norm_a + a[i] * a[i];
        norm_b := norm_b + b[i] * b[i];
    END LOOP;
    IF norm_a = 0 OR norm_b = 0 THEN
        RETURN 0;
    END IF;
    RETURN dot / (sqrt(norm_a) * sqrt(norm_b));
END;
$$ LANGUAGE plpgsql IMMUTABLE;