"""
ekran_uputstvo.py
Ekran "Uputstvo za upotrebu" - prikazuje sve opcije aplikacije
objasnjene jednu po jednu (SekcijaUputstva kartice), plus izvoz istog
sadrzaja u PDF.

Izdvojeno iz main.py - isti obrazac kao grafik_zarade.py.
"""

import os

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty

from servisi import jezici


# ============================================================
# main.py ovo postavlja posle uvoza (izbegava kruzni import)
# ============================================================

_REGISTRUJ_FONT_ZA_PDF = None     # main._registruj_font_za_pdf
_IMA_DOZVOLU_SVI_FAJLOVI = None   # main._ima_dozvolu_svi_fajlovi
_PUTANJA_BACKUP_FOLDERA = None    # main._putanja_backup_foldera
_PRIKAZI_POPUP = None             # main._prikazi_popup_poruku


def poveži(registruj_font_fn, ima_dozvolu_fn, putanja_backup_fn, prikazi_popup_fn):
    """main.py poziva ovo jednom, odmah posle 'import ekran_uputstvo'."""
    global _REGISTRUJ_FONT_ZA_PDF, _IMA_DOZVOLU_SVI_FAJLOVI, _PUTANJA_BACKUP_FOLDERA, _PRIKAZI_POPUP
    _REGISTRUJ_FONT_ZA_PDF = registruj_font_fn
    _IMA_DOZVOLU_SVI_FAJLOVI = ima_dozvolu_fn
    _PUTANJA_BACKUP_FOLDERA = putanja_backup_fn
    _PRIKAZI_POPUP = prikazi_popup_fn


# ============================================================
# UPUTSTVO ZA UPOTREBU - sadrzaj koji se prikazuje i u samoj app-i
# (ekran UputstvoScreen) i u PDF izvozu (generisi_uputstvo_pdf) - ISTI
# podaci, dva razlicita prikaza, da ne moramo da odrzavamo tekst na
# dva mesta.
#
# Svaka stavka je (naslov_sekcije, [lista pasusa/tacaka teksta]).
# ============================================================

SR_SADRZAJ = [
    ("Prvo pokretanje i zakljucavanje otiskom prsta", [
        "Kad prvi put otvoris app, pojavice se Pocetni ekran direktno - "
        "zakljucavanje otiskom je iskljuceno po difoltu.",
        "Ako u Podesavanjima ukljucis Sigurnost (otisak prsta), sledeci "
        "put kad pokrenes app prvo ces videti ekran sa zahtevom da "
        "prislonis prst na senzor. Bez uspesnog otiska ne mozes dalje.",
        "Ako telefon nema citac otiska, ili nijedan otisak nije "
        "registrovan u sistemskim podesavanjima telefona, app te "
        "automatski propusta dalje i samo te obavestava zasto - nema "
        "opasnosti da se trajno zakljucas van app-a.",
        "Zakljucavanje se proverava samo pri pokretanju app-a (hladnom "
        "startu), ne pri svakom povratku iz pozadine - tako da te ne "
        "prekida usred aktivne voznje (npr. ako primis poziv).",
        "Ukljucuje se / iskljucuje u Podesavanja -> Sigurnost (otisak "
        "prsta).",
    ]),
    ("Pocetni ekran", [
        "GPS voznja (auto) - otvara automatsko pracenje voznje preko "
        "GPS-a.",
        "Pocetak voznje (rucno) - otvara Kalkulator za rucni unos "
        "voznje.",
        "Istorija voznji - otvara Evidenciju, spisak svih voznji sa "
        "pretragom.",
        "Izvestaj - dnevni/nedeljni/mesecni pregled zarade.",
        "Profil vozaca - licni podaci i podaci o vozilu.",
        "Podesavanja - svi ostali meniji aplikacije.",
        "Uputstvo za upotrebu - ekran koji sad citas.",
    ]),
    ("GPS voznja (automatski unos) - najcesca opcija", [
        "1. Opciono, pre klika na 'Pocni voznju' mozes uneti krajnju "
        "adresu - ako je unesеs, cim krene voznja odmah se otvara "
        "Google navigacija korak-po-korak ka toj adresi.",
        "2. Klik na POCNI VOZNJU. App trazi dozvolu za lokaciju ako je "
        "prvi put, pa pocinje da meri kilometrazu uzivo.",
        "3. Ekran u toku voznje prikazuje adresu polaska, predjene "
        "kilometre, trajanje i trenutnu cenu.",
        "4. Kad stignes, klik na ZAVRSI VOZNJU - app sam pronalazi "
        "trenutnu adresu i cuva voznju u Evidenciju.",
        "GPS voznja koristi samo Osnovnu ili Nocnu tarifu, zavisno od "
        "prekidaca u Podesavanja -> Nocna tarifa (nije automatski po "
        "satu). Za Vikend ili Aerodromski transfer koristi rucni unos "
        "(Kalkulator).",
        "App filtrira losu GPS preciznost - ignorise tacke losije od "
        "50m preciznosti, mikro-skokove ispod 10m i nerealne skokove "
        "brzine preko 180 km/h, da kilometraza ne bi bila lazno "
        "naduvana.",
        "Ako GPS ne uspe da izmeri kilometrazu, na ekranu za zavrsetak "
        "voznje postoji polje za rucni unos km kao rezerva.",
    ]),
    ("Kalkulator (rucni unos voznje)", [
        "Za voznje koje ne pratis uzivo preko GPS-a, ili kad ti treba "
        "tarifa koju GPS voznja ne podrzava (Vikend, Aerodromski "
        "transfer).",
        "1. Izaberi tarifu iz padajuceg menija.",
        "2. Unesi kilometrazu - cena se odmah preracunava ispod.",
        "3. Adresa polaska, adresa dolaska i napomena su opcioni.",
        "4. Klik na Sacuvaj voznju.",
        "Ako je ukljucena Nocna tarifa, ekran automatski predlaze "
        "Nocnu tarifu pri otvaranju - i dalje mozes rucno da je "
        "promenis za tu konkretnu voznju.",
    ]),
    ("Evidencija (istorija voznji)", [
        "Prikazuje sve sacuvane voznje, najnovije prve - datum, vreme "
        "pocetka/kraja, kilometraza, tarifa, adrese i cena.",
        "Pretraga se moze kombinovati: tekst (adrese i napomena), "
        "period (datum od / datum do, format GGGG-MM-DD) i opseg cene "
        "(cena od / cena do). Klik na Pretrazi ispisuje i zbir za "
        "rezultate. Resetuj vraca pun spisak.",
        "Svaka voznja ima dva dugmeta: Izmeni (otvara Kalkulator "
        "popunjen tim podacima) i Obrisi (trajno brise voznju, bez "
        "potvrde - pazi).",
    ]),
    ("Izvestaj zarade", [
        "Tri kartice sa zbirovima: Danas (spisak voznji danas + "
        "ukupno), Ova nedelja (zbirna zarada za tekucu nedelju), Ovaj "
        "mesec (zbirna zarada za tekuci mesec).",
        "Odavde ide dugme Izvoz PDF ka ekranu za izvoz izvestaja.",
    ]),
    ("Grafikon zarade", [
        "Vizuelni prikaz kroz vreme. Period: Dnevni / Nedeljni / "
        "Mesecni. Prikaz: Zarada ili Kilometri.",
        "Strelice < i > pomeraju kroz prethodne/naredne periode. Klik "
        "na tacku u grafikonu prikazuje tacan iznos za taj dan/"
        "nedelju/mesec.",
        "Ispod grafikona: dodatne statistike i, kad ima podataka, "
        "pregled potrosnje goriva i servisa za taj period.",
        "Pristupa se preko Podesavanja -> Grafik zarade.",
    ]),
    ("Izvoz izvestaja (PDF / CSV za Excel)", [
        "Ekran Izvestaj -> Izvoz PDF. Izaberi vrstu perioda (Dnevno, "
        "Nedeljno, Mesecno, Polugodisnje, Godisnje) i unesi period u "
        "trazenom formatu.",
        "Izvezi PDF - pravi PDF za stampu/pregled sa podacima o "
        "vozacu, servisima, ostalim troskovima, potrosnjom goriva, "
        "svim voznjama i zbirnim redom na kraju (broj voznji, ukupno "
        "km, bruto zarada i NETO = zarada - gorivo - servisi - ostali "
        "troskovi).",
        "Izvezi CSV (Excel) - pravi jedan CSV fajl gde su voznje, "
        "gorivo, servisi i troskovi pomesani u JEDNU tabelu (Datum, "
        "Tip, Opis, Prihod, Rashod, Napomena), sortirano po datumu - "
        "lakse za knjigovodju da otvori u Excel-u i sam sabira/"
        "filtrira.",
        "Oba fajla se cuvaju u Preuzimanja/TaksiApp na telefonu (isti "
        "folder kao backup) - potrebna je dozvola 'pristup svim "
        "fajlovima' (Podesavanja -> Backup podataka).",
    ]),
    ("Cene / Tarife", [
        "Menjaju se cene po kilometru za sve cetiri tarife (Osnovna, "
        "Nocna, Vikend, Aerodromski transfer) plus start taksa.",
        "Klik na Sacuvaj cene primenjuje ih na SVE naredne voznje - ne "
        "menja retroaktivno vec sacuvane voznje.",
    ]),
    ("Nocna tarifa (prekidac)", [
        "Jedan prekidac: kad je ukljucen, i Kalkulator i GPS voznja "
        "automatski koriste Nocnu tarifu (i dalje mozes rucno "
        "promeniti tarifu za pojedinacnu voznju u Kalkulatoru).",
        "Ne ukljucuje se sam po satu - ti ga ukljucujes i iskljucujes "
        "rucno kad pocinje/prestaje tvoja nocna smena.",
    ]),
    ("Gorivo", [
        "Evidencija sipanja goriva: vrsta (Benzin/TNG), kolicina "
        "(litara), cena, kilometraza na pumpi (opciono ali VAZNO - "
        "bez nje se ne moze izracunati potrosnja niti radi podsetnik "
        "za servis), napomena.",
        "Na vrhu ekrana vidi se ukupno potroseno na gorivo (posebno "
        "benzin, posebno TNG). Potrosnja u l/100km se automatski "
        "racuna iz razlike kilometraze izmedju dva uzastopna sipanja "
        "koja imaju upisanu kilometrazu.",
    ]),
    ("Servis vozila", [
        "Evidencija servisa (zamena ulja, kocnice, itd.) - vrsta, "
        "cena, kilometraza, napomena.",
        "Podsetnik za servis: postavis interval (npr. na svakih 10000 "
        "km), a app sam prati koliko je predjeno od poslednjeg "
        "servisa - poredeci kilometrazu poslednjeg servisa sa "
        "najnovijom kilometrazom upisanom kod Goriva (ne sa ukupnim "
        "km iz voznji). Kartica menja boju: zeleno (sve OK), zuto "
        "(ostalo manje od 20% intervala), crveno (vreme je za "
        "servis).",
        "Ako nema jos dovoljno podataka (bar jedan servis SA "
        "kilometrazom i bar jedno gorivo SA kilometrazom sa pumpe), "
        "kartica samo kaze da nema dovoljno podataka.",
    ]),
    ("Ostali troskovi", [
        "Za sve sto ne spada u gorivo/servis: Parking, Putarina, "
        "Pranje, Ostalo - cena i napomena. Ovi troskovi ulaze u NETO "
        "izracun u PDF izvestaju.",
    ]),
    ("Profil vozaca", [
        "Licni podaci (ime, telefon, licenca, tablice, vozilo) koji "
        "se prikazuju u zaglavlju PDF izvestaja, plus datum isteka "
        "registracije i datum isteka osiguranja.",
        "Kartica na dnu prati oba datuma: sivo (nije unet), zeleno "
        "(vise od 30 dana do isteka), zuto (30 dana ili manje), "
        "crveno (vec isteklo - pise koliko dana kasni).",
    ]),
    ("Navigacija", [
        "Nezavisan ekran za brzo otvaranje Google navigacije ka bilo "
        "kojoj adresi - unesi adresu i klikni 'Otvori navigaciju'. "
        "Automatski krece korak-po-korak od tvoje trenutne GPS "
        "pozicije.",
    ]),
    ("Google API", [
        "Opciono polje za Google Geocoding API kljuc. Ako ga ne "
        "unesеs, app i dalje radi normalno - koristi besplatan "
        "OpenStreetMap servis za pronalazenje adresa. Google-ov "
        "servis je samo precizniji u pojedinim slucajevima. Kljuc se "
        "pravi na console.cloud.google.com (Geocoding API).",
    ]),
    ("Valuta", [
        "Bira se samo kako se cene PRIKAZUJU u app-i - u pozadini se "
        "sve uvek racuna i cuva u RSD (dinarima), bez obzira na ovaj "
        "izbor. Dugmad: Prikazuj u RSD ili Prikazuj u EUR.",
        "Kurs se automatski osvezava jednom dnevno (prvi put kad tog "
        "dana otvoris app). Dugme Osvezi kurs sada za rucno "
        "osvezavanje ako npr. juce nije bilo interneta.",
    ]),
    ("Backup podataka", [
        "Cuva SVE podatke (voznje, gorivo, servisi, troskovi, profil "
        "vozaca) u jedan fajl van same aplikacije, u Preuzimanja/"
        "TaksiApp - ostaje na telefonu i posle brisanja/reinstalacije "
        "app-a.",
        "Odobri pristup fajlovima - daje app-u Android dozvolu da "
        "pise u taj javni folder (trazi se jednom).",
        "App sam pravi svez backup jednom dnevno pri pokretanju, "
        "tiho, bez poruke. Sacuvaj backup sada je za rucni backup kad "
        "god pozelis.",
        "Vrati podatke iz backupa - ucitava sve podatke iz backup "
        "fajla (koristi se pri promeni telefona ili posle "
        "reinstalacije).",
        "Podeli backup (Drive, WhatsApp...) - otvara sistemski meni "
        "za deljenje da posaljes backup fajl sebi na mejl, Google "
        "Drive, WhatsApp itd.",
        "Pri promeni telefona: napravi backup na starom -> prebaci "
        "fajl (WhatsApp/Drive/USB) u isti folder na novom -> "
        "instaliraj app -> klikni 'Vrati podatke'.",
    ]),
    ("Sigurnost (otisak prsta)", [
        "Ukljucuje/iskljucuje zakljucavanje app-a otiskom prsta pri "
        "pokretanju - detaljno objasnjeno na pocetku ovog uputstva. "
        "Ekran ti kaze i da li tvoj telefon uopste ima registrovan "
        "otisak.",
    ]),
    ("Poziv / Dispecer", [
        "Ova stavka u meniju trenutno prikazuje samo 'Uskoro...' - "
        "funkcionalnost jos nije implementirana.",
    ]),
    ("Najcesci problemi", [
        "GPS ne pokazuje kilometrazu -> proveri dozvolu za lokaciju "
        "(Podesavanja telefona -> Aplikacije -> Taksi App -> Dozvole "
        "-> Lokacija -> Dozvoli) i da li je GPS ukljucen na telefonu.",
        "Ne mogu da izvezem PDF/CSV -> Podesavanja -> Backup podataka "
        "-> 'Odobri pristup fajlovima'.",
        "Ne radi otisak prsta -> proveri da li telefon uopste ima "
        "citac otiska i da li je otisak registrovan u sistemskim "
        "podesavanjima telefona - bez toga app te automatski "
        "propusta dalje.",
        "Podsetnik za servis kaze 'nema dovoljno podataka' -> potreban "
        "je bar jedan servis SA upisanom kilometrazom i bar jedno "
        "gorivo SA upisanom kilometrazom sa pumpe.",
        "Cene se ne poklapaju sa novim tarifama -> nove cene vaze "
        "samo za voznje UNETE POSLE izmene, ne menjaju retroaktivno "
        "vec sacuvane voznje.",
    ]),
]

EN_SADRZAJ = [
    ("First launch and fingerprint lock", [
        "The first time you open the app, the Home screen appears "
        "directly - fingerprint lock is off by default.",
        "If you turn on Security (fingerprint) in Settings, the next "
        "time you launch the app you'll first see a screen asking "
        "you to place your finger on the sensor. You can't continue "
        "without a successful fingerprint.",
        "If the phone has no fingerprint reader, or no fingerprint is "
        "registered in the phone's system settings, the app "
        "automatically lets you through and just tells you why - "
        "there's no risk of being permanently locked out of the app.",
        "The lock is only checked when the app starts (a cold start), "
        "not every time you return from the background - so it "
        "won't interrupt you mid-ride (e.g. if you get a call).",
        "Turned on/off in Settings -> Security (fingerprint).",
    ]),
    ("Home screen", [
        "GPS ride (auto) - opens automatic ride tracking via GPS.",
        "Start ride (manual) - opens the Calculator for manual ride "
        "entry.",
        "Ride history - opens Ride history, a searchable list of all "
        "rides.",
        "Report - daily/weekly/monthly earnings overview.",
        "Driver profile - personal and vehicle details.",
        "Settings - all other menus of the app.",
        "Instructions - the screen you're reading now.",
    ]),
    ("GPS ride (automatic entry) - the most common option", [
        "1. Optionally, before tapping 'Start ride' you can enter a "
        "destination address - if you do, as soon as the ride "
        "starts Google navigation opens turn-by-turn to that "
        "address.",
        "2. Tap START RIDE. The app asks for location permission the "
        "first time, then starts measuring distance live.",
        "3. The screen during the ride shows the pickup address, "
        "distance driven, duration and the current price.",
        "4. When you arrive, tap END RIDE - the app finds the "
        "current address itself and saves the ride to Ride history.",
        "GPS ride only uses the Standard or Night tariff, depending "
        "on the switch in Settings -> Night tariff (it does not "
        "switch automatically by the clock). For Weekend or Airport "
        "transfer, use manual entry (Calculator).",
        "The app filters out poor GPS accuracy - it ignores points "
        "worse than 50m accuracy, micro-jumps under 10m, and "
        "unrealistic speed jumps over 180 km/h, so the distance "
        "isn't falsely inflated.",
        "If GPS fails to measure the distance, the ride-end screen "
        "has a manual km entry field as a backup.",
    ]),
    ("Calculator (manual ride entry)", [
        "For rides you don't track live via GPS, or when you need a "
        "tariff GPS ride doesn't support (Weekend, Airport "
        "transfer).",
        "1. Choose a tariff from the dropdown.",
        "2. Enter the distance - the price updates instantly below.",
        "3. Pickup address, destination address and note are "
        "optional.",
        "4. Tap Save ride.",
        "If Night tariff is turned on, the screen automatically "
        "suggests the Night tariff when opened - you can still "
        "manually change it for that specific ride.",
    ]),
    ("Ride history", [
        "Shows all saved rides, newest first - date, start/end time, "
        "distance, tariff, addresses and price.",
        "Search can be combined: text (addresses and note), period "
        "(date from / date to, YYYY-MM-DD format) and price range "
        "(price from / price to). Tapping Search also shows a total "
        "for the results. Reset restores the full list.",
        "Each ride has two buttons: Edit (opens the Calculator "
        "filled in with that data) and Delete (permanently deletes "
        "the ride, no confirmation - be careful).",
    ]),
    ("Earnings report", [
        "Three cards with totals: Today (list of today's rides + "
        "total), This week (total earnings for the current week), "
        "This month (total earnings for the current month).",
        "From here, the Export PDF button leads to the report export "
        "screen.",
    ]),
    ("Earnings chart", [
        "A visual view over time. Period: Daily / Weekly / Monthly. "
        "View: Earnings or Kilometers.",
        "The < and > arrows move through previous/next periods. "
        "Tapping a point on the chart shows the exact amount for "
        "that day/week/month.",
        "Below the chart: extra stats and, when data is available, "
        "an overview of fuel and service spending for that period.",
        "Accessed via Settings -> Earnings chart.",
    ]),
    ("Report export (PDF / CSV for Excel)", [
        "Report screen -> Export PDF. Choose the period type (Daily, "
        "Weekly, Monthly, Half-year, Yearly) and enter the period in "
        "the requested format.",
        "Export PDF - creates a PDF for printing/review with driver "
        "details, service, other expenses, fuel consumption, all "
        "rides and a summary row at the end (number of rides, total "
        "km, gross earnings and NET = earnings - fuel - service - "
        "other expenses).",
        "Export CSV (Excel) - creates a single CSV file where rides, "
        "fuel, service and expenses are combined into ONE table "
        "(Date, Type, Description, Income, Expense, Note), sorted by "
        "date - easier for an accountant to open in Excel and total/"
        "filter themselves.",
        "Both files are saved to Downloads/TaksiApp on the phone "
        "(same folder as the backup) - the 'access all files' "
        "permission is required (Settings -> Data backup).",
    ]),
    ("Prices / Tariffs", [
        "Changes the price per kilometer for all four tariffs "
        "(Standard, Night, Weekend, Airport transfer) plus the start "
        "fee.",
        "Tapping Save prices applies them to ALL future rides - it "
        "does not retroactively change rides already saved.",
    ]),
    ("Night tariff (switch)", [
        "A single switch: when on, both the Calculator and GPS ride "
        "automatically use the Night tariff (you can still manually "
        "change the tariff for an individual ride in the "
        "Calculator).",
        "It does not turn on by the clock automatically - you turn "
        "it on and off manually when your night shift starts/ends.",
    ]),
    ("Fuel", [
        "Fuel entry log: type (Gasoline/LPG), quantity (liters), "
        "price, mileage at the pump (optional but IMPORTANT - "
        "without it, consumption can't be calculated and the service "
        "reminder won't work), note.",
        "At the top of the screen you see total fuel spending "
        "(gasoline and LPG separately). Consumption in l/100km is "
        "calculated automatically from the mileage difference "
        "between two consecutive fill-ups that have mileage entered.",
    ]),
    ("Vehicle service", [
        "Service log (oil change, brakes, etc.) - type, price, "
        "mileage, note.",
        "Service reminder: you set an interval (e.g. every 10000 "
        "km), and the app tracks how far you've driven since the "
        "last service by itself - comparing the last service's "
        "mileage with the most recent mileage entered under Fuel "
        "(not the total km from rides). The card changes color: "
        "green (all OK), yellow (less than 20% of the interval "
        "left), red (time for service).",
        "If there isn't enough data yet (at least one service WITH "
        "mileage and at least one fuel entry WITH pump mileage), the "
        "card just says there isn't enough data.",
    ]),
    ("Other expenses", [
        "For anything that isn't fuel/service: Parking, Tolls, "
        "Washing, Other - price and note. These expenses are "
        "included in the NET calculation in the PDF report.",
    ]),
    ("Driver profile", [
        "Personal details (name, phone, license, plates, vehicle) "
        "shown in the header of the PDF report, plus registration "
        "expiry date and insurance expiry date.",
        "The card at the bottom tracks both dates: gray (not "
        "entered), green (more than 30 days to expiry), yellow (30 "
        "days or less), red (already expired - shows how many days "
        "overdue).",
    ]),
    ("Navigation", [
        "A standalone screen for quickly opening Google navigation "
        "to any address - enter the address and tap 'Open "
        "navigation'. It automatically starts turn-by-turn from your "
        "current GPS position.",
    ]),
    ("Google API", [
        "An optional field for a Google Geocoding API key. If you "
        "don't enter one, the app still works normally - it uses the "
        "free OpenStreetMap service to find addresses. Google's "
        "service is only more accurate in some cases. The key is "
        "created at console.cloud.google.com (Geocoding API).",
    ]),
    ("Currency", [
        "This only chooses how prices are DISPLAYED in the app - in "
        "the background, everything is always calculated and stored "
        "in RSD (dinars), regardless of this choice. Buttons: "
        "Display in RSD or Display in EUR.",
        "The exchange rate refreshes automatically once a day (the "
        "first time you open the app that day). The Refresh rate now "
        "button is for manually refreshing it, e.g. if there was no "
        "internet yesterday.",
    ]),
    ("Data backup", [
        "Saves ALL data (rides, fuel, service, expenses, driver "
        "profile) into a single file outside the app itself, in "
        "Downloads/TaksiApp - it stays on the phone even after the "
        "app is deleted/reinstalled.",
        "Grant file access - gives the app Android permission to "
        "write to that public folder (asked once).",
        "The app makes a fresh backup by itself once a day on "
        "startup, silently, with no message. Save backup now is for "
        "a manual backup whenever you want.",
        "Restore data from backup - loads all data from the backup "
        "file (used when switching phones or after reinstalling).",
        "Share backup (Drive, WhatsApp...) - opens the system share "
        "menu to send the backup file to yourself by email, Google "
        "Drive, WhatsApp, etc.",
        "When switching phones: make a backup on the old one -> "
        "transfer the file (WhatsApp/Drive/USB) into the same folder "
        "on the new one -> install the app -> tap 'Restore data'.",
    ]),
    ("Security (fingerprint)", [
        "Turns the app's fingerprint lock on startup on/off - "
        "explained in detail at the start of these instructions. "
        "The screen also tells you whether your phone has a "
        "registered fingerprint at all.",
    ]),
    ("Call / Dispatcher", [
        "Keep a list of dispatchers with their shift times, call "
        "them with one tap, and see at a glance whose shift is "
        "active right now.",
    ]),
    ("Common problems", [
        "GPS doesn't show distance -> check the location permission "
        "(Phone Settings -> Apps -> Downtown Taxi -> Permissions -> "
        "Location -> Allow) and whether GPS is turned on on the "
        "phone.",
        "Can't export PDF/CSV -> Settings -> Data backup -> 'Grant "
        "file access'.",
        "Fingerprint doesn't work -> check whether the phone even has "
        "a fingerprint reader and whether a fingerprint is "
        "registered in the phone's system settings - without that, "
        "the app automatically lets you through.",
        "The service reminder says 'not enough data' -> at least one "
        "service WITH mileage entered and at least one fuel entry "
        "WITH pump mileage entered are needed.",
        "Prices don't match the new tariffs -> new prices only apply "
        "to rides ENTERED AFTER the change, they don't retroactively "
        "change rides already saved.",
    ]),
]


def _sadrzaj():
    """Vraca sadrzaj uputstva na trenutno izabranom jeziku."""
    return EN_SADRZAJ if jezici.get_current_language() == "en" else SR_SADRZAJ


def generisi_uputstvo_pdf(putanja_fajla):
    """Pravi PDF verziju uputstva za upotrebu, sa jasno odvojenim
    naslovom za svaku sekciju/opciju - isti tekst kao na ekranu
    Uputstvo u samoj app-i (vidi UPUTSTVO_SADRZAJ)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle

    _REGISTRUJ_FONT_ZA_PDF()

    doc = SimpleDocTemplate(
        putanja_fajla,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Uputstvo za upotrebu - Taxi Zoran",
    )

    stil_naslov = ParagraphStyle(
        "naslov", fontName="DejaVuSans-Bold", fontSize=19, leading=24,
        textColor=colors.HexColor("#3a3560"),
    )
    stil_podnaslov = ParagraphStyle(
        "podnaslov", fontName="DejaVuSans", fontSize=10, leading=14,
        textColor=colors.HexColor("#666666"),
    )
    stil_sekcija = ParagraphStyle(
        "sekcija", fontName="DejaVuSans-Bold", fontSize=13, leading=17,
        textColor=colors.white, backColor=colors.HexColor("#3a3560"),
        borderPadding=(6, 6, 6, 6), spaceBefore=4,
    )
    stil_tekst = ParagraphStyle(
        "tekst", fontName="DejaVuSans", fontSize=9.5, leading=14,
        leftIndent=4,
    )

    elementi = [
        Paragraph("Uputstvo za upotrebu", stil_naslov),
        Paragraph("Taxi Zoran - aplikacija za evidenciju voznji i troskova", stil_podnaslov),
        Spacer(1, 8 * mm),
    ]

    for naslov_sekcije, pasusi in _sadrzaj():
        elementi.append(Paragraph(naslov_sekcije, stil_sekcija))
        elementi.append(Spacer(1, 2 * mm))
        for pasus in pasusi:
            elementi.append(Paragraph(pasus, stil_tekst))
            elementi.append(Spacer(1, 1.5 * mm))
        elementi.append(Spacer(1, 5 * mm))

    doc.build(elementi)


class SekcijaUputstva(BoxLayout):
    """Jedna kartica (naslov + tekst) na ekranu Uputstvo - vidi
    <SekcijaUputstva>: pravilo u KV-u."""
    naslov = StringProperty("")
    tekst = StringProperty("")


class UputstvoScreen(Screen):
    tekst_status = StringProperty("")
    tekst_naslov = StringProperty("Uputstvo za upotrebu")
    tekst_pocetna = StringProperty("Pocetna")
    tekst_izvezi_pdf_dugme = StringProperty("Izvezi u PDF")

    _poslednji_jezik = None

    def on_pre_enter(self, *args):
        from kivy.factory import Factory
        self.tekst_naslov = jezici._t("uputstvo.naslov")
        self.tekst_pocetna = jezici._t("buttons.pocetna")
        self.tekst_izvezi_pdf_dugme = jezici._t("uputstvo.izvezi_pdf_dugme")
        self.tekst_status = jezici._t("uputstvo.tekst_status")

        kontejner = self.ids.lista_uputstvo
        trenutni_jezik = jezici.get_current_language()
        # Ponovo napravi kartice ako jos nisu napravljene ILI ako se
        # jezik promenio od poslednjeg ulaska na ovaj ekran (inace bi
        # sadrzaj ostao na starom jeziku posle promene).
        if not kontejner.children or self._poslednji_jezik != trenutni_jezik:
            kontejner.clear_widgets()
            for naslov_sekcije, pasusi in _sadrzaj():
                sekcija = Factory.SekcijaUputstva(
                    naslov=naslov_sekcije,
                    tekst="\n\n".join(pasusi),
                )
                kontejner.add_widget(sekcija)
            self._poslednji_jezik = trenutni_jezik

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
            putanja = os.path.join(folder, "uputstvo_za_upotrebu.pdf")
            generisi_uputstvo_pdf(putanja)
            _PRIKAZI_POPUP(
                jezici._t("backup.sacuvano_naslov"),
                jezici._t("uputstvo.sacuvano_poruka", putanja=putanja),
                size_hint=(0.85, 0.4),
            )
        except Exception as e:
            _PRIKAZI_POPUP(
                jezici._t("profil.greska"), jezici._t("izvoz.pdf_neuspeo", greska=e), size_hint=(0.88, 0.45)
            )



UPUTSTVO_KV = """
# ============================================================
# UPUTSTVO ZA UPOTREBU
# ============================================================

<SekcijaUputstva>:
    orientation: "vertical"
    size_hint_y: None
    height: self.minimum_height
    padding: dp(14)
    spacing: dp(6)
    canvas.before:
        Color:
            rgba: 0.30, 0.29, 0.42, 0.92
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]
    Label:
        text: root.naslov
        font_size: '16sp'
        bold: True
        color: 1, 0.85, 0.35, 1
        halign: "left"
        valign: "top"
        size_hint_y: None
        text_size: self.width, None
        height: self.texture_size[1]
    Label:
        text: root.tekst
        font_size: '13.5sp'
        color: 0.95, 0.95, 1, 1
        halign: "left"
        valign: "top"
        size_hint_y: None
        text_size: self.width, None
        height: self.texture_size[1]

<UputstvoScreen>:
    name: "uputstvo"
    ScreenRoot:

        TitleLabel:
            text: root.tekst_naslov

        NavBar:
            RoundButton:
                label_text: root.tekst_pocetna
                tint: 0.36, 0.46, 0.64, 1
                on_release: root.manager.current = "home"

        PastelCard:
            orientation: "vertical"
            tint: 0.30, 0.29, 0.42, 0.92
            size_hint_y: None
            height: self.minimum_height
            padding: dp(12)
            Label:
                text: root.tekst_status
                color: 1, 1, 1, 1
                halign: "left"
                valign: "middle"
                size_hint_y: None
                text_size: self.width, None
                height: self.texture_size[1]

        RoundButton:
            label_text: root.tekst_izvezi_pdf_dugme
            tint: 0.30, 0.52, 0.36, 1
            text_color: 1, 1, 1, 1
            size_hint_y: None
            height: dp(52)
            on_release: root.izvezi_pdf()

        ScrollView:
            do_scroll_x: False
            BoxLayout:
                id: lista_uputstvo
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: dp(2), dp(4)


"""
