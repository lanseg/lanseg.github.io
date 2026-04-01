import collections
import pathlib
import sqlite3

import numpy as np

Face = collections.namedtuple("Face", ["enc", "img", "location", "label"])

class DB:
    def __init__(self, filename):
        self.db = sqlite3.connect(filename)
        with self.db:
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    enc BLOB NOT NULL,
                    image TEXT NOT NULL,
                    location TEXT NOT NULL,
                    label INTEGER
                );""")
            self.db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_object ON faces(enc, image);")
            self.db.execute("CREATE INDEX IF NOT EXISTS idx_label ON faces(label);")
            self.db.execute("CREATE INDEX IF NOT EXISTS idx_image ON faces(image);")

    def save(self, faces: list[Face]):
        with self.db:
            for face in faces:
                self.db.execute("""
                           INSERT INTO faces (enc, image, location, label) VALUES (?, ?, ?, ?)
                           ON CONFLICT(enc, image) DO UPDATE
                           SET label=excluded.label, location=excluded.location;
                    """, (
                    face.enc.tobytes(),
                    str(face.img),
                    ",".join(map(str, face.location)),
                    face.label
                ))

    def load(self) -> list[Face]:
        all_faces = []
        with self.db:
            for row in self.db.execute("""SELECT enc, image, location, label FROM faces"""):
                all_faces.append(Face(
                    np.frombuffer(row[0], dtype=np.float32),
                    pathlib.Path(row[1]),
                    list(map(int, row[2].split(","))),
                    row[3]
                ))
        return all_faces

    def find(self, label):
        result = []
        with self.db:
            for row in self.db.execute("""
                SELECT DISTINCT t1.enc, t1.image, t1.location, t1.label
                FROM faces t1
                JOIN faces t2 ON t1.image = t2.image
                WHERE t2.label = ?;
            """, (label,)):
                result.append(Face(
                    np.frombuffer(row[0], dtype=np.float32),
                    pathlib.Path(row[1]),
                    list(map(int, row[2].split(","))),
                    row[3]
                ))
        return result

    def stats(self):
        result = []
        with self.db:
            for row in self.db.execute("""
                SELECT label, COUNT(*) as cnt FROM faces GROUP BY label ORDER BY cnt DESC;
            """):
                result.append({"label": row[0], "count": row[1]})
        return result