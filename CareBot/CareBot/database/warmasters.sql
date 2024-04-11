PRAGMA foreign_keys = 0;

CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                          FROM warmasters;

DROP TABLE warmasters;

CREATE TABLE warmasters (
    id          INTEGER PRIMARY KEY
                        UNIQUE
                        NOT NULL,
    telegram_id TEXT    UNIQUE,
    alliance    TEXT    DEFAULT (0) 
);

INSERT INTO warmasters (
                           id,
                           telegram_id,
                           alliance
                       )
                       SELECT id,
                              telegram_id,
                              alliance
                         FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;
