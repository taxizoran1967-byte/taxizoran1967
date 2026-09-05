
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
# uvozimo VEC POSTOJECI recept objekat iz p4a i menjamo mu samo
# atribut "url" da pokazuje na SourceForge mirror, koji freetype
# projekat i dalje zvanicno odrzava. Sve ostalo (verzija, patch-evi,
# build_arch metoda, zavisnosti) ostaje potpuno isto kao u originalu.
#
# Da bi ovaj fajl bio pronadjen, u buildozer.spec mora postojati:
#   p4a.local_recipes = ./p4a-recipes
# (vidi izmenu u buildozer.spec)

from pythonforandroid.recipes.freetype import recipe as _izvorni_recept

# Originalni URL (za referencu, ne koristi se):
#   https://download.savannah.gnu.org/releases/freetype/freetype-{version}.tar.gz
#
# Novi URL - zvanicni SourceForge mirror, isti fajl, ista verzija:
_izvorni_recept.url = (
    "https://downloads.sourceforge.net/project/freetype/freetype2/"
    "{version}/freetype-{version}.tar.gz"
)

recipe = _izvorni_recept
