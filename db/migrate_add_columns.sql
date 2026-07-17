-- Миграция для уже существующей таблицы vacancies (созданной по старой схеме).
-- Безопасно запускать повторно — IF NOT EXISTS.

ALTER TABLE vacancies ADD COLUMN IF NOT EXISTS category VARCHAR(150);
ALTER TABLE vacancies ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE vacancies ADD COLUMN IF NOT EXISTS last_checked_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_vacancies_active_created ON vacancies (is_active, created_at);