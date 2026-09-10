"""
i18n.py
Minimalna dvojezicna podrska za SR/EN interfejs.
"""

import json
import os


SUPPORTED_LANGUAGES = ("sr", "en")

TRANSLATIONS = {
    "nav_home": {"sr": "Pocetna", "en": "Home"},
    "nav_settings": {"sr": "Podesavanja", "en": "Settings"},
    "home_gps_auto": {"sr": "GPS voznja (auto)", "en": "GPS ride (auto)"},
    "home_manual_ride": {"sr": "Pocetak voznje (rucno)", "en": "Manual ride entry"},
    "home_history": {"sr": "Istorija voznji", "en": "Ride history"},
    "home_report": {"sr": "Izvestaj", "en": "Report"},
    "home_profile": {"sr": "Profil vozaca", "en": "Driver profile"},
    "home_settings": {"sr": "Podesavanja", "en": "Settings"},
    "home_instructions": {"sr": "Uputstvo za upotrebu", "en": "Instructions"},
    "settings_title": {"sr": "Podesavanja", "en": "Settings"},
    "settings_chart": {"sr": "Grafik zarade", "en": "Earnings chart"},
    "settings_navigation": {"sr": "Navigacija", "en": "Navigation"},
    "settings_night_tariff": {"sr": "Nocna tarifa", "en": "Night tariff"},
    "settings_service": {"sr": "Servis vozila", "en": "Vehicle service"},
    "settings_fuel": {"sr": "Gorivo", "en": "Fuel"},
    "settings_other_costs": {"sr": "Ostali troskovi", "en": "Other costs"},
    "settings_weekly_report": {"sr": "Nedeljni izvestaj", "en": "Weekly report"},
    "settings_monthly_report": {"sr": "Mesecni izvestaj", "en": "Monthly report"},
    "settings_calculator": {"sr": "Kalkulator", "en": "Calculator"},
    "settings_profile": {"sr": "Profil vozaca", "en": "Driver profile"},
    "settings_dispatcher": {"sr": "Poziv / Dispecer", "en": "Call / Dispatcher"},
    "settings_prices": {"sr": "Cene / Tarife", "en": "Prices / Tariffs"},
    "settings_google_api": {"sr": "Google API", "en": "Google API"},
    "settings_currency": {"sr": "Valuta", "en": "Currency"},
    "settings_backup": {"sr": "Backup podataka", "en": "Data backup"},
    "settings_security": {"sr": "Sigurnost (otisak prsta)", "en": "Security (fingerprint)"},
    "settings_language": {"sr": "Jezik / Language", "en": "Language / Jezik"},
    "language_title": {"sr": "Jezik", "en": "Language"},
    "language_current": {"sr": "Trenutni jezik: {language}", "en": "Current language: {language}"},
    "language_serbian": {"sr": "Srpski", "en": "Serbian"},
    "language_english": {"sr": "Engleski", "en": "English"},
    "language_trial_info": {
        "sr": "Za probu su prevedeni pocetni ekran, podesavanja, kalkulator i GPS voznja.",
        "en": "For this trial, the home screen, settings, calculator, and GPS ride screens are translated.",
    },
    "calc_title": {"sr": "Kalkulator voznje", "en": "Ride calculator"},
    "calc_nav_history": {"sr": "Evidencija", "en": "History"},
    "calc_nav_report": {"sr": "Izvestaj", "en": "Report"},
    "calc_tariff": {"sr": "Tarifa", "en": "Tariff"},
    "calc_distance": {"sr": "Kilometraza (km)", "en": "Distance (km)"},
    "calc_distance_hint": {"sr": "npr. 8.5", "en": "e.g. 8.5"},
    "calc_from": {"sr": "Od (opciono)", "en": "From (optional)"},
    "calc_from_hint": {"sr": "adresa polazista", "en": "pickup address"},
    "calc_to": {"sr": "Do (opciono)", "en": "To (optional)"},
    "calc_to_hint": {"sr": "adresa odredista", "en": "destination address"},
    "calc_note": {"sr": "Napomena (opciono)", "en": "Note (optional)"},
    "calc_note_hint": {"sr": "npr. cekanje, prtljag...", "en": "e.g. waiting, luggage..."},
    "calc_enter_km": {"sr": "Unesi kilometrazu da vidis cenu", "en": "Enter distance to see the price"},
    "calc_price": {"sr": "Cena: {price}", "en": "Price: {price}"},
    "calc_formula": {"sr": "(start {start} + {km} km x {price})", "en": "(start {start} + {km} km x {price})"},
    "calc_save_ride": {"sr": "Sacuvaj voznju", "en": "Save ride"},
    "calc_save_edit": {"sr": "Sacuvaj izmenu", "en": "Save changes"},
    "calc_invalid_km": {"sr": "Unesi ispravnu kilometrazu pre cuvanja.", "en": "Enter a valid distance before saving."},
    "calc_km_positive": {"sr": "Kilometraza mora biti veca od 0.", "en": "Distance must be greater than 0."},
    "calc_edit_saved": {"sr": "Izmena sacuvana! Cena voznje: {price}", "en": "Changes saved! Ride price: {price}"},
    "calc_saved": {"sr": "Sacuvano! Cena voznje: {price}", "en": "Saved! Ride price: {price}"},
    "gps_title": {"sr": "GPS voznja", "en": "GPS ride"},
    "gps_nav_history": {"sr": "Istorija", "en": "History"},
    "gps_start_card": {"sr": "POLAZAK", "en": "START"},
    "gps_destination": {
        "sr": "Krajnja adresa (opciono - unesi je PRE 'Pocni voznju' da odmah krene Google navigacija)",
        "en": "Destination address (optional - enter it BEFORE 'Start ride' to launch Google navigation immediately)",
    },
    "gps_destination_hint": {"sr": "npr. Nemanjina 4, Beograd", "en": "e.g. Nemanjina 4, Belgrade"},
    "gps_destination_info": {
        "sr": "Ostavi prazno da sve radi kao do sad - GPS sam nalazi i polaznu i krajnju adresu.",
        "en": "Leave this empty to keep the current behavior - GPS will detect both the start and destination address.",
    },
    "gps_start_button": {"sr": "POCNI VOZNJU", "en": "START RIDE"},
    "gps_finish_button": {"sr": "ZAVRSI VOZNJU", "en": "FINISH RIDE"},
    "gps_not_started": {"sr": "Nije zapoceta", "en": "Not started"},
    "gps_distance": {"sr": "Predjeno: {km:.2f} km", "en": "Distance: {km:.2f} km"},
    "gps_duration": {"sr": "Trajanje: {duration}", "en": "Duration: {duration}"},
    "gps_price": {"sr": "Cena: {price}", "en": "Price: {price}"},
    "gps_address_unavailable": {"sr": "Adresa nije dostupna", "en": "Address unavailable"},
    "gps_searching_location": {"sr": "Trazim lokaciju...", "en": "Searching for location..."},
    "gps_request_permission": {"sr": "Trazim dozvolu za lokaciju...", "en": "Requesting location permission..."},
    "gps_permission_denied": {
        "sr": "Dozvola za lokaciju NIJE odobrena. Idi u Podesavanja telefona -> Aplikacije -> Taksi App -> Dozvole -> Lokacija -> Dozvoli.",
        "en": "Location permission was NOT granted. Go to Phone Settings -> Apps -> Taksi App -> Permissions -> Location -> Allow.",
    },
    "gps_start_error": {"sr": "Greska pri pokretanju GPS-a.", "en": "Error while starting GPS."},
    "gps_searching_signal": {"sr": "Trazim GPS signal...", "en": "Searching for GPS signal..."},
    "gps_active": {"sr": "GPS aktivan, pratim voznju.", "en": "GPS is active, tracking the ride."},
    "gps_weak_signal": {"sr": "Slab GPS signal (+/-{accuracy:.0f}m), cekam bolji...", "en": "Weak GPS signal (+/-{accuracy:.0f}m), waiting for a better fix..."},
    "gps_no_signal_yet": {
        "sr": "Jos uvek nema GPS signala. Voznja je pokrenuta i ceka prvi signal - km i cena ce poceti da se racunaju cim GPS uhvati poziciju.",
        "en": "There is still no GPS signal. The ride has started and is waiting for the first fix - distance and price will start updating as soon as GPS gets a position.",
    },
    "gps_still_searching_signal": {"sr": "Jos uvek trazim signal... ({seconds}s)", "en": "Still searching for signal... ({seconds}s)"},
    "gps_navigation_error_title": {"sr": "Greska", "en": "Error"},
    "gps_navigation_error": {
        "sr": "Ne mogu da otvorim navigaciju, ali GPS voznja je pokrenuta normalno.",
        "en": "I can't open navigation, but the GPS ride started normally.",
    },
    "gps_lookup_destination": {"sr": "Trazim krajnju adresu...", "en": "Looking up destination address..."},
    "gps_auto_note": {"sr": "GPS voznja (automatski unos)", "en": "GPS ride (automatic entry)"},
    "gps_finished_title": {"sr": "Voznja zavrsena", "en": "Ride finished"},
    "gps_finished_body": {
        "sr": "Voznja sacuvana!\n{start}\n-> {end}\n{km:.2f} km, {price}",
        "en": "Ride saved!\n{start}\n-> {end}\n{km:.2f} km, {price}",
    },
}

TARIFF_TRANSLATIONS = {
    "Osnovna (07-22h)": {"sr": "Osnovna (07-22h)", "en": "Base (07-22h)"},
    "Nocna (22-07h)": {"sr": "Nocna (22-07h)", "en": "Night (22-07h)"},
    "Vikend": {"sr": "Vikend", "en": "Weekend"},
    "Aerodromski transfer": {"sr": "Aerodromski transfer", "en": "Airport transfer"},
}

LANGUAGE_NAMES = {
    "sr": {"sr": "Srpski", "en": "Serbian"},
    "en": {"sr": "Engleski", "en": "English"},
}


class JezikPodesavanja:
    def __init__(self):
        self.jezik = "sr"

    def _putanja(self, user_data_dir):
        return os.path.join(user_data_dir, "jezik.json")

    def ucitaj(self, user_data_dir):
        try:
            with open(self._putanja(user_data_dir), "r", encoding="utf-8") as f:
                podaci = json.load(f)
            jezik = podaci.get("jezik", "sr")
            self.jezik = jezik if jezik in SUPPORTED_LANGUAGES else "sr"
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            self.jezik = "sr"

    def sacuvaj(self, user_data_dir):
        with open(self._putanja(user_data_dir), "w", encoding="utf-8") as f:
            json.dump({"jezik": self.jezik}, f, ensure_ascii=False, indent=2)


def prevedi(jezik, kljuc, **kwargs):
    prevodi = TRANSLATIONS.get(kljuc)
    if not prevodi:
        tekst = kljuc
    else:
        tekst = prevodi.get(jezik) or prevodi.get("sr") or kljuc
    return tekst.format(**kwargs) if kwargs else tekst


def prevedi_tarifu(tarifa, jezik):
    prevodi = TARIFF_TRANSLATIONS.get(tarifa)
    if not prevodi:
        return tarifa
    return prevodi.get(jezik) or prevodi.get("sr") or tarifa


def naziv_jezika(jezik, prikaz_jezik=None):
    prikaz_jezik = prikaz_jezik or jezik
    nazivi = LANGUAGE_NAMES.get(jezik)
    if not nazivi:
        return jezik
    return nazivi.get(prikaz_jezik) or nazivi.get("sr") or jezik
