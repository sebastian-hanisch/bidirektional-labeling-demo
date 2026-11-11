"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: lädt app.py mit den Standardeinstellungen, klickt jeden Knopf, fährt jeden Regler an seine Grenzen
(einzeln sowie alle Minima und alle Maxima zugleich), prüft jede Voreinstellung mit ihrer erwarteten Verdikt-Zeile und den Permalink.
Expander werden nie per Index oder als feste Titelliste angesprochen (DEMO-PLAYBOOK §2)."""

import os
import re

import pytest
from streamlit.testing.v1 import AppTest

import bdl_constants as C

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
NBSP = " "


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at) -> str:
    return " ".join(x.value for kind in (at.success, at.warning, at.info, at.error) for x in kind).replace(NBSP, " ")


def _alle_texte(at) -> str:
    return (_texts(at) + " " + " ".join(m.value for m in at.markdown)).replace(NBSP, " ")


def test_app_loads_without_exception():
    at = _fresh_app()
    assert not at.error


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


@pytest.mark.parametrize("key, optionen", [("q_slider", C.KAPAZITAETEN), ("k_slider", C.K_OPTIONEN), ("runde_slider", C.RUNDEN_OPTIONEN)])
def test_every_option_of_the_choice_sliders_runs(key, optionen):
    for option in optionen:
        at = _fresh_app()
        at.sidebar.select_slider(key=key).set_value(option).run(timeout=TIMEOUT)
        assert not at.exception and not at.error, (key, option, [str(e) for e in at.exception])


@pytest.mark.parametrize("typ", C.TYPEN)
def test_both_instance_types_run(typ):
    at = _fresh_app()
    at.sidebar.radio(key="typ_radio").set_value(typ).run(timeout=TIMEOUT)
    assert not at.exception and not at.error


@pytest.mark.parametrize("edge", ["min", "max"])
def test_all_controls_at_their_minimum_or_maximum_together(edge):
    """Alle Regler am Rand zugleich; „max“ ist der Worst-Case der Live-Rechnung (30 Kunden, Fensterbreite 100, gruppiert, Kapazität 120, Gedächtnis 8, Runde Ende): er rechnet oder meldet seine Größe."""
    at = _fresh_app()
    for key in ("hand_m", "n_slider", "breite_slider", "halbweg_slider"):
        s = at.sidebar.slider(key=key)
        s.set_value(int(s.min if edge == "min" else s.max))
    at.sidebar.select_slider(key="q_slider").set_value(max(C.KAPAZITAETEN) if edge == "max" else min(C.KAPAZITAETEN))
    at.sidebar.select_slider(key="k_slider").set_value(max(C.K_OPTIONEN) if edge == "max" else min(C.K_OPTIONEN))
    at.sidebar.select_slider(key="runde_slider").set_value(max(C.RUNDEN_OPTIONEN) if edge == "max" else min(C.RUNDEN_OPTIONEN))
    at.sidebar.radio(key="typ_radio").set_value("gruppiert" if edge == "max" else "zufaellig")
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert not at.error


def test_seed_extremes_do_not_raise():
    for seed in (0, C.SEED_MAX):
        at = _fresh_app()
        at.sidebar.number_input(key="seed_input").set_value(seed).run(timeout=TIMEOUT)
        assert not at.exception, (seed, [str(e) for e in at.exception])


# --- Voreinstellungen: erwartete Verdikt-Zeile -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name, erwartet", [
    ("Standard: Handbeispiel und 15 Kunden", ["Halbweg 20: bidirektional **16** Labels (8 vorwärts + 8 rückwärts) gegen **35** einseitig", "Bidirektional erzeugt hier **36 %** der Labels", "189 (121 vorwärts + 68 rückwärts) gegen 520",
                                              "dieselbe beste Route 1-5-6", "Am wenigsten Labels bei einem Halbweg von **50 % von H**", "Dynamisch ist hier in allen vier Fassungen schlechter als fest H/2"]),
    ("Handbeispiel: nur rückwärts (M = 0)", ["Halbweg 0: bidirektional **36** Labels (1 vorwärts + 35 rückwärts) gegen **35** einseitig", "**nicht weniger** Labels als einseitig"]),
    ("Halbweg zu früh (25 % von H)", ["Bidirektional erzeugt hier **mehr Labels als einseitig**: 889 (6 vorwärts + 883 rückwärts) gegen 748, also 119 %", "**Halbweg ungünstig:** bei 25 % von H sind es 889 Labels, bei H/2 nur 280"]),
    ("Gruppiert, weite Fenster, Ende der Spaltenerzeugung", ["Bidirektional erzeugt hier **56 %** der Labels", "1 059 (544 vorwärts + 515 rückwärts) gegen 1 887", "keine Route mit negativen reduzierten Kosten"]),
    ("Kapazität 120, 20 Kunden, erste Runde", ["Bidirektional erzeugt hier **20 %** der Labels", "679 (359 vorwärts + 320 rückwärts) gegen 3 438", "dieselbe beste Route 16-2-20-13-11-12-1"]),
    ("Kleine Instanz (8 Kunden), Ende", ["Bidirektional erzeugt hier **50 %** der Labels", "29 (11 vorwärts + 18 rückwärts) gegen 58", "keine Route mit negativen reduzierten Kosten"]),
])
def test_each_preset_runs_and_shows_its_expected_verdict(name, erwartet):
    at = _fresh_app()
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    text = _alle_texte(at)
    for stueck in erwartet:
        assert stueck in text, (name, stueck)


def test_preset_sets_every_regler_value():
    at = _fresh_app()
    name = "Kapazität 120, 20 Kunden, erste Runde"
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    p = C.PRESETS[name]
    assert [at.sidebar.slider(key=k).value for k in ("hand_m", "n_slider", "breite_slider", "halbweg_slider")] == [p["hand_m"], p["n"], p["breite"], p["halbweg"]]
    assert at.sidebar.number_input(key="seed_input").value == p["seed"] and at.sidebar.radio(key="typ_radio").value == p["typ"]
    assert [at.sidebar.select_slider(key=k).value for k in ("q_slider", "k_slider", "runde_slider")] == [p["q"], p["k"], p["runde"]]


# --- Permalink ---------------------------------------------------------------------------------------------------------------------------

def test_permalink_sets_the_regler_clamps_to_the_bounds_and_snaps_to_the_grid():
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.query_params["n"] = "999"          # über dem Maximum
    at.query_params["b"] = "63"           # nicht auf dem Raster 40, 60, 80, 100
    at.query_params["k"] = "6"            # zwischen den Optionen 5 und 8: die nähere gewinnt
    at.query_params["q"] = "100"          # zwischen 70 und 120: die nähere
    at.query_params["r"] = "50"           # zwischen 8 und 99: die nähere (8)
    at.query_params["hm"] = "13"          # Raster 5: 15
    at.query_params["m"] = "-20"          # unter dem Minimum
    at.query_params["t"] = "gruppiert"
    at.query_params["seed"] = "42"
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert at.sidebar.slider(key="n_slider").value == C.N_MAX
    assert at.sidebar.slider(key="breite_slider").value == 60
    assert at.sidebar.select_slider(key="k_slider").value == 5 and at.sidebar.select_slider(key="q_slider").value == 120 and at.sidebar.select_slider(key="runde_slider").value == 8
    assert at.sidebar.slider(key="hand_m").value == 15 and at.sidebar.slider(key="halbweg_slider").value == C.HALBWEG_MIN
    assert at.sidebar.radio(key="typ_radio").value == "gruppiert" and at.sidebar.number_input(key="seed_input").value == 42


def test_permalink_ignores_garbage_values():
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.query_params["n"] = "abc"
    at.query_params["seed"] = ""
    at.query_params["t"] = "kreis"
    at.query_params["k"] = "x"
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert at.sidebar.slider(key="n_slider").value == C.DEFAULT_N and at.sidebar.radio(key="typ_radio").value == "zufaellig" and at.sidebar.select_slider(key="k_slider").value == C.DEFAULT_K


# --- Experimente -------------------------------------------------------------------------------------------------------------------------

def test_the_handbeispiel_slider_changes_the_hand_counts_and_the_table_rows():
    at = _fresh_app()
    assert [m.value for m in at.metric if m.label == "Vorwärtslabels"] == ["8"] and [m.value for m in at.metric if m.label == "Rückwärtslabels"] == ["8"]
    at.sidebar.slider(key="hand_m").set_value(30).run(timeout=TIMEOUT)
    assert not at.exception
    assert [m.value for m in at.metric if m.label == "Vorwärtslabels"] == ["29"] and [m.value for m in at.metric if m.label == "Rückwärtslabels"] == ["4"]


def test_the_halfway_slider_changes_the_live_counts():
    at = _fresh_app()
    vorher = [m.value for m in at.metric if m.label == "Labels bidirektional"]
    at.sidebar.slider(key="halbweg_slider").set_value(25).run(timeout=TIMEOUT)
    assert not at.exception
    nachher = [m.value for m in at.metric if m.label == "Labels bidirektional"]
    assert vorher and nachher and vorher != nachher


def test_the_cell_table_follows_the_round_choice():
    at = _fresh_app()
    erste = [m for m in at.markdown if m.value.startswith("**Je Zelle**")]
    assert erste and "dem Ende" in erste[0].value
    at.radio(key="band_runde").set_value("1").run(timeout=TIMEOUT)
    assert not at.exception
    assert any("Runde 1" in m.value for m in at.markdown if m.value.startswith("**Je Zelle**"))


def test_the_curve_waits_for_the_button_when_the_instance_is_large():
    """Bei mehr einseitigen Labels als LIVE_KURVE_LIMIT rechnet die App die Kurve nur auf Knopfdruck."""
    at = _fresh_app()
    at.sidebar.slider(key="n_slider").set_value(27)
    at.sidebar.slider(key="breite_slider").set_value(100)
    at.sidebar.radio(key="typ_radio").set_value("gruppiert")
    at.sidebar.select_slider(key="runde_slider").set_value(1)
    at.sidebar.select_slider(key="q_slider").set_value(120).run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("rechnet die App sie nur auf Knopfdruck" in i.value.replace(NBSP, " ") for i in at.info)
    assert [b.label for b in at.button if b.key == "kurve_knopf"] == ["Kurve trotzdem live rechnen"]
    at.button(key="kurve_knopf").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("Am wenigsten Labels bei einem Halbweg" in s.value for s in list(at.success) + list(at.info))


# --- Aufbau ------------------------------------------------------------------------------------------------------------------------------

def test_expanders_are_found_by_their_titles_and_the_first_is_the_how_it_works_one():
    at = _fresh_app()
    titel = {e.label for e in at.expander}
    assert {"So funktioniert bidirektionales Labeling", "📐 Mathematische Formulierung", "⚠️ Annahmen, Grenzen und bekannte Probleme"} <= titel
    assert next(e for e in at.expander if e.label == "So funktioniert bidirektionales Labeling").proto.expanded


def test_five_experiments_and_the_section_of_the_assumptions_exist():
    at = _fresh_app()
    koepfe = [s.value for s in at.subheader]
    assert len([k for k in koepfe if k.startswith("🔬 Experiment")]) == 5
    assert "🚧 Wo die Annahmen enden" in koepfe


def test_no_dead_file_links_in_the_markdown():
    at = _fresh_app()
    for m in at.markdown:
        for ziel in re.findall(r"\]\(([^)]+)\)", m.value):
            assert ziel.startswith("http"), ziel


def test_every_chart_has_its_own_key_and_the_page_has_no_error_box():
    at = _fresh_app()
    assert not at.error and len(at.get("plotly_chart")) >= 8
