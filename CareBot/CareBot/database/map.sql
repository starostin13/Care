CREATE TABLE map (
    id        INTEGER PRIMARY KEY
                      UNIQUE
                      NOT NULL,
    planet_id INTEGER,
    state     TEXT,
    patron    INTEGER
);

INSERT INTO map (
                    patron,
                    state,
                    planet_id,
                    id
                )
                VALUES (
                    1,
                    NULL,
                    1,
                    2
                ),
                (
                    0,
                    NULL,
                    1,
                    3
                ),
                (
                    2,
                    NULL,
                    1,
                    4
                ),
                (
                    1,
                    NULL,
                    1,
                    5
                ),
                (
                    0,
                    NULL,
                    1,
                    6
                ),
                (
                    2,
                    NULL,
                    1,
                    7
                ),
                (
                    1,
                    NULL,
                    1,
                    8
                );
