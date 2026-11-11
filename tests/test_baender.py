"""Feste Messreihen (data/*.json): Raster, Quellen und Schlüssigkeit der 4800 Zeilen, Zusammenfassungen aus den Einzelwerten, und Stichproben, die mit dem Kern der Demo neu gerechnet werden.

Die Messreihe `data/baender_v9.json` ist mit `tools/messreihe_baender.py` und demselben Kern wie die App gerechnet (Instanzen aus SplitMix64, Dualpreise aus `data/duale_v9.json`). Die Zählungen hängen
nur von Instanz, Dualpreisen und Kern ab und werden exakt nachgerechnet. Die Dualpreise selbst hängen vom LP-Löser ab (Entartung, HiGHS-Version): sie werden nicht neu erzeugt verglichen, sondern
auf ihre Eigenschaften geprüft (Runde 1 = Einzelfahrten, Ende = das Pricing findet keine negative Route) und die Schranke der Spaltenerzeugung mit Toleranz.
Die frühere Messreihe der Planung (Python-Zufallszahlen, andere Dualpreise) steht nur aus ihrer Datei da; dass der Kern ihre Zeilen auf ihren Instanzen und mit ihren Dualpreisen trifft, prüft eine Stichprobe."""

import importlib.util
import json
import statistics
from pathlib import Path

import pytest
from alt_instanz import alte_instanz

import bdl_algorithm as A
import bdl_baender as B
import bdl_colgen as G
import bdl_constants as C
import bdl_scenario as S

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAUM = {"1": 1, "3": 3, "8": 8, "ende": C.RUNDE_ENDE}


def _tool():
    spec = importlib.util.spec_from_file_location("messreihe_baender", ROOT / "tools" / "messreihe_baender.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def band():
    return B.lade_baender()


@pytest.fixture(scope="module")
def duale():
    return json.loads((DATA / "duale_v9.json").read_text(encoding="utf-8"))


# --- Raster, Quellen, Schlüssigkeit -----------------------------------------------------------------------------------------------------------

def test_the_grid_is_48_cells_of_10_seeds_with_ten_methods(band):
    zeilen = band["zeilen"]
    erwartet = [(q, typ, b, k, r) for q, k in C.BAND_ZELLEN for typ in C.TYPEN for b in C.BAND_BREITEN for r in B.RUNDEN_NAMEN]
    assert sorted((z["q"], z["typ"], z["breite"], z["k"], z["runde"]) for z in zeilen) == sorted(erwartet) and len(zeilen) == 48
    assert len(B.laeufe(band)) == 480
    for z in zeilen:
        assert [l["seed"] for l in z["laeufe"]] == list(range(10))
        for l in z["laeufe"]:
            assert list(l["v"]) == list(C.VERFAHREN) and all(len(w) == len(B.FELDER) for w in l["v"].values())


def test_every_row_names_its_source_and_the_file_names_the_environment(band):
    assert band["umgebung"].startswith("Python 3.") and "numpy" in band["umgebung"] and "scipy" in band["umgebung"] and band["beschreibung"]
    assert band["felder"] == B.FELDER and band["verfahren"] == list(C.VERFAHREN)
    for z in band["zeilen"]:
        assert z["quelle"].startswith("tools/messreihe_baender.py mess") and f"Kapazität {z['q']}" in z["quelle"] and f"Fensterbreite {z['breite']}" in z["quelle"]
        assert f"k = {z['k']}" in z["quelle"] and f"Dualpreise der Runde {z['runde']}" in z["quelle"] and "n = 30" in z["quelle"]


def test_all_4800_rows_are_consistent_in_themselves(band):
    """Alle Zeilen: Labels = Vorwärts + Rückwärts, das einseitige Verfahren hat keine Rückwärtsseite und keine Paare, lebende Labels nie mehr als erzeugte, Paare nie mehr als ohne Vorprüfung,
    und in allen 480 Läufen liefern alle zehn Verfahren dieselben besten reduzierten Kosten."""
    zeilen = 0
    for l in B.laeufe(band):
        rc0 = B.wert(l, "uni", "rc")
        for name, v in l["v"].items():
            zeilen += 1
            f = dict(zip(B.FELDER, v))
            assert f["labels"] == f["gF"] + f["gB"] and f["liveF"] <= f["gF"] and f["liveB"] <= f["gB"] and f["paare"] <= f["paare_alle"] and f["kanten"] <= f["kanten_alle"]
            assert f["rc"] == pytest.approx(rc0, abs=1e-5), (l["q"], l["typ"], l["seed"], name)
            if name == "uni":
                assert f["gB"] == 0 and f["paare"] == 0 and f["liveB"] == 0
            else:
                assert f["gB"] >= 1 and f["gF"] >= 1
            if name.startswith("fest"):
                assert f["halbweg"] == pytest.approx(float(name[4:]) * C.HORIZONT)
    assert zeilen == 4800


def test_at_the_end_of_the_column_generation_no_method_finds_a_negative_route(band):
    for l in B.laeufe(band):
        if l["runde"] == "ende":
            assert all(v[B.IDX["rc"]] == 0.0 for v in l["v"].values())
        else:
            assert B.wert(l, "uni", "rc") < 0                                                  # in den Runden 1, 3, 8 gibt es noch eine negative Route


def test_the_duals_file_has_all_rounds_and_the_first_round_is_the_single_trips(duale):
    assert duale["quelle"].startswith("tools/messreihe_baender.py duale") and duale["umgebung"].startswith("Python 3.")
    assert len(duale["eintraege"]) == 120
    tool = _tool()
    for (typ, b, seed, k, q) in tool.alle_schluessel():
        rec = duale["eintraege"][tool.schluessel(typ, b, seed, k, q)]
        assert not rec["abgebrochen"] and set(rec["duale"]) == {"1", "3", "8", "ende"} and rec["runden"] >= 9
        inst = S.instanz_aus_seed(30, seed, b, typ, Q=q)
        assert rec["duale"]["1"] == pytest.approx(list(S.einzelfahrt_preise(inst)), abs=1e-9)    # Runde 1: Dualpreis = Kosten der Einzelfahrt 2 d(0, j)


def test_the_duals_at_the_end_admit_no_negative_route_for_a_sample(duale):
    """Am Ende der Spaltenerzeugung findet das einseitige Pricing mit den gespeicherten Dualpreisen keine negative Route (je Zelle der Seed 0)."""
    tool = _tool()
    for q, k in C.BAND_ZELLEN:
        for typ in C.TYPEN:
            for b in C.BAND_BREITEN:
                inst = S.instanz_aus_seed(30, 0, b, typ, Q=q)
                pi = tuple(duale["eintraege"][tool.schluessel(typ, b, 0, k, q)]["duale"]["ende"])
                assert A.pricing_einseitig(inst, pi, k, max_labels=10 ** 9).routen == [], (q, k, typ, b)


@pytest.mark.parametrize("typ, b, seed, k, q", [("zufaellig", 40, 0, 5, 70), ("gruppiert", 40, 1, 8, 70), ("zufaellig", 100, 2, 5, 120)])
def test_a_column_generation_reproduces_the_stored_bound(duale, typ, b, seed, k, q):
    """Die Spaltenerzeugung mit dem Kern der Demo erreicht die gespeicherte Schranke (der LP-Wert hängt nicht von der Wahl der Dualpreise ab); die Rundenzahl nur mit Toleranz."""
    rec = duale["eintraege"][_tool().schluessel(typ, b, seed, k, q)]
    g = G.duale_der_runden(S.instanz_aus_seed(30, seed, b, typ, Q=q), k, max_labels=10 ** 9)
    assert not g.abgebrochen and g.schranke == pytest.approx(rec["schranke"], abs=1e-4) and abs(g.runden - rec["runden"]) <= 6


# --- Zusammenfassungen -----------------------------------------------------------------------------------------------------------------------

def test_the_pool_summary_follows_from_the_single_values(band):
    p = B.pool(band)
    alle = [(l["v"]["fest0.5"][0] / l["v"]["uni"][0]) for l in B.laeufe(band)]
    assert p["fest0.5"] == {"n": 480, "median": statistics.median(alle), "min": min(alle), "max": max(alle), "weniger": sum(1 for x in alle if x < 1)}
    assert set(p) == set(B.BIDI) and all(v["n"] == 480 for v in p.values())
    z = B.zelle(band["zeilen"][0])
    laeufe = band["zeilen"][0]["laeufe"]
    r = [l["v"]["fest0.5"][0] / l["v"]["uni"][0] for l in laeufe]
    assert z["median"] == statistics.median(r) and z["mittel"] == statistics.mean(r) and z["max"] == max(r) and z["n"] == 10
    assert z["paare_je_label"] == statistics.median(l["v"]["fest0.5"][5] / l["v"]["uni"][0] for l in laeufe)


def test_classes_by_size_cover_every_run_once(band):
    assert sum(n for _, _, n, _ in B.nach_groesse(band)) == 480
    assert sum(B.haeufigkeit_bester_fester(band, q)["n"] for q in C.KAPAZITAETEN) == 480
    for q in C.KAPAZITAETEN:
        h = B.haeufigkeit_bester_fester(band, q)
        assert sum(h[n] for n in B.FESTE) == h["n"]


def test_the_earlier_series_file_names_its_source_and_says_it_is_not_recomputed():
    z = B.lade_fruehere()
    assert "nicht neu gerechnet" in z["quelle"] and "Rohdateien" in z["quelle"] and z["laeufe"] == 480 and set(z["pool"]) == set(B.BIDI)


def test_the_earlier_series_file_equals_the_summary_of_the_raw_files_if_they_are_there():
    tool = _tool()
    if not tool.VORMESSUNG.exists():
        pytest.skip("Rohdateien der Vormessung nicht vorhanden (nur lokal neben diesem Ordner)")
    neu = tool.frueher_zusammenfassung()
    alt = B.lade_fruehere()
    assert json.loads(json.dumps(neu)) == alt


# --- Stichproben neu gerechnet ---------------------------------------------------------------------------------------------------------------

def _gerechnet(inst, pi, k, name):
    tool = _tool()
    return dict(zip(B.FELDER, tool.messe_verfahren(inst, pi, k, name)))


@pytest.mark.parametrize("typ, b, seed, k, q, runde", [("zufaellig", 40, 0, 5, 70, "1"), ("gruppiert", 100, 3, 8, 70, "ende"), ("zufaellig", 100, 9, 5, 120, "3"), ("gruppiert", 40, 5, 5, 120, "8")])
def test_a_band_row_is_reproduced_with_the_kernel_for_all_ten_methods(band, duale, typ, b, seed, k, q, runde):
    """Neu gerechnet mit dem Kern, den gespeicherten Dualpreisen und der Instanz aus dem Zufalls-Seed: jede Spalte jedes Verfahrens stimmt exakt (Rundung wie in der Datei)."""
    z = next(z for z in band["zeilen"] if (z["q"], z["typ"], z["breite"], z["k"], z["runde"]) == (q, typ, b, k, runde))
    gespeichert = next(l for l in z["laeufe"] if l["seed"] == seed)["v"]
    inst = S.instanz_aus_seed(30, seed, b, typ, Q=q)
    pi = tuple(duale["eintraege"][_tool().schluessel(typ, b, seed, k, q)]["duale"][runde])
    for name in C.VERFAHREN:
        assert list(_gerechnet(inst, pi, k, name).values()) == gespeichert[name], name


def test_the_kernel_hits_the_rows_of_the_earlier_series_on_the_earlier_instances():
    """Gegenprobe gegen die frühere Implementierung: drei Instanzen der Vormessung (Pythons `random.Random`, tests/alt_instanz.py) mit ihren Dualpreisen; Labels, Paare, Kanten, Vergleiche,
    beste Kosten, Halbweg und zurückgestellte Verlängerungen aller zehn Verfahren und vier Runden stimmen mit den Zeilen der Rohdatei überein (120 Läufe)."""
    d = json.loads((DATA / "vormessung_stichprobe.json").read_text(encoding="utf-8"))
    assert "Rohdateien" in d["quelle"] and len(d["instanzen"]) == 3
    gezaehlt = 0
    for e in d["instanzen"]:
        inst = alte_instanz(30, e["seed"], e["breite"], Q=e["q"], gruppiert=e["typ"] == "cluster")
        for runde, pi in e["duale"].items():
            for name in C.VERFAHREN:
                got = _gerechnet(inst, tuple(pi), e["k"], name)
                erw = e["erwartet"][runde][name]
                gezaehlt += 1
                assert [got[f] for f in ("labels", "gF", "gB", "liveF", "liveB", "paare", "kanten", "vergleiche", "zurueckgestellt")] == [erw[f] for f in ("labels", "gF", "gB", "liveF", "liveB", "paare", "kanten", "vergleiche", "zurueckgestellt")]
                assert got["rc"] == pytest.approx(erw["rc"], abs=1e-5) and got["halbweg"] == pytest.approx(erw["halbweg"], abs=0.06)
    assert gezaehlt == 120
