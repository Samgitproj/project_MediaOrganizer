import sqlite3
import os

# Pad naar de database (pas eventueel aan)
DB_PATH = os.path.join("C:/OneDrive/Vioprint/OneDrive - Vioprint/software projecten/MediaOrganizer", "media_analyse.db")

def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabel 1: foto's
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fotos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pad TEXT NOT NULL,
        bestandsnaam TEXT,
        map TEXT,
        extensie TEXT,
        bestandsgrootte INTEGER,
        aanmaakdatum TEXT,
        exif_datum TEXT,
        laatst_bewerkt TEXT
    )
    """)

    # Tabel 2: analyse
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analyse (
        foto_id INTEGER PRIMARY KEY,
        bevat_gezicht BOOLEAN,
        FOREIGN KEY(foto_id) REFERENCES fotos(id)
    )
    """)

    # Tabel 3: interactie
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interactie (
        foto_id INTEGER PRIMARY KEY,
        geselecteerd BOOLEAN,
        te_verwijderen BOOLEAN,
        verplaatst_naar TEXT,
        beoordeling TEXT,
        FOREIGN KEY(foto_id) REFERENCES fotos(id)
    )
    """)

    # Tabel 4: reeksen
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reeksen (
        reeks_id INTEGER PRIMARY KEY AUTOINCREMENT,
        starttijd TEXT,
        eindtijd TEXT,
        aantal_fotos INTEGER,
        map TEXT,
        interval INTEGER
    )
    """)

    # Tabel 5: logging
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        foto_id INTEGER,
        actietype TEXT,
        timestamp TEXT,
        detail TEXT,
        FOREIGN KEY(foto_id) REFERENCES fotos(id)
    )
    """)

    conn.commit()
    conn.close()
    print(f"[INFO] Database aangemaakt of bijgewerkt op: {DB_PATH}")

if __name__ == "__main__":
    create_database()
