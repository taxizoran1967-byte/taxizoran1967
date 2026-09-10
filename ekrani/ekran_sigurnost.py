"""
ekran_sigurnost.py
Ekran zakljucavanja otiskom prsta pri pokretanju (LockScreen) i ekran
za ukljucivanje/iskljucivanje te opcije (SigurnostScreen).

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py. Ovaj modul
je POTPUNO SAMOSTALAN (ne treba mu nista injektovano iz main.py) jer
SigurnostPodesavanja ne zavisi ni od cega osim standardne biblioteke,
a biometrics.py je vec zaseban modul bez kruznog uvoza.
"""

import os
import json

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty
from kivy.app import App
from kivy.clock import Clock

from servisi import biometrics


class SigurnostPodesavanja:
    """Da li je ukljuceno otkljucavanje aplikacije otiskom prsta pri
    pokretanju. Podrazumevano ISKLJUCENO - korisnik ga sam ukljucuje u
    Podesavanja -> Sigurnost, jer zahteva da telefon vec ima
    registrovan otisak u sistemskim podesavanjima."""

    def __init__(self):
        self.ukljucena = False

    def _putanja(self, user_data_dir):
        return os.path.join(user_data_dir, "sigurnost.json")

    def ucitaj(self, user_data_dir):
        try:
            with open(self._putanja(user_data_dir), "r", encoding="utf-8") as f:
                podaci = json.load(f)
            self.ukljucena = bool(podaci.get("ukljucena", False))
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass

    def sacuvaj(self, user_data_dir):
        podaci = {"ukljucena": self.ukljucena}
        with open(self._putanja(user_data_dir), "w", encoding="utf-8") as f:
            json.dump(podaci, f, ensure_ascii=False, indent=2)


SIGURNOST = SigurnostPodesavanja()


class LockScreen(Screen):
    """Prvi ekran koji se prikazuje pri pokretanju app-a - ako je
    otkljucavanje otiskom ukljuceno u Podesavanja -> Sigurnost i
    uredjaj ima registrovan otisak, korisnik mora da prisloni prst
    pre nego sto udje u app. U suprotnom (iskljuceno, ili uredjaj
    nema citac/registrovan otisak) automatski se propusta dalje."""

    tekst_status = StringProperty("Proveravam...")
    tekst_dugme = StringProperty("Pokusaj ponovo")
    prikazi_dugme = BooleanProperty(False)

    def pokusaj_ili_preskoci(self):
        """Poziva se JEDNOM, iz TaksiApp.build() (preko Clock.schedule_once,
        posto je citav ScreenManager vec sagradjen) - a ne iz
        on_pre_enter(), jer ScreenManager postavlja 'current' na ovaj
        (prvi) ekran JOS DOK se KV gradi, pre nego sto ekran 'home'
        uopste postoji, pa bi automatski prelazak na 'home' u tom
        trenutku pukao sa 'No Screen with name home'."""
        self.prikazi_dugme = False

        if not SIGURNOST.ukljucena:
            self._nastavi_dalje()
            return

        dostupno, poruka = biometrics.hardver_dostupan()
        if not dostupno:
            # Bez alternative za otkljucavanje (nema PIN-a), pa ne
            # smemo trajno da zakljucamo korisnika van app-a - samo
            # ga obavestavamo i propustamo dalje.
            self.tekst_status = poruka
            Clock.schedule_once(lambda dt: self._nastavi_dalje(), 1.5)
            return

        self.pokusaj_ponovo()

    def pokusaj_ponovo(self):
        self.tekst_status = "Prislonite prst na senzor za otisak..."
        self.prikazi_dugme = False
        biometrics.pokreni_autentifikaciju(
            on_uspeh=lambda: Clock.schedule_once(lambda dt: self._nastavi_dalje()),
            on_greska=lambda poruka: Clock.schedule_once(
                lambda dt, p=poruka: self._neuspeh(p)
            ),
            on_neuspesno=lambda: Clock.schedule_once(
                lambda dt: self._neuspeh("Otisak nije prepoznat.")
            ),
        )

    def _neuspeh(self, poruka):
        self.tekst_status = poruka
        self.tekst_dugme = "Pokusaj ponovo"
        self.prikazi_dugme = True

    def _nastavi_dalje(self):
        self.manager.current = "home"


class SigurnostScreen(Screen):
    tekst_status = StringProperty("")
    tekst_dugme = StringProperty("")
    tint_dugme = (0.7, 0.9, 0.72, 1)
    tekst_napomena = StringProperty("")

    def on_pre_enter(self, *args):
        self._osvezi()

    def _osvezi(self):
        if SIGURNOST.ukljucena:
            self.tekst_status = "Otkljucavanje otiskom: UKLJUCENO"
            self.tekst_dugme = "Iskljuci otisak"
            self.tint_dugme = (0.66, 0.30, 0.34, 1)
        else:
            self.tekst_status = "Otkljucavanje otiskom: ISKLJUCENO"
            self.tekst_dugme = "Ukljuci otisak"
            self.tint_dugme = (0.30, 0.52, 0.36, 1)

        dostupno, poruka = biometrics.hardver_dostupan()
        if dostupno:
            self.tekst_napomena = (
                "Otisak je registrovan na ovom uredjaju - ekran za "
                "otkljucavanje ce se prikazati svaki put kad pokrenes app."
            )
        else:
            self.tekst_napomena = (
                f"Napomena: {poruka} Ako ukljucis ovu opciju bez "
                "registrovanog otiska, app ce te automatski propustiti "
                "dalje - iz bezbednosnih razloga se ne mozes zakljucati "
                "van app-a bez registrovanog otiska."
            )

    def promeni(self):
        SIGURNOST.ukljucena = not SIGURNOST.ukljucena
        app = App.get_running_app()
        SIGURNOST.sacuvaj(app.user_data_dir)
        self._osvezi()



SIGURNOST_KV = """
# ============================================================
# EKRAN ZAKLJUCAVANJA - otisak prsta pri pokretanju app-a
# ============================================================

<LockScreen>:
    name: "lock"
    ScreenRoot:

        Widget:

        TaxiZoranNaslov:

        Widget:
            size_hint_y: None
            height: dp(30)

        Label:
            text: root.tekst_status
            font_size: '18sp'
            color: 1, 1, 1, 1
            size_hint_y: None
            height: dp(110)
            text_size: self.width, None
            halign: "center"
            valign: "middle"

        RoundButton:
            label_text: root.tekst_dugme
            tint: 0.30, 0.52, 0.36, 1
            text_color: 0.1, 0.1, 0.1, 1
            size_hint_y: None
            height: dp(52)
            opacity: 1 if root.prikazi_dugme else 0
            disabled: not root.prikazi_dugme
            on_release: root.pokusaj_ponovo()

        Widget:


# ============================================================
# SIGURNOST - otkljucavanje otiskom prsta
# ============================================================

<SigurnostScreen>:
    name: "sigurnost"
    ScreenRoot:

        TitleLabel:
            text: "Sigurnost"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Podesavanja"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "podesavanja"

        PastelCard:
            tint: 0.38, 0.32, 0.52, 0.92
            size_hint_y: None
            height: self.minimum_height
            padding: dp(14)
            Label:
                text: root.tekst_status
                font_size: '18sp'
                bold: True
                color: 0.92, 0.88, 1, 1
                halign: "center"
                valign: "middle"
                size_hint_y: None
                text_size: self.width, None
                height: self.texture_size[1]

        RoundButton:
            label_text: root.tekst_dugme
            tint: root.tint_dugme
            text_color: 0.1, 0.1, 0.1, 1
            size_hint_y: None
            height: dp(52)
            on_release: root.promeni()

        FieldLabel:
            text: root.tekst_napomena
            size_hint_y: None
            height: dp(110)
            text_size: self.width, None

        Widget:


"""
