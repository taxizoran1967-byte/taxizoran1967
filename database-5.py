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
    conn.commit()
    conn.close()


def dodaj_voznju(od_adresa, do_adresa, km, tarifa_naziv, cena_po_km, start_taksa, ukupna_cena, napomena=""):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now()
    cur.execute("""
        INSERT INTO voznje (datum, vreme, od_adresa, do_adresa, km, tarifa_naziv,
                             cena_po_km, start_taksa, ukupna_cena, napomena)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now.strftime("%Y-%m-%d"), now.strftime("%H:%M"),
        od_adresa, do_adresa, km, tarifa_naziv,
        cena_po_km, start_taksa, ukupna_cena, napomena
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


def zbir_voznji(rows):
    """Vraca (broj_voznji, ukupan_prihod, ukupno_km)"""
    broj = len(rows)
    prihod = sum(r["ukupna_cena"] for r in rows)
    km = sum(r["km"] for r in rows)
    return broj, prihod, km
