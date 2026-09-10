# 🚕 Taksi Zoran App

**Mobilna aplikacija za taksistu** — GPS praćenje vožnji, upravljanje tarifama, praćenje troškova (gorivo, servis), generisanje PDF/CSV izveštaja i dnevni/nedeljni/mesečni pregled zarade.

---

## ✨ Glavne funkcije

### 📍 Praćenje vožnji
- **GPS vožnja (automatski)** — prati GPS u realnom vremenu, automatski računa kilometražu i cenu
- **Ručni unos** — kalkulator za vožnje koje se ne prate GPS-om
- **Evidencija** — pregled svih vožnji sa pretragom po datumu, tekstu, ceni
- **Izmena/brisanje** — editujem ili brišem postojeće vožnje

### 💰 Tarife (4 tipa)
- Osnovna (07-22h)
- Noćna (22-07h) — sa prekidačem za brzo uključivanje
- Vikend
- Aerodromski transfer

Svaka tarifa ima svoju cenu po km + start taksu (menja se u app-u bez rebilda).

### 📊 Izveštaji i statistika
- **Dnevni pregled** — vožnje + zarada današnjeg dana
- **Nedeljni pregled** — zarada za tekuću nedelju
- **Mesečni pregled** — zarada za tekući mesec
- **Grafikon zarade** — vizuelni prikaz zarade/km po danima/nedelama/mesecima
- **PDF/CSV izvoz** — kompletan izveštaj sa svim podataka za štampu/Excel

### ⛽ Upravljanje troškovima
- **Gorivo** — evidencija sipanja (benzin/TNG), automatski računa potrošnju l/100km
- **Servis** — evidencija servisa sa podsetnicima po km intervalu (zeleno/žuto/crveno status)
- **Ostali troškovi** — parking, putarina, pranje itd.

### 🔐 Sigurnost
- **Zaključavanje otiskom prsta** — biometrijsko zaključavanje pri pokretanju app-a
- **Backup** — čuvanje i vraćanje svih podataka u `Downloads/TaksiApp/`

### 🌍 Dodatno
- **Navigacija** — brzo otvaranje Google Maps-a
- **Valuta** — prikaz u RSD ili EUR (kurs se osvežava dnevno)
- **Profil vozača** — lični podaci, datumi registracije/osiguranja sa obaveštenjima

---

## 🚀 Brz start

### Za razvoj (Desktop)

**Preduslov:** Python 3.8+

```bash
# 1. Kloniraj repozitorijum
git clone https://github.com/taxizoran1967-byte/taxizoran1967.git
cd taxizoran1967

# 2. Instaliraj zavisnosti
pip install -r requirements.txt

# 3. Pokreni aplikaciju
python3 main.py
```

### Za Android (APK)

**Preduslov:** Linux sa Buildozer-om

```bash
# 1. Instaliraj Buildozer
sudo apt-get install buildozer cython python3-dev

# 2. Prvi build (skida sve - može biti dugačko)
buildozer android debug

# 3. Kasnije reprebuild-ove
buildozer android debug

# APK se nalazi u: bin/taksiapp-0.1-debug.apk
# Instalacija: adb install bin/taksiapp-0.1-debug.apk
```

---

## 📁 Struktura projekta

```
taxizoran1967/
├── main.py                          # Glavna aplikacija, početni ekran
├── README.md                        # Ovaj fajl
├── UPUTSTVO.md                      # Detaljno uputstvo za korisnike
├── buildozer.spec                   # Android build konfiguracija
├── requirements.txt                 # Python zavisnosti
├── .gitignore                       # Git ignore pravila
│
├── ekrani/                          # UI ekrani (16 screen-ova)
│   ├── ekran_backup.py              # Backup podataka
│   ├── ekran_cenovnik.py            # Upravljanje tarifama/cenama
│   ├── ekran_dispeceri.py           # Dispečer/pozivi (Stub - "Uskoro...")
│   ├── ekran_evidencija.py          # Pretraga i pregled vožnji
│   ├── ekran_google_api.py          # Google Geocoding API ključ
│   ├── ekran_gorivo.py              # Evidencija sipanja goriva
│   ├── ekran_gps_voznja.py          # GPS praćenje vožnje (GLAVNI)
│   ├── ekran_izvestaj.py            # Dnevni/nedeljni/mesečni pregled
│   ├── ekran_izvoz.py               # Izvoz PDF/CSV izveštaja
│   ├── ekran_kalkulator.py          # Ručni unos vožnje
│   ├── ekran_navigacija.py          # Google navigacija
│   ├── ekran_profil.py              # Podaci o vozaču
│   ├── ekran_servis.py              # Evidencija servisa + podsetnik
│   ├── ekran_sigurnost.py           # Zaključavanje otiskom prsta
│   ├── ekran_troskovi.py            # Ostali troškovi
│   ├── ekran_uputstvo.py            # In-app uputstvo
│   └── ekran_valuta.py              # RSD/EUR konverzija
│
├── servisi/                         # Poslovni sloj (backend logika)
│   ├── biometrics.py                # Biometrijsko otključavanje (Java bridge)
│   ├── database.py                  # SQLite baza podataka
│   ├── grafik_zarade.py             # Grafikon zarade
│   ├── validators.py                # Validacija ulaza ✨ NOVO
│   └── api_helper.py                # Safe API pozivi ✨ NOVO
│
├── java-src/                        # Java kod za biometriju na Androidu
├── assets/                          # Pozadine, ikone, fontovi
├── p4a-recipes/                     # Python 4 Android recepti
└── androidstorage4kivy/             # Android storage helper
```

---

## 🛠️ Tehnički detalji

| Aspekt | Vrednost |
|--------|----------|
| **Jezik** | Python 3 |
| **Framework** | Kivy (UI za mobilne/desktop) |
| **Baza** | SQLite3 (lokalna, na telefonu) |
| **Android API** | 33 (min 21) |
| **Architektura** | ARM64-v8a |
| **Build sistem** | Buildozer |
| **Izveštaji** | PDF (ReportLab) |

### Ključne biblioteke
- `kivy` — UI framework
- `sqlite3` — baza podataka
- `plyer` — pristup hardware-u (GPS, biometrija)
- `reportlab` — PDF generisanje
- `pillow` — obrada slika
- `certifi` — SSL/HTTPS

---

## 📊 Gde se čuvaju podaci?

### SQLite baza
```
Lokacija: Android app-specific storage / Desktop: app_data_dir
Fajl: taksi_evidencija.db
Tabela: voznje (id, datum, vreme, od_adresa, do_adresa, km, tarifa, cena...)
```

### JSON fajlovi (app-specific storage)
- `cene.json` — tarife i start taksa
- `gorivo.json` — evidencija sipanja
- `servis.json` — evidencija servisa
- `troskovi.json` — ostali troškovi
- `vozac.json` — profil vozača
- `kurs.json` — EUR→RSD kurs

### Backup (javni folder)
```
Lokacija: Downloads/TaksiApp/
Sadrži: sve vožnje, troškovi, profil - backup.json
Ostaje čak i posle deinstalacije app-a
```

---

## 🐛 Poznati problemi

| Problem | Status | Prioritet |
|---------|--------|----------|
| `main.py` je 1350 linija (trebalo bi rastavljanje) | ⏳ Planirano | 🔴 Visok |
| Nema unit testova | ❌ Nedostaje | 🟡 Srednji |
| Backup bez šifrovanja | ⚠️ Sigurnosni rizik | 🔴 Visok |
| Nema error handling-a za API | ⚠️ Može da padne | 🟡 Srednji |
| Dispečer ekran je stub ("Uskoro...") | ⏳ Nije implementirano | 🟢 Nizak |

---

## 📝 Kako da doprinesiš?

1. **Fork** repozitorijum
2. **Kreiraj feature granu:** `git checkout -b feature/tvoja-funkcija`
3. **Radi** — dodaj kod sa docstring-ima
4. **Commit:** `git commit -m "feat: opis šta si dodao"`
5. **Push:** `git push origin feature/tvoja-funkcija`
6. **Pull Request** — opis šta i zašto

### Coding style
- Indentacija: **4 space-a**
- Nazivi: **Srpski jezik** (varijable, funkcije, komentari)
- Docstring-i: **Obavezni za nove funkcije**
- Testovi: **Preporučeni za novu logiku**

---

## 📜 Licenca

(Nije specificirana u kodu - razmotri dodavanje)

---

## 📧 Kontakt

- **Autor:** taxizoran1967-byte
- **GitHub:** https://github.com/taxizoran1967-byte/taxizoran1967
- **Verzija:** 0.1

---

**Zadnja ažuriranja:** Septembar 2026  
**Status:** Aktivna razvoja