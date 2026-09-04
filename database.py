"""
database.py
Lokalna SQLite baza za evidenciju voznji taksi aplikacije.
"""

import sqlite3
import os
from datetime import datetime

DB_NAME = "taksi_evidencija.db"


def get_db_path():
    """Vraca putanju do baze - na Androidu koristi app-specific storage."""
    try:
        from android.storage import app_storage_path  # type: ignore
        base = app_storage_path()
    except Exception:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, DB_NAME)


def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS voznje (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum TEXT NOT NULL,
            vreme TEXT NOT NULL,
            od_adresa TEXT,
            do_adresa TEXT,
            km REAL NOT NULL,
            tarifa_naziv TEXT NOT NULL,
            cena_po_km REAL NOT NULL,
            start_taksa REAL NOT NULL,
            ukupna_cena REAL NOT NULL,
            napomena TEXT
        )
    """)

    # Migracija za stare baze: dodajemo kolonu za vreme pocetka voznje.
    # "vreme" kolona od ranije vec sluzi kao vreme KRAJA (upisuje se
    # onog trenutka kad se voznja sacuva, tj. kad se zavrsi), samo do
    # sad nije postojalo posebno vreme pocetka da se prikaze pored njega.
    cur.execute("PRAGMA table_info(voznje)")
    postojece_kolone = [red[1] for red in cur.fetchall()]
    if "vreme_pocetka" not in postojece_kolone:
        cur.execute("ALTER TABLE voznje ADD COLUMN vreme_pocetka TEXT")

    conn.commit()
    conn.close()


def dodaj_voznju(od_adresa, do_adresa, km, tarifa_naziv, cena_po_km, start_taksa, ukupna_cena, napomena="", vreme_pocetka=None):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now()
    cur.execute("""
        INSERT INTO voznje (datum, vreme, od_adresa, do_adresa, km, tarifa_naziv,
                             cena_po_km, start_taksa, ukupna_cena, napomena, vreme_pocetka)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now.strftime("%Y-%m-%d"), now.strftime("%H:%M"),
        od_adresa, do_adresa, km, tarifa_naziv,
        cena_po_km, start_taksa, ukupna_cena, napomena, vreme_pocetka
    ))
    conn.commit()
    conn.close()


def obrisi_voznju(voznja_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM voznje WHERE id = ?", (voznja_id,))
    conn.commit()
    conn.close()


def sve_voznje(limit=200):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM voznje ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def voznje_za_datum(datum_str):
    """datum_str format YYYY-MM-DD"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM voznje WHERE datum = ? ORDER BY vreme", (datum_str,))
    rows = cur.fetchall()
    conn.close()
    return rows


def voznje_za_mesec(godina_mesec_str):
    """godina_mesec_str format YYYY-MM"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM voznje WHERE datum LIKE ? ORDER BY datum, vreme", (f"{godina_mesec_str}-%",))
    rows = cur.fetchall()
    conn.close()
    return rows


def voznje_izmedju(pocetak_str, kraj_str):
    """pocetak_str i kraj_str format YYYY-MM-DD, oba kraja ukljucena.
    Koristi se npr. za nedeljni izvestaj (ponedeljak - danas)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM voznje WHERE datum BETWEEN ? AND ? ORDER BY datum, vreme",
        (pocetak_str, kraj_str),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def sve_voznje_za_izvoz():
    """Vraca BAS SVE voznje, bez limita - koristi se za pravljenje
    backup fajla (za razliku od sve_voznje() koja ima limit za prikaz
    u Evidenciji)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM voznje ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows


def broj_voznji():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS n FROM voznje")
    n = cur.fetchone()["n"]
    conn.close()
    return n


def voznja_postoji(datum, vreme, km, ukupna_cena):
    """Provera da li vec postoji ista voznja u bazi - koristi se pri
    vracanju iz backup fajla, da se ista voznja ne doda dvaput ako se
    backup ucita vise puta."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM voznje WHERE datum = ? AND vreme = ? AND km = ? AND ukupna_cena = ? LIMIT 1",
        (datum, vreme, km, ukupna_cena),
    )
    red = cur.fetchone()
    conn.close()
    return red is not None


def uvezi_voznju_sirovo(v):
    """Ubacuje voznju sa TACNO onim vrednostima iz backup fajla - za
    razliku od dodaj_voznju(), ne stavlja 'sada' kao datum/vreme, nego
    zadrzava original (jer se ovde vraca stara, vec zavrsena voznja)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO voznje (datum, vreme, od_adresa, do_adresa, km, tarifa_naziv,
                             cena_po_km, start_taksa, ukupna_cena, napomena, vreme_pocetka)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        v.get("datum"), v.get("vreme"), v.get("od_adresa"), v.get("do_adresa"),
        v.get("km"), v.get("tarifa_naziv"), v.get("cena_po_km"), v.get("start_taksa"),
        v.get("ukupna_cena"), v.get("napomena", ""), v.get("vreme_pocetka"),
    ))
    conn.commit()
    conn.close()


def zbir_voznji(rows):
    """Vraca (broj_voznji, ukupan_prihod, ukupno_km)"""
    broj = len(rows)
    prihod = sum(r["ukupna_cena"] for r in rows)
    km = sum(r["km"] for r in rows)
    return broj, prihod, km
