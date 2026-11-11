"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Raster."""

import bdl_constants as C
import bdl_evaluation as ev
import bdl_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_on_the_grid():
    for name, p in C.PRESETS.items():
        assert C.HAND_M_MIN <= p["hand_m"] <= C.HAND_M_MAX and p["hand_m"] % C.HAND_M_STEP == 0, name
        assert C.N_MIN <= p["n"] <= C.N_MAX and C.BREITE_MIN <= p["breite"] <= C.BREITE_MAX and (p["breite"] - C.BREITE_MIN) % C.BREITE_STEP == 0, name
        assert p["typ"] in C.TYPEN and p["q"] in C.KAPAZITAETEN and p["k"] in C.K_OPTIONEN and p["runde"] in C.RUNDEN_OPTIONEN, name
        assert C.HALBWEG_MIN <= p["halbweg"] <= C.HALBWEG_MAX and p["halbweg"] % C.HALBWEG_STEP == 0 and 0 <= p["seed"] <= C.SEED_MAX, name


def test_default_preset_equals_the_default_settings():
    standard = next(iter(C.PRESETS.values()))
    assert ev.Settings(standard["hand_m"], standard["n"], standard["breite"], standard["typ"], standard["q"], standard["k"], standard["runde"], standard["halbweg"], standard["seed"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key_and_defaults_are_valid_options():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    for key in ("q_slider", "k_slider", "runde_slider"):
        assert P.SETTING_SPECS[key].default in P.SETTING_SPECS[key].optionen


def test_presets_names_say_what_they_set():
    """Namen gegen die Werte (DEMO-PLAYBOOK §11 Punkt 5): „nur rückwärts“ heißt M = 0, „zu früh“ ein Viertel, „Kapazität 120, 20 Kunden, erste Runde“ genau das, usw."""
    p = C.PRESETS
    assert p["Handbeispiel: nur rückwärts (M = 0)"]["hand_m"] == 0
    assert p["Halbweg zu früh (25 % von H)"]["halbweg"] == 25
    k = p["Kapazität 120, 20 Kunden, erste Runde"]
    assert (k["q"], k["n"], k["runde"]) == (120, 20, 1)
    g = p["Gruppiert, weite Fenster, Ende der Spaltenerzeugung"]
    assert (g["typ"], g["breite"], g["runde"]) == ("gruppiert", C.BREITE_MAX, C.RUNDE_ENDE)
    assert p["Kleine Instanz (8 Kunden), Ende"]["n"] == 8 and p["Kleine Instanz (8 Kunden), Ende"]["runde"] == C.RUNDE_ENDE
