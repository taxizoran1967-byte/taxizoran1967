# Lokalni p4a recept koji GAZI ugradjeni "freetype" recept.
#
# ZASTO POSTOJI OVAJ FAJL:
# Ugradjeni p4a recept skida freetype izvorni kod sa
# https://download.savannah.gnu.org/... - taj server je hronicno
# nepouzdan (cesto vraca 502/504 greske), sto je uzrok povremenog
# padanja GitHub Actions build-a na koraku "Downloading freetype".
#
# STA OVAJ FAJL RADI:
# Ne pise se ceo recept iznova (rizicno - izgubili bismo patch-eve i
# configure flagove koje ugradjeni recept koristi). Umesto toga,
# PRAVIMO PODKLASU vec postojece recept klase i u njoj definisemo
# svoj "url" kao obicno polje. To automatski "pregazi" atribut iz
# roditeljske klase - bez obzira da li je tamo obicna promenljiva
# ili (kao u ovoj verziji p4a-a) @property koja se racuna u kodu i
# ne moze se direktno menjati spolja. Sve ostalo (verzija, patch-evi,
# build_arch metoda, zavisnosti) ostaje potpuno isto kao u originalu,
# jer nasledjujemo pravu klasu, ne prepisujemo je.
#
# Da bi ovaj fajl bio pronadjen, u buildozer.spec mora postojati:
#   p4a.local_recipes = ./p4a-recipes
# (vidi izmenu u buildozer.spec)

from pythonforandroid.recipes.freetype import recipe as _izvorni_recept

# Uzimamo STVARNU klasu originalnog recepta (ne moramo da znamo njeno
# ime napamet - ovo radi bez obzira kako se klasa zapravo zove).
_OriginalnaKlasa = type(_izvorni_recept)


class _FreetypeMirrorRecipe(_OriginalnaKlasa):
    # Originalni URL (za referencu, ne koristi se):
    #   https://download.savannah.gnu.org/releases/freetype/freetype-{version}.tar.gz
    #
    # Novi URL - zvanicni SourceForge mirror, isti fajl, ista verzija.
    # Definisan kao obicno polje klase - ovo pregazi @property iz
    # roditeljske klase.
    url = (
        "https://downloads.sourceforge.net/project/freetype/freetype2/"
        "{version}/freetype-{version}.tar.gz"
    )


recipe = _FreetypeMirrorRecipe()
