"""
ekran_gps_voznja.py
Automatsko pracenje voznje preko GPS-a: haversine_km (racunanje
udaljenosti), reverse_geocode (GPS koordinate -> adresa, Google ili
OpenStreetMap), AktivnaVoznjaState (trajno stanje aktivne voznje,
prezivljava gasenje app-a) i sam GpsVoznjaScreen.

Ovo je najveci i najosetljiviji ekran u app-i - direktno koristi
Android LocationManager preko pyjnius, i ima posebnu logiku da
prezivi kad app ode u pozadinu (npr. korisnik otvori Google Maps).

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py.
"""

import os
import json
import math
import time
import threading
import urllib.parse
import webbrowser
from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty
from kivy.app import App
from kivy.clock import Clock

from servisi import database as db
from servisi import api_helper  # ← NOVO: Import api_helper-a


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


def haversine_km(lat1, lon1, lat2, lon2):
    """Udaljenost izmedju dve GPS tacke u km (haversine formula)."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def reverse_geocode(lat, lon, callback, dijagnoza_callback=None):
    """
    Pretvara GPS koordinate u adresu koristeći api_helper modul.
    
    Ako je unet Google API ključ (Podesavanja -> Google API), koristi
    Google Geocoding (tačnije). Ako ključa nema ili Google poziv ne uspe,
    koristi besplatan OpenStreetMap Nominatim kao fallback.
    
    Radi u pozadinskoj niti da ne blokira interfejs; rezultat vraća
    preko callback-a na glavnoj niti.
    
    Args:
        lat (float): Geografska širina
        lon (float): Geografska dužina
        callback: Funkcija(adresa) koja se poziva sa rezultatom
        dijagnoza_callback: Opciono - funkcija(tekst) sa debug info-om
    """
    def posao():
        google_kljuc = _API_REF.google_kljuc.strip() if _API_REF else ""
        
        # Koristi api_helper za pronalaženje adrese
        ok, adresa, poruka_greske = api_helper.poveži_google_geocoding(
            google_kljuc, lat, lon, timeout=8
        )
        
        if ok:
            Clock.schedule_once(lambda dt: callback(adresa))
        else:
            # Fallback - koristi "nepoznato" umesto praznog
            Clock.schedule_once(lambda dt: callback("Adresa nije dostupna"))
            if dijagnoza_callback and poruka_greske:
                Clock.schedule_once(lambda dt: dijagnoza_callback(poruka_greske))

    threading.Thread(target=posao, daemon=True).start()


class AktivnaVoznjaState:
    """Čuva stanje trenutno aktivne GPS vožnje u fajl, da se ne
    izgubi ako korisnik zatvori i ponovo otvori aplikaciju."""

    def __init__(self):
        self.aktivna = False
        self.pocetak_vreme = None
        self.pocetak_lat = None
        self.pocetak_lon = None
        self.pocetak_adresa = ""
        self.zadnja_lat = None
        self.zadnja_lon = None
        self.zadnje_vreme = None  # time.time() kad je zadnja_lat/lon primljena -
                                   # služi da se izračuna PRAVO proteklo vreme
                                   # do sledeće tačke (vidi _obradi_lokaciju)
        self.km = 0.0

    def _putanja(self, user_data_dir):
        return os.path.join(user_data_dir, "aktivna_voznja.json")

    def ucitaj(self, user_data_dir):
        try:
            with open(self._putanja(user_data_dir), "r", encoding="utf-8") as f:
                podaci = json.load(f)
            self.aktivna = podaci.get("aktivna", False)
            self.pocetak_vreme = podaci.get("pocetak_vreme")
            self.pocetak_lat = podaci.get("pocetak_lat")
            self.pocetak_lon = podaci.get("pocetak_lon")
            self.pocetak_adresa = podaci.get("pocetak_adresa", "")
            self.zadnja_lat = podaci.get("zadnja_lat")
            self.zadnja_lon = podaci.get("zadnja_lon")
            self.zadnje_vreme = podaci.get("zadnje_vreme")
            self.km = podaci.get("km", 0.0)
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass

    def sacuvaj(self, user_data_dir):
        podaci = {
            "aktivna": self.aktivna,
            "pocetak_vreme": self.pocetak_vreme,
            "pocetak_lat": self.pocetak_lat,
            "pocetak_lon": self.pocetak_lon,
            "pocetak_adresa": self.pocetak_adresa,
            "zadnja_lat": self.zadnja_lat,
            "zadnja_lon": self.zadnja_lon,
            "zadnje_vreme": self.zadnje_vreme,
            "km": self.km,
        }
        with open(self._putanja(user_data_dir), "w", encoding="utf-8") as f:
            json.dump(podaci, f, ensure_ascii=False, indent=2)

    def resetuj(self, user_data_dir):
        self.__init__()
        self.sacuvaj(user_data_dir)


AKTIVNA_VOZNJA = AktivnaVoznjaState()


class GpsVoznjaScreen(Screen):
    tekst_polazak = StringProperty("Nije zapoceta")
    tekst_km = StringProperty("Predjeno: 0.00 km")
    tekst_trajanje = StringProperty("Trajanje: 00:00:00")
    tekst_cena = StringProperty("Cena: 0 RSD")
    tekst_gps_status = StringProperty("")
    tekst_dijagnoza = StringProperty("")
    voznja_aktivna = BooleanProperty(False)

    MIN_TACNOST_M = 50       # ignorisi GPS tačke lošije preciznosti od ovoga (metri)
    MIN_POMERAJ_KM = 0.01    # ignorisi mikro-skokove manje od 10m (GPS šum)
    MAX_BRZINA_KMH = 180     # ignorisi nerealne skokove (loša GPS tačka)

    def on_pre_enter(self, *args):
        self._tajmer = None
        self._brojac_signala = None
        self._brojac_poll = None
        self._sekundi_bez_signala = 0
        self._zadnje_vreme_lok = None
        if AKTIVNA_VOZNJA.aktivna:
            self.voznja_aktivna = True
            self.tekst_polazak = AKTIVNA_VOZNJA.pocetak_adresa or "Adresa nije dostupna"
            self._osvezi_prikaz()
            self._pokreni_tajmer()
            self._android_gps_start()  # ponovo zakači listener + omogući poll
            self._brojac_poll = Clock.schedule_interval(self._pull_lokaciju, 2)
        else:
            self.voznja_aktivna = False
            self.tekst_polazak = "Nije zapoceta"
            self.tekst_km = "Predjeno: 0.00 km"
            self.tekst_trajanje = "Trajanje: 00:00:00"
            self.tekst_cena = "Cena: 0 RSD"

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

    # ---------------- POČETAK VOŽNJE ----------------

    def _dijagnostika_lokacije(self):
        """Vraća tekst sa stvarnim stanjem dozvola i GPS-a na uređaju,
        da se tačno vidi gde je problem umesto nagađanja."""
        redovi = []
        try:
            from android.permissions import check_permission, Permission
            fine = check_permission(Permission.ACCESS_FINE_LOCATION)
            coarse = check_permission(Permission.ACCESS_COARSE_LOCATION)
            redovi.append(f"Dozvola FINE_LOCATION: {'DA' if fine else 'NE'}")
            redovi.append(f"Dozvola COARSE_LOCATION: {'DA' if coarse else 'NE'}")
        except Exception as e:
            redovi.append(f"Ne mogu da proverim dozvole: {e}")

        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            activity = PythonActivity.mActivity
            lm = activity.getSystemService(Context.LOCATION_SERVICE)
            gps_on = lm.isProviderEnabled("gps")
            mreza_on = lm.isProviderEnabled("network")
            redovi.append(f"GPS provajder uključen: {'DA' if gps_on else 'NE'}")
            redovi.append(f"Mrežni provajder uključen: {'DA' if mreza_on else 'NE'}")
        except Exception as e:
            redovi.append(f"Ne mogu da proverim GPS status: {e}")

        return "\n".join(redovi)

    def pocni_voznju(self):
        try:
            from android.permissions import (
                request_permissions, check_permission, Permission,
            )
            potrebne = [
                Permission.ACCESS_FINE_LOCATION,
                Permission.ACCESS_COARSE_LOCATION,
            ]
            if not all(check_permission(p) for p in potrebne):
                self.tekst_gps_status = "Tražim dozvolu za lokaciju..."

                def na_odgovor(dozvole, rezultati):
                    if all(rezultati):
                        Clock.schedule_once(lambda dt: self._stvarno_pokreni_gps())
                    else:
                        self.tekst_gps_status = (
                            "Dozvola za lokaciju NIJE odobrena. Idi u "
                            "Podesavanja telefona -> Aplikacije -> Taksi App "
                            "-> Dozvole -> Lokacija -> Dozvoli."
                        )

                request_permissions(potrebne, na_odgovor)
                return
        except Exception:
            pass  # nije Android (desktop test) ili modul nije dostupan

        self._stvarno_pokreni_gps()

    def _stvarno_pokreni_gps(self):
        dijagnoza = self._dijagnostika_lokacije()
        self.tekst_dijagnoza = dijagnoza

        pokrenuto = self._android_gps_start()
        if not pokrenuto:
            self.tekst_gps_status = "Greška pri pokretanju GPS-a."
            return

        self.voznja_aktivna = True
        self.tekst_gps_status = "Tražim GPS signal..."
        self._sekundi_bez_signala = 0
        self._zadnje_vreme_lok = None
        self._brojac_signala = Clock.schedule_interval(self._proveri_signal, 1)
        self._brojac_poll = Clock.schedule_interval(self._pull_lokaciju, 2)
        AKTIVNA_VOZNJA.aktivna = True
        AKTIVNA_VOZNJA.pocetak_vreme = datetime.now().isoformat()
        AKTIVNA_VOZNJA.pocetak_lat = None
        AKTIVNA_VOZNJA.pocetak_lon = None
        AKTIVNA_VOZNJA.pocetak_adresa = "Tražim lokaciju..."
        AKTIVNA_VOZNJA.zadnja_lat = None
        AKTIVNA_VOZNJA.zadnja_lon = None
        AKTIVNA_VOZNJA.km = 0.0

        app = App.get_running_app()
        AKTIVNA_VOZNJA.sacuvaj(app.user_data_dir)

        # Ako je krajnja adresa unesena PRE klika na "Počni voznju",
        # odmah otvaramo Google navigaciju ka njoj. GPS vožnja (merenje
        # km i cene) je već pokrenuta iznad i nastavlja da radi u
        # pozadini - otvaranje Google Maps-a ne gasi ovu app, Android
        # je samo stavlja u pozadinu (a on_pause/on_resume u app.py
        # već vodi računa da GPS nastavi da meri kad se vratiš).
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
                    "Greška",
                    "Ne mogu da otvorim navigaciju, ali GPS vožnja je pokrenuta normalno.",
                    size_hint=(0.8, 0.3),
                )

    def _pull_lokaciju(self, dt):
        """Umesto da čekamo da Android sam pošalje novu tačku (push,
        što se pokazalo nepouzdano - verovatno MIUI blokira stalno
        slanje u pozadini), aktivno pitamo za trenutnu poslednju
        poznatu lokaciju na svakih 2 sekunde (pull). Isti trik koji je
        upralio za početnu tačku vožnje."""
        try:
            from jnius import autoclass

            LocationManager = autoclass("android.location.LocationManager")
            lm = getattr(self, "_android_lm", None)
            if lm is None:
                return

            najbolja = None
            for provider in (LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER):
                try:
                    if lm.isProviderEnabled(provider):
                        tacka = lm.getLastKnownLocation(provider)
                        if tacka is not None:
                            if najbolja is None or tacka.getTime() > najbolja.getTime():
                                najbolja = tacka
                except Exception:
                    pass

            if najbolja is None:
                return

            vreme = najbolja.getTime()
            if self._zadnje_vreme_lok is not None and vreme <= self._zadnje_vreme_lok:
                return  # ista tačka kao pre, ništa novo

            self._zadnje_vreme_lok = vreme
            self._obradi_lokaciju({
                "lat": najbolja.getLatitude(),
                "lon": najbolja.getLongitude(),
                "accuracy": najbolja.getAccuracy(),
            })
        except Exception:
            pass

    def _android_gps_start(self):
        """Direktno preko Android sistema traži lokaciju - i GPS i
        mrežni provajder istovremeno (šta god prvo javi signal), jer
        plyer sam po sebi koristi samo GPS provajder što se pokazalo
        nepouzdano na nekim uređajima/podešavanjima."""
        try:
            from jnius import autoclass, PythonJavaClass, java_method

            LocationManager = autoclass("android.location.LocationManager")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            Looper = autoclass("android.os.Looper")

            activity = PythonActivity.mActivity
            lm = activity.getSystemService(Context.LOCATION_SERVICE)
            glavni_looper = Looper.getMainLooper()

            ekran = self

            class _Listener(PythonJavaClass):
                __javainterfaces__ = ["android/location/LocationListener"]
                __javacontext__ = "app"

                @java_method("(Landroid/location/Location;)V")
                def onLocationChanged(self, location):
                    Clock.schedule_once(lambda dt: ekran._obradi_lokaciju({
                        "lat": location.getLatitude(),
                        "lon": location.getLongitude(),
                        "accuracy": location.getAccuracy(),
                    }))

                @java_method("(Ljava/lang/String;)V")
                def onProviderEnabled(self, provider):
                    pass

                @java_method("(Ljava/lang/String;)V")
                def onProviderDisabled(self, provider):
                    pass

                @java_method("(Ljava/lang/String;ILandroid/os/Bundle;)V")
                def onStatusChanged(self, provider, status, extras):
                    pass

            listener = _Listener()
            self._android_listener = listener
            self._android_lm = lm

            pokrenut_bar_jedan = False
            greske = []
            for provider in (LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER):
                try:
                    if lm.isProviderEnabled(provider):
                        lm.requestLocationUpdates(
                            provider, 1000, 3.0, listener, glavni_looper
                        )
                        pokrenut_bar_jedan = True
                except Exception as pe:
                    greske.append(f"{provider}: {pe}")

            if not pokrenut_bar_jedan and greske:
                self.tekst_dijagnoza += "\n" + "\n".join(greske)

            # Odmah probaj i poslednju poznatu (keširana) lokaciju -
            # ne čekaj obavezno novi "živi" signal. Google Maps i
            # slične app također prvo koriste ovo, zato deluju trenutno.
            najbolja = None
            for provider in (LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER):
                try:
                    if lm.isProviderEnabled(provider):
                        poslednja = lm.getLastKnownLocation(provider)
                        if poslednja is not None:
                            if najbolja is None or poslednja.getTime() > najbolja.getTime():
                                najbolja = poslednja
                except Exception:
                    pass

            if najbolja is not None:
                self.tekst_dijagnoza += "\nPronađena keširana lokacija - koristim je."
                Clock.schedule_once(lambda dt: self._obradi_lokaciju({
                    "lat": najbolja.getLatitude(),
                    "lon": najbolja.getLongitude(),
                    "accuracy": najbolja.getAccuracy(),
                }))
            else:
                self.tekst_dijagnoza += "\nNema keširane lokacije, čekam živi signal."

            return pokrenut_bar_jedan
        except Exception as e:
            self.tekst_gps_status = f"Greška pri pokretanju GPS-a: {e}"
            return False

    def _android_gps_stop(self):
        try:
            lm = getattr(self, "_android_lm", None)
            listener = getattr(self, "_android_listener", None)
            if lm is not None and listener is not None:
                lm.removeUpdates(listener)
        except Exception:
            pass

    def _proveri_signal(self, dt):
        if AKTIVNA_VOZNJA.pocetak_lat is not None:
            if self._brojac_signala:
                self._brojac_signala.cancel()
                self._brojac_signala = None
            return
        self._sekundi_bez_signala += 1
        if self._sekundi_bez_signala == 15:
            self.tekst_gps_status = (
                "Još uvek nema GPS signala. Vožnja je pokrenuta i čeka "
                "prvi signal - km i cena će početi da se računaju čim "
                "GPS uhvati poziciju."
            )
        elif self._sekundi_bez_signala > 15 and self._sekundi_bez_signala % 10 == 0:
            self.tekst_gps_status = f"Još uvek tražim signal... ({self._sekundi_bez_signala}s)"

        self.tekst_polazak = "Tražim lokaciju..."
        self._pokreni_tajmer()

    # ---------------- TOKOM VOŽNJE ----------------

    def _obradi_lokaciju(self, podaci):
        lat = podaci.get("lat")
        lon = podaci.get("lon")
        tacnost = podaci.get("accuracy", 0) or 0
        if lat is None or lon is None:
            return

        app = App.get_running_app()

        if AKTIVNA_VOZNJA.pocetak_lat is None:
            # ovo je prva validna tačka - početak vožnje.
            # Ne filtriramo je po preciznosti (keširane/mrežne lokacije
            # su često manje precizne od 50m, ali su i dalje mnogo
            # bolje nego ništa za početnu adresu i orijentaciju).
            AKTIVNA_VOZNJA.pocetak_lat = lat
            AKTIVNA_VOZNJA.pocetak_lon = lon
            AKTIVNA_VOZNJA.zadnja_lat = lat
            AKTIVNA_VOZNJA.zadnja_lon = lon
            AKTIVNA_VOZNJA.zadnje_vreme = time.time()
            AKTIVNA_VOZNJA.sacuvaj(app.user_data_dir)
            self.tekst_gps_status = "GPS aktivan, pratim vožnju."
            reverse_geocode(
                lat, lon, self._postavi_pocetnu_adresu,
                dijagnoza_callback=self._geokod_dijagnoza,
            )
            return

        # od druge tačke nadalje, filtriramo loše precizne skokove
        # (bitno za tačnost kilometraže tokom stvarne vožnje)
        if tacnost and tacnost > self.MIN_TACNOST_M:
            self.tekst_gps_status = f"Slab GPS signal (+/-{tacnost:.0f}m), čekam bolji..."
            return

        # računaj pomeraj od poslednje tačke
        udaljenost = haversine_km(
            AKTIVNA_VOZNJA.zadnja_lat, AKTIVNA_VOZNJA.zadnja_lon, lat, lon
        )

        if udaljenost < self.MIN_POMERAJ_KM:
            return  # mikro-šum, ignoriši

        # PRAVO proteklo vreme od poslednje prihvaćene tačke (ne
        # pretpostavljeni fiksni razmak) - bitno kad je telefon bio u
        # pozadini (npr. korisnik gledao Google Maps par minuta): bez
        # ovoga bi provera brzine ispod pogrešno protumačila normalan
        # pomeraj kao "nerealan skok" i TRAJNO odbacila te kilometre.
        sada = time.time()
        proteklo_sec = sada - (AKTIVNA_VOZNJA.zadnje_vreme or sada)
        proteklo_sec = max(proteklo_sec, 1.0)  # minimum 1s - štiti od deljenja
                                                 # gotovo nulom kod dve tačke
                                                 # koje stignu skoro istovremeno

        # provera nerealnog skoka (loša GPS tačka)
        brzina_kmh = udaljenost / (proteklo_sec / 3600.0)
        if brzina_kmh > self.MAX_BRZINA_KMH:
            return  # verovatno GPS greška, ignoriši tačku

        AKTIVNA_VOZNJA.km += udaljenost
        AKTIVNA_VOZNJA.zadnja_lat = lat
        AKTIVNA_VOZNJA.zadnja_lon = lon
        AKTIVNA_VOZNJA.zadnje_vreme = sada
        AKTIVNA_VOZNJA.sacuvaj(app.user_data_dir)
        self._osvezi_prikaz()

    def _postavi_pocetnu_adresu(self, adresa):
        AKTIVNA_VOZNJA.pocetak_adresa = adresa
        app = App.get_running_app()
        AKTIVNA_VOZNJA.sacuvaj(app.user_data_dir)
        self.tekst_polazak = adresa

    def _geokod_dijagnoza(self, tekst):
        self.tekst_dijagnoza += "\n[Adresa] " + tekst

    def _pokreni_tajmer(self):
        if self._tajmer is None:
            self._tajmer = Clock.schedule_interval(lambda dt: self._osvezi_prikaz(), 1)

    def _osvezi_prikaz(self):
        self.tekst_km = f"Predjeno: {AKTIVNA_VOZNJA.km:.2f} km"

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

        if AKTIVNA_VOZNJA.pocetak_adresa and AKTIVNA_VOZNJA.pocetak_adresa != "Tražim lokaciju...":
            self.tekst_polazak = AKTIVNA_VOZNJA.pocetak_adresa

    # ---------------- KRAJ VOŽNJE ----------------

    def zavrsi_voznju(self):
        if not AKTIVNA_VOZNJA.aktivna:
            return

        self._android_gps_stop()

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
        self.tekst_gps_status = "Tražim krajnju adresu..."

        # ako GPS nije uspeo da izmeri km, koristi ručni unos (ako postoji polje)
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
        if polazak_adresa == "Tražim lokaciju...":
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
            napomena="GPS vožnja (automatski unos)",
            vreme_pocetka=vreme_pocetka_txt,
        )

        app = App.get_running_app()
        AKTIVNA_VOZNJA.resetuj(app.user_data_dir)

        self.tekst_gps_status = ""
        self.tekst_dijagnoza = ""
        self.tekst_polazak = "Nije zapoceta"
        self.tekst_km = "Predjeno: 0.00 km"
        self.tekst_trajanje = "Trajanje: 00:00:00"
        self.tekst_cena = f"Cena: {_FORMATIRAJ_CENU(0)}"
        self.ids.input_dolazak_rucno.text = ""

        self._poruka(
            f"Vožnja sačuvana!\n{polazak_adresa}\n-> {dolazak_adresa}\n"
            f"{km:.2f} km, {_FORMATIRAJ_CENU(ukupno)}"
        )

    def _poruka(self, tekst):
        _PRIKAZI_POPUP("Vožnja završena", tekst, size_hint=(0.85, 0.4))

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
                    text: "Ostavi prazno da sve radi kao do sad - GPS sam nalazi i polaznu i krajnju adresu."
                    size_hint_y: None
                    height: dp(34)
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
