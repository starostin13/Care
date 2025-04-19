CREATE TABLE edges (
    id            INTEGER PRIMARY KEY
                          UNIQUE
                          NOT NULL,
    left_hexagon  INTEGER,
    right_hexagon INTEGER,
    state         INTEGER
);


INSERT INTO edges (
                      state,
                      right_hexagon,
                      left_hexagon,
                      id
                  )
                  VALUES (
                      NULL,
                      8,
                      2,
                      1
                  ),
                  (
                      NULL,
                      7,
                      2,
                      2
                  ),
                  (
                      NULL,
                      7,
                      6,
                      3
                  ),
                  (
                      NULL,
                      6,
                      2,
                      4
                  ),
                  (
                      NULL,
                      6,
                      5,
                      5
                  ),
                  (
                      NULL,
                      5,
                      2,
                      6
                  ),
                  (
                      NULL,
                      5,
                      4,
                      7
                  ),
                  (
                      NULL,
                      4,
                      2,
                      8
                  ),
                  (
                      NULL,
                      4,
                      3,
                      9
                  ),
                  (
                      NULL,
                      2,
                      3,
                      10
                  ),
                  (
                      NULL,
                      8,
                      3,
                      11
                  ),
                  (
                      NULL,
                      8,
                      7,
                      12
                  );
