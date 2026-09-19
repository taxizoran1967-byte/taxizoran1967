"""
ekran_uputstvo.py
Ekran "Uputstvo za upotrebu" - prikazuje kompletno uputstvo za app na
trenutno izabranom jeziku (sadrzaj je u servisi/uputstvo_tekstovi.py)
i nudi izvoz istog teksta u PDF.

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py.
"""

import os
from xml.sax.saxutils import escape

from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.properties import StringProperty

from servisi import jezici
from servisi import uputstvo_tekstovi as ut


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_REGISTRUJ_FONT_ZA_PDF = None    # main._registruj_font_za_pdf (deljeno i sa ekran_izvoz.py)
_IMA_DOZVOLU_SVI_FAJLOVI = None  # main._ima_dozvolu_svi_fajlovi
_PUTANJA_BACKUP_FOLDERA = None   # main._putanja_backup_foldera
_PRIKAZI_POPUP = None            # main._prikazi_popup_poruku


def poveži(registruj_font_fn, ima_dozvolu_fn, putanja_backup_fn, prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_uputstvo'."""
    global _REGISTRUJ_FONT_ZA_PDF, _IMA_DOZVOLU_SVI_FAJLOVI
    global _PUTANJA_BACKUP_FOLDERA, _PRIKAZI_POPUP
    _REGISTRUJ_FONT_ZA_PDF = registruj_font_fn
    _IMA_DOZVOLU_SVI_FAJLOVI = ima_dozvolu_fn
    _PUTANJA_BACKUP_FOLDERA = putanja_backup_fn
    _PRIKAZI_POPUP = prikazi_popup_fn


def generisi_uputstvo_pdf(naslov, podnaslov, sekcije, putanja_fajla):
    """Pravi PDF sa celim uputstvom - naslov, podnaslov, pa svaka
    sekcija (naslov + pasusi) redom. 'sekcije' je lista (naslov,
    [pasusi]) torki, na trenutno izabranom jeziku."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle

    _REGISTRUJ_FONT_ZA_PDF()

    def _p(tekst, stil):
        # Paragraph tumaci tekst kao XML/HTML oznake, pa se znakovi
        # < > & moraju "escape"-ovati.
        return Paragraph(escape(str(tekst)), stil)

    doc = SimpleDocTemplate(
        putanja_fajla,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=naslov,
    )

    stil_naslov = ParagraphStyle(
        "naslov", fontName="DejaVuSans-Bold", fontSize=17, leading=21,
    )
    stil_podnaslov = ParagraphStyle(
        "podnaslov", fontName="DejaVuSans", fontSize=10, leading=14,
        textColor=colors.HexColor("#444444"),
    )
    stil_sekcija = ParagraphStyle(
        "sekcija", fontName="DejaVuSans-Bold", fontSize=13, leading=17,
        textColor=colors.HexColor("#3a3560"), spaceBefore=10,
    )
    stil_pasus = ParagraphStyle(
        "pasus", fontName="DejaVuSans", fontSize=9.5, leading=13.5,
        spaceAfter=4,
    )

    elementi = [
        _p(naslov, stil_naslov),
        _p(podnaslov, stil_podnaslov),
        Spacer(1, 6 * mm),
    ]
    for naslov_sekcije, pasusi in sekcije:
        elementi.append(_p(naslov_sekcije, stil_sekcija))
        for pasus in pasusi:
            elementi.append(_p(pasus, stil_pasus))

    doc.build(elementi)


class UputstvoScreen(Screen):
    tekst_naslov = StringProperty("Uputstvo za upotrebu")
    tekst_status = StringProperty("")
    tekst_dugme_pdf = StringProperty("Izvezi u PDF")

    def on_pre_enter(self, *args):
        """Osvezi naslove i sadrzaj na trenutnom jeziku svaki put kad
        se udje na ekran (jezik se moze promeniti u medjuvremenu)."""
        self.tekst_naslov = jezici._t("uputstvo.naslov")
        self.tekst_status = jezici._t("uputstvo.tekst_status")
        self.tekst_dugme_pdf = jezici._t("uputstvo.izvezi_pdf_dugme")
        self._popuni_sadrzaj()

    def _sekcije_trenutnog_jezika(self):
        lang = jezici.get_current_language()
        return ut.SADRZAJ.get(lang, ut.SADRZAJ["sr"])

    def _popuni_sadrzaj(self):
        """Ispuni scrollable kontejner sekcijama uputstva (naslov +
        pasusi) na trenutnom jeziku."""
        kontejner = self.ids.get("sadrzaj_kontejner")
        if kontejner is None:
            return
        kontejner.clear_widgets()

        for naslov_sekcije, pasusi in self._sekcije_trenutnog_jezika():
            naslov_lbl = Label(
                text=f"[b]{naslov_sekcije}[/b]",
                markup=True,
                font_size="16sp",
                color=(0.227, 0.208, 0.376, 1),
                size_hint_y=None,
                halign="left",
                valign="middle",
            )
            naslov_lbl.bind(
                width=lambda inst, w: setattr(inst, "text_size", (w, None)),
                texture_size=lambda inst, ts: setattr(inst, "height", ts[1] + dp(10)),
            )
            kontejner.add_widget(naslov_lbl)

            for pasus in pasusi:
                pasus_lbl = Label(
                    text=pasus,
                    font_size="13sp",
                    color=(0.15, 0.15, 0.18, 1),
                    size_hint_y=None,
                    halign="left",
                    valign="top",
                )
                pasus_lbl.bind(
                    width=lambda inst, w: setattr(inst, "text_size", (w, None)),
                    texture_size=lambda inst, ts: setattr(inst, "height", ts[1] + dp(6)),
                )
                kontejner.add_widget(pasus_lbl)

    def izvezi_pdf(self):
        if not _IMA_DOZVOLU_SVI_FAJLOVI():
            _PRIKAZI_POPUP(
                jezici._t("backup.nedostaje_dozvola_naslov"),
                jezici._t("izvoz.nedostaje_dozvola_poruka"),
                size_hint=(0.88, 0.4),
            )
            return

        try:
            folder = _PUTANJA_BACKUP_FOLDERA()
            os.makedirs(folder, exist_ok=True)
            putanja = os.path.join(folder, "uputstvo.pdf")

            lang = jezici.get_current_language()
            naslov = jezici._t("uputstvo.naslov")
            podnaslov = ut.PODNASLOV.get(lang, ut.PODNASLOV["sr"])
            sekcije = self._sekcije_trenutnog_jezika()

            generisi_uputstvo_pdf(naslov, podnaslov, sekcije, putanja)

            _PRIKAZI_POPUP(
                jezici._t("backup.sacuvano_naslov"),
                jezici._t("uputstvo.sacuvano_poruka", putanja=putanja),
                size_hint=(0.85, 0.4),
            )
        except Exception as e:
            _PRIKAZI_POPUP(
                jezici._t("profil.greska"),
                jezici._t("izvoz.pdf_neuspeo", greska=e),
                size_hint=(0.88, 0.4),
            )


UPUTSTVO_KV = """
# ============================================================
# UPUTSTVO ZA UPOTREBU
# ============================================================

<UputstvoScreen>:
    name: "uputstvo"
    ScreenRoot:

        TitleLabel:
            text: root.tekst_naslov

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                font_size: '13sp'
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: root.tekst_dugme_pdf
                tint: 0.42, 0.58, 0.4, 1
                font_size: '13sp'
                on_release: root.izvezi_pdf()

        FieldLabel:
            text: root.tekst_status

        ScrollView:
            do_scroll_x: False
            BoxLayout:
                id: sadrzaj_kontejner
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(8)
                padding: dp(16)
"""
