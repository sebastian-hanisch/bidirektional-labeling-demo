"""Jede Zahl der README an den festen Zufalls-Seeds nachgerechnet (DEMO-PLAYBOOK §4, §11a). Zeiten werden nie festgeschrieben.

Die README-Tabellen werden aus den Messreihen in data/ und dem Kern erzeugt (`tools/readme_tabellen.py`, `tools/readme_fuellen.py`); der Test erzeugt sie noch einmal und sucht sie in der README.
Die Sätze mit Zahlen werden hier aus den Daten gebildet und müssen wörtlich in der README stehen. Die Zahlen der früheren Messreihe stehen nur aus der Datei da und werden nicht neu gerechnet.
Nicht im Test, nur Messung der README: der Abgleich aller 4800 Zeilen mit der Vormessung und die Orakel-Läufe im Scratch (siehe README, „Zahl → Test“)."""

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import bdl_algorithm as A
import bdl_baender as B
import bdl_constants as C
import bdl_evaluation as ev
import bdl_scenario as S
from bdl_texts import ASSUMPTIONS_MARKDOWN

ROOT = Path(__file__).resolve().parent.parent
NBSP = " "
MINUS = "−"


def _norm(text: str) -> str:
    return text.replace(NBSP, " ").replace(MINUS, "-")


README = _norm((ROOT / "README.md").read_text(encoding="utf-8"))
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def _tabellen() -> dict:
    spec = importlib.util.spec_from_file_location("readme_tabellen", ROOT / "tools" / "readme_tabellen.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return {k: _norm(v) for k, v in m.alle().items()}


def _zwischen(name: str) -> str:
    m = re.search(rf"<!-- tabelle:{name} -->\n(.*?)\n<!-- /tabelle -->", README, flags=re.S)
    assert m, name
    return m.group(1)


def test_readme_tables_are_generated_from_the_data_and_the_kernel():
    for name, text in _tabellen().items():
        assert _zwischen(name) == text, name


def test_the_assumptions_text_of_the_app_is_in_the_readme_verbatim():
    m = re.search(r"<!-- annahmen -->\n(.*?)\n<!-- /annahmen -->", README, flags=re.S)
    assert m and m.group(1) == _norm(ASSUMPTIONS_MARKDOWN).strip()
    assert "ASSUMPTIONS_MARKDOWN" in APP


def test_readme_names_the_same_test_count_as_the_suite():
    p = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "tests", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True, text=True, timeout=300)
    m = re.search(r"(\d+) tests? collected", p.stdout)
    assert m, p.stdout[-300:]
    assert f"{m.group(1)} Tests (`pytest --collect-only -q tests`)" in README


def test_forbidden_words_do_not_occur_in_the_texts():
    texte = {"README": README, "app": APP, "texts": (ROOT / "bdl_texts.py").read_text(encoding="utf-8"), "constants": (ROOT / "bdl_constants.py").read_text(encoding="utf-8"),
             "evaluation": (ROOT / "bdl_evaluation.py").read_text(encoding="utf-8"), "tabellen": (ROOT / "bdl_tabellen.py").read_text(encoding="utf-8")}
    for name, t in texte.items():
        for wort in ("trägt", "tragen", "läuft lokal", "Saatwert", "Phase 0", "Stück", "geplant", "Preset"):
            if wort == "Preset" and name in ("app", "constants", "evaluation", "tabellen"):
                continue                                                                        # der Name im Code (apply_preset, PRESETS) ist kein Text
            assert not re.search(rf"{wort}", t), (name, wort)                                   # ganze Wörter: „betragen“ ist erlaubt, „tragen“ nicht


# --- Handbeispiel -----------------------------------------------------------------------------------------------------------------------------

def test_hand_example_sentences_follow_from_the_kernel():
    h = ev.analyse_hand(20)
    uni, bidi = h.uni, h.bidi
    assert (f"erzeugt **{uni.labels} Labels** (davon {uni.dominiert_v} dominiert, {uni.lebend_v} leben am Ende) mit {uni.vergleiche} Dominanzvergleichen" in README
            and "5-6-3 mit -3, 5-6-1 mit -1 und 6-5-4 mit -0,5" in README and uni.routen[:3] == [(-3.0, (5, 6, 3)), (-1.0, (5, 6, 1)), (-0.5, (6, 5, 4))])
    assert (f"**{bidi.erzeugt_v} Vorwärtslabels und {bidi.erzeugt_r} Rückwärtslabels, zusammen {bidi.labels} Labels** ({bidi.labels} von {uni.labels}, also {bidi.labels / uni.labels:.2f}".replace(".", ",") in README
            and f"{bidi.lebend_v} + {bidi.lebend_r} leben am Ende, {bidi.vergleiche} Dominanzvergleiche), dazu **{bidi.paare} Verbindungspaare** über {bidi.kanten} Kanten" in README)
    assert f"findet {len(h.wege)} Routen, drei davon" in README and h.negativ_wege == 3 and h.bester_weg == (-3.0, (5, 6, 3)) and h.gleich
    assert f"Bei allen {len(h.reihe)} Halbwegen der Reihe ist die beste Route dieselbe" in README.replace("**", "")


def test_hand_pair_counts_with_and_without_the_precheck_named_in_the_readme():
    h = ev.analyse_hand(20)
    mit = {r[0]: r[3] for r in h.reihe}
    ohne = {r[0]: r[5] for r in h.reihe}
    assert [ohne[m] for m in (10, 15, 25, 30)] == [72, 54, 113, 72] and [mit[m] for m in (10, 15, 25, 30)] == [70, 52, 97, 62] and mit[20] == ohne[20] == 48
    assert "(72, 54, 113, 72 bei M = 10, 15, 25, 30)" in README and "(70, 52, 97, 62)" in README and "bei M = 20 sind sie gleich (48)" in README
    assert [r[1] + r[2] for r in h.reihe] == [36, 34, 26, 16, 32, 33, 36] and "36 Labels gegen 35" in README


def test_preset_sentences_follow_from_the_live_rechnung():
    a = ev.analyse_live(ev.settings_aus_preset(C.PRESETS["Halbweg zu früh (25 % von H)"]))
    assert (a.bidi.labels, a.uni.labels) == (889, 748) and "(889 gegen 748)" in README and "Zufalls-Seed 3 mit dem Halbweg bei 25 % von H" in README
    ende = ev.analyse_live(ev.settings_aus_preset(C.PRESETS["Kleine Instanz (8 Kunden), Ende"]))
    assert ende.uni.routen == [] and ende.bidi.routen == []


# --- Messreihe ------------------------------------------------------------------------------------------------------------------------------

def test_measured_sentences_follow_from_the_data():
    band = B.lade_baender()
    z = B.zusammenfassung(band)
    p = z["pool"]
    d = lambda x: f"{x:.2f}".replace(".", ",")                                                  # noqa: E731
    f5 = p["fest0.5"]
    assert f"**Fest H/2** erzeugt in **{f5['weniger']} von {f5['n']}** Läufen weniger Labels als das einseitige Verfahren: Median {d(f5['median'])}, kleinster Wert {d(f5['min'])}, größter {d(f5['max'])}." in README
    assert (f5["weniger"], f5["n"]) == (480, 480)
    ausnahme = [l for l in B.laeufe(band) if B.verhaeltnis(l, "fest0.4") >= 1]
    assert len(ausnahme) == 1
    l = ausnahme[0]
    assert (f"Fest H/4 ({p['fest0.25']['weniger']} von 480) und fest 0,4 H ({p['fest0.4']['weniger']} von 480, die Ausnahme ist ein Lauf mit Kapazität {l['q']}, {C.TYP_NAMEN[l['typ']].split(' ')[0]}, "
            f"Breite {l['breite']}, k = {l['k']}, Dualpreisen der Runde {l['runde']} und dem Zufalls-Seed {l['seed']})") in README
    dyn = [p[n]["median"] for n in B.DYNAMISCHE]
    assert f"({d(min(dyn))} bis {d(max(dyn))} gegen {d(f5['median'])})" in README
    assert f"in {p['dyn']['n'] - p['dyn']['weniger']} von {p['dyn']['n']} Läufen gleich viele oder mehr Labels als einseitig" in README
    assert f"läge der Median bei {d(z['bester_fester_median'])}" in README
    assert f"das {z['paare_je_label']:.1f}-Fache der einseitigen Label-Zahl".replace(".", ",") in README and f"im Median {round(100 * z['vergleiche'])} % der Vergleiche" in README
    ms, vs = B.halbweg_dynd(band), B.verschwendet_anteil(band)
    assert f"dynD erzeugt in {z['dynd_besser_als_fest']} von {z['laeufe']} Läufen weniger Labels als fest H/2" in README
    assert p["dynD"]["median"] < min(p["fest0.25"]["median"], p["fest0.75"]["median"])                                        # gegen die ungünstigeren Halbwege ist dynD im Median besser
    assert f"liegt dynD im Median niedriger: {d(p['dynD']['median'])} gegen {d(p['fest0.25']['median'])} und {d(p['fest0.75']['median'])}" in README
    assert f"im Median bei {d(ms['median'])} H (Spanne {d(ms['min'])} bis {d(ms['max'])} H, {ms['n']} Läufe)" in README
    assert f"im Median {round(100 * vs['median'])} % der von dynD erzeugten Labels (Spanne {round(100 * vs['min'])} % bis {round(100 * vs['max'])} %)" in README


def test_cell_and_size_sentences_follow_from_the_data():
    band = B.lade_baender()
    d = lambda x: f"{x:.2f}".replace(".", ",")                                                  # noqa: E731
    meds = [B.zelle(c)["median"] for c in B.zellen_der_runde(band, "ende")]
    assert len(meds) == 12 and f"in den zwölf Zellen zwischen {d(min(meds))} und {d(max(meds))}" in README
    schwach, schwach1 = B.schwaechste_zelle(band, "ende"), B.schwaechste_zelle(band, "1")
    assert (schwach["q"], schwach["typ"], schwach["breite"], schwach["k"]) == (70, "gruppiert", 100, 5) == (schwach1["q"], schwach1["typ"], schwach1["breite"], schwach1["k"])
    assert f"k = 5 ({d(schwach['median'])}); mit den Dualpreisen der ersten Runde ist es dieselbe Zelle mit {d(schwach1['median'])}" in README
    ls = B.laeufe(band)
    uni = sorted(B.wert(l, "uni", "labels") for l in ls)
    gross = lambda x: f"{int(x):,}".replace(",", " ")                                           # noqa: E731
    assert f"erzeugt {gross(max(uni))} Labels, der Median aller Läufe liegt bei {gross(B.statistics.median(uni))}" in README
    klassen = B.nach_groesse(band)
    assert klassen[3][3] > max(klassen[0][3], klassen[1][3], klassen[2][3]) and klassen[4][2] == 4 and "nur 4 Läufe" in README
    runden = {(q, k): B.je_runde(band, q, k) for q, k in C.BAND_ZELLEN}
    assert all(r["1"]["median"] < min(r["3"]["median"], r["8"]["median"], r["ende"]["median"]) for r in runden.values())      # Runde 1: der kleinste Anteil, also der größte Vorteil
    assert all(r["ende"]["median"] < 1 for r in runden.values())                                  # und bleibt bis zum Ende bestehen
    for q in C.KAPAZITAETEN:
        h = B.haeufigkeit_bester_fester(band, q)
        assert max(B.FESTE, key=lambda n: h[n]) == "fest0.5"                                      # „am häufigsten die wenigsten Labels“


def test_comparison_table_follows_from_the_data_and_the_named_differences():
    z, f = B.zusammenfassung(B.lade_baender()), B.lade_fruehere()
    assert f["pool"]["fest0.4"]["weniger"] == 480 and z["pool"]["fest0.4"]["weniger"] == 479 and "479 gegen 480 von 480 Läufen" in README
    assert f"{z['paare_je_label']:.1f} gegen {f['paare_je_label']:.1f} je Label".replace(".", ",") in README
    assert f["pool"]["fest0.5"]["weniger"] == z["pool"]["fest0.5"]["weniger"] == 480 and f["dynd_besser_als_fest"] == z["dynd_besser_als_fest"] == 0
    assert min(("fest0.25", "fest0.4", "fest0.5", "fest0.6", "fest0.75"), key=lambda n: z["pool"][n]["median"]) == "fest0.5"


def test_limits_named_in_the_readme_are_the_constants():
    assert C.LABEL_CAP == 150_000 and C.LABEL_CAP_SPALTENERZEUGUNG == 800_000 and C.LIVE_KURVE_LIMIT == 40_000 and C.N_MAX == 30
    assert "bei 150 000 erzeugten Labels" in README and "bei 800 000 Labels" in README and "höchstens 40 000 Labels" in README and "Kundenzahl der Live-Instanz geht bis 30" in README


def test_constants_comment_names_the_largest_run_of_the_series():
    band = B.lade_baender()
    assert max(B.wert(l, "uni", "labels") for l in B.laeufe(band)) == 180281
    assert "bis zu 180 281 Labels je Lauf" in (ROOT / "bdl_constants.py").read_text(encoding="utf-8").replace(NBSP, " ")


def test_readme_names_the_hand_example_from_the_scenario():
    s = S.handbeispiel()
    assert (s.n, s.Q, s.H, s.svc) == (6, 9, 40, 2) and "Depot bei (5, 5) und 6 Kunden" in README and "Kapazität 9, Rückkehr bis H = 40" in README and "Bedienzeit 2" in README
    assert A.alle_zulaessigen_wege(s) and len(A.alle_zulaessigen_wege(s)) == 39
