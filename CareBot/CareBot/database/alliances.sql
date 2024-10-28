CREATE TABLE alliances (
    name TEXT    NOT NULL
                 UNIQUE,
    id   INTEGER UNIQUE
                 NOT NULL
                 PRIMARY KEY
);
