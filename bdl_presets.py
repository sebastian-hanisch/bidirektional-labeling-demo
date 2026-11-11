"""Permalink (Begrenzen), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio)."""

import random
from dataclasses import dataclass

import streamlit as st

import bdl_constants as C


def typ_aus_text(text) -> str:
    """Instanztyp aus der Adresszeile; unbekannte Werte lösen einen ValueError aus (der Wert wird dann ignoriert)."""
    if str(text) not in C.TYPEN:
        raise ValueError(text)
    return str(text)


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: object
    default: object
    lo: float | None = None
    hi: float | None = None
    step: int | None = None          # Rasterweite des Reglers: Werte aus der Adresszeile rasten auf das Raster ein
    optionen: tuple | None = None    # feste Auswahl (select_slider): Werte aus der Adresszeile rasten auf die nächste Option ein


SETTING_SPECS = {
    "hand_m": SettingSpec("hm", int, C.DEFAULT_HAND_M, C.HAND_M_MIN, C.HAND_M_MAX, C.HAND_M_STEP),
    "n_slider": SettingSpec("n", int, C.DEFAULT_N, C.N_MIN, C.N_MAX),
    "breite_slider": SettingSpec("b", int, C.DEFAULT_BREITE, C.BREITE_MIN, C.BREITE_MAX, C.BREITE_STEP),
    "typ_radio": SettingSpec("t", typ_aus_text, "zufaellig"),
    "q_slider": SettingSpec("q", int, C.KAPAZITAET, min(C.KAPAZITAETEN), max(C.KAPAZITAETEN), optionen=C.KAPAZITAETEN),
    "k_slider": SettingSpec("k", int, C.DEFAULT_K, min(C.K_OPTIONEN), max(C.K_OPTIONEN), optionen=C.K_OPTIONEN),
    "runde_slider": SettingSpec("r", int, C.DEFAULT_RUNDE, min(C.RUNDEN_OPTIONEN), max(C.RUNDEN_OPTIONEN), optionen=C.RUNDEN_OPTIONEN),
    "halbweg_slider": SettingSpec("m", int, C.DEFAULT_HALBWEG, C.HALBWEG_MIN, C.HALBWEG_MAX, C.HALBWEG_STEP),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
}
PRESET_KEYS = {"hand_m": "hand_m", "n": "n_slider", "breite": "breite_slider", "typ": "typ_radio", "q": "q_slider", "k": "k_slider", "runde": "runde_slider", "halbweg": "halbweg_slider",
               "seed": "seed_input"}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf die Reglergrenzen begrenzt und aufs Raster der Regler gerastet."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
            except (ValueError, TypeError):
                continue
            if isinstance(value, (int, float)):
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
                if spec.step:
                    value = spec.lo + round((value - spec.lo) / spec.step) * spec.step
                if spec.optionen:
                    value = min(spec.optionen, key=lambda o: (abs(o - value), o))
            st.session_state[state_key] = value
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][key]


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen
    Standardwert) mit dem Session State. Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS,
    dann hebt auch seine Änderung die Markierung auf (tests/test_layout.py prüft das für jeden Regler)."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            st.session_state.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default)
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
