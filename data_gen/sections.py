"""Działy podstawy programowej historii (LO, podstawa 2018, zakres podstawowy i rozszerzony).

Tytuły zgodne z informatorem CKE (formuła 2023). Przy XXVIII, XLIV, XLIX oraz LIX–LX
dopisano braki wskazane w specyfikacji: kultura oświecenia, kultura II RP, Zagłada,
III RP. Polityka zagraniczna II RP jest wymagana jako podtemat działu XLII.
"""

SECTIONS = [
    "II. Pradzieje i historia starożytnego Wschodu",
    "III. Świat starożytnych Greków",
    "IV. Społeczeństwo, życie polityczne i kultura starożytnego Rzymu",
    "V. Bizancjum i świat islamu",
    "VI. Europa wczesnego średniowiecza",
    "VII. Europa w okresie krucjat",
    "VIII. Gospodarcze i społeczne realia średniowiecznej Europy",
    "IX. Polska w okresie wczesnopiastowskim",
    "X. Polska w okresie rozbicia dzielnicowego",
    "XI. Europa późnego średniowiecza",
    "XII. Polska w XIV i XV w.",
    "XIII. Kultura średniowiecza",
    "XIV. Odkrycia geograficzne i europejski kolonializm doby nowożytnej",
    "XV. Czasy renesansu",
    "XVI. Reformacja i jej skutki",
    "XVII. Europa w XVI i XVII w.",
    "XVIII. Państwo polsko-litewskie w czasach ostatnich Jagiellonów",
    "XIX. Powstanie Rzeczypospolitej Obojga Narodów",
    "XX. Pierwsze wolne elekcje i ich następstwa",
    "XXI. Renesans w Polsce",
    "XXII. Polityka wewnętrzna i zagraniczna Rzeczypospolitej Obojga Narodów",
    "XXIII. Ustrój, społeczeństwo i kultura Rzeczypospolitej Obojga Narodów",
    "XXIV. Europa w dobie oświecenia",
    "XXV. Rewolucje XVIII w.",
    "XXVI. Rzeczpospolita w XVIII w. (od czasów saskich do Konstytucji 3 maja)",
    "XXVII. Upadek Rzeczypospolitej (wojna z Rosją i powstanie kościuszkowskie)",
    "XXVIII. Kultura polskiego oświecenia",
    "XXIX. Epoka napoleońska",
    "XXX. Europa i świat po kongresie wiedeńskim",
    "XXXI. Ziemie polskie i ich mieszkańcy w latach 1815–1848",
    "XXXII. Powstanie styczniowe i jego następstwa",
    "XXXIII. Europa i świat w II połowie XIX i na początku XX w.",
    "XXXIV. Przemiany gospodarcze i społeczne. Nowe prądy ideowe",
    "XXXV. Ziemie polskie pod zaborami w II połowie XIX i na początku XX w.",
    "XXXVI. Kultura i nauka polska w II połowie XIX i na początku XX w.",
    "XXXVII. I wojna światowa",
    "XXXVIII. Sprawa polska w przededniu i podczas I wojny światowej",
    "XXXIX. Europa i świat po I wojnie światowej",
    "XL. Narodziny i rozwój totalitaryzmów w okresie międzywojennym",
    "XLI. Walka o odrodzenie państwa polskiego po I wojnie światowej",
    "XLII. Dzieje polityczne II Rzeczypospolitej",
    "XLIII. Społeczeństwo i gospodarka II Rzeczypospolitej",
    "XLIV. Kultura i nauka w II Rzeczypospolitej",
    "XLV. Świat na drodze do II wojny światowej",
    "XLVI. Wojna obronna Polski w 1939 r.",
    "XLVII. II wojna światowa i jej etapy",
    "XLVIII. Polska pod okupacją niemiecką i sowiecką",
    "XLIX. Zagłada Żydów na ziemiach polskich i postawy społeczeństwa wobec Holokaustu",
    "L. Działalność władz RP na uchodźstwie i w okupowanym kraju",
    "LI. Świat po II wojnie światowej. Początek zimnej wojny",
    "LII. Dekolonizacja, integracja i nowe konflikty",
    "LIII. Przemiany cywilizacyjne na świecie",
    "LIV. Świat na przełomie tysiącleci",
    "LV. Proces przejmowania władzy przez komunistów w Polsce (1944–1948)",
    "LVI. Stalinizm w Polsce i jego erozja",
    "LVII. Polska w latach 1957–1981",
    "LVIII. Dekada 1981–1989",
    "LIX. Narodziny III Rzeczypospolitej",
    "LX. Polska i świat na przełomie XX i XXI wieku",
]

BY_ROMAN = {}
for _s in SECTIONS:
    _rom, _rest = _s.split(".", 1)
    BY_ROMAN[_rom.strip()] = _s


def canon_section(raw):
    """Zwraca kanoniczną nazwę działu albo pusty string."""
    if not raw:
        return ""
    text = " ".join(str(raw).replace("–", "-").split())
    if text in BY_ROMAN.values():
        return text
    head = text.split(".", 1)[0].strip().upper()
    head = head.replace(" ", "")
    if head in BY_ROMAN:
        return BY_ROMAN[head]
    for rom, full in BY_ROMAN.items():
        if text.lower().startswith(full.lower()[:24]):
            return full
    return ""
