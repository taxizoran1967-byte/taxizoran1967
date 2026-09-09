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

UPUTSTVO_SADRZAJ = [
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

    for naslov_sekcije, pasusi in UPUTSTVO_SADRZAJ:
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
    tekst_status = StringProperty(
        "Sve opcije aplikacije, objasnjene jedna po jedna."
    )

    def on_pre_enter(self, *args):
        from kivy.factory import Factory
        kontejner = self.ids.lista_uputstvo
        if not kontejner.children:
            for naslov_sekcije, pasusi in UPUTSTVO_SADRZAJ:
                sekcija = Factory.SekcijaUputstva(
                    naslov=naslov_sekcije,
                    tekst="\n\n".join(pasusi),
                )
                kontejner.add_widget(sekcija)

    def izvezi_pdf(self):
        if not _IMA_DOZVOLU_SVI_FAJLOVI():
            _PRIKAZI_POPUP(
                "Nedostaje dozvola",
                "Idi u Podesavanja -> Backup podataka i klikni "
                "'Odobri pristup fajlovima', pa se vrati ovde.",
                size_hint=(0.88, 0.4),
            )
            return
        try:
            folder = _PUTANJA_BACKUP_FOLDERA()
            os.makedirs(folder, exist_ok=True)
            putanja = os.path.join(folder, "uputstvo_za_upotrebu.pdf")
            generisi_uputstvo_pdf(putanja)
            _PRIKAZI_POPUP(
                "Sacuvano",
                f"Uputstvo sacuvano kao PDF u:\n{putanja}",
                size_hint=(0.85, 0.4),
            )
        except Exception as e:
            _PRIKAZI_POPUP(
                "Greska", f"Pravljenje PDF-a nije uspelo:\n{e}", size_hint=(0.88, 0.45)
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
            text: "Uputstvo za upotrebu"

        NavBar:
            RoundButton:
                label_text: "Pocetna"
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
            label_text: "Izvezi u PDF"
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
