PRAGMA foreign_keys = 0;

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

INSERT INTO warmasters (
                           id,
                           telegram_id,
                           alliance,
                           nickname,
                           registered_as
                       )
                       SELECT id,
                              telegram_id,
                              alliance,
                              nickname,
                              registered_as
                         FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;
