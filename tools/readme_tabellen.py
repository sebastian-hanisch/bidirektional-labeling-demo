"""Druckt die Markdown-Tabellen der README aus den festen Messreihen (data/*.json) und den Rechnungen des Kerns; `tests/test_claims.py` prüft, dass genau diese Tabellen in der README stehen.

    python tools/readme_tabellen.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bdl_baender as B  # noqa: E402
import bdl_evaluation as ev  # noqa: E402
import bdl_tabellen as T  # noqa: E402


def alle() -> dict:
    band = B.lade_baender()
    zus = B.zusammenfassung(band)
    h = ev.analyse_hand(20)
    md = T.markdown_tabelle
    return {
        "hand_netz": md(T.tabelle_hand_netz()),
        "hand_reihe": md(T.tabelle_hand_reihe(h)),
        "hand_reihe_ohne": md(T.tabelle_hand_reihe(h, ohne_vorpruefung=True)),
        "presets": md(T.tabelle_presets()),
        "pool": md(T.tabelle_pool(zus["pool"])),
        "zellen_ende": md(T.tabelle_zellen(band, "ende")),
        "zellen_1": md(T.tabelle_zellen(band, "1")),
        "runden": md(T.tabelle_runden(band)),
        "klassen": md(T.tabelle_groessen(band)),
        "bester_fester": md(T.tabelle_bester_fester(band)),
        "vergleich": md(T.tabelle_vergleich(zus, B.lade_fruehere())),
    }


if __name__ == "__main__":
    for name, text in alle().items():
        print(f"### {name}\n{text}\n")
