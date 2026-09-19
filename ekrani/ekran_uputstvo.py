"""
uputstvo_tekstovi.py
Tekst uputstva za upotrebu (ekran "Uputstvo" i PDF izvoz) na svim
jezicima aplikacije.

Svaki jezik je lista sekcija; svaka sekcija je (naslov, [pasusi]).
Redosled i broj sekcija/pasusa je isti u svim jezicima.

Kad se doda novi jezik: napravi novu listu (npr. ES_SADRZAJ) i upisi je
u recnike SADRZAJ i PODNASLOV na dnu fajla. Ako za neki jezik nema
uputstva, ekran prikazuje srpsku verziju.
"""

SR_SADRZAJ = [
    ("Prvo pokretanje i zakljucavanje otiskom prsta", [
        "Kad prvi put otvoris app, pojavice se Pocetni ekran direktno - zakljucavanje otiskom je iskljuceno po difoltu.",
        "Ako u Podesavanjima ukljucis Sigurnost (otisak prsta), sledeci put kad pokrenes app prvo ces videti ekran sa zahtevom da prislonis prst na senzor. Bez uspesnog otiska ne mozes dalje.",
        "Ako telefon nema citac otiska, ili nijedan otisak nije registrovan u sistemskim podesavanjima telefona, app te automatski propusta dalje i samo te obavestava zasto - nema opasnosti da se trajno zakljucas van app-a.",
        "Zakljucavanje se proverava samo pri pokretanju app-a (hladnom startu), ne pri svakom povratku iz pozadine - tako da te ne prekida usred aktivne voznje (npr. ako primis poziv).",
        "Ukljucuje se / iskljucuje u Podesavanja -> Sigurnost (otisak prsta).",
    ]),
    ("Pocetni ekran", [
        "GPS voznja (auto) - otvara automatsko pracenje voznje preko GPS-a.",
        "Pocetak voznje (rucno) - otvara Kalkulator za rucni unos voznje.",
        "Istorija voznji - otvara Evidenciju, spisak svih voznji sa pretragom.",
        "Izvestaj - dnevni/nedeljni/mesecni pregled zarade.",
        "Profil vozaca - licni podaci i podaci o vozilu.",
        "Podesavanja - svi ostali meniji aplikacije.",
        "Uputstvo za upotrebu - ekran koji sad citas.",
    ]),
    ("GPS voznja (automatski unos) - najcesca opcija", [
        "1. Opciono, pre klika na 'Pocni voznju' mozes uneti krajnju adresu - ako je uneses, cim krene voznja odmah se otvara Google navigacija korak-po-korak ka toj adresi.",
        "2. Klik na POCNI VOZNJU. App trazi dozvolu za lokaciju ako je prvi put, pa pocinje da meri kilometrazu uzivo.",
        "3. Ekran u toku voznje prikazuje adresu polaska, predjene kilometre, trajanje i trenutnu cenu.",
        "4. Kad stignes, klik na ZAVRSI VOZNJU - app sam pronalazi trenutnu adresu i cuva voznju u Evidenciju.",
        "GPS voznja koristi samo Osnovnu ili Nocnu tarifu, zavisno od prekidaca u Podesavanja -> Nocna tarifa (nije automatski po satu). Za Vikend ili Aerodromski transfer koristi rucni unos (Kalkulator).",
        "App filtrira losu GPS preciznost - ignorise tacke losije od 50m preciznosti, mikro-skokove ispod 10m i nerealne skokove brzine preko 180 km/h, da kilometraza ne bi bila lazno naduvana.",
        "Ako GPS ne uspe da izmeri kilometrazu, na ekranu za zavrsetak voznje postoji polje za rucni unos km kao rezerva.",
    ]),
    ("Kalkulator (rucni unos voznje)", [
        "Za voznje koje ne pratis uzivo preko GPS-a, ili kad ti treba tarifa koju GPS voznja ne podrzava (Vikend, Aerodromski transfer).",
        "1. Izaberi tarifu iz padajuceg menija.",
        "2. Unesi kilometrazu - cena se odmah preracunava ispod.",
        "3. Adresa polaska, adresa dolaska i napomena su opcioni.",
        "4. Klik na Sacuvaj voznju.",
        "Ako je ukljucena Nocna tarifa, ekran automatski predlaze Nocnu tarifu pri otvaranju - i dalje mozes rucno da je promenis za tu konkretnu voznju.",
    ]),
    ("Evidencija (istorija voznji)", [
        "Prikazuje sve sacuvane voznje, najnovije prve - datum, vreme pocetka/kraja, kilometraza, tarifa, adrese i cena.",
        "Pretraga se moze kombinovati: tekst (adrese i napomena), period (datum od / datum do, format GGGG-MM-DD) i opseg cene (cena od / cena do). Klik na Pretrazi ispisuje i zbir za rezultate. Resetuj vraca pun spisak.",
        "Svaka voznja ima dva dugmeta: Izmeni (otvara Kalkulator popunjen tim podacima) i Obrisi (trajno brise voznju, bez potvrde - pazi).",
    ]),
    ("Izvestaj zarade", [
        "Tri kartice sa zbirovima: Danas (spisak voznji danas + ukupno), Ova nedelja (zbirna zarada za tekucu nedelju), Ovaj mesec (zbirna zarada za tekuci mesec).",
        "Odavde ide dugme Izvoz PDF ka ekranu za izvoz izvestaja.",
    ]),
    ("Grafikon zarade", [
        "Vizuelni prikaz kroz vreme. Period: Dnevni / Nedeljni / Mesecni. Prikaz: Zarada ili Kilometri.",
        "Strelice < i > pomeraju kroz prethodne/naredne periode. Klik na tacku u grafikonu prikazuje tacan iznos za taj dan/nedelju/mesec.",
        "Ispod grafikona: dodatne statistike i, kad ima podataka, pregled potrosnje goriva i servisa za taj period.",
        "Pristupa se preko Podesavanja -> Grafik zarade.",
    ]),
    ("Izvoz izvestaja (PDF / Excel)", [
        "Ekran Izvestaj -> Izvoz PDF. Izaberi vrstu perioda (Dnevno, Nedeljno, Mesecno, Polugodisnje, Godisnje) i unesi period u trazenom formatu.",
        "Izvezi PDF - pravi PDF za stampu/pregled sa podacima o vozacu, servisima, ostalim troskovima, potrosnjom goriva, svim voznjama i zbirnim redom na kraju (broj voznji, ukupno km, bruto zarada i NETO = zarada - gorivo - servisi - ostali troskovi).",
        "Izvezi Excel - pravi Excel fajl sa 5 listova i formulama, namenjen knjigovodji da ga otvori u Excel-u i sam sabira/filtrira.",
        "Oba fajla se cuvaju u Preuzimanja/TaksiApp na telefonu (isti folder kao backup) - potrebna je dozvola 'pristup svim fajlovima' (Podesavanja -> Backup podataka).",
    ]),
    ("Cene / Tarife", [
        "Menjaju se cene po kilometru za sve cetiri tarife (Osnovna, Nocna, Vikend, Aerodromski transfer) plus start taksa.",
        "Klik na Sacuvaj cene primenjuje ih na SVE naredne voznje - ne menja retroaktivno vec sacuvane voznje.",
    ]),
    ("Nocna tarifa (prekidac)", [
        "Jedan prekidac: kad je ukljucen, i Kalkulator i GPS voznja automatski koriste Nocnu tarifu (i dalje mozes rucno promeniti tarifu za pojedinacnu voznju u Kalkulatoru).",
        "Ne ukljucuje se sam po satu - ti ga ukljucujes i iskljucujes rucno kad pocinje/prestaje tvoja nocna smena.",
    ]),
    ("Gorivo", [
        "Evidencija sipanja goriva: vrsta (Benzin/TNG), kolicina (litara), cena, kilometraza na pumpi (opciono ali VAZNO - bez nje se ne moze izracunati potrosnja niti radi podsetnik za servis), napomena.",
        "Na vrhu ekrana vidi se ukupno potroseno na gorivo (posebno benzin, posebno TNG). Potrosnja u l/100km se automatski racuna iz razlike kilometraze izmedju dva uzastopna sipanja koja imaju upisanu kilometrazu.",
    ]),
    ("Servis vozila", [
        "Evidencija servisa (zamena ulja, kocnice, itd.) - vrsta, cena, kilometraza, napomena.",
        "Podsetnik za servis: postavis interval (npr. na svakih 10000 km), a app sam prati koliko je predjeno od poslednjeg servisa - poredeci kilometrazu poslednjeg servisa sa najnovijom kilometrazom upisanom kod Goriva (ne sa ukupnim km iz voznji). Kartica menja boju: zeleno (sve OK), zuto (ostalo manje od 20% intervala), crveno (vreme je za servis).",
        "Ako nema jos dovoljno podataka (bar jedan servis SA kilometrazom i bar jedno gorivo SA kilometrazom sa pumpe), kartica samo kaze da nema dovoljno podataka.",
    ]),
    ("Ostali troskovi", [
        "Za sve sto ne spada u gorivo/servis: Parking, Putarina, Pranje, Ostalo - cena i napomena. Ovi troskovi ulaze u NETO izracun u PDF izvestaju.",
    ]),
    ("Profil vozaca", [
        "Licni podaci (ime, telefon, licenca, tablice, vozilo) koji se prikazuju u zaglavlju PDF izvestaja, plus datum isteka registracije i datum isteka osiguranja.",
        "Kartica na dnu prati oba datuma: sivo (nije unet), zeleno (vise od 30 dana do isteka), zuto (30 dana ili manje), crveno (vec isteklo - pise koliko dana kasni).",
    ]),
    ("Navigacija", [
        "Nezavisan ekran za brzo otvaranje Google navigacije ka bilo kojoj adresi - unesi adresu i klikni 'Otvori navigaciju'. Automatski krece korak-po-korak od tvoje trenutne GPS pozicije.",
    ]),
    ("Google API", [
        "Opciono polje za Google Geocoding API kljuc. Ako ga ne uneses, app i dalje radi normalno - koristi besplatan OpenStreetMap servis za pronalazenje adresa. Google-ov servis je samo precizniji u pojedinim slucajevima. Kljuc se pravi na console.cloud.google.com (Geocoding API).",
    ]),
    ("Valuta", [
        "Bira se samo kako se cene PRIKAZUJU u app-i - u pozadini se sve uvek racuna i cuva u RSD (dinarima), bez obzira na ovaj izbor. Dugmad: Prikazuj u RSD ili Prikazuj u EUR.",
        "Kurs se automatski osvezava jednom dnevno (prvi put kad tog dana otvoris app). Dugme Osvezi kurs sada za rucno osvezavanje ako npr. juce nije bilo interneta.",
    ]),
    ("Backup podataka", [
        "Cuva SVE podatke (voznje, gorivo, servisi, troskovi, profil vozaca) u jedan fajl van same aplikacije, u Preuzimanja/TaksiApp - ostaje na telefonu i posle brisanja/reinstalacije app-a.",
        "Odobri pristup fajlovima - daje app-u Android dozvolu da pise u taj javni folder (trazi se jednom).",
        "App sam pravi svez backup jednom dnevno pri pokretanju, tiho, bez poruke. Sacuvaj backup sada je za rucni backup kad god pozelis.",
        "Vrati podatke iz backupa - ucitava sve podatke iz backup fajla (koristi se pri promeni telefona ili posle reinstalacije).",
        "Podeli backup (Drive, WhatsApp...) - otvara sistemski meni za deljenje da posaljes backup fajl sebi na mejl, Google Drive, WhatsApp itd.",
        "Pri promeni telefona: napravi backup na starom -> prebaci fajl (WhatsApp/Drive/USB) u isti folder na novom -> instaliraj app -> klikni 'Vrati podatke'.",
    ]),
    ("Sigurnost (otisak prsta)", [
        "Ukljucuje/iskljucuje zakljucavanje app-a otiskom prsta pri pokretanju - detaljno objasnjeno na pocetku ovog uputstva. Ekran ti kaze i da li tvoj telefon uopste ima registrovan otisak.",
    ]),
    ("Poziv / Dispecer", [
        "Vodis spisak dispecera sa vremenom njihovih smena, pozivas ih jednim dodirom i na prvi pogled vidis cija je smena trenutno aktivna.",
    ]),
    ("Najcesci problemi", [
        "GPS ne pokazuje kilometrazu -> proveri dozvolu za lokaciju (Podesavanja telefona -> Aplikacije -> Downtown Taxi -> Dozvole -> Lokacija -> Dozvoli) i da li je GPS ukljucen na telefonu.",
        "Ne mogu da izvezem PDF/Excel -> Podesavanja -> Backup podataka -> 'Odobri pristup fajlovima'.",
        "Ne radi otisak prsta -> proveri da li telefon uopste ima citac otiska i da li je otisak registrovan u sistemskim podesavanjima telefona - bez toga app te automatski propusta dalje.",
        "Podsetnik za servis kaze 'nema dovoljno podataka' -> potreban je bar jedan servis SA upisanom kilometrazom i bar jedno gorivo SA upisanom kilometrazom sa pumpe.",
        "Cene se ne poklapaju sa novim tarifama -> nove cene vaze samo za voznje UNETE POSLE izmene, ne menjaju retroaktivno vec sacuvane voznje.",
    ]),
]

EN_SADRZAJ = [
    ("First launch and fingerprint lock", [
        "The first time you open the app, the Home screen appears directly - fingerprint lock is off by default.",
        "If you turn on Security (fingerprint) in Settings, the next time you launch the app you'll first see a screen asking you to place your finger on the sensor. You can't continue without a successful fingerprint.",
        "If the phone has no fingerprint reader, or no fingerprint is registered in the phone's system settings, the app automatically lets you through and just tells you why - there's no risk of being permanently locked out of the app.",
        "The lock is only checked when the app starts (a cold start), not every time you return from the background - so it won't interrupt you mid-ride (e.g. if you get a call).",
        "Turned on/off in Settings -> Security (fingerprint).",
    ]),
    ("Home screen", [
        "GPS ride (auto) - opens automatic ride tracking via GPS.",
        "Start ride (manual) - opens the Calculator for manual ride entry.",
        "Ride history - opens Ride history, a searchable list of all rides.",
        "Report - daily/weekly/monthly earnings overview.",
        "Driver profile - personal and vehicle details.",
        "Settings - all other menus of the app.",
        "Instructions - the screen you're reading now.",
    ]),
    ("GPS ride (automatic entry) - the most common option", [
        "1. Optionally, before tapping 'Start ride' you can enter a destination address - if you do, as soon as the ride starts Google navigation opens turn-by-turn to that address.",
        "2. Tap START RIDE. The app asks for location permission the first time, then starts measuring distance live.",
        "3. The screen during the ride shows the pickup address, distance driven, duration and the current price.",
        "4. When you arrive, tap END RIDE - the app finds the current address itself and saves the ride to Ride history.",
        "GPS ride only uses the Standard or Night tariff, depending on the switch in Settings -> Night tariff (it does not switch automatically by the clock). For Weekend or Airport transfer, use manual entry (Calculator).",
        "The app filters out poor GPS accuracy - it ignores points worse than 50m accuracy, micro-jumps under 10m, and unrealistic speed jumps over 180 km/h, so the distance isn't falsely inflated.",
        "If GPS fails to measure the distance, the ride-end screen has a manual km entry field as a backup.",
    ]),
    ("Calculator (manual ride entry)", [
        "For rides you don't track live via GPS, or when you need a tariff GPS ride doesn't support (Weekend, Airport transfer).",
        "1. Choose a tariff from the dropdown.",
        "2. Enter the distance - the price updates instantly below.",
        "3. Pickup address, destination address and note are optional.",
        "4. Tap Save ride.",
        "If Night tariff is turned on, the screen automatically suggests the Night tariff when opened - you can still manually change it for that specific ride.",
    ]),
    ("Ride history", [
        "Shows all saved rides, newest first - date, start/end time, distance, tariff, addresses and price.",
        "Search can be combined: text (addresses and note), period (date from / date to, YYYY-MM-DD format) and price range (price from / price to). Tapping Search also shows a total for the results. Reset restores the full list.",
        "Each ride has two buttons: Edit (opens the Calculator filled in with that data) and Delete (permanently deletes the ride, no confirmation - be careful).",
    ]),
    ("Earnings report", [
        "Three cards with totals: Today (list of today's rides + total), This week (total earnings for the current week), This month (total earnings for the current month).",
        "From here, the Export PDF button leads to the report export screen.",
    ]),
    ("Earnings chart", [
        "A visual view over time. Period: Daily / Weekly / Monthly. View: Earnings or Kilometers.",
        "The < and > arrows move through previous/next periods. Tapping a point on the chart shows the exact amount for that day/week/month.",
        "Below the chart: extra stats and, when data is available, an overview of fuel and service spending for that period.",
        "Accessed via Settings -> Earnings chart.",
    ]),
    ("Report export (PDF / Excel)", [
        "Report screen -> Export PDF. Choose the period type (Daily, Weekly, Monthly, Half-year, Yearly) and enter the period in the requested format.",
        "Export PDF - creates a PDF for printing/review with driver details, service, other expenses, fuel consumption, all rides and a summary row at the end (number of rides, total km, gross earnings and NET = earnings - fuel - service - other expenses).",
        "Export Excel - creates an Excel file with 5 sheets and formulas, meant for your accountant to open in Excel and total/filter on their own.",
        "Both files are saved to Downloads/TaksiApp on the phone (same folder as the backup) - the 'access all files' permission is required (Settings -> Data backup).",
    ]),
    ("Prices / Tariffs", [
        "Changes the price per kilometer for all four tariffs (Standard, Night, Weekend, Airport transfer) plus the start fee.",
        "Tapping Save prices applies them to ALL future rides - it does not retroactively change rides already saved.",
    ]),
    ("Night tariff (switch)", [
        "A single switch: when on, both the Calculator and GPS ride automatically use the Night tariff (you can still manually change the tariff for an individual ride in the Calculator).",
        "It does not turn on by the clock automatically - you turn it on and off manually when your night shift starts/ends.",
    ]),
    ("Fuel", [
        "Fuel entry log: type (Gasoline/LPG), quantity (liters), price, mileage at the pump (optional but IMPORTANT - without it, consumption can't be calculated and the service reminder won't work), note.",
        "At the top of the screen you see total fuel spending (gasoline and LPG separately). Consumption in l/100km is calculated automatically from the mileage difference between two consecutive fill-ups that have mileage entered.",
    ]),
    ("Vehicle service", [
        "Service log (oil change, brakes, etc.) - type, price, mileage, note.",
        "Service reminder: you set an interval (e.g. every 10000 km), and the app tracks how far you've driven since the last service by itself - comparing the last service's mileage with the most recent mileage entered under Fuel (not the total km from rides). The card changes color: green (all OK), yellow (less than 20% of the interval left), red (time for service).",
        "If there isn't enough data yet (at least one service WITH mileage and at least one fuel entry WITH pump mileage), the card just says there isn't enough data.",
    ]),
    ("Other expenses", [
        "For anything that isn't fuel/service: Parking, Tolls, Washing, Other - price and note. These expenses are included in the NET calculation in the PDF report.",
    ]),
    ("Driver profile", [
        "Personal details (name, phone, license, plates, vehicle) shown in the header of the PDF report, plus registration expiry date and insurance expiry date.",
        "The card at the bottom tracks both dates: gray (not entered), green (more than 30 days to expiry), yellow (30 days or less), red (already expired - shows how many days overdue).",
    ]),
    ("Navigation", [
        "A standalone screen for quickly opening Google navigation to any address - enter the address and tap 'Open navigation'. It automatically starts turn-by-turn from your current GPS position.",
    ]),
    ("Google API", [
        "An optional field for a Google Geocoding API key. If you don't enter one, the app still works normally - it uses the free OpenStreetMap service to find addresses. Google's service is only more accurate in some cases. The key is created at console.cloud.google.com (Geocoding API).",
    ]),
    ("Currency", [
        "This only chooses how prices are DISPLAYED in the app - in the background, everything is always calculated and stored in RSD (dinars), regardless of this choice. Buttons: Display in RSD or Display in EUR.",
        "The exchange rate refreshes automatically once a day (the first time you open the app that day). The Refresh rate now button is for manually refreshing it, e.g. if there was no internet yesterday.",
    ]),
    ("Data backup", [
        "Saves ALL data (rides, fuel, service, expenses, driver profile) into a single file outside the app itself, in Downloads/TaksiApp - it stays on the phone even after the app is deleted/reinstalled.",
        "Grant file access - gives the app Android permission to write to that public folder (asked once).",
        "The app makes a fresh backup by itself once a day on startup, silently, with no message. Save backup now is for a manual backup whenever you want.",
        "Restore data from backup - loads all data from the backup file (used when switching phones or after reinstalling).",
        "Share backup (Drive, WhatsApp...) - opens the system share menu to send the backup file to yourself by email, Google Drive, WhatsApp, etc.",
        "When switching phones: make a backup on the old one -> transfer the file (WhatsApp/Drive/USB) into the same folder on the new one -> install the app -> tap 'Restore data'.",
    ]),
    ("Security (fingerprint)", [
        "Turns the app's fingerprint lock on startup on/off - explained in detail at the start of these instructions. The screen also tells you whether your phone has a registered fingerprint at all.",
    ]),
    ("Call / Dispatcher", [
        "Keep a list of dispatchers with their shift times, call them with one tap, and see at a glance whose shift is active right now.",
    ]),
    ("Common problems", [
        "GPS doesn't show distance -> check the location permission (Phone Settings -> Apps -> Downtown Taxi -> Permissions -> Location -> Allow) and whether GPS is turned on on the phone.",
        "Can't export PDF/Excel -> Settings -> Data backup -> 'Grant file access'.",
        "Fingerprint doesn't work -> check whether the phone even has a fingerprint reader and whether a fingerprint is registered in the phone's system settings - without that, the app automatically lets you through.",
        "The service reminder says 'not enough data' -> at least one service WITH mileage entered and at least one fuel entry WITH pump mileage entered are needed.",
        "Prices don't match the new tariffs -> new prices only apply to rides ENTERED AFTER the change, they don't retroactively change rides already saved.",
    ]),
]

IT_SADRZAJ = [
    ("Primo avvio e blocco con impronta digitale", [
        "La prima volta che apri l'app, appare direttamente la schermata Home - il blocco con impronta digitale è disattivato per impostazione predefinita.",
        "Se attivi Sicurezza (impronta digitale) nelle Impostazioni, al prossimo avvio dell'app vedrai prima una schermata che ti chiede di appoggiare il dito sul sensore. Senza un'impronta riconosciuta non puoi proseguire.",
        "Se il telefono non ha un lettore di impronte digitali, o nessuna impronta è registrata nelle impostazioni di sistema del telefono, l'app ti lascia passare automaticamente e ti dice solo il motivo - non c'è il rischio di restare bloccato fuori dall'app in modo permanente.",
        "Il blocco viene controllato solo all'avvio dell'app (avvio a freddo), non ogni volta che torni dallo sfondo - quindi non ti interrompe durante una corsa in corso (ad esempio se ricevi una chiamata).",
        "Si attiva/disattiva in Impostazioni -> Sicurezza (impronta digitale).",
    ]),
    ("Schermata Home", [
        "Corsa GPS (auto) - apre il tracciamento automatico della corsa tramite GPS.",
        "Inizia corsa (manuale) - apre il Calcolatore per l'inserimento manuale di una corsa.",
        "Cronologia corse - apre la Cronologia, l'elenco di tutte le corse con ricerca.",
        "Rapporto - panoramica dei guadagni giornaliera/settimanale/mensile.",
        "Profilo conducente - dati personali e del veicolo.",
        "Impostazioni - tutti gli altri menu dell'app.",
        "Istruzioni - la schermata che stai leggendo ora.",
    ]),
    ("Corsa GPS (inserimento automatico) - l'opzione più usata", [
        "1. Facoltativamente, prima di toccare 'Inizia corsa' puoi inserire l'indirizzo di destinazione - in tal caso, appena la corsa parte si apre la navigazione Google passo dopo passo verso quell'indirizzo.",
        "2. Tocca INIZIA CORSA. La prima volta l'app chiede l'autorizzazione alla posizione, poi inizia a misurare i chilometri in tempo reale.",
        "3. Durante la corsa la schermata mostra l'indirizzo di prelievo, i chilometri percorsi, la durata e il prezzo attuale.",
        "4. Quando arrivi, tocca TERMINA CORSA - l'app trova da sola l'indirizzo attuale e salva la corsa nella Cronologia.",
        "La corsa GPS usa solo la tariffa Standard o Notturna, in base all'interruttore in Impostazioni -> Tariffa notturna (non cambia automaticamente in base all'ora). Per Weekend o Transfer aeroporto usa l'inserimento manuale (Calcolatore).",
        "L'app filtra la scarsa precisione del GPS - ignora i punti con precisione peggiore di 50 m, i micro-spostamenti sotto i 10 m e i salti di velocità irrealistici oltre 180 km/h, così i chilometri non vengono gonfiati artificialmente.",
        "Se il GPS non riesce a misurare i chilometri, nella schermata di fine corsa c'è un campo per l'inserimento manuale dei km come riserva.",
    ]),
    ("Calcolatore (inserimento manuale della corsa)", [
        "Per le corse che non tracci in tempo reale con il GPS, o quando ti serve una tariffa che la corsa GPS non supporta (Weekend, Transfer aeroporto).",
        "1. Scegli la tariffa dal menu a tendina.",
        "2. Inserisci la distanza - il prezzo si ricalcola subito qui sotto.",
        "3. Indirizzo di partenza, indirizzo di destinazione e note sono facoltativi.",
        "4. Tocca Salva corsa.",
        "Se la Tariffa notturna è attiva, la schermata propone automaticamente la tariffa Notturna all'apertura - puoi comunque cambiarla manualmente per quella corsa specifica.",
    ]),
    ("Cronologia (storico delle corse)", [
        "Mostra tutte le corse salvate, le più recenti per prime - data, ora di inizio/fine, distanza, tariffa, indirizzi e prezzo.",
        "La ricerca si può combinare: testo (indirizzi e note), periodo (data da / data a, formato AAAA-MM-GG) e intervallo di prezzo (prezzo da / prezzo a). Toccando Cerca viene mostrato anche il totale dei risultati. Reimposta ripristina l'elenco completo.",
        "Ogni corsa ha due pulsanti: Modifica (apre il Calcolatore compilato con quei dati) ed Elimina (cancella definitivamente la corsa, senza conferma - fai attenzione).",
    ]),
    ("Rapporto guadagni", [
        "Tre schede con i totali: Oggi (elenco delle corse di oggi + totale), Questa settimana (guadagno totale della settimana corrente), Questo mese (guadagno totale del mese corrente).",
        "Da qui il pulsante Esporta PDF porta alla schermata di esportazione del rapporto.",
    ]),
    ("Grafico guadagni", [
        "Una visualizzazione grafica nel tempo. Periodo: Giornaliero / Settimanale / Mensile. Vista: Guadagno o Chilometri.",
        "Le frecce < e > scorrono tra i periodi precedenti/successivi. Toccando un punto del grafico si vede l'importo esatto per quel giorno/settimana/mese.",
        "Sotto il grafico: statistiche aggiuntive e, quando ci sono dati, una panoramica delle spese di carburante e manutenzione per quel periodo.",
        "Si apre da Impostazioni -> Grafico guadagni.",
    ]),
    ("Esportazione rapporti (PDF / Excel)", [
        "Schermata Rapporto -> Esporta PDF. Scegli il tipo di periodo (Giornaliero, Settimanale, Mensile, Semestrale, Annuale) e inserisci il periodo nel formato richiesto.",
        "Esporta PDF - crea un PDF per la stampa/consultazione con i dati del conducente, manutenzione, altre spese, consumo di carburante, tutte le corse e una riga riepilogativa alla fine (numero di corse, km totali, guadagno lordo e NETTO = guadagno - carburante - manutenzione - altre spese).",
        "Esporta Excel - crea un file Excel con 5 fogli e formule, pensato per il commercialista, che può aprirlo in Excel e sommare/filtrare da solo.",
        "Entrambi i file vengono salvati in Downloads/TaksiApp sul telefono (la stessa cartella del backup) - serve l'autorizzazione 'accesso a tutti i file' (Impostazioni -> Backup dati).",
    ]),
    ("Prezzi / Tariffe", [
        "Modifica il prezzo al chilometro per tutte e quattro le tariffe (Standard, Notturna, Weekend, Transfer aeroporto) più la tariffa di partenza.",
        "Toccando Salva prezzi vengono applicati a TUTTE le corse future - non modifica retroattivamente le corse già salvate.",
    ]),
    ("Tariffa notturna (interruttore)", [
        "Un unico interruttore: quando è attivo, sia il Calcolatore sia la corsa GPS usano automaticamente la tariffa Notturna (puoi comunque cambiare manualmente la tariffa per una singola corsa nel Calcolatore).",
        "Non si attiva da solo in base all'ora - lo attivi e lo disattivi tu manualmente quando inizia/finisce il tuo turno di notte.",
    ]),
    ("Carburante", [
        "Registro dei rifornimenti: tipo (Benzina/GPL), quantità (litri), prezzo, chilometraggio al distributore (facoltativo ma IMPORTANTE - senza di esso non si può calcolare il consumo e il promemoria di manutenzione non funziona), note.",
        "In alto nella schermata vedi il totale speso in carburante (benzina e GPL separatamente). Il consumo in l/100km viene calcolato automaticamente dalla differenza di chilometraggio tra due rifornimenti consecutivi che hanno il chilometraggio inserito.",
    ]),
    ("Manutenzione veicolo", [
        "Registro delle manutenzioni (cambio olio, freni, ecc.) - tipo, prezzo, chilometraggio, note.",
        "Promemoria manutenzione: imposti un intervallo (ad esempio ogni 10000 km) e l'app tiene traccia da sola di quanti km hai percorso dall'ultima manutenzione - confrontando il chilometraggio dell'ultima manutenzione con il chilometraggio più recente inserito in Carburante (non con i km totali delle corse). La scheda cambia colore: verde (tutto OK), giallo (rimane meno del 20% dell'intervallo), rosso (è ora della manutenzione).",
        "Se non ci sono ancora dati sufficienti (almeno una manutenzione CON chilometraggio e almeno un rifornimento CON chilometraggio al distributore), la scheda dice solo che i dati non sono sufficienti.",
    ]),
    ("Altre spese", [
        "Per tutto ciò che non è carburante/manutenzione: Parcheggio, Pedaggi, Lavaggio, Altro - prezzo e note. Queste spese rientrano nel calcolo del NETTO nel rapporto PDF.",
    ]),
    ("Profilo conducente", [
        "Dati personali (nome, telefono, licenza, targa, veicolo) che compaiono nell'intestazione del rapporto PDF, più la data di scadenza dell'immatricolazione e la data di scadenza dell'assicurazione.",
        "La scheda in basso tiene traccia di entrambe le date: grigio (non inserita), verde (più di 30 giorni alla scadenza), giallo (30 giorni o meno), rosso (già scaduta - indica quanti giorni di ritardo).",
    ]),
    ("Navigazione", [
        "Una schermata indipendente per aprire rapidamente la navigazione Google verso qualsiasi indirizzo - inserisci l'indirizzo e tocca 'Apri navigazione'. Parte automaticamente passo dopo passo dalla tua posizione GPS attuale.",
    ]),
    ("Google API", [
        "Campo facoltativo per la chiave API Google Geocoding. Se non la inserisci, l'app funziona comunque normalmente - usa il servizio gratuito OpenStreetMap per trovare gli indirizzi. Il servizio Google è solo più preciso in alcuni casi. La chiave si crea su console.cloud.google.com (Geocoding API).",
    ]),
    ("Valuta", [
        "Sceglie solo come vengono VISUALIZZATI i prezzi nell'app - in background tutto viene sempre calcolato e salvato in RSD (dinari), indipendentemente da questa scelta. Pulsanti: Visualizza in RSD o Visualizza in EUR.",
        "Il tasso di cambio si aggiorna automaticamente una volta al giorno (la prima volta che apri l'app quel giorno). Il pulsante Aggiorna tasso ora serve per aggiornarlo manualmente, ad esempio se ieri non c'era internet.",
    ]),
    ("Backup dati", [
        "Salva TUTTI i dati (corse, carburante, manutenzione, spese, profilo conducente) in un unico file fuori dall'app, in Downloads/TaksiApp - resta sul telefono anche dopo l'eliminazione/reinstallazione dell'app.",
        "Concedi accesso ai file - dà all'app l'autorizzazione Android a scrivere in quella cartella pubblica (viene richiesta una sola volta).",
        "L'app crea da sola un nuovo backup una volta al giorno all'avvio, in silenzio, senza messaggi. Salva backup ora serve per un backup manuale quando vuoi.",
        "Ripristina dati dal backup - carica tutti i dati dal file di backup (si usa quando cambi telefono o dopo una reinstallazione).",
        "Condividi backup (Drive, WhatsApp...) - apre il menu di condivisione del sistema per inviare il file di backup a te stesso via email, Google Drive, WhatsApp ecc.",
        "Quando cambi telefono: fai un backup sul vecchio -> trasferisci il file (WhatsApp/Drive/USB) nella stessa cartella sul nuovo -> installa l'app -> tocca 'Ripristina dati'.",
    ]),
    ("Sicurezza (impronta digitale)", [
        "Attiva/disattiva il blocco dell'app con impronta digitale all'avvio - spiegato in dettaglio all'inizio di queste istruzioni. La schermata ti dice anche se il tuo telefono ha un'impronta registrata.",
    ]),
    ("Chiamata / Centralino", [
        "Tieni un elenco di centralinisti con i loro orari di turno, li chiami con un solo tocco e vedi a colpo d'occhio di chi è il turno attivo in questo momento.",
    ]),
    ("Problemi più comuni", [
        "Il GPS non mostra i chilometri -> controlla l'autorizzazione alla posizione (Impostazioni telefono -> App -> Downtown Taxi -> Autorizzazioni -> Posizione -> Consenti) e se il GPS è attivo sul telefono.",
        "Non riesco a esportare PDF/Excel -> Impostazioni -> Backup dati -> 'Concedi accesso ai file'.",
        "L'impronta digitale non funziona -> controlla se il telefono ha davvero un lettore di impronte e se un'impronta è registrata nelle impostazioni di sistema del telefono - altrimenti l'app ti lascia passare automaticamente.",
        "Il promemoria di manutenzione dice 'dati non sufficienti' -> servono almeno una manutenzione CON chilometraggio inserito e almeno un rifornimento CON chilometraggio al distributore inserito.",
        "I prezzi non corrispondono alle nuove tariffe -> i nuovi prezzi valgono solo per le corse INSERITE DOPO la modifica, non cambiano retroattivamente le corse già salvate.",
    ]),
]

FR_SADRZAJ = [
    ("Premier lancement et verrouillage par empreinte digitale", [
        "La première fois que vous ouvrez l'application, l'écran d'accueil s'affiche directement - le verrouillage par empreinte digitale est désactivé par défaut.",
        "Si vous activez Sécurité (empreinte digitale) dans les Paramètres, au prochain lancement de l'application vous verrez d'abord un écran vous demandant de poser votre doigt sur le capteur. Sans empreinte reconnue, vous ne pouvez pas continuer.",
        "Si le téléphone n'a pas de lecteur d'empreintes, ou si aucune empreinte n'est enregistrée dans les paramètres système du téléphone, l'application vous laisse passer automatiquement et vous indique simplement pourquoi - il n'y a aucun risque d'être définitivement bloqué hors de l'application.",
        "Le verrouillage n'est vérifié qu'au démarrage de l'application (démarrage à froid), et non à chaque retour depuis l'arrière-plan - il ne vous interrompt donc pas en pleine course (par exemple si vous recevez un appel).",
        "Il s'active/se désactive dans Paramètres -> Sécurité (empreinte digitale).",
    ]),
    ("Écran d'accueil", [
        "Course GPS (auto) - ouvre le suivi automatique de la course par GPS.",
        "Démarrer une course (manuel) - ouvre le Calculateur pour la saisie manuelle d'une course.",
        "Historique des courses - ouvre l'Historique, la liste de toutes les courses avec recherche.",
        "Rapport - aperçu des gains quotidien/hebdomadaire/mensuel.",
        "Profil du chauffeur - données personnelles et du véhicule.",
        "Paramètres - tous les autres menus de l'application.",
        "Mode d'emploi - l'écran que vous lisez en ce moment.",
    ]),
    ("Course GPS (saisie automatique) - l'option la plus courante", [
        "1. Facultatif : avant d'appuyer sur 'Démarrer la course', vous pouvez saisir l'adresse d'arrivée - dans ce cas, dès que la course démarre, la navigation Google s'ouvre en guidage pas à pas vers cette adresse.",
        "2. Appuyez sur DÉMARRER LA COURSE. La première fois, l'application demande l'autorisation de localisation, puis commence à mesurer la distance en direct.",
        "3. Pendant la course, l'écran affiche l'adresse de prise en charge, les kilomètres parcourus, la durée et le prix actuel.",
        "4. Une fois arrivé, appuyez sur TERMINER LA COURSE - l'application trouve elle-même l'adresse actuelle et enregistre la course dans l'Historique.",
        "La course GPS n'utilise que le tarif Standard ou Nuit, selon l'interrupteur dans Paramètres -> Tarif de nuit (il ne change pas automatiquement selon l'heure). Pour Week-end ou Transfert aéroport, utilisez la saisie manuelle (Calculateur).",
        "L'application filtre les mauvaises précisions GPS - elle ignore les points dont la précision est inférieure à 50 m, les micro-sauts de moins de 10 m et les sauts de vitesse irréalistes de plus de 180 km/h, afin que la distance ne soit pas artificiellement gonflée.",
        "Si le GPS n'arrive pas à mesurer la distance, l'écran de fin de course comporte un champ de saisie manuelle des km en secours.",
    ]),
    ("Calculateur (saisie manuelle d'une course)", [
        "Pour les courses que vous ne suivez pas en direct par GPS, ou lorsque vous avez besoin d'un tarif que la course GPS ne prend pas en charge (Week-end, Transfert aéroport).",
        "1. Choisissez un tarif dans le menu déroulant.",
        "2. Saisissez la distance - le prix se recalcule aussitôt en dessous.",
        "3. L'adresse de départ, l'adresse d'arrivée et la remarque sont facultatives.",
        "4. Appuyez sur Enregistrer la course.",
        "Si le Tarif de nuit est activé, l'écran propose automatiquement le tarif Nuit à l'ouverture - vous pouvez toujours le modifier manuellement pour cette course précise.",
    ]),
    ("Historique (liste des courses)", [
        "Affiche toutes les courses enregistrées, les plus récentes d'abord - date, heure de début/fin, distance, tarif, adresses et prix.",
        "La recherche peut être combinée : texte (adresses et remarque), période (date de début / date de fin, format AAAA-MM-JJ) et fourchette de prix (prix min. / prix max.). Appuyer sur Rechercher affiche aussi le total des résultats. Réinitialiser rétablit la liste complète.",
        "Chaque course a deux boutons : Modifier (ouvre le Calculateur rempli avec ces données) et Supprimer (supprime définitivement la course, sans confirmation - attention).",
    ]),
    ("Rapport des gains", [
        "Trois cartes avec les totaux : Aujourd'hui (liste des courses du jour + total), Cette semaine (gains totaux de la semaine en cours), Ce mois (gains totaux du mois en cours).",
        "D'ici, le bouton Exporter en PDF mène à l'écran d'exportation du rapport.",
    ]),
    ("Graphique des gains", [
        "Une vue graphique dans le temps. Période : Quotidien / Hebdomadaire / Mensuel. Affichage : Gains ou Kilomètres.",
        "Les flèches < et > font défiler les périodes précédentes/suivantes. Appuyer sur un point du graphique affiche le montant exact pour ce jour/cette semaine/ce mois.",
        "Sous le graphique : statistiques supplémentaires et, lorsqu'il y a des données, un aperçu des dépenses de carburant et d'entretien pour cette période.",
        "On y accède via Paramètres -> Graphique des gains.",
    ]),
    ("Exportation des rapports (PDF / Excel)", [
        "Écran Rapport -> Exporter en PDF. Choisissez le type de période (Quotidien, Hebdomadaire, Mensuel, Semestriel, Annuel) et saisissez la période au format demandé.",
        "Exporter en PDF - crée un PDF pour l'impression/la consultation avec les données du chauffeur, l'entretien, les autres dépenses, la consommation de carburant, toutes les courses et une ligne de synthèse à la fin (nombre de courses, total km, gains bruts et NET = gains - carburant - entretien - autres dépenses).",
        "Exporter en Excel - crée un fichier Excel de 5 feuilles avec formules, destiné au comptable, qui peut l'ouvrir dans Excel et faire lui-même les totaux/filtres.",
        "Les deux fichiers sont enregistrés dans Downloads/TaksiApp sur le téléphone (le même dossier que la sauvegarde) - l'autorisation 'accès à tous les fichiers' est nécessaire (Paramètres -> Sauvegarde des données).",
    ]),
    ("Prix / Tarifs", [
        "Modifie le prix au kilomètre pour les quatre tarifs (Standard, Nuit, Week-end, Transfert aéroport) ainsi que la prise en charge.",
        "Appuyer sur Enregistrer les prix les applique à TOUTES les courses futures - cela ne modifie pas rétroactivement les courses déjà enregistrées.",
    ]),
    ("Tarif de nuit (interrupteur)", [
        "Un seul interrupteur : lorsqu'il est activé, le Calculateur comme la course GPS utilisent automatiquement le tarif Nuit (vous pouvez toujours modifier manuellement le tarif d'une course individuelle dans le Calculateur).",
        "Il ne s'active pas tout seul selon l'heure - c'est vous qui l'activez et le désactivez manuellement lorsque votre service de nuit commence/se termine.",
    ]),
    ("Carburant", [
        "Journal des pleins : type (Essence/GPL), quantité (litres), prix, kilométrage à la pompe (facultatif mais IMPORTANT - sans lui, la consommation ne peut pas être calculée et le rappel d'entretien ne fonctionne pas), remarque.",
        "En haut de l'écran, vous voyez le total dépensé en carburant (essence et GPL séparément). La consommation en l/100km est calculée automatiquement à partir de la différence de kilométrage entre deux pleins consécutifs dont le kilométrage est renseigné.",
    ]),
    ("Entretien du véhicule", [
        "Journal des entretiens (vidange, freins, etc.) - type, prix, kilométrage, remarque.",
        "Rappel d'entretien : vous définissez un intervalle (par exemple tous les 10000 km), et l'application suit elle-même la distance parcourue depuis le dernier entretien - en comparant le kilométrage du dernier entretien au kilométrage le plus récent saisi dans Carburant (et non aux km totaux des courses). La carte change de couleur : verte (tout va bien), jaune (moins de 20 % de l'intervalle restant), rouge (il est temps de faire l'entretien).",
        "S'il n'y a pas encore assez de données (au moins un entretien AVEC kilométrage et au moins un plein AVEC kilométrage à la pompe), la carte indique simplement qu'il n'y a pas assez de données.",
    ]),
    ("Autres dépenses", [
        "Pour tout ce qui n'est pas carburant/entretien : Parking, Péages, Lavage, Autre - prix et remarque. Ces dépenses entrent dans le calcul du NET dans le rapport PDF.",
    ]),
    ("Profil du chauffeur", [
        "Données personnelles (nom, téléphone, licence, plaque, véhicule) affichées dans l'en-tête du rapport PDF, ainsi que la date d'expiration de l'immatriculation et la date d'expiration de l'assurance.",
        "La carte en bas suit les deux dates : gris (non saisie), vert (plus de 30 jours avant l'expiration), jaune (30 jours ou moins), rouge (déjà expirée - indique le nombre de jours de retard).",
    ]),
    ("Navigation", [
        "Un écran indépendant pour ouvrir rapidement la navigation Google vers n'importe quelle adresse - saisissez l'adresse et appuyez sur 'Ouvrir la navigation'. Le guidage pas à pas démarre automatiquement depuis votre position GPS actuelle.",
    ]),
    ("Google API", [
        "Champ facultatif pour une clé API Google Geocoding. Si vous n'en saisissez pas, l'application fonctionne quand même normalement - elle utilise le service gratuit OpenStreetMap pour trouver les adresses. Le service de Google n'est plus précis que dans certains cas. La clé se crée sur console.cloud.google.com (Geocoding API).",
    ]),
    ("Devise", [
        "Ce réglage choisit seulement comment les prix sont AFFICHÉS dans l'application - en arrière-plan, tout est toujours calculé et enregistré en RSD (dinars), quel que soit ce choix. Boutons : Afficher en RSD ou Afficher en EUR.",
        "Le taux de change s'actualise automatiquement une fois par jour (à la première ouverture de l'application ce jour-là). Le bouton Actualiser le taux maintenant sert à l'actualiser manuellement, par exemple s'il n'y avait pas d'Internet hier.",
    ]),
    ("Sauvegarde des données", [
        "Enregistre TOUTES les données (courses, carburant, entretien, dépenses, profil du chauffeur) dans un seul fichier en dehors de l'application, dans Downloads/TaksiApp - il reste sur le téléphone même après la suppression/réinstallation de l'application.",
        "Accorder l'accès aux fichiers - donne à l'application l'autorisation Android d'écrire dans ce dossier public (demandée une seule fois).",
        "L'application fait elle-même une nouvelle sauvegarde une fois par jour au démarrage, en silence, sans message. Enregistrer la sauvegarde maintenant sert à faire une sauvegarde manuelle quand vous le souhaitez.",
        "Restaurer les données depuis la sauvegarde - charge toutes les données du fichier de sauvegarde (utilisé lors d'un changement de téléphone ou après une réinstallation).",
        "Partager la sauvegarde (Drive, WhatsApp...) - ouvre le menu de partage du système pour vous envoyer le fichier de sauvegarde par e-mail, Google Drive, WhatsApp, etc.",
        "En changeant de téléphone : faites une sauvegarde sur l'ancien -> transférez le fichier (WhatsApp/Drive/USB) dans le même dossier sur le nouveau -> installez l'application -> appuyez sur 'Restaurer les données'.",
    ]),
    ("Sécurité (empreinte digitale)", [
        "Active/désactive le verrouillage de l'application par empreinte digitale au démarrage - expliqué en détail au début de ce mode d'emploi. L'écran vous indique aussi si votre téléphone a une empreinte enregistrée.",
    ]),
    ("Appel / Dispatcher", [
        "Tenez une liste de dispatchers avec leurs horaires d'équipe, appelez-les d'un seul appui et voyez d'un coup d'œil quelle équipe est active en ce moment.",
    ]),
    ("Problèmes courants", [
        "Le GPS n'affiche pas la distance -> vérifiez l'autorisation de localisation (Paramètres du téléphone -> Applications -> Downtown Taxi -> Autorisations -> Localisation -> Autoriser) et si le GPS est activé sur le téléphone.",
        "Impossible d'exporter en PDF/Excel -> Paramètres -> Sauvegarde des données -> 'Accorder l'accès aux fichiers'.",
        "L'empreinte digitale ne fonctionne pas -> vérifiez si le téléphone a bien un lecteur d'empreintes et si une empreinte est enregistrée dans les paramètres système du téléphone - sinon, l'application vous laisse passer automatiquement.",
        "Le rappel d'entretien indique 'pas assez de données' -> il faut au moins un entretien AVEC kilométrage saisi et au moins un plein AVEC kilométrage à la pompe saisi.",
        "Les prix ne correspondent pas aux nouveaux tarifs -> les nouveaux prix ne s'appliquent qu'aux courses SAISIES APRÈS la modification, ils ne changent pas rétroactivement les courses déjà enregistrées.",
    ]),
]

DE_SADRZAJ = [
    ("Erster Start und Fingerabdrucksperre", [
        "Wenn Sie die App zum ersten Mal öffnen, erscheint direkt der Startbildschirm - die Fingerabdrucksperre ist standardmäßig ausgeschaltet.",
        "Wenn Sie in den Einstellungen Sicherheit (Fingerabdruck) einschalten, sehen Sie beim nächsten Start der App zuerst einen Bildschirm, der Sie auffordert, den Finger auf den Sensor zu legen. Ohne erkannten Fingerabdruck kommen Sie nicht weiter.",
        "Wenn das Handy keinen Fingerabdruckleser hat oder in den Systemeinstellungen des Handys kein Fingerabdruck registriert ist, lässt die App Sie automatisch durch und sagt Ihnen nur, warum - es besteht keine Gefahr, dauerhaft aus der App ausgesperrt zu werden.",
        "Die Sperre wird nur beim Start der App geprüft (Kaltstart), nicht bei jeder Rückkehr aus dem Hintergrund - sie unterbricht Sie also nicht mitten in einer Fahrt (z. B. wenn Sie einen Anruf bekommen).",
        "Ein-/Ausschalten unter Einstellungen -> Sicherheit (Fingerabdruck).",
    ]),
    ("Startbildschirm", [
        "GPS-Fahrt (auto) - öffnet die automatische Fahrtverfolgung per GPS.",
        "Fahrt starten (manuell) - öffnet den Fahrtenrechner für die manuelle Eingabe einer Fahrt.",
        "Fahrtenverlauf - öffnet den Verlauf, eine durchsuchbare Liste aller Fahrten.",
        "Bericht - tägliche/wöchentliche/monatliche Einnahmenübersicht.",
        "Fahrerprofil - persönliche Daten und Fahrzeugdaten.",
        "Einstellungen - alle übrigen Menüs der App.",
        "Anleitung - der Bildschirm, den Sie gerade lesen.",
    ]),
    ("GPS-Fahrt (automatische Erfassung) - die häufigste Option", [
        "1. Optional können Sie vor dem Tippen auf 'Fahrt starten' eine Zieladresse eingeben - dann öffnet sich, sobald die Fahrt beginnt, die Google-Navigation Schritt für Schritt zu dieser Adresse.",
        "2. Tippen Sie auf FAHRT STARTEN. Beim ersten Mal fragt die App nach der Standortberechtigung und beginnt dann, die Strecke live zu messen.",
        "3. Während der Fahrt zeigt der Bildschirm die Abholadresse, die gefahrenen Kilometer, die Dauer und den aktuellen Preis.",
        "4. Wenn Sie angekommen sind, tippen Sie auf FAHRT BEENDEN - die App ermittelt die aktuelle Adresse selbst und speichert die Fahrt im Verlauf.",
        "Die GPS-Fahrt verwendet nur den Standard- oder Nachttarif, je nach Schalter unter Einstellungen -> Nachttarif (er wechselt nicht automatisch nach Uhrzeit). Für Wochenende oder Flughafentransfer nutzen Sie die manuelle Eingabe (Fahrtenrechner).",
        "Die App filtert schlechte GPS-Genauigkeit - sie ignoriert Punkte mit schlechterer Genauigkeit als 50 m, Mikrosprünge unter 10 m und unrealistische Geschwindigkeitssprünge über 180 km/h, damit die Strecke nicht fälschlich aufgebläht wird.",
        "Wenn das GPS die Strecke nicht messen kann, gibt es auf dem Bildschirm zum Fahrtende ein Feld zur manuellen Eingabe der km als Ersatz.",
    ]),
    ("Fahrtenrechner (manuelle Fahrterfassung)", [
        "Für Fahrten, die Sie nicht live per GPS verfolgen, oder wenn Sie einen Tarif brauchen, den die GPS-Fahrt nicht unterstützt (Wochenende, Flughafentransfer).",
        "1. Wählen Sie einen Tarif aus dem Dropdown-Menü.",
        "2. Geben Sie die Strecke ein - der Preis wird darunter sofort neu berechnet.",
        "3. Abfahrtsadresse, Zieladresse und Notiz sind optional.",
        "4. Tippen Sie auf Fahrt speichern.",
        "Wenn der Nachttarif eingeschaltet ist, schlägt der Bildschirm beim Öffnen automatisch den Nachttarif vor - Sie können ihn für diese bestimmte Fahrt weiterhin manuell ändern.",
    ]),
    ("Fahrtenverlauf", [
        "Zeigt alle gespeicherten Fahrten, die neuesten zuerst - Datum, Start-/Endzeit, Strecke, Tarif, Adressen und Preis.",
        "Die Suche lässt sich kombinieren: Text (Adressen und Notiz), Zeitraum (Datum von / Datum bis, Format JJJJ-MM-TT) und Preisspanne (Preis ab / Preis bis). Beim Tippen auf Suchen wird auch eine Summe für die Ergebnisse angezeigt. Zurücksetzen stellt die vollständige Liste wieder her.",
        "Jede Fahrt hat zwei Schaltflächen: Bearbeiten (öffnet den Fahrtenrechner mit diesen Daten) und Löschen (löscht die Fahrt dauerhaft, ohne Bestätigung - Vorsicht).",
    ]),
    ("Einnahmenbericht", [
        "Drei Karten mit Summen: Heute (Liste der heutigen Fahrten + Summe), Diese Woche (Gesamteinnahmen der aktuellen Woche), Diesen Monat (Gesamteinnahmen des aktuellen Monats).",
        "Von hier führt die Schaltfläche PDF exportieren zum Bildschirm für den Berichtsexport.",
    ]),
    ("Einnahmen-Diagramm", [
        "Eine grafische Ansicht über die Zeit. Zeitraum: Täglich / Wöchentlich / Monatlich. Ansicht: Einnahmen oder Kilometer.",
        "Die Pfeile < und > blättern durch vorherige/nächste Zeiträume. Tippen auf einen Punkt im Diagramm zeigt den genauen Betrag für diesen Tag/diese Woche/diesen Monat.",
        "Unter dem Diagramm: zusätzliche Statistiken und, wenn Daten vorhanden sind, eine Übersicht über Kraftstoff- und Wartungskosten für diesen Zeitraum.",
        "Aufruf über Einstellungen -> Einnahmen-Diagramm.",
    ]),
    ("Berichtsexport (PDF / Excel)", [
        "Bildschirm Bericht -> PDF exportieren. Wählen Sie die Zeitraumart (Täglich, Wöchentlich, Monatlich, Halbjährlich, Jährlich) und geben Sie den Zeitraum im geforderten Format ein.",
        "PDF exportieren - erstellt ein PDF zum Drucken/Ansehen mit Fahrerdaten, Wartung, sonstigen Ausgaben, Kraftstoffverbrauch, allen Fahrten und einer Zusammenfassungszeile am Ende (Anzahl der Fahrten, Gesamt-km, Bruttoeinnahmen und NETTO = Einnahmen - Kraftstoff - Wartung - sonstige Ausgaben).",
        "Excel exportieren - erstellt eine Excel-Datei mit 5 Blättern und Formeln, gedacht für den Buchhalter, der sie in Excel öffnen und selbst summieren/filtern kann.",
        "Beide Dateien werden im Ordner Downloads/TaksiApp auf dem Handy gespeichert (derselbe Ordner wie die Sicherung) - die Berechtigung 'Zugriff auf alle Dateien' ist erforderlich (Einstellungen -> Datensicherung).",
    ]),
    ("Preise / Tarife", [
        "Ändert den Preis pro Kilometer für alle vier Tarife (Standard, Nacht, Wochenende, Flughafentransfer) sowie die Grundgebühr.",
        "Ein Tippen auf Preise speichern wendet sie auf ALLE künftigen Fahrten an - bereits gespeicherte Fahrten werden nicht rückwirkend geändert.",
    ]),
    ("Nachttarif (Schalter)", [
        "Ein einziger Schalter: Wenn er eingeschaltet ist, verwenden sowohl der Fahrtenrechner als auch die GPS-Fahrt automatisch den Nachttarif (im Fahrtenrechner können Sie den Tarif für eine einzelne Fahrt weiterhin manuell ändern).",
        "Er schaltet sich nicht automatisch nach der Uhrzeit ein - Sie schalten ihn manuell ein und aus, wenn Ihre Nachtschicht beginnt/endet.",
    ]),
    ("Kraftstoff", [
        "Tankprotokoll: Art (Benzin/LPG), Menge (Liter), Preis, Kilometerstand an der Zapfsäule (optional, aber WICHTIG - ohne ihn kann der Verbrauch nicht berechnet werden und die Wartungserinnerung funktioniert nicht), Notiz.",
        "Oben auf dem Bildschirm sehen Sie die gesamten Kraftstoffausgaben (Benzin und LPG getrennt). Der Verbrauch in l/100km wird automatisch aus der Differenz des Kilometerstands zwischen zwei aufeinanderfolgenden Tankvorgängen berechnet, bei denen der Kilometerstand eingetragen ist.",
    ]),
    ("Fahrzeugwartung", [
        "Wartungsprotokoll (Ölwechsel, Bremsen usw.) - Art, Preis, Kilometerstand, Notiz.",
        "Wartungserinnerung: Sie legen ein Intervall fest (z. B. alle 10000 km), und die App verfolgt selbst, wie weit Sie seit der letzten Wartung gefahren sind - indem sie den Kilometerstand der letzten Wartung mit dem neuesten unter Kraftstoff eingetragenen Kilometerstand vergleicht (nicht mit den Gesamt-km aus den Fahrten). Die Karte ändert die Farbe: grün (alles in Ordnung), gelb (weniger als 20 % des Intervalls übrig), rot (Zeit für die Wartung).",
        "Wenn noch nicht genügend Daten vorhanden sind (mindestens eine Wartung MIT Kilometerstand und mindestens ein Tankeintrag MIT Kilometerstand an der Zapfsäule), sagt die Karte nur, dass nicht genügend Daten vorhanden sind.",
    ]),
    ("Sonstige Ausgaben", [
        "Für alles, was nicht Kraftstoff/Wartung ist: Parken, Maut, Waschen, Sonstiges - Preis und Notiz. Diese Ausgaben fließen in die NETTO-Berechnung im PDF-Bericht ein.",
    ]),
    ("Fahrerprofil", [
        "Persönliche Daten (Name, Telefon, Lizenz, Kennzeichen, Fahrzeug), die in der Kopfzeile des PDF-Berichts erscheinen, plus Ablaufdatum der Zulassung und Ablaufdatum der Versicherung.",
        "Die Karte unten verfolgt beide Daten: grau (nicht eingegeben), grün (mehr als 30 Tage bis zum Ablauf), gelb (30 Tage oder weniger), rot (bereits abgelaufen - zeigt, wie viele Tage überfällig).",
    ]),
    ("Navigation", [
        "Ein eigenständiger Bildschirm, um schnell die Google-Navigation zu einer beliebigen Adresse zu öffnen - Adresse eingeben und auf 'Navigation öffnen' tippen. Die Routenführung startet automatisch von Ihrer aktuellen GPS-Position.",
    ]),
    ("Google API", [
        "Ein optionales Feld für einen Google-Geocoding-API-Schlüssel. Wenn Sie keinen eingeben, funktioniert die App trotzdem normal - sie nutzt den kostenlosen OpenStreetMap-Dienst, um Adressen zu finden. Der Google-Dienst ist nur in manchen Fällen genauer. Der Schlüssel wird auf console.cloud.google.com erstellt (Geocoding API).",
    ]),
    ("Währung", [
        "Hier wählen Sie nur, wie Preise in der App ANGEZEIGT werden - im Hintergrund wird immer alles in RSD (Dinar) berechnet und gespeichert, unabhängig von dieser Auswahl. Schaltflächen: In RSD anzeigen oder In EUR anzeigen.",
        "Der Wechselkurs wird automatisch einmal täglich aktualisiert (beim ersten Öffnen der App an diesem Tag). Die Schaltfläche Kurs jetzt aktualisieren dient zur manuellen Aktualisierung, z. B. wenn gestern kein Internet verfügbar war.",
    ]),
    ("Datensicherung", [
        "Speichert ALLE Daten (Fahrten, Kraftstoff, Wartung, Ausgaben, Fahrerprofil) in einer einzigen Datei außerhalb der App, unter Downloads/TaksiApp - sie bleibt auf dem Handy, auch nachdem die App gelöscht/neu installiert wurde.",
        "Dateizugriff erlauben - gibt der App die Android-Berechtigung, in diesen öffentlichen Ordner zu schreiben (wird einmal abgefragt).",
        "Die App erstellt beim Start einmal täglich selbst eine neue Sicherung, still, ohne Meldung. Sicherung jetzt speichern ist für eine manuelle Sicherung, wann immer Sie möchten.",
        "Daten aus Sicherung wiederherstellen - lädt alle Daten aus der Sicherungsdatei (wird beim Handywechsel oder nach einer Neuinstallation verwendet).",
        "Sicherung teilen (Drive, WhatsApp...) - öffnet das Teilen-Menü des Systems, um die Sicherungsdatei per E-Mail, Google Drive, WhatsApp usw. an sich selbst zu senden.",
        "Beim Handywechsel: Erstellen Sie auf dem alten eine Sicherung -> übertragen Sie die Datei (WhatsApp/Drive/USB) in denselben Ordner auf dem neuen -> installieren Sie die App -> tippen Sie auf 'Daten wiederherstellen'.",
    ]),
    ("Sicherheit (Fingerabdruck)", [
        "Schaltet die Fingerabdrucksperre der App beim Start ein/aus - ausführlich erklärt am Anfang dieser Anleitung. Der Bildschirm sagt Ihnen auch, ob Ihr Handy überhaupt einen registrierten Fingerabdruck hat.",
    ]),
    ("Anruf / Disponent", [
        "Führen Sie eine Liste von Disponenten mit ihren Schichtzeiten, rufen Sie sie mit einem Tippen an und sehen Sie auf einen Blick, wessen Schicht gerade aktiv ist.",
    ]),
    ("Häufige Probleme", [
        "GPS zeigt keine Strecke an -> prüfen Sie die Standortberechtigung (Telefoneinstellungen -> Apps -> Downtown Taxi -> Berechtigungen -> Standort -> Zulassen) und ob das GPS auf dem Handy eingeschaltet ist.",
        "PDF/Excel lässt sich nicht exportieren -> Einstellungen -> Datensicherung -> 'Dateizugriff erlauben'.",
        "Der Fingerabdruck funktioniert nicht -> prüfen Sie, ob das Handy überhaupt einen Fingerabdruckleser hat und ob in den Systemeinstellungen des Handys ein Fingerabdruck registriert ist - ohne das lässt die App Sie automatisch durch.",
        "Die Wartungserinnerung sagt 'nicht genügend Daten' -> es wird mindestens eine Wartung MIT eingetragenem Kilometerstand und mindestens ein Tankeintrag MIT eingetragenem Kilometerstand an der Zapfsäule benötigt.",
        "Die Preise stimmen nicht mit den neuen Tarifen überein -> neue Preise gelten nur für Fahrten, die NACH der Änderung ERFASST wurden, sie ändern bereits gespeicherte Fahrten nicht rückwirkend.",
    ]),
]

RU_SADRZAJ = [
    ("Первый запуск и блокировка по отпечатку пальца", [
        "При первом открытии приложения сразу появляется главный экран - блокировка по отпечатку пальца по умолчанию выключена.",
        "Если включить Безопасность (отпечаток пальца) в Настройках, то при следующем запуске приложения вы сначала увидите экран с просьбой приложить палец к сенсору. Без успешного распознавания отпечатка дальше пройти нельзя.",
        "Если в телефоне нет сканера отпечатков или ни один отпечаток не зарегистрирован в системных настройках телефона, приложение автоматически пропускает вас дальше и лишь сообщает причину - навсегда заблокироваться в приложении нельзя.",
        "Блокировка проверяется только при запуске приложения (холодный старт), а не при каждом возвращении из фона - поэтому она не прервёт вас посреди поездки (например, если вам позвонят).",
        "Включается/выключается в Настройки -> Безопасность (отпечаток пальца).",
    ]),
    ("Главный экран", [
        "GPS-поездка (авто) - открывает автоматическое отслеживание поездки по GPS.",
        "Начать поездку (вручную) - открывает Калькулятор для ручного ввода поездки.",
        "История поездок - открывает Историю, список всех поездок с поиском.",
        "Отчёт - обзор заработка по дням/неделям/месяцам.",
        "Профиль водителя - личные данные и данные об автомобиле.",
        "Настройки - все остальные меню приложения.",
        "Инструкция - экран, который вы сейчас читаете.",
    ]),
    ("GPS-поездка (автоматический ввод) - самый частый вариант", [
        "1. По желанию, перед нажатием 'Начать поездку' можно ввести адрес назначения - тогда сразу после начала поездки откроется навигация Google с пошаговым маршрутом до этого адреса.",
        "2. Нажмите НАЧАТЬ ПОЕЗДКУ. При первом запуске приложение запросит разрешение на определение местоположения, затем начнёт измерять расстояние в реальном времени.",
        "3. Во время поездки на экране отображаются адрес посадки, пройденные километры, длительность и текущая цена.",
        "4. Когда приедете, нажмите ЗАВЕРШИТЬ ПОЕЗДКУ - приложение само найдёт текущий адрес и сохранит поездку в Историю.",
        "GPS-поездка использует только Стандартный или Ночной тариф, в зависимости от переключателя в Настройки -> Ночной тариф (он не переключается автоматически по времени). Для Выходных или Трансфера в аэропорт используйте ручной ввод (Калькулятор).",
        "Приложение отфильтровывает плохую точность GPS - игнорирует точки с точностью хуже 50 м, микро-скачки менее 10 м и нереалистичные скачки скорости свыше 180 км/ч, чтобы расстояние не было ложно завышено.",
        "Если GPS не смог измерить расстояние, на экране завершения поездки есть поле для ручного ввода км в качестве запасного варианта.",
    ]),
    ("Калькулятор (ручной ввод поездки)", [
        "Для поездок, которые вы не отслеживаете по GPS в реальном времени, или когда нужен тариф, который GPS-поездка не поддерживает (Выходные, Трансфер в аэропорт).",
        "1. Выберите тариф в выпадающем меню.",
        "2. Введите расстояние - цена сразу пересчитывается ниже.",
        "3. Адрес отправления, адрес назначения и примечание необязательны.",
        "4. Нажмите Сохранить поездку.",
        "Если включён Ночной тариф, при открытии экран автоматически предлагает Ночной тариф - для конкретной поездки его всё равно можно изменить вручную.",
    ]),
    ("История (список поездок)", [
        "Показывает все сохранённые поездки, новые сверху - дата, время начала/конца, расстояние, тариф, адреса и цена.",
        "Поиск можно комбинировать: текст (адреса и примечание), период (дата с / дата по, формат ГГГГ-ММ-ДД) и диапазон цены (цена от / цена до). Нажатие Найти также показывает итог по результатам. Сбросить возвращает полный список.",
        "У каждой поездки две кнопки: Изменить (открывает Калькулятор с заполненными данными) и Удалить (безвозвратно удаляет поездку, без подтверждения - осторожно).",
    ]),
    ("Отчёт о заработке", [
        "Три карточки с итогами: Сегодня (список сегодняшних поездок + итог), Эта неделя (общий заработок за текущую неделю), Этот месяц (общий заработок за текущий месяц).",
        "Отсюда кнопка Экспорт в PDF ведёт на экран экспорта отчёта.",
    ]),
    ("График заработка", [
        "Наглядное представление во времени. Период: По дням / По неделям / По месяцам. Показатель: Заработок или Километры.",
        "Стрелки < и > перемещают по предыдущим/следующим периодам. Нажатие на точку графика показывает точную сумму за этот день/неделю/месяц.",
        "Под графиком: дополнительная статистика и, при наличии данных, обзор расходов на топливо и обслуживание за этот период.",
        "Открывается через Настройки -> График заработка.",
    ]),
    ("Экспорт отчётов (PDF / Excel)", [
        "Экран Отчёт -> Экспорт в PDF. Выберите тип периода (По дням, По неделям, По месяцам, Полугодие, Год) и введите период в требуемом формате.",
        "Экспорт в PDF - создаёт PDF для печати/просмотра с данными водителя, обслуживанием, прочими расходами, расходом топлива, всеми поездками и итоговой строкой в конце (количество поездок, всего км, валовый заработок и ЧИСТАЯ ПРИБЫЛЬ = заработок - топливо - обслуживание - прочие расходы).",
        "Экспорт в Excel - создаёт файл Excel с 5 листами и формулами, предназначенный для бухгалтера: его можно открыть в Excel и самостоятельно суммировать/фильтровать.",
        "Оба файла сохраняются в Downloads/TaksiApp на телефоне (в ту же папку, что и резервная копия) - требуется разрешение 'доступ ко всем файлам' (Настройки -> Резервная копия данных).",
    ]),
    ("Цены / Тарифы", [
        "Меняет цену за километр для всех четырёх тарифов (Стандартный, Ночной, Выходные, Трансфер в аэропорт) и плату за посадку.",
        "Нажатие Сохранить цены применяет их ко ВСЕМ будущим поездкам - уже сохранённые поездки задним числом не меняются.",
    ]),
    ("Ночной тариф (переключатель)", [
        "Один переключатель: когда он включён, и Калькулятор, и GPS-поездка автоматически используют Ночной тариф (в Калькуляторе тариф для отдельной поездки всё равно можно изменить вручную).",
        "Он не включается сам по времени - вы включаете и выключаете его вручную, когда начинается/заканчивается ваша ночная смена.",
    ]),
    ("Топливо", [
        "Журнал заправок: вид (Бензин/Газ (LPG)), количество (литры), цена, пробег на заправке (необязательно, но ВАЖНО - без него нельзя рассчитать расход, а напоминание об обслуживании не работает), примечание.",
        "Вверху экрана видна общая сумма расходов на топливо (отдельно бензин, отдельно газ). Расход в л/100км автоматически рассчитывается по разнице пробега между двумя последовательными заправками, для которых указан пробег.",
    ]),
    ("Обслуживание авто", [
        "Журнал обслуживания (замена масла, тормоза и т. д.) - вид, цена, пробег, примечание.",
        "Напоминание об обслуживании: вы задаёте интервал (например, каждые 10000 км), а приложение само отслеживает, сколько пройдено с последнего обслуживания - сравнивая пробег последнего обслуживания с самым свежим пробегом, указанным в разделе Топливо (а не с общими км по поездкам). Карточка меняет цвет: зелёная (всё в порядке), жёлтая (осталось меньше 20 % интервала), красная (пора на обслуживание).",
        "Если данных пока недостаточно (нужна хотя бы одна запись об обслуживании С пробегом и хотя бы одна запись о топливе С пробегом на заправке), карточка просто сообщает, что данных недостаточно.",
    ]),
    ("Прочие расходы", [
        "Для всего, что не относится к топливу/обслуживанию: Парковка, Платные дороги, Мойка, Прочее - цена и примечание. Эти расходы учитываются при расчёте ЧИСТОЙ ПРИБЫЛИ в PDF-отчёте.",
    ]),
    ("Профиль водителя", [
        "Личные данные (имя, телефон, лицензия, номерной знак, автомобиль), которые отображаются в шапке PDF-отчёта, а также дата окончания регистрации и дата окончания страховки.",
        "Карточка внизу отслеживает обе даты: серая (не введена), зелёная (до окончания больше 30 дней), жёлтая (30 дней или меньше), красная (уже истекла - показывает, на сколько дней просрочено).",
    ]),
    ("Навигация", [
        "Отдельный экран для быстрого открытия навигации Google до любого адреса - введите адрес и нажмите 'Открыть навигацию'. Пошаговый маршрут автоматически строится от вашей текущей GPS-позиции.",
    ]),
    ("Google API", [
        "Необязательное поле для API-ключа Google Geocoding. Если его не вводить, приложение всё равно работает нормально - для поиска адресов используется бесплатный сервис OpenStreetMap. Сервис Google лишь точнее в некоторых случаях. Ключ создаётся на console.cloud.google.com (Geocoding API).",
    ]),
    ("Валюта", [
        "Здесь выбирается только то, в какой валюте цены ОТОБРАЖАЮТСЯ в приложении - в фоне всё всегда рассчитывается и хранится в RSD (динарах), независимо от этого выбора. Кнопки: Показывать в RSD или Показывать в EUR.",
        "Курс валюты обновляется автоматически раз в день (при первом открытии приложения в этот день). Кнопка Обновить курс сейчас нужна для ручного обновления, например если вчера не было интернета.",
    ]),
    ("Резервная копия данных", [
        "Сохраняет ВСЕ данные (поездки, топливо, обслуживание, расходы, профиль водителя) в один файл вне самого приложения, в Downloads/TaksiApp - он остаётся на телефоне даже после удаления/переустановки приложения.",
        "Разрешить доступ к файлам - даёт приложению разрешение Android записывать в эту общедоступную папку (запрашивается один раз).",
        "Приложение само делает свежую копию раз в день при запуске, тихо, без сообщений. Сохранить копию сейчас нужна для ручной копии, когда вы захотите.",
        "Восстановить данные из копии - загружает все данные из файла копии (используется при смене телефона или после переустановки).",
        "Поделиться копией (Drive, WhatsApp...) - открывает системное меню обмена, чтобы отправить файл копии себе по почте, в Google Drive, WhatsApp и т. д.",
        "При смене телефона: сделайте копию на старом -> перенесите файл (WhatsApp/Drive/USB) в ту же папку на новом -> установите приложение -> нажмите 'Восстановить данные'.",
    ]),
    ("Безопасность (отпечаток пальца)", [
        "Включает/выключает блокировку приложения по отпечатку пальца при запуске - подробно описано в начале этой инструкции. Экран также сообщает, есть ли на вашем телефоне вообще зарегистрированный отпечаток.",
    ]),
    ("Звонок / Диспетчер", [
        "Ведите список диспетчеров со временем их смен, звоните им одним нажатием и с первого взгляда видите, чья смена сейчас активна.",
    ]),
    ("Частые проблемы", [
        "GPS не показывает расстояние -> проверьте разрешение на местоположение (Настройки телефона -> Приложения -> Downtown Taxi -> Разрешения -> Местоположение -> Разрешить) и включён ли GPS на телефоне.",
        "Не удаётся экспортировать PDF/Excel -> Настройки -> Резервная копия данных -> 'Разрешить доступ к файлам'.",
        "Отпечаток пальца не работает -> проверьте, есть ли на телефоне сканер отпечатков и зарегистрирован ли отпечаток в системных настройках телефона - иначе приложение автоматически пропускает вас дальше.",
        "Напоминание об обслуживании пишет 'недостаточно данных' -> нужна хотя бы одна запись об обслуживании С указанным пробегом и хотя бы одна запись о топливе С указанным пробегом на заправке.",
        "Цены не совпадают с новыми тарифами -> новые цены действуют только для поездок, ВВЕДЁННЫХ ПОСЛЕ изменения, и не меняют задним числом уже сохранённые поездки.",
    ]),
]


# ============================================================
# Sve jezike na jednom mestu
# ============================================================

SADRZAJ = {
    "sr": SR_SADRZAJ,
    "en": EN_SADRZAJ,
    "it": IT_SADRZAJ,
    "fr": FR_SADRZAJ,
    "de": DE_SADRZAJ,
    "ru": RU_SADRZAJ,
}

# Podnaslov ispod naslova u PDF verziji uputstva
PODNASLOV = {
    "sr": "Taxi Zoran - aplikacija za evidenciju voznji i troskova",
    "en": "Taxi Zoran - app for recording rides and expenses",
    "it": "Taxi Zoran - app per la registrazione di corse e spese",
    "fr": "Taxi Zoran - application de suivi des courses et des dépenses",
    "de": "Taxi Zoran - App zur Erfassung von Fahrten und Ausgaben",
    "ru": "Taxi Zoran - приложение для учёта поездок и расходов",
}
