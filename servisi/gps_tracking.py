"""
Deljena GPS logika za aktivnu voznju, Android pracenje i foreground servis.
"""

import json
import os
import time
from datetime import datetime

try:
    from kivy.app import App
except Exception:  # pragma: no cover - Kivy nije obavezan za unit/probe skripte
    App = None


ANDROID_SERVICE_CLASS = "org.licno.taksiapp.ServiceGpstracking"
STOP_FAJL = "gps_tracking_service.stop"


def odredi_user_data_dir(user_data_dir=None):
    if user_data_dir:
        return user_data_dir

    if App is not None:
        try:
            app = App.get_running_app()
            if app is not None and getattr(app, "user_data_dir", None):
                return app.user_data_dir
        except Exception:
            pass

    try:
        from android.storage import app_storage_path  # type: ignore

        return app_storage_path()
    except Exception:
        return os.path.dirname(os.path.abspath(__file__))


def putanja_stop_fajla(user_data_dir=None):
    return os.path.join(odredi_user_data_dir(user_data_dir), STOP_FAJL)


def ocisti_stop_fajl(user_data_dir=None):
    try:
        os.remove(putanja_stop_fajla(user_data_dir))
    except FileNotFoundError:
        pass
    except Exception:
        pass


def postavi_stop_fajl(user_data_dir=None):
    try:
        with open(putanja_stop_fajla(user_data_dir), "w", encoding="utf-8") as f:
            f.write(str(time.time()))
    except Exception:
        pass


def treba_zaustaviti_servis(user_data_dir=None):
    return os.path.exists(putanja_stop_fajla(user_data_dir))


def haversine_km(lat1, lon1, lat2, lon2):
    import math

    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class AktivnaVoznjaState:
    def __init__(self):
        self.aktivna = False
        self.pocetak_vreme = None
        self.pocetak_lat = None
        self.pocetak_lon = None
        self.pocetak_adresa = ""
        self.zadnja_lat = None
        self.zadnja_lon = None
        self.zadnje_vreme = None
        self.km = 0.0
        self.gps_status = ""
        self.dijagnoza = ""
        self.izvor_pracenja = ""

    def _putanja(self, user_data_dir=None):
        return os.path.join(odredi_user_data_dir(user_data_dir), "aktivna_voznja.json")

    def ucitaj(self, user_data_dir=None):
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
            self.gps_status = podaci.get("gps_status", "")
            self.dijagnoza = podaci.get("dijagnoza", "")
            self.izvor_pracenja = podaci.get("izvor_pracenja", "")
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass

    def sacuvaj(self, user_data_dir=None):
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
            "gps_status": self.gps_status,
            "dijagnoza": self.dijagnoza,
            "izvor_pracenja": self.izvor_pracenja,
        }
        with open(self._putanja(user_data_dir), "w", encoding="utf-8") as f:
            json.dump(podaci, f, ensure_ascii=False, indent=2)

    def resetuj(self, user_data_dir=None):
        self.__init__()
        self.sacuvaj(user_data_dir)


AKTIVNA_VOZNJA = AktivnaVoznjaState()


def ucitaj_aktivnu_voznju(user_data_dir=None):
    stanje = AktivnaVoznjaState()
    stanje.ucitaj(user_data_dir)
    return stanje


def postavi_status(gps_status=None, dijagnoza=None, izvor_pracenja=None, user_data_dir=None):
    stanje = ucitaj_aktivnu_voznju(user_data_dir)
    if gps_status is not None:
        stanje.gps_status = gps_status
    if dijagnoza is not None:
        stanje.dijagnoza = dijagnoza
    if izvor_pracenja is not None:
        stanje.izvor_pracenja = izvor_pracenja
    stanje.sacuvaj(user_data_dir)
    return stanje


def dodaj_dijagnozu(tekst, user_data_dir=None):
    if not tekst:
        return ucitaj_aktivnu_voznju(user_data_dir)

    stanje = ucitaj_aktivnu_voznju(user_data_dir)
    postojeci = [red for red in stanje.dijagnoza.splitlines() if red.strip()]
    novi = [red.strip() for red in tekst.splitlines() if red.strip()]
    for red in novi:
        if red not in postojeci:
            postojeci.append(red)
    stanje.dijagnoza = "\n".join(postojeci)
    stanje.sacuvaj(user_data_dir)
    return stanje


def inicijalizuj_aktivnu_voznju(izvor_pracenja, user_data_dir=None):
    stanje = ucitaj_aktivnu_voznju(user_data_dir)
    stanje.aktivna = True
    stanje.pocetak_vreme = datetime.now().isoformat()
    stanje.pocetak_lat = None
    stanje.pocetak_lon = None
    stanje.pocetak_adresa = "Trazim lokaciju..."
    stanje.zadnja_lat = None
    stanje.zadnja_lon = None
    stanje.zadnje_vreme = None
    stanje.km = 0.0
    stanje.gps_status = "Trazim GPS signal..."
    stanje.dijagnoza = ""
    stanje.izvor_pracenja = izvor_pracenja
    stanje.sacuvaj(user_data_dir)
    return stanje


def obradi_lokaciju_i_sacuvaj(
    podaci,
    stanje=None,
    user_data_dir=None,
    min_tacnost_m=50,
    min_pomeraj_km=0.01,
    max_brzina_kmh=180,
    sada=None,
):
    stanje = stanje or ucitaj_aktivnu_voznju(user_data_dir)
    if not stanje.aktivna:
        return {"promena": "ignorisano", "razlog": "voznja_nije_aktivna", "stanje": stanje}

    lat = podaci.get("lat")
    lon = podaci.get("lon")
    tacnost = podaci.get("accuracy", 0) or 0
    if lat is None or lon is None:
        return {"promena": "ignorisano", "razlog": "bez_koordinata", "stanje": stanje}

    sada = time.time() if sada is None else sada

    if stanje.pocetak_lat is None:
        stanje.pocetak_lat = lat
        stanje.pocetak_lon = lon
        stanje.zadnja_lat = lat
        stanje.zadnja_lon = lon
        stanje.zadnje_vreme = sada
        if not stanje.pocetak_vreme:
            stanje.pocetak_vreme = datetime.now().isoformat()
        if not stanje.pocetak_adresa:
            stanje.pocetak_adresa = "Trazim lokaciju..."
        stanje.gps_status = "GPS aktivan, pratim voznju."
        stanje.sacuvaj(user_data_dir)
        return {"promena": "prva_tacka", "stanje": stanje}

    if tacnost and tacnost > min_tacnost_m:
        stanje.gps_status = f"Slab GPS signal (+/-{tacnost:.0f}m), cekam bolji..."
        stanje.sacuvaj(user_data_dir)
        return {"promena": "ignorisano", "razlog": "slaba_tacnost", "stanje": stanje}

    udaljenost = haversine_km(stanje.zadnja_lat, stanje.zadnja_lon, lat, lon)
    if udaljenost < min_pomeraj_km:
        return {"promena": "ignorisano", "razlog": "mikro_pomeraj", "stanje": stanje}

    proteklo_sec = sada - (stanje.zadnje_vreme or sada)
    proteklo_sec = max(proteklo_sec, 1.0)
    brzina_kmh = udaljenost / (proteklo_sec / 3600.0)
    if brzina_kmh > max_brzina_kmh:
        return {"promena": "ignorisano", "razlog": "nerealna_brzina", "stanje": stanje}

    stanje.km += udaljenost
    stanje.zadnja_lat = lat
    stanje.zadnja_lon = lon
    stanje.zadnje_vreme = sada
    stanje.gps_status = "GPS aktivan, pratim voznju."
    stanje.sacuvaj(user_data_dir)
    return {
        "promena": "azurirano",
        "udaljenost_km": udaljenost,
        "brzina_kmh": brzina_kmh,
        "stanje": stanje,
    }


def dijagnostika_lokacije():
    redovi = []
    try:
        from android.permissions import check_permission, Permission  # type: ignore

        fine = check_permission(Permission.ACCESS_FINE_LOCATION)
        coarse = check_permission(Permission.ACCESS_COARSE_LOCATION)
        redovi.append(f"Dozvola FINE_LOCATION: {'DA' if fine else 'NE'}")
        redovi.append(f"Dozvola COARSE_LOCATION: {'DA' if coarse else 'NE'}")
        if hasattr(Permission, "ACCESS_BACKGROUND_LOCATION"):
            bg = check_permission(Permission.ACCESS_BACKGROUND_LOCATION)
            redovi.append(f"Dozvola BACKGROUND_LOCATION: {'DA' if bg else 'NE'}")
    except Exception as e:
        redovi.append(f"Ne mogu da proverim dozvole: {e}")

    try:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context = autoclass("android.content.Context")
        activity = PythonActivity.mActivity
        if activity is None:
            PythonService = autoclass("org.kivy.android.PythonService")
            activity = PythonService.mService
        lm = activity.getSystemService(Context.LOCATION_SERVICE)
        gps_on = lm.isProviderEnabled("gps")
        mreza_on = lm.isProviderEnabled("network")
        redovi.append(f"GPS provajder ukljucen: {'DA' if gps_on else 'NE'}")
        redovi.append(f"Mrezni provajder ukljucen: {'DA' if mreza_on else 'NE'}")
    except Exception as e:
        redovi.append(f"Ne mogu da proverim GPS status: {e}")

    return "\n".join(redovi)


class AndroidLocationTracker:
    def __init__(self, na_lokaciju, na_dijagnozu=None, na_gresku=None, dispatcher=None):
        self._na_lokaciju = na_lokaciju
        self._na_dijagnozu = na_dijagnozu
        self._na_gresku = na_gresku
        self._dispatcher = dispatcher or (lambda cb: cb())
        self._android_lm = None
        self._android_listener = None
        self._zadnje_vreme_lok = None

    def _pozovi(self, fn, *args):
        if fn is None:
            return
        self._dispatcher(lambda: fn(*args))

    def _najbolja_poslednja_lokacija(self, lm, LocationManager):
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
        return najbolja

    def pokreni(self):
        if self._android_lm is not None and self._android_listener is not None:
            return True
        try:
            from jnius import autoclass, PythonJavaClass, java_method

            LocationManager = autoclass("android.location.LocationManager")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            Looper = autoclass("android.os.Looper")

            activity = PythonActivity.mActivity
            if activity is None:
                PythonService = autoclass("org.kivy.android.PythonService")
                activity = PythonService.mService
            lm = activity.getSystemService(Context.LOCATION_SERVICE)
            glavni_looper = Looper.getMainLooper()
            tracker = self

            class _Listener(PythonJavaClass):
                __javainterfaces__ = ["android/location/LocationListener"]
                __javacontext__ = "app"

                @java_method("(Landroid/location/Location;)V")
                def onLocationChanged(self, location):
                    tracker._zadnje_vreme_lok = location.getTime()
                    tracker._pozovi(
                        tracker._na_lokaciju,
                        {
                            "lat": location.getLatitude(),
                            "lon": location.getLongitude(),
                            "accuracy": location.getAccuracy(),
                        },
                    )

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

            if greske:
                self._pozovi(self._na_dijagnozu, "\n".join(greske))

            najbolja = self._najbolja_poslednja_lokacija(lm, LocationManager)
            if najbolja is not None:
                self._zadnje_vreme_lok = najbolja.getTime()
                self._pozovi(
                    self._na_dijagnozu,
                    "Pronadjena keširana lokacija - koristim je.",
                )
                self._pozovi(
                    self._na_lokaciju,
                    {
                        "lat": najbolja.getLatitude(),
                        "lon": najbolja.getLongitude(),
                        "accuracy": najbolja.getAccuracy(),
                    },
                )
            else:
                self._pozovi(
                    self._na_dijagnozu,
                    "Nema keširane lokacije, cekam zivi signal.",
                )

            return pokrenut_bar_jedan
        except Exception as e:
            self._pozovi(self._na_gresku, str(e))
            return False

    def pull_lokaciju(self):
        try:
            from jnius import autoclass

            LocationManager = autoclass("android.location.LocationManager")
            lm = self._android_lm
            if lm is None:
                return

            najbolja = self._najbolja_poslednja_lokacija(lm, LocationManager)
            if najbolja is None:
                return

            vreme = najbolja.getTime()
            if self._zadnje_vreme_lok is not None and vreme <= self._zadnje_vreme_lok:
                return

            self._zadnje_vreme_lok = vreme
            self._pozovi(
                self._na_lokaciju,
                {
                    "lat": najbolja.getLatitude(),
                    "lon": najbolja.getLongitude(),
                    "accuracy": najbolja.getAccuracy(),
                },
            )
        except Exception:
            pass

    def zaustavi(self):
        try:
            if self._android_lm is not None and self._android_listener is not None:
                self._android_lm.removeUpdates(self._android_listener)
        except Exception:
            pass
        self._android_lm = None
        self._android_listener = None


def android_foreground_servis_dostupan():
    try:
        from jnius import autoclass

        autoclass(ANDROID_SERVICE_CLASS)
        return True
    except Exception:
        return False


def pokreni_android_foreground_servis(argument="", user_data_dir=None):
    try:
        from jnius import autoclass

        ocisti_stop_fajl(user_data_dir)
        service = autoclass(ANDROID_SERVICE_CLASS)
        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        service.start(activity, argument or "")
        return True, ""
    except Exception as e:
        return False, str(e)


def zaustavi_android_foreground_servis(user_data_dir=None):
    try:
        from jnius import autoclass

        postavi_stop_fajl(user_data_dir)
        service = autoclass(ANDROID_SERVICE_CLASS)
        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        service.stop(activity)
        return True, ""
    except Exception as e:
        return False, str(e)
