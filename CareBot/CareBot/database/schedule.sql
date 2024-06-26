CREATE TABLE schedule (
    id            INTEGER PRIMARY KEY
                          NOT NULL
                          UNIQUE,
    date          TEXT,
    rules         TEXT,
    user_telegram TEXT    NOT NULL,
    date_week     INTEGER
);

INSERT INTO schedule (
                         id,
                         date,
                         rules,
                         user_telegram
                     )
                     SELECT id,
                            date,
                            rules,
                            user_telegram
                       FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;
