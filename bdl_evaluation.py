"""Kennzahlen, Verdikt-Logik (reine Funktionen: (Art, Text)) und Analysen der Live-Ansichten.

Jedes Verdikt der App ist eine Funktion `verdict_*(...) -> (Art, Text)`; die App ruft `getattr(st, Art)(Text)`, `tests/test_verdicts.py` prüft Schwellen und jede Zahl
im Text an handgesetzten Werten. Die Analysen (`analyse_*`) rechnen mit dem Kern und geben einfache Daten zurück (für `st.cache_data`). Die festen Messreihen (Bänder) und ihre
Zusammenfassungen stehen in `bdl_baender.py`."""

from dataclasses import dataclass

import bdl_algorithm as A
import bdl_colgen as G
import bdl_constants as C
from bdl_scenario import HAND_DUAL, Instanz, einzelfahrt_preise, handbeispiel, instanz_aus_seed

NBSP = " "
EPS_RC = 1e-6


# --- Zahlenformat (deutsch) ---------------------------------------------------------------------------------------------------------------

def zahl(x, stellen: int = 0) -> str:
    """Deutsche Schreibweise: Dezimalkomma, geschütztes Leerzeichen als Tausendertrenner; ganze Zahlen ohne Nachkommastellen; „-0“ wird zu „0“."""
    if stellen == 0:
        if isinstance(x, float):
            x = int(round(x))
        text = f"{x:,}"
    else:
        text = f"{round(x, stellen) + 0.0:,.{stellen}f}"
    return text.replace(",", NBSP).replace(".", ",")


def zahl_kurz(x: float) -> str:
    """Ganze Werte ohne, sonst bis zu zwei Nachkommastellen (Kosten und Dualpreise im Handbeispiel)."""
    if abs(x - round(x)) < 1e-9:
        return zahl(int(round(x)))
    return zahl(x, 2)


def verhaeltnis_text(x: float) -> str:
    """Verhältnis zum einseitigen Verfahren mit zwei Stellen und Komma („0,27“)."""
    return zahl(x, 2)


def prozent(x: float, stellen: int = 0) -> str:
    """Ein Anteil (0,28) als Prozent mit Komma („28 %“)."""
    return zahl(100.0 * x, stellen) + NBSP + "%"


def prozent_genau(x: float) -> str:
    """Wie `prozent`, aber knapp unter oder über 100 % mit einer Stelle („99,9 %“): „100 %“ soll nur heißen, dass beide Verfahren gleich viele Labels erzeugen."""
    if x != 1.0 and round(100.0 * x) == 100:
        return prozent(x, 1)
    return prozent(x)


def weg_text(weg) -> str:
    return "-".join(str(v) for v in weg) if weg else "leer"


def menge_text(m: int) -> str:
    """Gedächtnis (Bitmaske) als Mengenschreibweise."""
    return "{" + ", ".join(str(i) for i in A.menge_aus_maske(m)) + "}"


def quote(a, b) -> float:
    """a / b; 0 bei b = 0 (kein Nenner)."""
    return 0.0 if not b else a / b


# --- Einstellungen ---------------------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Settings:
    hand_m: int = C.DEFAULT_HAND_M
    n: int = C.DEFAULT_N
    breite: int = C.DEFAULT_BREITE
    typ: str = "zufaellig"
    q: int = C.KAPAZITAET
    k: int = C.DEFAULT_K
    runde: int = C.DEFAULT_RUNDE
    halbweg_pct: int = C.DEFAULT_HALBWEG
    seed: int = C.DEFAULT_SEED

    @property
    def halbweg(self) -> float:
        """Halbweg der Kundeninstanz in Zeiteinheiten (Anteil des Horizonts)."""
        return C.HORIZONT * self.halbweg_pct / 100.0


def settings_aus_preset(p: dict) -> Settings:
    """Die Einstellungen einer Voreinstellung (Schlüssel wie in `bdl_constants.PRESETS`)."""
    return Settings(p["hand_m"], p["n"], p["breite"], p["typ"], p["q"], p["k"], p["runde"], p["halbweg"], p["seed"])


# --- Handbeispiel -------------------------------------------------------------------------------------------------------------------------------

def etikett(vorwaerts: bool, nr: int, einseitig: bool = False) -> str:
    """Name eines Labels: F00 (vorwärts, bidirektional), B00 (rückwärts), E00 (einseitiges Verfahren)."""
    return f"{'E' if einseitig else ('F' if vorwaerts else 'B')}{nr:02d}"


def status_text(seite: A.Seite, nr: int, einseitig: bool = False) -> str:
    """Schicksal eines Labels: „Start“, „behalten“, „dominiert von X“ (beim Erzeugen) oder „verdrängt von X“ (später von einem neueren Label)."""
    if nr == 0:
        return "Start"
    if not seite.tot[nr]:
        return "behalten"
    von = seite.dominiert_von[nr]
    name = etikett(seite.vorwaerts, von, einseitig)
    return f"dominiert von {name}" if von < nr else f"verdrängt von {name}"


def label_zeilen(seite: A.Seite, einseitig: bool = False) -> list:
    """Tabellenzeilen aller erzeugten Labels einer Richtung, in der Reihenfolge der Erzeugung."""
    zeilen = []
    for nr, lab in enumerate(seite.labels):
        eltern = "-" if lab[A.L_E] < 0 else etikett(seite.vorwaerts, lab[A.L_E], einseitig)
        zeilen.append({"Label": etikett(seite.vorwaerts, nr, einseitig), "Kunde": str(lab[A.L_K]) if lab[A.L_K] else "Depot", ("Beginn t" if seite.vorwaerts else "spätester Beginn T"): zahl_kurz(lab[A.L_Z]),
                       "reduzierte Kosten": zahl_kurz(lab[A.L_C]), "Last": zahl_kurz(lab[A.L_Q]), "gesperrt": menge_text(lab[A.L_M]),
                       ("aus" if seite.vorwaerts else "weiter zu"): eltern, "Schicksal": status_text(seite, nr, einseitig)})
    return zeilen


def paar_zeilen(inst: Instanz, vor: A.Seite, rueck: A.Seite) -> list:
    """Alle Paare (lebendes Vorwärtslabel in i, lebendes Rückwärtslabel in j) über jede Kante (i, j) mit Labels auf beiden Seiten, mit dem Ergebnis der Paarprüfung.

    Kanten, die die Vorprüfung der Zeit überspringt (das früheste Vorwärtslabel kommt schon zu spät für das späteste Rückwärts-T), stehen mit dem Vermerk „Kante übersprungen“."""
    zeilen = []
    for i in range(inst.n + 1):
        fl = vor.lebend[i]
        if not fl:
            continue
        s = inst.svc if i != 0 else 0.0
        tmin = min(vor.labels[x][A.L_Z] for x in fl)
        for j in range(inst.n + 1):
            bl = rueck.lebend[j]
            if i == j or not bl:
                continue
            uebersprungen = tmin + s + inst.d[i][j] > max(rueck.labels[x][A.L_Z] for x in bl) + A.EPS
            for f in fl:
                for b in bl:
                    grund, kosten = A.paar_pruefung(inst, vor.labels[f], rueck.labels[b], i, j)
                    ergebnis = f"passt, Kosten {zahl_kurz(kosten)}" if grund == "passt" else f"verworfen: {grund}"
                    zeilen.append({"Kante": f"({i}, {j})", "Vorwärts": etikett(True, f), "Rückwärts": etikett(False, b), "Ergebnis": ergebnis,
                                   "Kanten-Vorprüfung": "übersprungen (nicht gezählt)" if uebersprungen else "geprüft", "_grund": grund, "_kosten": kosten, "_uebersprungen": uebersprungen})
    return zeilen


@dataclass(frozen=True)
class HandAnalyse:
    inst: Instanz
    pi: tuple
    m: float                   # gewählter Halbweg in Zeiteinheiten
    uni: A.PricingErgebnis
    bidi: A.PricingErgebnis
    reihe: tuple               # je Halbweg der Reihe: (M, erzeugt_v, erzeugt_r, paare, kanten, paare_alle, kanten_alle, beste)
    wege: tuple                # alle zulässigen elementaren Routen (Aufzählung)
    negativ_wege: int
    bester_weg: tuple          # (reduzierte Kosten, Route) der Aufzählung
    gleich: bool               # beste reduzierte Kosten gleich: einseitig, bidirektional bei allen Halbwegen der Reihe und Aufzählung
    fehler: str | None


def pruefe_ergebnis(inst: Instanz, pi, erg: A.PricingErgebnis, elementar: bool) -> str | None:
    """Unabhängige Prüfung der gelieferten Routen: zulässig (Last, Fenster, Rückkehr) und mit richtig bewerteten reduzierten Kosten. None = in Ordnung."""
    for rc, route in erg.routen:
        ok, text = A.pruefe_route(inst, route, elementar)
        if not ok:
            return f"Route {weg_text(route)}: {text}"
        if abs(A.reduzierte_kosten(inst, pi, route) - rc) > EPS_RC:
            return f"Route {weg_text(route)}: reduzierte Kosten stimmen nicht"
    return None


def analyse_hand(m: int) -> HandAnalyse:
    inst, pi = handbeispiel(), HAND_DUAL
    uni = A.pricing_einseitig(inst, pi, None, behalte_seiten=True)
    bidi = A.pricing_bidirektional(inst, pi, None, "fest", float(m), behalte_seiten=True)
    reihe = []
    for mx in C.HAND_M_REIHE:
        r = A.pricing_bidirektional(inst, pi, None, "fest", float(mx))
        reihe.append((mx, r.erzeugt_v, r.erzeugt_r, r.paare, r.kanten, r.paare_alle, r.kanten_alle, r.beste))
    wege = tuple(A.alle_zulaessigen_wege(inst))
    rcs = sorted((A.reduzierte_kosten(inst, pi, w), w) for w in wege)
    negativ = sum(1 for rc, _ in rcs if rc < -A.FEHLSCHLAG)
    bester = rcs[0]
    gleich = all(abs(x[7][0] - bester[0]) < EPS_RC and x[7][1] == bester[1] for x in reihe) and abs(uni.beste_rc - bester[0]) < EPS_RC and uni.beste[1] == bester[1]
    fehler = pruefe_ergebnis(inst, pi, uni, True) or pruefe_ergebnis(inst, pi, bidi, True)
    return HandAnalyse(inst, pi, float(m), uni, bidi, tuple(reihe), wege, negativ, bester, gleich, fehler)


# --- Kundeninstanz live ---------------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class LiveAnalyse:
    inst: Instanz
    pi: tuple | None
    runde_tatsaechlich: int          # Runde, deren Dualpreise gelten (bei kleinen Instanzen endet die Spaltenerzeugung früher als die gewählte Runde)
    labels_duale: int                # Labels der Spaltenerzeugung, die die Dualpreise liefert
    uni: A.PricingErgebnis | None
    bidi: A.PricingErgebnis | None   # fester Halbweg des Reglers
    halb: A.PricingErgebnis | None   # fester Halbweg H/2 (gleich bidi, wenn der Regler auf 50 % steht)
    zu_gross: str | None             # Grund, wenn die Live-Rechnung abgebrochen wurde
    fehler: str | None


def duale_fuer(inst: Instanz, k: int, runde: int) -> tuple:
    """Die Dualpreise der gewählten Runde: Runde 1 sind die Einzelfahrten (ohne LP), spätere Runden aus der Spaltenerzeugung. Rückgabe: (pi, tatsächliche Runde, Labels, Abbruchgrund).
    Endet die Spaltenerzeugung vor der gewählten Runde, gelten die Dualpreise ihres Endes (tatsächliche Runde = Zahl der Master)."""
    if runde == 1:
        return einzelfahrt_preise(inst), 1, 0, None
    g = G.duale_der_runden(inst, k, runden=(runde,), bis_runde=None if runde == C.RUNDE_ENDE else runde)
    if g.abgebrochen:
        return None, 0, g.labels, f"Die Spaltenerzeugung für die Dualpreise überschreitet {zahl(C.LABEL_CAP_SPALTENERZEUGUNG)} Labels"
    if runde == C.RUNDE_ENDE or runde not in g.duale:
        return g.ende, g.runden, g.labels, None
    return g.duale[runde], runde, g.labels, None


def analyse_live(s: Settings) -> LiveAnalyse:
    inst = instanz_aus_seed(s.n, s.seed, s.breite, s.typ, Q=s.q)
    pi, runde, labels_duale, grund = duale_fuer(inst, s.k, s.runde)
    if grund:
        return LiveAnalyse(inst, None, 0, labels_duale, None, None, None, grund, None)
    uni = A.pricing_einseitig(inst, pi, s.k, max_labels=C.LABEL_CAP)
    bidi = A.pricing_bidirektional(inst, pi, s.k, "fest", s.halbweg, max_labels=C.LABEL_CAP)
    halb = bidi if s.halbweg_pct == 50 else A.pricing_bidirektional(inst, pi, s.k, "fest", inst.H / 2.0, max_labels=C.LABEL_CAP)
    if uni.abgebrochen or bidi.abgebrochen or halb.abgebrochen:
        return LiveAnalyse(inst, pi, runde, labels_duale, uni, bidi, halb, f"Ein Lauf überschreitet {zahl(C.LABEL_CAP)} erzeugte Labels", None)
    elementar = s.k >= s.n
    fehler = pruefe_ergebnis(inst, pi, uni, elementar) or pruefe_ergebnis(inst, pi, bidi, elementar)
    if fehler is None and abs(uni.beste_rc - bidi.beste_rc) > EPS_RC:
        fehler = f"beste reduzierte Kosten verschieden: einseitig {uni.beste_rc}, bidirektional {bidi.beste_rc}"
    return LiveAnalyse(inst, pi, runde, labels_duale, uni, bidi, halb, None, fehler)


def gleiche_route(uni: A.PricingErgebnis, bidi: A.PricingErgebnis) -> tuple:
    """(gleiche beste reduzierte Kosten, gleiche beste Route). Bei Gleichstand der Kosten kann eine andere Route gleich gut sein."""
    return abs(uni.beste_rc - bidi.beste_rc) <= EPS_RC, uni.beste == bidi.beste


@dataclass(frozen=True)
class KurvenPunkt:
    prozent: int
    erzeugt_v: int
    erzeugt_r: int
    paare: int
    abgebrochen: bool

    @property
    def summe(self) -> int:
        return self.erzeugt_v + self.erzeugt_r


@dataclass(frozen=True)
class Kurve:
    punkte: tuple
    uni_labels: int
    dynd: A.PricingErgebnis
    bester: KurvenPunkt          # fester Halbweg mit den wenigsten Labels
    fehler: str | None


def analyse_kurve(s: Settings) -> Kurve:
    """Labels über den Halbweg M = 0, 10, ..., 100 Prozent von H für die Kundeninstanz (Dualpreise wie in `analyse_live`), dazu die Fassung dynD."""
    inst = instanz_aus_seed(s.n, s.seed, s.breite, s.typ, Q=s.q)
    pi, _, _, grund = duale_fuer(inst, s.k, s.runde)
    if grund:
        raise ValueError(grund)
    punkte = []
    for p in C.HALBWEG_PUNKTE:
        r = A.pricing_bidirektional(inst, pi, s.k, "fest", inst.H * p / 100.0, max_labels=C.LABEL_CAP)
        punkte.append(KurvenPunkt(p, r.erzeugt_v, r.erzeugt_r, r.paare, r.abgebrochen))
    uni = A.pricing_einseitig(inst, pi, s.k, max_labels=C.LABEL_CAP)
    dynd = A.pricing_bidirektional(inst, pi, s.k, "dynD", max_labels=C.LABEL_CAP)
    fertig = [p for p in punkte if not p.abgebrochen]
    bester = min(fertig, key=lambda p: (p.summe, p.prozent)) if fertig else punkte[0]
    return Kurve(tuple(punkte), uni.erzeugt_v, dynd, bester, None if not (uni.abgebrochen or dynd.abgebrochen) else "Abbruch")


@dataclass(frozen=True)
class DynAnalyse:
    zeilen: tuple                # je Fassung: (Name, PricingErgebnis)
    halb: A.PricingErgebnis      # fest H/2
    uni_labels: int


def analyse_dynamisch(s: Settings) -> DynAnalyse:
    inst = instanz_aus_seed(s.n, s.seed, s.breite, s.typ, Q=s.q)
    pi, _, _, grund = duale_fuer(inst, s.k, s.runde)
    if grund:
        raise ValueError(grund)
    uni = A.pricing_einseitig(inst, pi, s.k, max_labels=C.LABEL_CAP)
    halb = A.pricing_bidirektional(inst, pi, s.k, "fest", inst.H / 2.0, max_labels=C.LABEL_CAP)
    zeilen = tuple((name, A.pricing_bidirektional(inst, pi, s.k, name, max_labels=C.LABEL_CAP)) for name in ("dyn", "dynF", "dynB", "dynD"))
    return DynAnalyse(zeilen, halb, uni.erzeugt_v)


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------

def verdict_hand(h: HandAnalyse) -> tuple:
    """Verdikt des Handbeispiels: Labels beider Verfahren, Verbindungspaare und die Gleichheit der besten Route bei allen Halbwegen der Reihe."""
    uni, bidi = h.uni, h.bidi
    summe = bidi.labels
    gleich = ("Dieselbe beste Route wie einseitig und wie die Aufzählung aller " + zahl(len(h.wege)) + " zulässigen Routen, bei allen " + zahl(len(h.reihe)) + " Halbwegen der Reihe."
              if h.gleich else "**Achtung:** Die beste Route weicht bei mindestens einem Halbweg ab.")
    kopf = (f"Halbweg {zahl_kurz(h.m)}: bidirektional **{zahl(summe)}** Labels ({zahl(bidi.erzeugt_v)} vorwärts + {zahl(bidi.erzeugt_r)} rückwärts) gegen **{zahl(uni.labels)}** einseitig, "
            f"dazu {zahl(bidi.paare)} Verbindungspaare. ")
    if summe < uni.labels:
        return "success", kopf + gleich
    return "warning", kopf + "Das sind **nicht weniger** Labels als einseitig (bei diesem Halbweg ist das Verfahren fast einseitig). " + gleich


def verdict_labels(a: LiveAnalyse) -> tuple:
    """Verdikt der Kernfrage an der Kundeninstanz: Anteil der bidirektionalen Labels an den einseitigen."""
    if a.zu_gross:
        return "warning", f"Für diese Einstellung ist die Live-Rechnung zu groß: {a.zu_gross}. Kleinere Kundenzahl, engere Fenster oder frühere Dualpreise wählen; die Messreihen weiter unten zeigen größere Fälle."
    uni, bidi = a.uni, a.bidi
    verh = quote(bidi.labels, uni.labels)
    gleich_rc, gleich_route = gleiche_route(uni, bidi)
    if not gleich_rc:
        return "error", "Die beiden Verfahren liefern verschiedene beste reduzierte Kosten: Das darf nicht vorkommen."
    if uni.beste is None:
        ergebnis = "Beide Verfahren finden keine Route mit negativen reduzierten Kosten: Das Pricing bestätigt nur, dass keine Spalte mehr lohnt."
    elif gleich_route:
        ergebnis = f"Beide finden dieselbe beste Route {weg_text(uni.beste[1])} mit reduzierten Kosten {zahl(uni.beste_rc, 2)}."
    else:
        ergebnis = f"Beide finden dieselben besten reduzierten Kosten ({zahl(uni.beste_rc, 2)}), mit verschiedenen, gleich guten Routen."
    kopf = f"Bidirektional erzeugt hier **{prozent_genau(verh)}** der Labels des einseitigen: {zahl(bidi.labels)} ({zahl(bidi.erzeugt_v)} vorwärts + {zahl(bidi.erzeugt_r)} rückwärts) gegen {zahl(uni.labels)}. "
    if verh >= 1:
        return "warning", f"Bidirektional erzeugt hier **mehr Labels als einseitig**: {zahl(bidi.labels)} ({zahl(bidi.erzeugt_v)} vorwärts + {zahl(bidi.erzeugt_r)} rückwärts) gegen {zahl(uni.labels)}, also {prozent_genau(verh)}. " + ergebnis
    return "success", kopf + ergebnis


def verdict_verbinden(a: LiveAnalyse) -> tuple:
    """Verdikt zum Preis des Verbindens: Paare im Verhältnis zur einseitigen Label-Zahl, Vergleiche im Verhältnis zu denen des einseitigen Laufs."""
    if a.zu_gross:
        return "info", "Ohne Live-Rechnung gibt es hier keine Zahl für das Verbinden."
    uni, bidi = a.uni, a.bidi
    faktor = quote(bidi.paare, uni.labels)
    vgl = quote(bidi.vergleiche, uni.vergleiche)
    return "info", (f"Das Verbinden prüft **{zahl(bidi.paare)}** Paare, das **{zahl(faktor, 1)}-Fache** der einseitigen Label-Zahl ({zahl(uni.labels)}); es ist als Matrixoperation je Kante gerechnet, nicht als einzelnes Label. "
                    f"Die Dominanzvergleiche der Labels betragen {prozent(vgl)} der Vergleiche des einseitigen Laufs ({zahl(bidi.vergleiche)} gegen {zahl(uni.vergleiche)}).")


def verdict_halbweg_wahl(a: LiveAnalyse, halbweg_pct: int) -> tuple:
    """Verdikt zur Halbweg-Wahl des Reglers: ungünstig, wenn der Regler mehr Labels erzeugt als der Halbweg H/2."""
    if a.zu_gross:
        return "info", "Ohne Live-Rechnung gibt es hier keinen Vergleich der Halbwege."
    if halbweg_pct == 50:
        return "info", "Der Regler steht auf H/2, dem Halbweg der Messreihe; stellen Sie ihn um, um andere Halbwege zu vergleichen."
    if a.bidi.labels > a.halb.labels:
        return "warning", (f"**Halbweg ungünstig:** bei {zahl(halbweg_pct)} % von H sind es {zahl(a.bidi.labels)} Labels, bei H/2 nur {zahl(a.halb.labels)} "
                           f"({prozent_genau(quote(a.bidi.labels, a.halb.labels))} der Labels bei H/2).")
    return "info", f"Bei {zahl(halbweg_pct)} % von H sind es {zahl(a.bidi.labels)} Labels, bei H/2 {zahl(a.halb.labels)}: der Regler-Halbweg ist hier nicht ungünstiger als H/2."


def verdict_kurve(k: Kurve) -> tuple:
    """Verdikt der Halbweg-Kurve: Lage des Minimums und Verhalten an den Rändern (M = 0 und M = H sind einseitige Verfahren)."""
    erster, letzter, b = k.punkte[0], k.punkte[-1], k.bester
    innen = 0 < b.prozent < 100
    u_form = innen and b.summe < erster.summe and b.summe < letzter.summe
    text = (f"Am wenigsten Labels bei einem Halbweg von **{zahl(b.prozent)} % von H**: {zahl(b.summe)} ({zahl(b.erzeugt_v)} vorwärts + {zahl(b.erzeugt_r)} rückwärts), "
            f"einseitig sind es {zahl(k.uni_labels)}. An den Rändern, M = 0 % (nur rückwärts) und M = 100 % (nur vorwärts), sind es {zahl(erster.summe)} und {zahl(letzter.summe)}.")
    if u_form:
        return "success", text + " Die Summe ist **U-förmig**: zu früh oder zu spät gewählt, wächst eine Seite zu stark."
    return "info", text + " Hier ist die Summe nicht U-förmig (das Minimum liegt am Rand oder die Ränder sind nicht schlechter)."


def verdict_dynamisch(d: DynAnalyse) -> tuple:
    """Verdikt zu den dynamischen Fassungen: schlechter oder besser als fest H/2, gemessen in erzeugten Labels (dynD ist die beste der vier Fassungen der Messreihe)."""
    besser = [name for name, r in d.zeilen if r.labels < d.halb.labels]
    text = (f"Fest H/2 erzeugt **{zahl(d.halb.labels)}** Labels, die Fassungen dyn, dynF, dynB, dynD erzeugen " + ", ".join(f"{zahl(r.labels)}" for _, r in d.zeilen) + ". ")
    if not besser:
        return "warning", text + "**Dynamisch ist hier in allen vier Fassungen schlechter als fest H/2.**"
    return "info", text + "Hier erzeugt mindestens eine dynamische Fassung weniger Labels als fest H/2: " + ", ".join(besser) + ". Die Messreihe zeigt das nicht (siehe unten)."


def runde_label(runde: int) -> str:
    """Beschriftung der Dualpreis-Runde im Regler: „Runde 1“, „Runde 3“, „Runde 8“ oder „Ende“."""
    return "Ende" if runde == C.RUNDE_ENDE else f"Runde {runde}"
