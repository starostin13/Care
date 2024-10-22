CREATE TABLE edges (
    id            INTEGER PRIMARY KEY
                          UNIQUE,
    left_hexagon  INTEGER,
    right_hexagon INTEGER,
    state         INTEGER
);
