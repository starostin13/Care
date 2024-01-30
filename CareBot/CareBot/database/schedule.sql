CREATE TABLE schedule (
    id            INTEGER PRIMARY KEY
                          NOT NULL
                          UNIQUE,
    date          TEXT    NOT NULL,
    rules         TEXT,
    user_telegram TEXT    NOT NULL
);