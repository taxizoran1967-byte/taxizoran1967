"""
ekran_izvoz.py
Izvoz izvestaja u PDF (za stampu) i CSV (za Excel/knjigovodju), za
proizvoljan period (dnevni/nedeljni/mesecni/polugodisnji/godisnji).

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py.
"""

import os
import calendar
import re
from datetime import datetime, timedelta

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty

from servisi import database as db


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_GORIVO_REF = None                # main._GORIVO_REF
_SERVIS_REF = None                # main._SERVIS_REF
_TROSKOVI_REF = None              # main._TROSKOVI_REF
_VOZAC_REF = None                 # main._VOZAC_REF
_FORMATIRAJ_CENU = None           # main.formatiraj_cenu
_STAVKE_IZMEDJU = None            # main._stavke_izmedju (deljeno i sa grafik_zarade.py)
_IZRACUNAJ_POTROSNJU_INTERVALE = None  # main._izracunaj_potrosnju_intervale (deljeno i sa grafik_zarade.py)
_REGISTRUJ_FONT_ZA_PDF = None     # main._registruj_font_za_pdf (deljeno i sa ekran_uputstvo.py)
_IMA_DOZVOLU_SVI_FAJLOVI = None   # main._ima_dozvolu_svi_fajlovi
_PUTANJA_BACKUP_FOLDERA = None    # main._putanja_backup_foldera
_PRIKAZI_POPUP = None             # main._prikazi_popup_poruku


def poveži(gorivo_obj, servis_obj, troskovi_obj, vozac_obj,
           formatiraj_cenu_fn, stavke_izmedju_fn, potrosnju_intervale_fn,
           registruj_font_fn, ima_dozvolu_fn, putanja_backup_fn, prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_izvoz'."""
    global _GORIVO_REF, _SERVIS_REF, _TROSKOVI_REF, _VOZAC_REF
    global _FORMATIRAJ_CENU, _STAVKE_IZMEDJU, _IZRACUNAJ_POTROSNJU_INTERVALE
    global _REGISTRUJ_FONT_ZA_PDF, _IMA_DOZVOLU_SVI_FAJLOVI, _PUTANJA_BACKUP_FOLDERA, _PRIKAZI_POPUP
    _GORIVO_REF = gorivo_obj
    _SERVIS_REF = servis_obj
    _TROSKOVI_REF = troskovi_obj
    _VOZAC_REF = vozac_obj
    _FORMATIRAJ_CENU = formatiraj_cenu_fn
    _STAVKE_IZMEDJU = stavke_izmedju_fn
    _IZRACUNAJ_POTROSNJU_INTERVALE = potrosnju_intervale_fn
    _REGISTRUJ_FONT_ZA_PDF = registruj_font_fn
    _IMA_DOZVOLU_SVI_FAJLOVI = ima_dozvolu_fn
    _PUTANJA_BACKUP_FOLDERA = putanja_backup_fn
    _PRIKAZI_POPUP = prikazi_popup_fn


def generisi_izvestaj_excel(naslov_izvestaja, pocetak_str, kraj_str, putanja_fajla):
    """Pravi profesionalni Excel (.xlsx) izvestaj za knjigovodstvo, za
    isti period koji koristi i generisi_izvestaj_pdf().

    Za razliku od PDF-a (napravljen za stampu/citanje), ovaj fajl je
    napravljen da se DALJE OBRADJUJE u Excel-u:
      - poseban list za svaku kategoriju (Voznje, Gorivo, Servisi,
        Troskovi) - sirovi podaci, red po red, sa zamrznutim
        zaglavljem i automatskim filterom na svakoj koloni,
      - list "Pregled" na pocetku sa zbirnim brojkama koje su PRAVE
        Excel formule (SUM/COUNT preko celih kolona drugih listova),
        ne samo gotovi brojevi - otvara se i moze da se proveri
        odakle dolazi svaki zbir, i automatski se osvezavaju ako
        neko naknadno rucno doda/izmeni po neki red.

    Iznosi su UVEK u RSD (dinarima), onako kako se cuvaju u bazi - bez
    obzira na to da li je u samoj app-i trenutno izabran prikaz u RSD
    ili EUR, jer za knjigovodstvo treba prava, nepromenjena vrednost.

    Vraca broj redova (voznje + gorivo + servisi + troskovi) upisanih
    ukupno, za prikaz u potvrdnoj poruci.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    voznje = db.voznje_izmedju(pocetak_str, kraj_str)
    gorivo_period = _STAVKE_IZMEDJU(_GORIVO_REF.stavke, pocetak_str, kraj_str)
    servisi_period = _STAVKE_IZMEDJU(_SERVIS_REF.stavke, pocetak_str, kraj_str)
    troskovi_period = _STAVKE_IZMEDJU(_TROSKOVI_REF.stavke, pocetak_str, kraj_str)

    FONT_ZAGLAVLJA = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    FILL_ZAGLAVLJA = PatternFill(start_color="3A3560", end_color="3A3560", fill_type="solid")
    FONT_NASLOV = Font(name="Calibri", bold=True, size=16, color="3A3560")
    FONT_PODNASLOV = Font(name="Calibri", size=10, italic=True, color="666666")
    FONT_SEKCIJA = Font(name="Calibri", bold=True, size=12, color="3A3560")
    FONT_ZBIR = Font(name="Calibri", bold=True, size=11)
    FONT_NETO = Font(name="Calibri", bold=True, size=13, color="FFFFFF")
    FILL_NETO = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
    OKVIR = Border(
        left=Side(style="thin", color="CCCCCC"), right=Side(style="thin", color="CCCCCC"),
        top=Side(style="thin", color="CCCCCC"), bottom=Side(style="thin", color="CCCCCC"),
    )
    RSD = '#,##0.00" RSD"'
    DATUM_FMT = "yyyy-mm-dd"

    def _datum_celija(datum_str):
        try:
            return datetime.strptime(datum_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return datum_str or "-"

    def _list_sa_zaglavljem(ws, kolone, sirine):
        for idx, naziv in enumerate(kolone, start=1):
            c = ws.cell(row=1, column=idx, value=naziv)
            c.font = FONT_ZAGLAVLJA
            c.fill = FILL_ZAGLAVLJA
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.freeze_panes = "A2"
        ws.row_dimensions[1].height = 26
        for idx, sirina in enumerate(sirine, start=1):
            ws.column_dimensions[get_column_letter(idx)].width = sirina

    wb = Workbook()

    # ------------------------------------------------------------
    # LIST: Voznje
    # ------------------------------------------------------------
    ws_v = wb.active
    ws_v.title = "Voznje"
    _list_sa_zaglavljem(
        ws_v,
        ["R.br.", "Datum", "Pocetak", "Kraj", "Adresa polaska", "Adresa dolaska",
         "Km", "Tarifa", "Cena/km", "Start taksa", "Ukupna cena", "Napomena"],
        [6, 12, 9, 9, 32, 32, 8, 20, 10, 12, 13, 30],
    )
    for i, v in enumerate(voznje, start=1):
        vreme_pocetka = v["vreme_pocetka"] if ("vreme_pocetka" in v.keys() and v["vreme_pocetka"]) else "-"
        red = i + 1
        ws_v.append([
            i, _datum_celija(v["datum"]), vreme_pocetka, v["vreme"],
            v["od_adresa"] or "-", v["do_adresa"] or "-",
            v["km"], v["tarifa_naziv"], v["cena_po_km"], v["start_taksa"],
            v["ukupna_cena"], v["napomena"] or "",
        ])
        ws_v.cell(row=red, column=2).number_format = DATUM_FMT
        ws_v.cell(row=red, column=7).number_format = "#,##0.0"
        ws_v.cell(row=red, column=9).number_format = RSD
        ws_v.cell(row=red, column=10).number_format = RSD
        ws_v.cell(row=red, column=11).number_format = RSD
    if voznje:
        ws_v.auto_filter.ref = f"A1:L{len(voznje) + 1}"

    # ------------------------------------------------------------
    # LIST: Gorivo
    # ------------------------------------------------------------
    ws_g = wb.create_sheet("Gorivo")
    _list_sa_zaglavljem(
        ws_g,
        ["R.br.", "Datum", "Tip", "Litara", "Km na pumpi", "Cena", "Napomena"],
        [6, 12, 12, 10, 14, 13, 32],
    )
    gorivo_sortirano = sorted(gorivo_period, key=lambda s: s.get("datum", ""))
    for i, s in enumerate(gorivo_sortirano, start=1):
        red = i + 1
        ws_g.append([
            i, _datum_celija(s.get("datum")), s.get("tip", "-"),
            s.get("litara", 0), s.get("km_pumpe") or "-", s.get("cena", 0),
            s.get("napomena") or "",
        ])
        ws_g.cell(row=red, column=2).number_format = DATUM_FMT
        ws_g.cell(row=red, column=4).number_format = "#,##0.00"
        ws_g.cell(row=red, column=6).number_format = RSD
    if gorivo_sortirano:
        ws_g.auto_filter.ref = f"A1:G{len(gorivo_sortirano) + 1}"

    # ------------------------------------------------------------
    # LIST: Servisi
    # ------------------------------------------------------------
    ws_s = wb.create_sheet("Servisi")
    _list_sa_zaglavljem(
        ws_s,
        ["R.br.", "Datum", "Vrsta servisa", "Kilometraza", "Cena", "Napomena"],
        [6, 12, 26, 14, 13, 32],
    )
    servisi_sortirano = sorted(servisi_period, key=lambda s: s.get("datum", ""))
    for i, s in enumerate(servisi_sortirano, start=1):
        red = i + 1
        ws_s.append([
            i, _datum_celija(s.get("datum")), s.get("vrsta", "-"),
            s.get("km") or "-", s.get("cena", 0), s.get("napomena") or "",
        ])
        ws_s.cell(row=red, column=2).number_format = DATUM_FMT
        ws_s.cell(row=red, column=5).number_format = RSD
    if servisi_sortirano:
        ws_s.auto_filter.ref = f"A1:F{len(servisi_sortirano) + 1}"

    # ------------------------------------------------------------
    # LIST: Troskovi
    # ------------------------------------------------------------
    ws_t = wb.create_sheet("Troskovi")
    _list_sa_zaglavljem(
        ws_t,
        ["R.br.", "Datum", "Vrsta", "Cena", "Napomena"],
        [6, 12, 22, 13, 32],
    )
    troskovi_sortirano = sorted(troskovi_period, key=lambda s: s.get("datum", ""))
    for i, s in enumerate(troskovi_sortirano, start=1):
        red = i + 1
        ws_t.append([
            i, _datum_celija(s.get("datum")), s.get("vrsta", "-"),
            s.get("cena", 0), s.get("napomena") or "",
        ])
        ws_t.cell(row=red, column=2).number_format = DATUM_FMT
        ws_t.cell(row=red, column=4).number_format = RSD
    if troskovi_sortirano:
        ws_t.auto_filter.ref = f"A1:E{len(troskovi_sortirano) + 1}"

    # ------------------------------------------------------------
    # LIST: Pregled (summary) - formule preko celih kolona drugih
    # listova, tako da rade tacno bez obzira koliko redova ima.
    # ------------------------------------------------------------
    ws_p = wb.create_sheet("Pregled", 0)
    ws_p.column_dimensions["A"].width = 38
    ws_p.column_dimensions["B"].width = 24

    ws_p.merge_cells("A1:B1")
    ws_p["A1"] = naslov_izvestaja
    ws_p["A1"].font = FONT_NASLOV

    ws_p.merge_cells("A2:B2")
    ws_p["A2"] = f"Period: {pocetak_str} do {kraj_str}"
    ws_p["A2"].font = FONT_PODNASLOV

    red = 4

    linije_vozaca = []
    if _VOZAC_REF.ime_prezime:
        linije_vozaca.append(("Ime i prezime", _VOZAC_REF.ime_prezime))
    if _VOZAC_REF.broj_licence:
        linije_vozaca.append(("Licenca", _VOZAC_REF.broj_licence))
    if _VOZAC_REF.telefon:
        linije_vozaca.append(("Telefon", _VOZAC_REF.telefon))
    if _VOZAC_REF.vozilo:
        linije_vozaca.append(("Vozilo", _VOZAC_REF.vozilo))
    if _VOZAC_REF.tablice:
        linije_vozaca.append(("Tablice", _VOZAC_REF.tablice))

    if linije_vozaca:
        ws_p.cell(row=red, column=1, value="Podaci o vozacu").font = FONT_SEKCIJA
        red += 1
        for naziv, vrednost in linije_vozaca:
            ws_p.cell(row=red, column=1, value=naziv)
            ws_p.cell(row=red, column=2, value=vrednost)
            red += 1
        red += 1

    ws_p.cell(row=red, column=1, value="Zbirni pregled (formule - vidi ostale listove)").font = FONT_SEKCIJA
    red += 1

    def _red_pregleda(naziv, formula, fmt=None, bold=False):
        nonlocal red
        c1 = ws_p.cell(row=red, column=1, value=naziv)
        c2 = ws_p.cell(row=red, column=2, value=formula)
        c1.border = OKVIR
        c2.border = OKVIR
        if fmt:
            c2.number_format = fmt
        if bold:
            c1.font = FONT_ZBIR
            c2.font = FONT_ZBIR
        vraceni_red = red
        red += 1
        return vraceni_red

    red_km = _red_pregleda("Ukupno predjeno (voznje)", "=SUM(Voznje!G:G)", fmt='#,##0.0" km"')
    _red_pregleda("Broj voznji", "=COUNT(Voznje!G:G)")
    red_bruto = _red_pregleda("Bruto zarada (voznje)", "=SUM(Voznje!K:K)", fmt=RSD, bold=True)
    red_gorivo = _red_pregleda("Gorivo (trosak)", "=SUM(Gorivo!F:F)", fmt=RSD)
    _red_pregleda("   od toga - litara goriva", "=SUM(Gorivo!D:D)", fmt='#,##0.00" l"')
    red_servisi = _red_pregleda("Servisi (trosak)", "=SUM(Servisi!E:E)", fmt=RSD)
    red_troskovi = _red_pregleda("Ostali troskovi", "=SUM(Troskovi!D:D)", fmt=RSD)

    red += 1
    ws_p.row_dimensions[red].height = 30
    c1 = ws_p.cell(row=red, column=1, value="NETO (bruto zarada - gorivo - servisi - ostali troskovi)")
    c2 = ws_p.cell(row=red, column=2, value=f"=B{red_bruto}-B{red_gorivo}-B{red_servisi}-B{red_troskovi}")
    c1.font = FONT_NETO
    c1.fill = FILL_NETO
    c1.alignment = Alignment(wrap_text=True, vertical="center")
    c2.font = FONT_NETO
    c2.fill = FILL_NETO
    c2.alignment = Alignment(vertical="center")
    c2.number_format = RSD

    wb.active = wb.sheetnames.index("Pregled")
    wb.save(putanja_fajla)

    return len(voznje) + len(gorivo_period) + len(servisi_period) + len(troskovi_period)


def generisi_izvestaj_pdf(naslov_izvestaja, pocetak_str, kraj_str, putanja_fajla):
    """Pravi kompletan PDF izvestaj za izabrani period (pocetak_str i
    kraj_str, format GGGG-MM-DD, oba kraja ukljucena). Sadrzi, tim
    redosledom: podatke o vozacu, servise u periodu, potrosnju goriva
    (l/100km izmedju uzastopnih sipanja) i sve unose goriva u periodu,
    pa na kraju voznje u periodu (adrese, cene, datumi) sa ukupnim
    zbirom.

    Ista funkcija se koristi za dnevni, nedeljni, mesecni, polugodisnji
    i godisnji izvestaj - jedina razlika je koji se pocetak_str/
    kraj_str prosledi (to racuna _izracunaj_period u IzvozPdfScreen)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import ParagraphStyle

    _REGISTRUJ_FONT_ZA_PDF()

    voznje = db.voznje_izmedju(pocetak_str, kraj_str)
    broj, prihod, km = db.zbir_voznji(voznje)

    gorivo_period = _STAVKE_IZMEDJU(_GORIVO_REF.stavke, pocetak_str, kraj_str)
    servisi_period = _STAVKE_IZMEDJU(_SERVIS_REF.stavke, pocetak_str, kraj_str)
    troskovi_period = _STAVKE_IZMEDJU(_TROSKOVI_REF.stavke, pocetak_str, kraj_str)

    svi_intervali_potrosnje = _IZRACUNAJ_POTROSNJU_INTERVALE(_GORIVO_REF.stavke)
    intervali_perioda = [
        i for i in svi_intervali_potrosnje if pocetak_str <= i["datum"] <= kraj_str
    ]

    doc = SimpleDocTemplate(
        putanja_fajla,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=naslov_izvestaja,
    )

    stil_celija = ParagraphStyle(
        "celija", fontName="DejaVuSans", fontSize=8.5, leading=11,
    )
    stil_naslov = ParagraphStyle(
        "naslov", fontName="DejaVuSans-Bold", fontSize=16, leading=20,
    )
    stil_podnaslov = ParagraphStyle(
        "podnaslov", fontName="DejaVuSans", fontSize=10, leading=14,
        textColor=colors.HexColor("#444444"),
    )
    stil_zaglavlje = ParagraphStyle(
        "zaglavlje", fontName="DejaVuSans-Bold", fontSize=8.5, leading=11,
        textColor=colors.white,
    )
    stil_zbir = ParagraphStyle(
        "zbir", fontName="DejaVuSans-Bold", fontSize=12, leading=16,
    )
    stil_vozac = ParagraphStyle(
        "vozac", fontName="DejaVuSans", fontSize=10, leading=14,
    )

    def _tabela_stil():
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3a3560")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f5")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ])

    elementi = []
    elementi.append(Paragraph(naslov_izvestaja, stil_naslov))
    elementi.append(Paragraph(f"Period: {pocetak_str} do {kraj_str}", stil_podnaslov))

    # ------------------------------------------------------------
    # PODACI O VOZACU
    # ------------------------------------------------------------
    linije_vozaca = []
    if _VOZAC_REF.ime_prezime:
        linije_vozaca.append(f"Ime i prezime: {_VOZAC_REF.ime_prezime}")
    if _VOZAC_REF.broj_licence:
        linije_vozaca.append(f"Licenca: {_VOZAC_REF.broj_licence}")
    if _VOZAC_REF.telefon:
        linije_vozaca.append(f"Telefon: {_VOZAC_REF.telefon}")
    if _VOZAC_REF.vozilo:
        linije_vozaca.append(f"Vozilo: {_VOZAC_REF.vozilo}")
    if _VOZAC_REF.tablice:
        linije_vozaca.append(f"Tablice: {_VOZAC_REF.tablice}")

    if linije_vozaca:
        elementi.append(Spacer(1, 3 * mm))
        redovi_vozaca = [[Paragraph(linija, stil_vozac)] for linija in linije_vozaca]
        box_vozaca = Table(redovi_vozaca, colWidths=[80 * mm])
        box_vozaca.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#3a3560")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elementi.append(box_vozaca)

    # ------------------------------------------------------------
    # SERVISI u periodu
    # ------------------------------------------------------------
    elementi.append(Spacer(1, 10 * mm))
    elementi.append(Paragraph("Servisi vozila u periodu", stil_naslov))
    elementi.append(Spacer(1, 5 * mm))

    ukupno_servis = 0.0
    if servisi_period:
        zaglavlje_servis = [
            Paragraph("R.br.", stil_zaglavlje),
            Paragraph("Datum", stil_zaglavlje),
            Paragraph("Vrsta servisa", stil_zaglavlje),
            Paragraph("Kilometraza", stil_zaglavlje),
            Paragraph("Cena", stil_zaglavlje),
            Paragraph("Napomena", stil_zaglavlje),
        ]
        podaci_servis = [zaglavlje_servis]
        for i, s in enumerate(sorted(servisi_period, key=lambda s: s.get("datum", "")), start=1):
            km_s = s.get("km")
            podaci_servis.append([
                Paragraph(str(i), stil_celija),
                Paragraph(s.get("datum", "-"), stil_celija),
                Paragraph(s.get("vrsta", "-"), stil_celija),
                Paragraph(f"{km_s:g} km" if km_s else "-", stil_celija),
                Paragraph(_FORMATIRAJ_CENU(s.get("cena", 0)), stil_celija),
                Paragraph(s.get("napomena") or "-", stil_celija),
            ])
            ukupno_servis += s.get("cena", 0)

        sirine_servis = [12 * mm, 22 * mm, 45 * mm, 25 * mm, 25 * mm, 51 * mm]
        tabela_servis = Table(podaci_servis, colWidths=sirine_servis, repeatRows=1)
        tabela_servis.setStyle(_tabela_stil())
        elementi.append(tabela_servis)
        elementi.append(Spacer(1, 6 * mm))
        elementi.append(Paragraph(f"Ukupno potroseno na servise u periodu: {_FORMATIRAJ_CENU(ukupno_servis)}", stil_zbir))
    else:
        elementi.append(Paragraph("Nema unetih servisa u ovom periodu.", stil_celija))

    # ------------------------------------------------------------
    # OSTALI _TROSKOVI_REF u periodu (parking, putarina, pranje...)
    # ------------------------------------------------------------
    elementi.append(Spacer(1, 10 * mm))
    elementi.append(Paragraph("Ostali troskovi u periodu", stil_naslov))
    elementi.append(Spacer(1, 5 * mm))

    ukupno_troskovi = 0.0
    if troskovi_period:
        zaglavlje_troskovi = [
            Paragraph("R.br.", stil_zaglavlje),
            Paragraph("Datum", stil_zaglavlje),
            Paragraph("Vrsta", stil_zaglavlje),
            Paragraph("Cena", stil_zaglavlje),
            Paragraph("Napomena", stil_zaglavlje),
        ]
        podaci_troskovi = [zaglavlje_troskovi]
        for i, s in enumerate(sorted(troskovi_period, key=lambda s: s.get("datum", "")), start=1):
            podaci_troskovi.append([
                Paragraph(str(i), stil_celija),
                Paragraph(s.get("datum", "-"), stil_celija),
                Paragraph(s.get("vrsta", "-"), stil_celija),
                Paragraph(_FORMATIRAJ_CENU(s.get("cena", 0)), stil_celija),
                Paragraph(s.get("napomena") or "-", stil_celija),
            ])
            ukupno_troskovi += s.get("cena", 0)

        sirine_troskovi = [12 * mm, 25 * mm, 35 * mm, 30 * mm, 78 * mm]
        tabela_troskovi = Table(podaci_troskovi, colWidths=sirine_troskovi, repeatRows=1)
        tabela_troskovi.setStyle(_tabela_stil())
        elementi.append(tabela_troskovi)
        elementi.append(Spacer(1, 6 * mm))
        elementi.append(Paragraph(f"Ukupno ostalih troskova u periodu: {_FORMATIRAJ_CENU(ukupno_troskovi)}", stil_zbir))
    else:
        elementi.append(Paragraph("Nema unetih ostalih troskova u ovom periodu.", stil_celija))

    # ------------------------------------------------------------
    # POTROSNJA GORIVA + svi unosi goriva u periodu
    # ------------------------------------------------------------
    elementi.append(Spacer(1, 10 * mm))
    elementi.append(Paragraph("Potrosnja goriva", stil_naslov))
    elementi.append(Spacer(1, 5 * mm))

    if intervali_perioda:
        zaglavlje_potrosnja = [
            Paragraph("Datum", stil_zaglavlje),
            Paragraph("Predjeno (od proslog sipanja)", stil_zaglavlje),
            Paragraph("Sipano", stil_zaglavlje),
            Paragraph("Potrosnja", stil_zaglavlje),
            Paragraph("Cena sipanja", stil_zaglavlje),
        ]
        podaci_potrosnja = [zaglavlje_potrosnja]
        ukupno_km_potrosnja = 0.0
        ukupno_litara_potrosnja = 0.0
        for interval in intervali_perioda:
            podaci_potrosnja.append([
                Paragraph(interval["datum"], stil_celija),
                Paragraph(f"{interval['km_predjeno']:g} km", stil_celija),
                Paragraph(f"{interval['litara']:g} l", stil_celija),
                Paragraph(f"{interval['potrosnja']:.1f} l/100km", stil_celija),
                Paragraph(_FORMATIRAJ_CENU(interval["cena"]), stil_celija),
            ])
            ukupno_km_potrosnja += interval["km_predjeno"]
            ukupno_litara_potrosnja += interval["litara"]

        sirine_potrosnja = [22 * mm, 45 * mm, 25 * mm, 35 * mm, 30 * mm]
        tabela_potrosnja = Table(podaci_potrosnja, colWidths=sirine_potrosnja, repeatRows=1)
        tabela_potrosnja.setStyle(_tabela_stil())
        elementi.append(tabela_potrosnja)
        elementi.append(Spacer(1, 6 * mm))

        if ukupno_km_potrosnja > 0:
            prosek = ukupno_litara_potrosnja / ukupno_km_potrosnja * 100
            elementi.append(Paragraph(
                f"Prosecna potrosnja za period: {prosek:.1f} l/100km "
                f"({ukupno_litara_potrosnja:g} l na {ukupno_km_potrosnja:g} km)",
                stil_zbir,
            ))
    else:
        elementi.append(Paragraph(
            "Nema izracunate potrosnje za ovaj period - potrebna su bar dva "
            "uzastopna sipanja sa upisanom kilometrazom (km na pumpi), pri "
            "cemu drugo od njih pada u izabrani period.",
            stil_celija,
        ))

    elementi.append(Spacer(1, 8 * mm))
    elementi.append(Paragraph("Gorivo - svi unosi u periodu", stil_naslov))
    elementi.append(Spacer(1, 5 * mm))

    ukupno_gorivo_cena = 0.0
    ukupno_gorivo_litara = 0.0
    if gorivo_period:
        zaglavlje_gorivo = [
            Paragraph("R.br.", stil_zaglavlje),
            Paragraph("Datum", stil_zaglavlje),
            Paragraph("Vrsta", stil_zaglavlje),
            Paragraph("Litara", stil_zaglavlje),
            Paragraph("Km na pumpi", stil_zaglavlje),
            Paragraph("Cena", stil_zaglavlje),
            Paragraph("Napomena", stil_zaglavlje),
        ]
        podaci_gorivo = [zaglavlje_gorivo]
        for i, s in enumerate(sorted(gorivo_period, key=lambda s: s.get("datum", "")), start=1):
            km_pumpe = s.get("km_pumpe")
            podaci_gorivo.append([
                Paragraph(str(i), stil_celija),
                Paragraph(s.get("datum", "-"), stil_celija),
                Paragraph(s.get("tip", "-"), stil_celija),
                Paragraph(f"{s.get('litara', 0):g} l", stil_celija),
                Paragraph(f"{km_pumpe:g} km" if km_pumpe else "-", stil_celija),
                Paragraph(_FORMATIRAJ_CENU(s.get("cena", 0)), stil_celija),
                Paragraph(s.get("napomena") or "-", stil_celija),
            ])
            ukupno_gorivo_cena += s.get("cena", 0)
            ukupno_gorivo_litara += s.get("litara", 0)

        sirine_gorivo = [10 * mm, 20 * mm, 18 * mm, 16 * mm, 22 * mm, 22 * mm, 42 * mm]
        tabela_gorivo = Table(podaci_gorivo, colWidths=sirine_gorivo, repeatRows=1)
        tabela_gorivo.setStyle(_tabela_stil())
        elementi.append(tabela_gorivo)
        elementi.append(Spacer(1, 6 * mm))
        elementi.append(Paragraph(f"Ukupno potroseno na gorivo u periodu: {_FORMATIRAJ_CENU(ukupno_gorivo_cena)}", stil_zbir))
        elementi.append(Paragraph(f"Ukupno litara u periodu: {ukupno_gorivo_litara:g} l", stil_zbir))
    else:
        elementi.append(Paragraph("Nema unetih goriva u ovom periodu.", stil_celija))

    # ------------------------------------------------------------
    # VOZNJE u periodu
    # ------------------------------------------------------------
    elementi.append(Spacer(1, 10 * mm))
    elementi.append(Paragraph("Voznje u periodu", stil_naslov))
    elementi.append(Spacer(1, 5 * mm))

    zaglavlje = [
        Paragraph("R.br.", stil_zaglavlje),
        Paragraph("Datum", stil_zaglavlje),
        Paragraph("Pocetak", stil_zaglavlje),
        Paragraph("Kraj", stil_zaglavlje),
        Paragraph("Adresa polaska", stil_zaglavlje),
        Paragraph("Adresa dolaska", stil_zaglavlje),
        Paragraph("Cena", stil_zaglavlje),
    ]
    podaci_tabele = [zaglavlje]

    for i, v in enumerate(voznje, start=1):
        vreme_pocetka = v["vreme_pocetka"] if ("vreme_pocetka" in v.keys() and v["vreme_pocetka"]) else "-"
        red = [
            Paragraph(str(i), stil_celija),
            Paragraph(v["datum"], stil_celija),
            Paragraph(vreme_pocetka, stil_celija),
            Paragraph(v["vreme"], stil_celija),
            Paragraph(v["od_adresa"] or "-", stil_celija),
            Paragraph(v["do_adresa"] or "-", stil_celija),
            Paragraph(_FORMATIRAJ_CENU(v["ukupna_cena"]), stil_celija),
        ]
        podaci_tabele.append(red)

    if voznje:
        # sirine kolona u mm - A4 sirina 210mm, minus margine 2x15mm = 180mm dostupno
        sirine = [13 * mm, 23 * mm, 17 * mm, 15 * mm, 42 * mm, 42 * mm, 21 * mm]
        tabela = Table(podaci_tabele, colWidths=sirine, repeatRows=1)
        tabela.setStyle(_tabela_stil())
        elementi.append(tabela)
        elementi.append(Spacer(1, 8 * mm))
    else:
        elementi.append(Paragraph("Nema voznji u ovom periodu.", stil_celija))
        elementi.append(Spacer(1, 8 * mm))

    elementi.append(Paragraph(f"Ukupan broj voznji: {broj}", stil_zbir))
    elementi.append(Paragraph(f"Ukupno predjeno (voznje): {km:.1f} km", stil_zbir))
    elementi.append(Paragraph(f"Ukupna zarada za period: {_FORMATIRAJ_CENU(prihod)}", stil_zbir))
    neto_ukupno = prihod - ukupno_gorivo_cena - ukupno_servis - ukupno_troskovi
    elementi.append(Paragraph(
        f"Neto (zarada - gorivo - servisi - ostali troskovi): {_FORMATIRAJ_CENU(neto_ukupno)}",
        stil_zbir,
    ))

    doc.build(elementi)




def _izracunaj_period(tip, unos):
    """Na osnovu izabranog tipa perioda ('Dnevno', 'Nedeljno', 'Mesecno',
    'Polugodisnje', 'Godisnje') i teksta koji je korisnik uneo, vraca
    (pocetak_str, kraj_str, naslov) - pocetak/kraj u formatu GGGG-MM-DD,
    oba kraja ukljucena, spremni da se proslede generisi_izvestaj_pdf().
    Baca ValueError sa razumljivom porukom ako format unosa ne odgovara
    izabranom tipu perioda."""
    unos = unos.strip()

    if tip == "Dnevno":
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", unos):
            raise ValueError("Unesi datum u formatu GGGG-MM-DD, npr. 2026-09-05")
        pocetak = kraj = unos
        naslov = f"Dnevni izvestaj - {unos}"
        return pocetak, kraj, naslov

    if tip == "Nedeljno":
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", unos):
            raise ValueError("Unesi datum u formatu GGGG-MM-DD, npr. 2026-09-05")
        try:
            dan = datetime.strptime(unos, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Datum ne postoji - proveri dan i mesec.")
        pocetak_dt = dan - timedelta(days=dan.weekday())
        kraj_dt = pocetak_dt + timedelta(days=6)
        pocetak = pocetak_dt.strftime("%Y-%m-%d")
        kraj = kraj_dt.strftime("%Y-%m-%d")
        naslov = f"Nedeljni izvestaj - {pocetak} do {kraj}"
        return pocetak, kraj, naslov

    if tip == "Mesecno":
        if not re.match(r"^\d{4}-\d{2}$", unos):
            raise ValueError("Unesi mesec u formatu GGGG-MM, npr. 2026-09")
        godina_str, mesec_str = unos.split("-")
        godina_i, mesec_i = int(godina_str), int(mesec_str)
        if not (1 <= mesec_i <= 12):
            raise ValueError("Mesec mora biti izmedju 01 i 12.")
        pocetak = f"{godina_str}-{mesec_str}-01"
        poslednji_dan = calendar.monthrange(godina_i, mesec_i)[1]
        kraj = f"{godina_str}-{mesec_str}-{poslednji_dan:02d}"
        naslov = f"Mesecni izvestaj - {unos}"
        return pocetak, kraj, naslov

    if tip == "Polugodisnje":
        if not re.match(r"^\d{4}-[12]$", unos):
            raise ValueError("Unesi u formatu GGGG-P gde je P 1 ili 2, npr. 2026-1")
        godina_str, pol_str = unos.split("-")
        if pol_str == "1":
            pocetak = f"{godina_str}-01-01"
            kraj = f"{godina_str}-06-30"
            naslov = f"Polugodisnji izvestaj - {godina_str} (januar-jun)"
        else:
            pocetak = f"{godina_str}-07-01"
            kraj = f"{godina_str}-12-31"
            naslov = f"Polugodisnji izvestaj - {godina_str} (jul-decembar)"
        return pocetak, kraj, naslov

    if tip == "Godisnje":
        if not re.match(r"^\d{4}$", unos):
            raise ValueError("Unesi godinu u formatu GGGG, npr. 2026")
        pocetak = f"{unos}-01-01"
        kraj = f"{unos}-12-31"
        naslov = f"Godisnji izvestaj - {unos}"
        return pocetak, kraj, naslov

    raise ValueError("Nepoznat tip perioda.")


class IzvozPdfScreen(Screen):
    tekst_status = StringProperty("")
    tekst_format_perioda = StringProperty("Mesec (format GGGG-MM):")
    hint_perioda = StringProperty("npr. 2026-09")

    def on_pre_enter(self, *args):
        if not self.ids.input_period.text:
            self._popuni_podrazumevano()
        self._osvezi_status()

    def promeni_period(self, tip):
        """Poziva se iz KV-a kad korisnik promeni izbor u spinneru za
        tip perioda - menja natpis/hint iznad polja i upisuje
        podrazumevanu vrednost (danas/ovaj mesec/ova godina...)."""
        if tip == "Dnevno":
            self.tekst_format_perioda = "Datum (format GGGG-MM-DD):"
            self.hint_perioda = "npr. 2026-09-05"
        elif tip == "Nedeljno":
            self.tekst_format_perioda = "Bilo koji datum iz te nedelje (format GGGG-MM-DD):"
            self.hint_perioda = "npr. 2026-09-05"
        elif tip == "Mesecno":
            self.tekst_format_perioda = "Mesec (format GGGG-MM):"
            self.hint_perioda = "npr. 2026-09"
        elif tip == "Polugodisnje":
            self.tekst_format_perioda = "Godina i polugodiste, P je 1 ili 2 (format GGGG-P):"
            self.hint_perioda = "2026-1 = jan-jun, 2026-2 = jul-dec"
        elif tip == "Godisnje":
            self.tekst_format_perioda = "Godina (format GGGG):"
            self.hint_perioda = "npr. 2026"
        self._popuni_podrazumevano()

    def _popuni_podrazumevano(self):
        tip = self.ids.spinner_period.text
        danas = datetime.now()
        if tip in ("Dnevno", "Nedeljno"):
            self.ids.input_period.text = danas.strftime("%Y-%m-%d")
        elif tip == "Mesecno":
            self.ids.input_period.text = danas.strftime("%Y-%m")
        elif tip == "Polugodisnje":
            polugodiste = 1 if danas.month <= 6 else 2
            self.ids.input_period.text = f"{danas.year}-{polugodiste}"
        elif tip == "Godisnje":
            self.ids.input_period.text = danas.strftime("%Y")

    def _osvezi_status(self):
        if _IMA_DOZVOLU_SVI_FAJLOVI():
            self.tekst_status = "Dozvola za fajlove: DA"
        else:
            self.tekst_status = (
                "Dozvola za fajlove: NE\n"
                "Idi u Podesavanja -> Backup podataka i klikni "
                "'Odobri pristup fajlovima', pa se vrati ovde."
            )

    def izvezi_pdf(self):
        tip = self.ids.spinner_period.text
        unos = self.ids.input_period.text.strip()

        try:
            pocetak, kraj, naslov = _izracunaj_period(tip, unos)
        except ValueError as e:
            _PRIKAZI_POPUP("Greska", str(e), size_hint=(0.85, 0.4))
            return

        if not _IMA_DOZVOLU_SVI_FAJLOVI():
            _PRIKAZI_POPUP(
                "Nedostaje dozvola",
                "Idi u Podesavanja -> Backup podataka i klikni "
                "'Odobri pristup fajlovima', pa se vrati ovde.",
                size_hint=(0.88, 0.4),
            )
            return

        try:
            voznje = db.voznje_izmedju(pocetak, kraj)
        except Exception as e:
            _PRIKAZI_POPUP("Greska", f"Ne mogu da procitam bazu:\n{e}", size_hint=(0.88, 0.4))
            return

        gorivo_period = _STAVKE_IZMEDJU(_GORIVO_REF.stavke, pocetak, kraj)
        servisi_period = _STAVKE_IZMEDJU(_SERVIS_REF.stavke, pocetak, kraj)

        if not voznje and not gorivo_period and not servisi_period:
            _PRIKAZI_POPUP(
                "Nema podataka",
                f"Nema nijedne voznje, unosa goriva ni servisa za period "
                f"{pocetak} do {kraj} - PDF nije napravljen.",
                size_hint=(0.88, 0.45),
            )
            return

        try:
            folder = _PUTANJA_BACKUP_FOLDERA()
            os.makedirs(folder, exist_ok=True)
            putanja = os.path.join(folder, f"izvestaj_{pocetak}_do_{kraj}.pdf")
            generisi_izvestaj_pdf(naslov, pocetak, kraj, putanja)
            _PRIKAZI_POPUP(
                "Sacuvano",
                f"PDF izvestaj sacuvan u:\n{putanja}\n\n"
                f"Voznji: {len(voznje)}   Gorivo: {len(gorivo_period)}   "
                f"Servisi: {len(servisi_period)}",
                size_hint=(0.88, 0.5),
            )
        except Exception as e:
            _PRIKAZI_POPUP(
                "Greska", f"Pravljenje PDF-a nije uspelo:\n{e}", size_hint=(0.88, 0.45)
            )

    def izvezi_excel(self):
        tip = self.ids.spinner_period.text
        unos = self.ids.input_period.text.strip()

        try:
            pocetak, kraj, naslov = _izracunaj_period(tip, unos)
        except ValueError as e:
            _PRIKAZI_POPUP("Greska", str(e), size_hint=(0.85, 0.4))
            return

        if not _IMA_DOZVOLU_SVI_FAJLOVI():
            _PRIKAZI_POPUP(
                "Nedostaje dozvola",
                "Idi u Podesavanja -> Backup podataka i klikni "
                "'Odobri pristup fajlovima', pa se vrati ovde.",
                size_hint=(0.88, 0.4),
            )
            return

        try:
            voznje = db.voznje_izmedju(pocetak, kraj)
        except Exception as e:
            _PRIKAZI_POPUP("Greska", f"Ne mogu da procitam bazu:\n{e}", size_hint=(0.88, 0.4))
            return

        gorivo_period = _STAVKE_IZMEDJU(_GORIVO_REF.stavke, pocetak, kraj)
        servisi_period = _STAVKE_IZMEDJU(_SERVIS_REF.stavke, pocetak, kraj)
        troskovi_period = _STAVKE_IZMEDJU(_TROSKOVI_REF.stavke, pocetak, kraj)

        if not voznje and not gorivo_period and not servisi_period and not troskovi_period:
            _PRIKAZI_POPUP(
                "Nema podataka",
                f"Nema nijedne voznje, unosa goriva, servisa ni troskova za period "
                f"{pocetak} do {kraj} - Excel nije napravljen.",
                size_hint=(0.88, 0.45),
            )
            return

        try:
            folder = _PUTANJA_BACKUP_FOLDERA()
            os.makedirs(folder, exist_ok=True)
            putanja = os.path.join(folder, f"izvestaj_{pocetak}_do_{kraj}.xlsx")
            broj_redova = generisi_izvestaj_excel(naslov, pocetak, kraj, putanja)
            _PRIKAZI_POPUP(
                "Sacuvano",
                f"Excel izvestaj ({broj_redova} redova, 5 listova) sacuvan u:\n{putanja}\n\n"
                f"Otvori ga u Excel-u ili prosledi knjigovodji.",
                size_hint=(0.88, 0.5),
            )
        except Exception as e:
            _PRIKAZI_POPUP(
                "Greska", f"Pravljenje Excel fajla nije uspelo:\n{e}", size_hint=(0.88, 0.45)
            )

IZVOZ_KV = """
# ============================================================
# IZVOZ PDF - mesecni izvestaj kao PDF fajl
# ============================================================

<IzvozPdfScreen>:
    name: "izvoz_pdf"
    ScreenRoot:

        TitleLabel:
            text: "Izvoz PDF izvestaja"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Izvestaj"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "izvestaj"

        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(16)
                padding: dp(2), dp(4)

                FieldLabel:
                    text: "Pravi PDF sa svim voznjama, gorivom, servisima i potrosnjom za izabrani period, sa ukupnim zbirom na kraju."

                FieldLabel:
                    text: "Vrsta perioda:"

                Spinner:
                    id: spinner_period
                    text: "Mesecno"
                    values: ["Dnevno", "Nedeljno", "Mesecno", "Polugodisnje", "Godisnje"]
                    size_hint_y: None
                    height: dp(48)
                    background_color: 0.78, 0.80, 0.90, 1
                    color: 0.12, 0.12, 0.24, 1
                    on_text: root.promeni_period(self.text)

                FieldLabel:
                    text: root.tekst_format_perioda

                PastelTextInput:
                    id: input_period
                    hint_text: root.hint_perioda

                PastelCard:
                    orientation: "vertical"
                    tint: 0.30, 0.29, 0.42, 0.92
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(14)
                    Label:
                        text: root.tekst_status
                        color: 1, 1, 1, 1
                        halign: "left"
                        valign: "top"
                        size_hint_y: None
                        text_size: self.width, None
                        height: self.texture_size[1]

                RoundButton:
                    label_text: "Izvezi PDF"
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 1, 1, 1, 1
                    size_hint_y: None
                    height: dp(56)
                    on_release: root.izvezi_pdf()

                RoundButton:
                    label_text: "Izvezi Excel"
                    tint: 0.30, 0.46, 0.56, 1
                    text_color: 1, 1, 1, 1
                    size_hint_y: None
                    height: dp(56)
                    on_release: root.izvezi_excel()

                FieldLabel:
                    text: "PDF je za stampu, Excel (sa 5 listova i formulama) je za knjigovodju - oba se cuvaju u isti folder kao i backup: Preuzimanja/TaksiApp."
                    size_hint_y: None
                    height: dp(60)
                    text_size: self.width, None


"""
