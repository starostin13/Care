PRAGMA foreign_keys = 0;

CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                          FROM battles;

DROP TABLE battles;

CREATE TABLE battles (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER,
    fstplayer  INTEGER,
    sndplayer  INTEGER
);

INSERT INTO battles (
                        id,
                        mission_id,
                        fstplayer,
                        sndplayer
                    )
                    SELECT id,
                           mission_id,
                           "1stplayer",
                           "2ndplayer"
                      FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;
