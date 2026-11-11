"""Die festen Messreihen (Bänder) und ihre Zusammenfassungen: reine Funktionen auf den Einzelwerten in `data/baender_v9.json`.

Die Datei hält 480 Läufe (30 Kunden; Kapazität 70 mit Gedächtnis k = 5 und 8, Kapazität 120 mit k = 5; zwei Instanztypen; Fensterbreite 40 und 100; Zufalls-Seeds 0 bis 9; Dualpreise der Runden
1, 3, 8 und des Endes der Spaltenerzeugung), je Lauf das einseitige Labeling und neun bidirektionale Einstellungen. Alle Zahlen sind mit dem Kern dieser Demo gerechnet (`tools/messreihe_baender.py`).
Hier steht nur die Auswertung; jede Zusammenfassung folgt aus den Einzelwerten (`tests/test_baender.py` rechnet sie nach)."""

import json
import statistics
from functools import lru_cache
from pathlib import Path

import bdl_constants as C

DATA = Path(__file__).resolve().parent / "data"
FELDER = ["labels", "gF", "gB", "liveF", "liveB", "paare", "kanten", "vergleiche", "rc", "halbweg", "verschwendet", "zurueckgestellt", "paare_alle", "kanten_alle"]
IDX = {name: i for i, name in enumerate(FELDER)}
FESTE = ("fest0.25", "fest0.4", "fest0.5", "fest0.6", "fest0.75")
DYNAMISCHE = ("dyn", "dynF", "dynB", "dynD")
BIDI = FESTE + DYNAMISCHE
GROESSEN_KLASSEN = ((0, 1000), (1000, 5000), (5000, 20000), (20000, 100000), (100000, 10 ** 12))
RUNDEN_NAMEN = ("1", "3", "8", "ende")


@lru_cache(maxsize=None)
def lade_baender(name: str = "v9") -> dict:
    """Lädt eine feste Messreihe aus data/ (JSON; jede Zeile mit Quelle)."""
    return json.loads((DATA / f"baender_{name}.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def lade_fruehere() -> dict:
    """Zusammenfassung der früheren Messreihe (Vormessung), aus deren Rohdateien übernommen und nicht neu gerechnet."""
    return json.loads((DATA / "fruehere_messreihe.json").read_text(encoding="utf-8"))


def laeufe(band: dict) -> list:
    """Alle Läufe als flache Liste von Wörterbüchern (Zelle und Seed) mit den Werten je Verfahren."""
    aus = []
    for z in band["zeilen"]:
        for l in z["laeufe"]:
            aus.append({"q": z["q"], "typ": z["typ"], "breite": z["breite"], "k": z["k"], "runde": z["runde"], "seed": l["seed"], "v": l["v"]})
    return aus


def wert(lauf: dict, name: str, feld: str):
    return lauf["v"][name][IDX[feld]]


def verhaeltnis(lauf: dict, name: str, feld: str = "labels") -> float:
    """Labels (oder ein anderes Feld) des Verfahrens im Verhältnis zum einseitigen Lauf."""
    return wert(lauf, name, feld) / wert(lauf, "uni", feld)


def statistik(werte) -> dict:
    w = list(werte)
    return {"n": len(w), "mittel": statistics.mean(w), "median": statistics.median(w), "min": min(w), "max": max(w)}


def pool(band: dict) -> dict:
    """Je bidirektionalem Verfahren über alle Läufe: Median, Minimum, Maximum des Verhältnisses der Labels zum einseitigen Lauf und die Zahl der Läufe mit weniger Labels als einseitig."""
    ls = laeufe(band)
    aus = {}
    for name in BIDI:
        r = [verhaeltnis(l, name) for l in ls]
        aus[name] = {"n": len(r), "median": statistics.median(r), "min": min(r), "max": max(r), "weniger": sum(1 for x in r if x < 1)}
    return aus


def bester_fester_median(band: dict) -> float:
    """Median des Verhältnisses beim je Lauf besten festen Halbweg (nachträglich gewählt, nur ein Rückblick)."""
    return statistics.median(min(wert(l, n, "labels") for n in FESTE) / wert(l, "uni", "labels") for l in laeufe(band))


def dynd_besser_als_fest(band: dict) -> int:
    """Zahl der Läufe, in denen dynD weniger Labels erzeugt als fest H/2."""
    return sum(1 for l in laeufe(band) if wert(l, "dynD", "labels") < wert(l, "fest0.5", "labels"))


def median_paare_je_label(band: dict, name: str = "fest0.5") -> float:
    """Median der Verbindungspaare im Verhältnis zur Label-Zahl des einseitigen Laufs."""
    return statistics.median(wert(l, name, "paare") / wert(l, "uni", "labels") for l in laeufe(band))


def median_vergleiche(band: dict, name: str = "fest0.5") -> float:
    """Median der Dominanzvergleiche im Verhältnis zu denen des einseitigen Laufs."""
    return statistics.median(verhaeltnis(l, name, "vergleiche") for l in laeufe(band))


def zelle(z: dict, name: str = "fest0.5") -> dict:
    """Zusammenfassung einer Zelle (je 10 Läufe): einseitige Labels (Median), Verhältnis des Verfahrens (Median, Mittel, Maximum), Läufe mit weniger Labels, Paare je einseitigem Label (Median)."""
    ls = z["laeufe"]
    r = [l["v"][name][IDX["labels"]] / l["v"]["uni"][IDX["labels"]] for l in ls]
    return {"n": len(ls), "uni_labels": statistics.median(l["v"]["uni"][IDX["labels"]] for l in ls), "median": statistics.median(r), "mittel": statistics.mean(r), "max": max(r),
            "weniger": sum(1 for x in r if x < 1), "paare_je_label": statistics.median(l["v"][name][IDX["paare"]] / l["v"]["uni"][IDX["labels"]] for l in ls)}


def zellen_der_runde(band: dict, runde: str) -> list:
    """Die Zellen einer Dualpreis-Runde ("1", "3", "8", "ende"), in der Reihenfolge der Datei."""
    return [z for z in band["zeilen"] if z["runde"] == runde]


def je_runde(band: dict, q: int, k: int, name: str = "fest0.5") -> dict:
    """Median des Verhältnisses je Runde, alle Zellen (beide Typen, beide Breiten, 40 Läufe) mit Kapazität q und Gedächtnis k."""
    aus = {}
    for runde in RUNDEN_NAMEN:
        r = [verhaeltnis(l, name) for l in laeufe(band) if (l["q"], l["k"], l["runde"]) == (q, k, runde)]
        aus[runde] = {"n": len(r), "median": statistics.median(r), "min": min(r), "max": max(r)}
    return aus


def nach_groesse(band: dict, name: str = "fest0.5") -> list:
    """Median des Verhältnisses nach der Label-Zahl des einseitigen Laufs in Klassen: [(von, bis, n, Median)]."""
    ls = laeufe(band)
    aus = []
    for lo, hi in GROESSEN_KLASSEN:
        r = [verhaeltnis(l, name) for l in ls if lo <= wert(l, "uni", "labels") < hi]
        aus.append((lo, hi, len(r), statistics.median(r) if r else None))
    return aus


def haeufigkeit_bester_fester(band: dict, q: int) -> dict:
    """Wie oft hat je Lauf (Kapazität q) jeder feste Halbweg die wenigsten Labels? Bei Gleichstand zählt der kleinere Anteil von H. Rückgabe: {Verfahren: Zahl}, dazu "n"."""
    ls = [l for l in laeufe(band) if l["q"] == q]
    aus = {n: 0 for n in FESTE}
    for l in ls:
        aus[min(FESTE, key=lambda n: (wert(l, n, "labels"), float(n[4:])))] += 1
    aus["n"] = len(ls)
    return aus


def halbweg_dynd(band: dict) -> dict:
    """Halbweg M* von dynD in Anteilen von H (Dualpreise am Ende): Median, Minimum, Maximum über alle Läufe."""
    r = [wert(l, "dynD", "halbweg") / C.HORIZONT for l in laeufe(band) if l["runde"] == "ende"]
    return {"n": len(r), "median": statistics.median(r), "min": min(r), "max": max(r)}


def verschwendet_anteil(band: dict, runde: str = "ende") -> dict:
    """Anteil der von dynD erzeugten Labels jenseits des endgültigen M*: Median, Minimum, Maximum je Lauf (Dualpreise der Runde `runde`)."""
    r = [wert(l, "dynD", "verschwendet") / wert(l, "dynD", "labels") for l in laeufe(band) if l["runde"] == runde]
    return {"n": len(r), "median": statistics.median(r), "min": min(r), "max": max(r)}


def schwaechste_zelle(band: dict, runde: str = "ende") -> dict:
    """Die Zelle (einer Runde) mit dem größten Median-Verhältnis von fest H/2."""
    z = max(zellen_der_runde(band, runde), key=lambda c: zelle(c)["median"])
    return {"q": z["q"], "typ": z["typ"], "breite": z["breite"], "k": z["k"], **zelle(z)}


def zusammenfassung(band: dict) -> dict:
    """Die Kennzahlen, die App und README nennen, in einem Wörterbuch (auch für den Vergleich mit der früheren Messreihe)."""
    p = pool(band)
    return {"laeufe": len(laeufe(band)), "pool": p, "bester_fester_median": bester_fester_median(band), "dynd_besser_als_fest": dynd_besser_als_fest(band),
            "paare_je_label": median_paare_je_label(band), "vergleiche": median_vergleiche(band)}
