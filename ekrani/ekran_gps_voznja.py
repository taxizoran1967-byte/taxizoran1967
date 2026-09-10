"""
ekran_gps_voznja.py
UI sloj za GPS voznju: prikaz, start/stop toka, reverse geocoding i
osvezavanje aktivne voznje koju sada vodi foreground servis na
Androidu, uz lokalni fallback kad servis nije dostupan.
"""

import json
import threading
import urllib.request
import urllib.parse
import webbrowser
import ssl
from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty
from kivy.app import App
from kivy.clock import Clock

from servisi import database as db
from servisi.gps_tracking import (
    AKTIVNA_VOZNJA,
    AndroidLocationTracker,
    android_foreground_servis_pokrenut,
    android_foreground_servis_dostupan,
    dijagnostika_lokacije,
    dodaj_dijagnozu,
    inicijalizuj_aktivnu_voznju,
    obradi_lokaciju_i_sacuvaj,
    pokreni_android_foreground_servis,
    postavi_status,
    zaustavi_android_foreground_servis,
)

try:
    import certifi
    SSL_KONTEKST = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_KONTEKST = ssl.create_default_context()


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_CENE_REF = None         # main._CENE_REF
_API_REF = None          # main.API (za Google Geocoding kljuc)
_FORMATIRAJ_CENU = None  # main.formatiraj_cenu
_PRIKAZI_POPUP = None    # main._prikazi_popup_poruku


def poveži(cene_obj, api_obj, formatiraj_cenu_fn, prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_gps_voznja'."""
    global _CENE_REF, _API_REF, _FORMATIRAJ_CENU, _PRIKAZI_POPUP
    _CENE_REF = cene_obj
    _API_REF = api_obj
    _FORMATIRAJ_CENU = formatiraj_cenu_fn
    _PRIKAZI_POPUP = prikazi_popup_fn


def reverse_geocode(lat, lon, callback, dijagnoza_callback=None):
    """Pretvara GPS koordinate u adresu. Ako je unet Google API kljuc
    (Podesavanja -> Google API), koristi Google Geocoding (tacnije).
    Ako kljuca nema, ili Google poziv ne uspe, koristi besplatan
    OpenStreetMap Nominatim kao rezervu. Radi u pozadinskoj niti da
    ne blokira interfejs; rezultat vraca preko callback-a na glavnoj
    niti. Ako je prosledjen dijagnoza_callback, saljepravi razlog
    google/osm neuspeha (za prikaz na ekranu, radi resavanja problema)."""

    def _osm_pokusaj(dnevnik):
        try:
            url = (
                "https://nominatim.openstreetmap.org/reverse?format=json"
                f"&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
            )
            req = urllib.request.Request(
                url, headers={"User-Agent": "TaksiApp/1.0"}
            )
            with urllib.request.urlopen(req, timeout=8, context=SSL_KONTEKST) as resp:
                podaci = json.loads(resp.read().decode("utf-8"))
            if podaci.get("display_name"):
                return podaci["display_name"]
            dnevnik.append(f"OSM: nema display_name u odgovoru ({podaci})")
        except Exception as e:
            dnevnik.append(f"OSM greska: {e}")
        return None

    def _google_pokusaj(kljuc, dnevnik):
        try:
            url = (
                "https://maps.googleapis.com/maps/api/geocode/json"
                f"?latlng={lat},{lon}&key={kljuc}&language=sr"
            )
            with urllib.request.urlopen(url, timeout=8, context=SSL_KONTEKST) as resp:
                podaci = json.loads(resp.read().decode("utf-8"))
            if podaci.get("status") == "OK" and podaci.get("results"):
                return podaci["results"][0]["formatted_address"]
            dnevnik.append(
                f"Google status: {podaci.get('status')} - "
                f"{podaci.get('error_message', '(bez poruke)')}"
            )
        except Exception as e:
            dnevnik.append(f"Google greska: {e}")
        return None

    def posao():
        dnevnik = []
        adresa = None
        kljuc = _API_REF.google_kljuc.strip()
        if kljuc:
            adresa = _google_pokusaj(kljuc, dnevnik)
        if not adresa:
            adresa = _osm_pokusaj(dnevnik)
        if not adresa:
            adresa = "Adresa nije dostupna"
        Clock.schedule_once(lambda dt: callback(adresa))
        if dijagnoza_callback and dnevnik:
            tekst = "\n".join(dnevnik)
            Clock.schedule_once(lambda dt: dijagnoza_callback(tekst))

    threading.Thread(target=posao, daemon=True).start()


class GpsVoznjaScreen(Screen):
    tekst_polazak = StringProperty("Nije zapoceta")
    tekst_km = StringProperty("Predjeno: 0.00 km")
    tekst_trajanje = StringProperty("Trajanje: 00:00:00")
    tekst_cena = StringProperty("Cena: 0 RSD")
    tekst_gps_status = StringProperty("")
    tekst_dijagnoza = StringProperty("")
    voznja_aktivna = BooleanProperty(False)

    MIN_TACNOST_M = 50       # ignorisi GPS tacke losije preciznosti od ovoga (metri)
    MIN_POMERAJ_KM = 0.01    # ignorisi mikro-skokove manje od 10m (GPS sum)
    MAX_BRZINA_KMH = 180     # ignorisi nerealne skokove (losa GPS tacka)

    def on_pre_enter(self, *args):
        self._tajmer = None
        self._brojac_signala = None
        self._brojac_poll = None
        self._sekundi_bez_signala = 0
        self._zadnje_vreme_lok = None
        self._lokalni_tracker = getattr(self, "_lokalni_tracker", None)
        self._geokod_polaska_u_toku = None
        self._ucitaj_stanje_voznje()
        if AKTIVNA_VOZNJA.aktivna:
            self.obnovi_pracenje_ako_treba()
        else:
            self.voznja_aktivna = False
            self.tekst_polazak = "Nije zapoceta"
            self.tekst_km = "Predjeno: 0.00 km"
            self.tekst_trajanje = "Trajanje: 00:00:00"
            self.tekst_cena = "Cena: 0 RSD"
            self.tekst_gps_status = ""
            self.tekst_dijagnoza = ""

    def on_leave(self, *args):
        if self._tajmer:
            self._tajmer.cancel()
            self._tajmer = None
        if getattr(self, "_brojac_signala", None):
            self._brojac_signala.cancel()
            self._brojac_signala = None
        if getattr(self, "_brojac_poll", None):
            self._brojac_poll.cancel()
            self._brojac_poll = None

    # ---------------- POCETAK VOZNJE ----------------

    def _ucitaj_stanje_voznje(self):
        app = App.get_running_app()
        if app is not None:
            AKTIVNA_VOZNJA.ucitaj(app.user_data_dir)

    def _radi_preko_foreground_servisa(self):
        return AKTIVNA_VOZNJA.izvor_pracenja == "foreground_service"

    def _pokreni_lokalni_gps(self):
        if getattr(self, "_lokalni_tracker", None) is None:
            self._lokalni_tracker = AndroidLocationTracker(
                na_lokaciju=self._obradi_lokaciju,
                na_dijagnozu=self._lokalna_dijagnoza,
                na_gresku=self._lokalna_greska,
                dispatcher=lambda cb: Clock.schedule_once(lambda dt: cb()),
            )

        pokrenuto = self._lokalni_tracker.pokreni()
        if not pokrenuto:
            self.tekst_gps_status = "Greska pri pokretanju GPS-a."
            return False

        self._sekundi_bez_signala = 0
        if getattr(self, "_brojac_signala", None) is None:
            self._brojac_signala = Clock.schedule_interval(self._proveri_signal, 1)
        if getattr(self, "_brojac_poll", None) is None:
            self._brojac_poll = Clock.schedule_interval(self._pull_lokaciju, 2)
        return True

    def obnovi_pracenje_ako_treba(self):
        self._ucitaj_stanje_voznje()
        if not AKTIVNA_VOZNJA.aktivna:
            return

        self.voznja_aktivna = True
        self.tekst_polazak = AKTIVNA_VOZNJA.pocetak_adresa or "Adresa nije dostupna"
        self._osvezi_prikaz()
        self._pokreni_tajmer()

        if AKTIVNA_VOZNJA.izvor_pracenja == "zavrsetak_u_toku":
            return

        if self._radi_preko_foreground_servisa():
            app = App.get_running_app()
            pokrenuto, greska = pokreni_android_foreground_servis(
                user_data_dir=app.user_data_dir,
            )
            if not pokrenuto:
                self.tekst_dijagnoza = (
                    (AKTIVNA_VOZNJA.dijagnoza + "\n") if AKTIVNA_VOZNJA.dijagnoza else ""
                ) + f"Foreground servis nije dostupan ({greska}), vracam fallback pracenje."
                postavi_status(
                    gps_status="Foreground servis nije dostupan, vracam lokalni fallback.",
                    dijagnoza=self.tekst_dijagnoza,
                    izvor_pracenja="lokalni_fallback",
                    user_data_dir=App.get_running_app().user_data_dir,
                )
                self._ucitaj_stanje_voznje()
                self._pokreni_lokalni_gps()
            return

        self._pokreni_lokalni_gps()

    def pocni_voznju(self):
        try:
            from android.permissions import (
                request_permissions, check_permission, Permission,
            )
            potrebne = [
                Permission.ACCESS_FINE_LOCATION,
                Permission.ACCESS_COARSE_LOCATION,
            ]
            pozadinska = getattr(Permission, "ACCESS_BACKGROUND_LOCATION", None)
            if not all(check_permission(p) for p in potrebne):
                self.tekst_gps_status = "Trazim dozvolu za lokaciju..."

                def na_odgovor(dozvole, rezultati):
                    if all(rezultati):
                        if pozadinska and not check_permission(pozadinska):
                            try:
                                request_permissions(
                                    [pozadinska],
                                    lambda _, rezultati_bg: Clock.schedule_once(
                                        lambda dt: self._nastavi_posle_pozadinske_dozvole(
                                            all(rezultati_bg)
                                        )
                                    ),
                                )
                                return
                            except Exception:
                                pass
                        Clock.schedule_once(lambda dt: self._stvarno_pokreni_gps())
                    else:
                        self.tekst_gps_status = (
                            "Dozvola za lokaciju NIJE odobrena. Idi u "
                            "Podesavanja telefona -> Aplikacije -> Taksi App "
                            "-> Dozvole -> Lokacija -> Dozvoli."
                        )

                request_permissions(potrebne, na_odgovor)
                return
            if pozadinska and not check_permission(pozadinska):
                try:
                    request_permissions(
                        [pozadinska],
                        lambda _, rezultati_bg: Clock.schedule_once(
                            lambda dt: self._nastavi_posle_pozadinske_dozvole(
                                all(rezultati_bg)
                            )
                        ),
                    )
                    return
                except Exception:
                    pass
        except Exception:
            pass  # nije Android (desktop test) ili modul nije dostupan

        self._stvarno_pokreni_gps()

    def _nastavi_posle_pozadinske_dozvole(self, dozvola_odobrena):
        if dozvola_odobrena:
            self._stvarno_pokreni_gps()
            return

        self._stvarno_pokreni_gps(
            koristi_foreground_servis=False,
            poruka_o_dozvoli=(
                "Pozadinska lokacija nije odobrena - koristim lokalni fallback, "
                "pa GPS mozda nece pratiti voznju dok je app u pozadini."
            ),
        )

    def _stvarno_pokreni_gps(self, koristi_foreground_servis=None, poruka_o_dozvoli=None):
        app = App.get_running_app()
        dijagnoza = dijagnostika_lokacije()
        if poruka_o_dozvoli:
            dijagnoza = f"{dijagnoza}\n{poruka_o_dozvoli}" if dijagnoza else poruka_o_dozvoli
        self.tekst_dijagnoza = dijagnoza
        self._zaustavi_lokalni_gps()

        if koristi_foreground_servis is None:
            koristi_servis = android_foreground_servis_dostupan()
        else:
            koristi_servis = koristi_foreground_servis and android_foreground_servis_dostupan()
        izvor_pracenja = "foreground_service" if koristi_servis else "lokalni_fallback"
        inicijalizuj_aktivnu_voznju(izvor_pracenja, app.user_data_dir)
        postavi_status(
            dijagnoza=dijagnoza,
            user_data_dir=app.user_data_dir,
        )
        self._ucitaj_stanje_voznje()
        self.voznja_aktivna = True
        self.tekst_gps_status = AKTIVNA_VOZNJA.gps_status
        self._pokreni_tajmer()

        pokrenuto = False
        if koristi_servis:
            pokrenuto, greska = pokreni_android_foreground_servis(user_data_dir=app.user_data_dir)
            if pokrenuto:
                self.tekst_gps_status = (
                    "Foreground servis pokrenut, GPS prati voznju i u pozadini."
                )
                postavi_status(
                    gps_status=self.tekst_gps_status,
                    user_data_dir=app.user_data_dir,
                )
            else:
                self.tekst_dijagnoza += f"\nForeground servis nije startovao: {greska}"
                postavi_status(
                    dijagnoza=self.tekst_dijagnoza,
                    izvor_pracenja="lokalni_fallback",
                    user_data_dir=app.user_data_dir,
                )
                self._ucitaj_stanje_voznje()

        if not pokrenuto:
            pokrenuto = self._pokreni_lokalni_gps()
            if not pokrenuto:
                self.tekst_gps_status = "Greska pri pokretanju GPS-a."
                return
            self.tekst_gps_status = "Lokalni GPS fallback aktivan, trazim signal..."
            postavi_status(
                gps_status=self.tekst_gps_status,
                izvor_pracenja="lokalni_fallback",
                user_data_dir=app.user_data_dir,
            )

        # Ako je krajnja adresa unesena PRE klika na "Pocni voznju",
        # odmah otvaramo Google navigaciju ka njoj. GPS voznja (merenje
        # km i cene) je vec pokrenuta iznad i nastavlja da radi u
        # pozadini - otvaranje Google Maps-a ne gasi ovu app, Android
        # je samo stavlja u pozadinu (a on_pause/on_resume u app.py
        # vec vodi racuna da GPS nastavi da meri kad se vratis).
        self._pokreni_navigaciju_ako_ima_adrese()

    def _pokreni_navigaciju_ako_ima_adrese(self):
        dolazak = self.ids.input_dolazak_rucno.text.strip()
        if not dolazak:
            return

        destinacija = urllib.parse.quote(dolazak)
        url_navigacija = f"google.navigation:q={destinacija}&mode=d"
        url_rezervni = f"https://www.google.com/maps/dir/?api=1&destination={destinacija}&travelmode=driving"
        try:
            webbrowser.open(url_navigacija)
        except Exception:
            try:
                webbrowser.open(url_rezervni)
            except Exception:
                _PRIKAZI_POPUP(
                    "Greska",
                    "Ne mogu da otvorim navigaciju, ali GPS voznja je pokrenuta normalno.",
                    size_hint=(0.8, 0.3),
                )

    def _pull_lokaciju(self, dt):
        tracker = getattr(self, "_lokalni_tracker", None)
        if tracker is not None:
            tracker.pull_lokaciju()

    def _zaustavi_lokalni_gps(self):
        tracker = getattr(self, "_lokalni_tracker", None)
        if tracker is not None:
            tracker.zaustavi()
            self._lokalni_tracker = None

    def _lokalna_dijagnoza(self, tekst):
        app = App.get_running_app()
        dodaj_dijagnozu(tekst, app.user_data_dir)
        self._ucitaj_stanje_voznje()
        self.tekst_dijagnoza = AKTIVNA_VOZNJA.dijagnoza

    def _lokalna_greska(self, tekst):
        app = App.get_running_app()
        self.tekst_gps_status = f"Greska pri pokretanju GPS-a: {tekst}"
        postavi_status(
            gps_status=self.tekst_gps_status,
            user_data_dir=app.user_data_dir,
        )

    def _proveri_signal(self, dt):
        self._ucitaj_stanje_voznje()
        if AKTIVNA_VOZNJA.pocetak_lat is not None:
            if self._brojac_signala:
                self._brojac_signala.cancel()
                self._brojac_signala = None
            return
        self._sekundi_bez_signala += 1
        if self._sekundi_bez_signala == 15:
            self.tekst_gps_status = (
                "Jos uvek nema GPS signala. Voznja je pokrenuta i ceka "
                "prvi signal - km i cena ce poceti da se racunaju cim "
                "GPS uhvati poziciju."
            )
        elif self._sekundi_bez_signala > 15 and self._sekundi_bez_signala % 10 == 0:
            self.tekst_gps_status = f"Jos uvek tražim signal... ({self._sekundi_bez_signala}s)"

        app = App.get_running_app()
        postavi_status(
            gps_status=self.tekst_gps_status,
            user_data_dir=app.user_data_dir,
        )
        self.tekst_polazak = "Trazim lokaciju..."
        self._pokreni_tajmer()

    # ---------------- TOKOM VOZNJE ----------------

    def _obradi_lokaciju(self, podaci):
        app = App.get_running_app()
        rezultat = obradi_lokaciju_i_sacuvaj(
            podaci,
            stanje=AKTIVNA_VOZNJA,
            user_data_dir=app.user_data_dir,
            min_tacnost_m=self.MIN_TACNOST_M,
            min_pomeraj_km=self.MIN_POMERAJ_KM,
            max_brzina_kmh=self.MAX_BRZINA_KMH,
        )
        self.tekst_gps_status = AKTIVNA_VOZNJA.gps_status
        self.tekst_dijagnoza = AKTIVNA_VOZNJA.dijagnoza
        if rezultat.get("promena") == "prva_tacka":
            self._pokreni_geokod_polaska_ako_treba()
        self._osvezi_prikaz()

    def _postavi_pocetnu_adresu(self, adresa):
        AKTIVNA_VOZNJA.pocetak_adresa = adresa
        app = App.get_running_app()
        AKTIVNA_VOZNJA.sacuvaj(app.user_data_dir)
        self._geokod_polaska_u_toku = None
        self.tekst_polazak = adresa

    def _geokod_dijagnoza(self, tekst):
        app = App.get_running_app()
        dodaj_dijagnozu("[Adresa] " + tekst, app.user_data_dir)
        self._ucitaj_stanje_voznje()
        self.tekst_dijagnoza = AKTIVNA_VOZNJA.dijagnoza

    def _pokreni_geokod_polaska_ako_treba(self):
        if AKTIVNA_VOZNJA.pocetak_lat is None or AKTIVNA_VOZNJA.pocetak_lon is None:
            return
        if AKTIVNA_VOZNJA.pocetak_adresa not in ("", "Trazim lokaciju..."):
            return

        kljuc = (AKTIVNA_VOZNJA.pocetak_lat, AKTIVNA_VOZNJA.pocetak_lon)
        if self._geokod_polaska_u_toku == kljuc:
            return

        self._geokod_polaska_u_toku = kljuc
        reverse_geocode(
            AKTIVNA_VOZNJA.pocetak_lat,
            AKTIVNA_VOZNJA.pocetak_lon,
            self._postavi_pocetnu_adresu,
            dijagnoza_callback=self._geokod_dijagnoza,
        )

    def _pokreni_tajmer(self):
        if self._tajmer is None:
            self._tajmer = Clock.schedule_interval(lambda dt: self._osvezi_prikaz(), 1)

    def _osvezi_prikaz(self):
        self._ucitaj_stanje_voznje()
        self.voznja_aktivna = AKTIVNA_VOZNJA.aktivna
        self.tekst_km = f"Predjeno: {AKTIVNA_VOZNJA.km:.2f} km"
        self.tekst_gps_status = AKTIVNA_VOZNJA.gps_status
        self.tekst_dijagnoza = AKTIVNA_VOZNJA.dijagnoza

        if AKTIVNA_VOZNJA.pocetak_vreme:
            pocetak = datetime.fromisoformat(AKTIVNA_VOZNJA.pocetak_vreme)
            trajanje = datetime.now() - pocetak
            ukupno_sec = int(trajanje.total_seconds())
            h, ostatak = divmod(ukupno_sec, 3600)
            m, s = divmod(ostatak, 60)
            self.tekst_trajanje = f"Trajanje: {h:02d}:{m:02d}:{s:02d}"

        cena_po_km = _CENE_REF.tarife.get(
            "Nocna (22-07h)" if _CENE_REF.nocna_aktivna else "Osnovna (07-22h)",
            _CENE_REF.tarife["Osnovna (07-22h)"],
        )
        cena = _CENE_REF.start_fee + AKTIVNA_VOZNJA.km * cena_po_km
        self.tekst_cena = f"Cena: {_FORMATIRAJ_CENU(cena)}"

        if AKTIVNA_VOZNJA.pocetak_adresa and AKTIVNA_VOZNJA.pocetak_adresa != "Trazim lokaciju...":
            self.tekst_polazak = AKTIVNA_VOZNJA.pocetak_adresa
        elif AKTIVNA_VOZNJA.aktivna:
            self.tekst_polazak = "Trazim lokaciju..."

        if AKTIVNA_VOZNJA.aktivna:
            self._pokreni_geokod_polaska_ako_treba()

    # ---------------- KRAJ VOZNJE ----------------

    def zavrsi_voznju(self):
        if not AKTIVNA_VOZNJA.aktivna:
            return

        app = App.get_running_app()
        self._ucitaj_stanje_voznje()

        if self._tajmer:
            self._tajmer.cancel()
            self._tajmer = None
        if getattr(self, "_brojac_signala", None):
            self._brojac_signala.cancel()
            self._brojac_signala = None
        if getattr(self, "_brojac_poll", None):
            self._brojac_poll.cancel()
            self._brojac_poll = None

        self.voznja_aktivna = False
        self.tekst_gps_status = "Trazim krajnju adresu..."
        postavi_status(
            gps_status=self.tekst_gps_status,
            izvor_pracenja="zavrsetak_u_toku",
            user_data_dir=app.user_data_dir,
        )
        self._ucitaj_stanje_voznje()

        # ako GPS nije uspeo da izmeri km, koristi rucni unos (ako postoji polje)
        km = AKTIVNA_VOZNJA.km
        if km <= 0:
            polje_km = self.ids.get("input_km_rucno")
            rucni_km_tekst = polje_km.text.strip() if polje_km else ""
            if rucni_km_tekst:
                try:
                    km = float(rucni_km_tekst.replace(",", "."))
                except ValueError:
                    km = 0.0

        cena_po_km = _CENE_REF.tarife.get(
            "Nocna (22-07h)" if _CENE_REF.nocna_aktivna else "Osnovna (07-22h)",
            _CENE_REF.tarife["Osnovna (07-22h)"],
        )
        ukupno = _CENE_REF.start_fee + km * cena_po_km
        tarifa_naziv = "Nocna (22-07h)" if _CENE_REF.nocna_aktivna else "Osnovna (07-22h)"

        polazak_adresa = AKTIVNA_VOZNJA.pocetak_adresa or "Adresa nije dostupna"
        if polazak_adresa == "Trazim lokaciju...":
            polazak_adresa = "Adresa nije dostupna"

        rucni_dolazak = self.ids.input_dolazak_rucno.text.strip()

        if rucni_dolazak:
            self._sacuvaj_zavrsenu_voznju(
                km, cena_po_km, ukupno, tarifa_naziv, polazak_adresa, rucni_dolazak
            )
        elif AKTIVNA_VOZNJA.zadnja_lat is not None:
            reverse_geocode(
                AKTIVNA_VOZNJA.zadnja_lat,
                AKTIVNA_VOZNJA.zadnja_lon,
                lambda adresa: self._sacuvaj_zavrsenu_voznju(
                    km, cena_po_km, ukupno, tarifa_naziv, polazak_adresa, adresa
                ),
                dijagnoza_callback=self._geokod_dijagnoza,
            )
        else:
            self._sacuvaj_zavrsenu_voznju(
                km, cena_po_km, ukupno, tarifa_naziv, polazak_adresa,
                "Adresa nije dostupna",
            )

    def _sacuvaj_zavrsenu_voznju(self, km, cena_po_km, ukupno, tarifa_naziv,
                                   polazak_adresa, dolazak_adresa):
        app = App.get_running_app()
        self._ucitaj_stanje_voznje()
        if AKTIVNA_VOZNJA.km > km:
            km = AKTIVNA_VOZNJA.km

        self._zaustavi_lokalni_gps()
        if android_foreground_servis_pokrenut(app.user_data_dir):
            zaustavljeno, greska = zaustavi_android_foreground_servis(
                user_data_dir=app.user_data_dir,
            )
            if not zaustavljeno:
                self.tekst_dijagnoza = (
                    (AKTIVNA_VOZNJA.dijagnoza + "\n") if AKTIVNA_VOZNJA.dijagnoza else ""
                ) + f"Foreground servis nije zaustavljen cisto ({greska})."

        vreme_pocetka_txt = None
        if AKTIVNA_VOZNJA.pocetak_vreme:
            try:
                vreme_pocetka_txt = datetime.fromisoformat(
                    AKTIVNA_VOZNJA.pocetak_vreme
                ).strftime("%H:%M")
            except Exception:
                vreme_pocetka_txt = None

        db.dodaj_voznju(
            od_adresa=polazak_adresa,
            do_adresa=dolazak_adresa,
            km=round(km, 2),
            tarifa_naziv=tarifa_naziv,
            cena_po_km=cena_po_km,
            start_taksa=_CENE_REF.start_fee,
            ukupna_cena=ukupno,
            napomena="GPS voznja (automatski unos)",
            vreme_pocetka=vreme_pocetka_txt,
        )

        AKTIVNA_VOZNJA.resetuj(app.user_data_dir)

        self.tekst_gps_status = ""
        self.tekst_dijagnoza = ""
        self.tekst_polazak = "Nije zapoceta"
        self.tekst_km = "Predjeno: 0.00 km"
        self.tekst_trajanje = "Trajanje: 00:00:00"
        self.tekst_cena = f"Cena: {_FORMATIRAJ_CENU(0)}"
        self.ids.input_dolazak_rucno.text = ""

        self._poruka(
            f"Voznja sacuvana!\n{polazak_adresa}\n-> {dolazak_adresa}\n"
            f"{km:.2f} km, {_FORMATIRAJ_CENU(ukupno)}"
        )

    def _poruka(self, tekst):
        _PRIKAZI_POPUP("Voznja zavrsena", tekst, size_hint=(0.85, 0.4))

GPS_VOZNJA_KV = """
# ============================================================
# GPS VOZNJA - automatsko pracenje
# ============================================================

<GpsVoznjaScreen>:
    name: "gps_voznja"
    ScreenRoot:

        TitleLabel:
            text: "GPS voznja"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"
            RoundButton:
                label_text: "Istorija"
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "evidencija"

        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: dp(4)

                PastelCard:
                    orientation: "vertical"
                    tint: 0.38, 0.32, 0.52, 0.92
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(14)
                    spacing: dp(4)
                    Label:
                        text: "POLAZAK"
                        font_size: '13sp'
                        bold: True
                        color: 0.78, 0.74, 0.92, 1
                        size_hint_y: None
                        height: dp(20)
                        halign: "left"
                        text_size: self.size
                    Label:
                        text: root.tekst_polazak
                        font_size: '15sp'
                        color: 0.94, 0.91, 1, 1
                        halign: "left"
                        valign: "top"
                        size_hint_y: None
                        text_size: self.width, None
                        height: self.texture_size[1]

                FieldLabel:
                    text: "Krajnja adresa (opciono - unesi je PRE 'Pocni voznju' da odmah krene Google navigacija)"

                PastelTextInput:
                    id: input_dolazak_rucno
                    hint_text: "npr. Nemanjina 4, Beograd"

                FieldLabel:
                    text: "Ostavi prazno da sve radi kao do sad - GPS sam nalazi i polaznu i krajnju adresu. Dok je voznja aktivna, na Androidu ostaje i trajna notifikacija da pracenje radi i u pozadini."
                    size_hint_y: None
                    height: dp(54)
                    text_size: self.width, None

                PastelCard:
                    tint: 0.28, 0.48, 0.34, 0.92
                    size_hint_y: None
                    height: dp(64)
                    padding: dp(14)
                    Label:
                        text: root.tekst_km
                        font_size: '20sp'
                        bold: True
                        color: 0.90, 1, 0.92, 1

                PastelCard:
                    tint: 0.55, 0.38, 0.26, 0.92
                    size_hint_y: None
                    height: dp(56)
                    padding: dp(14)
                    Label:
                        text: root.tekst_trajanje
                        font_size: '16sp'
                        bold: True
                        color: 1, 0.90, 0.80, 1

                PastelCard:
                    tint: 0.26, 0.40, 0.58, 0.92
                    size_hint_y: None
                    height: dp(64)
                    padding: dp(14)
                    Label:
                        text: root.tekst_cena
                        font_size: '20sp'
                        bold: True
                        color: 0.85, 0.92, 1, 1

                Label:
                    text: root.tekst_gps_status
                    size_hint_y: None
                    height: self.texture_size[1] + dp(10)
                    font_size: '13sp'
                    color: 0.85, 0.85, 0.95, 1
                    text_size: self.width, None

                Label:
                    text: root.tekst_dijagnoza
                    size_hint_y: None
                    height: self.texture_size[1] + dp(10)
                    font_size: '12sp'
                    color: 0.65, 0.85, 1, 1
                    text_size: self.width, None

                RoundButton:
                    id: dugme_start
                    label_text: "POCNI VOZNJU"
                    tint: 0.30, 0.52, 0.36, 1
                    text_color: 0.92, 1, 0.94, 1
                    size_hint_y: None
                    height: dp(56)
                    disabled: root.voznja_aktivna
                    on_release: root.pocni_voznju()

                RoundButton:
                    id: dugme_zavrsi
                    label_text: "ZAVRSI VOZNJU"
                    tint: 0.74, 0.28, 0.32, 1
                    text_color: 1, 1, 1, 1
                    size_hint_y: None
                    height: dp(56)
                    disabled: not root.voznja_aktivna
                    on_release: root.zavrsi_voznju()


"""
