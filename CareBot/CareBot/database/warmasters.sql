PRAGMA foreign_keys = 0;

-- БЕЗОПАСНАЯ миграция: сохраняем ВСЕ данные при добавлении новых колонок
CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                          FROM warmasters;

DROP TABLE warmasters;

CREATE TABLE warmasters (
    id            INTEGER PRIMARY KEY
                          UNIQUE
                          NOT NULL,
    telegram_id   TEXT    UNIQUE,
    alliance      INTEGER DEFAULT (0),
    nickname      TEXT,
    registered_as TEXT    UNIQUE,
    faction       TEXT,
    language      TEXT    DEFAULT ('ru'),
    notifications_enabled INTEGER DEFAULT (1),
    is_admin      INTEGER DEFAULT (0)
);

-- КРИТИЧНО: Восстанавливаем ВСЕ существующие данные с сохранением новых колонок
INSERT INTO warmasters (
    id,
    telegram_id,
    alliance,
    nickname,
    registered_as,
    faction,
    language,
    notifications_enabled,
    is_admin
) SELECT 
    id,
    telegram_id,
    alliance,
    nickname,
    registered_as,
    COALESCE(faction, NULL) as faction,
    COALESCE(language, 'ru') as language,
    COALESCE(notifications_enabled, 1) as notifications_enabled,
    COALESCE(is_admin, 0) as is_admin
FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;
