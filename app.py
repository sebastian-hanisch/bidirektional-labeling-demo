"""Bidirektionales Labeling – von beiden Enden rechnen und in der Mitte verbinden: interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Zeigt an einem Handbeispiel mit 6 Kunden und an Kundeninstanzen, wie das Labeling des Pricings (Spaltenerzeugung) mit Zeit, Last und Dominanz zusätzlich vom Ende des Horizonts
rückwärts rechnet, beide Seiten bis zu einem Halbweg in der Zeit wachsen lässt und die Hälften verbindet: wie viele Labels das spart und was das Verbinden kostet. Aufbau nach DEMO-PLAYBOOK §2.

Lauffähig mit: streamlit run app.py
"""

import dataclasses

import pandas as pd
import streamlit as st

import bdl_baender as B
import bdl_constants as C
import bdl_evaluation as ev
import bdl_tabellen as T
import bdl_visualization as V
from bdl_layout import dunkles_design, kopf_css
from bdl_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from bdl_texts import ASSUMPTIONS_MARKDOWN

st.set_page_config(page_title="Bidirektionales Labeling – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _hand(m):
    return ev.analyse_hand(m)


@st.cache_data(show_spinner=False)
def _live(settings):
    return ev.analyse_live(settings)


@st.cache_data(show_spinner=False)
def _kurve(settings):
    return ev.analyse_kurve(settings)


@st.cache_data(show_spinner=False)
def _dyn(settings):
    return ev.analyse_dynamisch(settings)


@st.cache_data(show_spinner=False)
def _band():
    band = B.lade_baender()
    return band, B.zusammenfassung(band), B.verschwendet_anteil(band), B.halbweg_dynd(band)


def _df(rows, ohne=()):
    """Tabelle ohne die Hilfsspalten (Schlüssel mit Unterstrich und die in `ohne` genannten)."""
    return pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_") and k not in ohne} for r in rows])


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in bdl_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("↔️ Bidirektionales Labeling – von beiden Enden rechnen, in der Mitte verbinden")
st.markdown(
    """
Bei der **Spaltenerzeugung** (etwa in der Tourenplanung) sucht das **Pricing** eine neue Tour, die weniger kostet, als ihre Kunden an **Dualpreisen** einbringen. Das **Labeling** der früheren Demos der Reihe
baut dazu Teilwege vom Depot aus auf; ein **Label** ist ein Teilweg mit Kosten, Zeit, Last und den gesperrten Kunden, und die **Dominanz** streicht Labels, die in allem schlechter sind.
Das **bidirektionale Labeling** rechnet zusätzlich vom **Ende** des Zeithorizonts rückwärts. Beide Seiten wachsen nur bis zu einem **Halbweg** in der Zeit, und in der Mitte werden passende Hälften **verbunden**.
Diese Demo zählt an einem Handbeispiel Label für Label und an Kundeninstanzen, wie viele Labels das gegenüber dem einseitigen Verfahren spart, wo der beste Halbweg liegt, was das Verbinden kostet und warum eine einfache dynamische
Wahl des Halbwegs gegenüber dem festen Halbweg H/2 hier nichts gewinnt. Gezählt werden **erzeugte Labels**; die Verbindungspaare stehen getrennt daneben.

Weiter unten: fünf Experimente (🔬), der Abschnitt **🚧 Wo die Annahmen enden** und die Expander **📐 Mathematische Formulierung** und **⚠️ Annahmen, Grenzen und bekannte Probleme**.
"""
)

with st.expander("So funktioniert bidirektionales Labeling", expanded=True):
    st.markdown(
        """
1. **Einseitig:** Vom Depot (Zeit 0) wächst jeder Teilweg Kunde für Kunde. Ein **Vorwärtslabel** hält den frühesten Beginn der Bedienung, die reduzierten Kosten (Entfernungen minus Dualpreise), die Last und die gesperrten Kunden.
   Passt kein Weiterfahren (Last, Fensterende), endet der Weg dort; ein Label, das in allem mindestens so gut ist wie ein anderes am selben Kunden, **dominiert** es.
2. **Rückwärts:** Dieselbe Rechnung vom Depot-Ende (Zeit H) aus. Ein **Rückwärtslabel** am Kunden j hält den **spätesten** Beginn der Bedienung, so dass der Rest der Route bis zum Ende noch zulässig bleibt, und die Kosten ab j.
   Dominanz gilt entsprechend, nur dass ein späterer spätester Beginn besser ist.
3. **Halbweg:** Vorwärtslabels wachsen nur, solange ihr Beginn höchstens M ist, Rückwärtslabels nur, solange ihr spätester Beginn mindestens M ist. Was jenseits liegt, übernimmt die andere Seite. Das spart Labels, wenn der Halbweg passt: Beide Seiten überbrücken dann nur etwa eine halbe Zeitspanne.
4. **Verbinden:** Für jede Kante (i, j) werden Vorwärtslabels in i und Rückwärtslabels in j zu Paaren gefügt. Ein Paar passt, wenn die Fahrt von i nach j rechtzeitig ist, die Lasten zusammen in das Fahrzeug passen und die gesperrten Kunden keinen gemeinsamen Kunden haben.
   Die Kosten des Paares sind Vorwärtskosten plus Kante plus Rückwärtskosten.
5. **Ergebnis:** Die beste Verbindung hat dieselben besten reduzierten Kosten wie beim einseitigen Verfahren (die Demo prüft das in jedem Lauf); bei Gleichstand kann die Route eine andere sein. Gespart werden Labels; das Verbinden kostet Paarprüfungen, die hier getrennt gezählt werden.

Was Labeling, Dominanz, Zeitfenster und Dualpreise genau sind, zeigen die früheren Demos der Reihe; hier steht nur, was die zweite Richtung ändert. Eine Anwendung im Pricing einer Tourenplanung mit einseitigem Labeling:
[crew-pairing-demo](https://github.com/sebastian-hanisch/crew-pairing-demo).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Handbeispiel (Experiment 1)**")
    hand_m = st.slider("Halbweg M des Handbeispiels", *bounds("hand_m"), step=C.HAND_M_STEP, key="hand_m",
                       help="Zeitpunkt, an dem sich Vorwärts- und Rückwärtsseite treffen (Horizont 40). 0: alles rückwärts, 40: alles vorwärts, 20: die Mitte.")
    st.markdown("**Kundeninstanz (Experimente 2 bis 4)**")
    n = st.slider("Kunden n", *bounds("n_slider"), key="n_slider", help="Zahl der Kunden der Live-Rechnung; das Depot liegt in der Mitte des Quadrats. Die Messreihen (Experiment 5) haben 30 Kunden.")
    breite = st.slider("Fensterbreite", *bounds("breite_slider"), step=C.BREITE_STEP, key="breite_slider",
                       help="Breite der Zeitfenster der Kunden: je enger, desto weniger Wege sind zulässig.")
    typ = st.radio("Lage der Kunden", list(C.TYPEN), format_func=lambda t: C.TYP_NAMEN[t], key="typ_radio", help="Gleichverteilt im Quadrat oder um fünf Zentren gruppiert.")
    q = st.select_slider("Kapazität", options=list(C.KAPAZITAETEN), key="q_slider", help="Kapazität des Fahrzeugs; die Last der Kunden liegt zwischen 5 und 25.")
    k = st.select_slider("Gedächtnis k", options=list(C.K_OPTIONEN), key="k_slider",
                         help="Wie viele der nächsten Kunden in einem Label gesperrt bleiben (ng-Routen). Größeres k verhindert mehr Wiederholungen, erzeugt aber mehr Labels; k = 1 sperrt nur den letzten Kunden.")
    runde = st.select_slider("Dualpreise aus", options=list(C.RUNDEN_OPTIONEN), format_func=ev.runde_label, key="runde_slider",
                             help="Aus welcher Runde einer Spaltenerzeugung die Dualpreise stammen: Runde 1 (nur Einzelfahrten im Master), Runde 3, Runde 8 oder das Ende (das Pricing findet keine neue Route mehr).")
    halbweg = st.slider("Halbweg M in Prozent von H", *bounds("halbweg_slider"), step=C.HALBWEG_STEP, key="halbweg_slider",
                        help="Wo sich beide Seiten treffen, als Anteil des Horizonts H = 300. 50: die Mitte.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"hand_m": int(hand_m), "n_slider": int(n), "breite_slider": int(breite), "typ_radio": typ, "q_slider": int(q), "k_slider": int(k), "runde_slider": int(runde),
                   "halbweg_slider": int(halbweg), "seed_input": int(seed)})

settings = ev.Settings(int(hand_m), int(n), int(breite), typ, int(q), int(k), int(runde), int(halbweg), int(seed))
live_key = dataclasses.replace(settings, hand_m=C.DEFAULT_HAND_M)                               # was nicht in die Live-Rechnung eingeht, steht nicht im Schlüssel
kurve_key = dataclasses.replace(live_key, halbweg_pct=C.DEFAULT_HALBWEG)
band, zus, verschw, mstar = _band()
h = _hand(settings.hand_m)
inst = h.inst
if h.fehler:
    st.error(f"Prüfung des Ergebnisses fehlgeschlagen: {h.fehler}")

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: das Handbeispiel")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Labels einseitig", ev.zahl(h.uni.labels), delta=f"{h.uni.dominiert_v} dominiert, {h.uni.lebend_v} am Ende", delta_color="off")
m2.metric(f"Labels bidirektional (M = {ev.zahl_kurz(h.m)})", ev.zahl(h.bidi.labels), delta=f"{h.bidi.erzeugt_v} vorwärts + {h.bidi.erzeugt_r} rückwärts", delta_color="off")
m3.metric("Verbindungspaare", ev.zahl(h.bidi.paare), delta=f"über {h.bidi.kanten} Kanten", delta_color="off")
m4.metric("Beste Route", ev.weg_text(h.bidi.beste[1]) if h.bidi.beste else "keine", delta=f"reduzierte Kosten {ev.zahl_kurz(h.bidi.beste_rc)}", delta_color="off")
st.plotly_chart(V.build_handnetz(inst, h.pi, h.bidi.beste[1] if h.bidi.beste else ()), width="stretch", key="hand_chart")
st.caption("Depot (Raute) und 6 Kunden mit Last, Dualpreis π und Zeitfenster [früh, spät] für den Beginn der Bedienung. Grün: die beste Route, die beide Verfahren finden. Die Linien sind Luftlinien; gerechnet wird mit dem Manhattan-Abstand.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie viele Labels spart das Rechnen von beiden Enden, und was kostet das Verbinden?")
with st.spinner("Die Dualpreise und beide Verfahren werden gerechnet …"):
    a = _live(live_key)
if a.fehler:
    st.error(f"Prüfung des Ergebnisses fehlgeschlagen: {a.fehler}")
st.caption(f"Kundeninstanz aus der Seitenleiste: {settings.n} Kunden, {C.TYP_NAMEN[settings.typ]}, Fensterbreite {settings.breite}, Kapazität {settings.q}, Gedächtnis k = {settings.k}, Dualpreise aus {ev.runde_label(settings.runde)}, Halbweg {settings.halbweg_pct} % von H.")
kind, text = ev.verdict_labels(a)
getattr(st, kind)(text)
kind, text = ev.verdict_verbinden(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 1: Handbeispiel Schritt für Schritt ----------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Von beiden Enden, Schritt für Schritt (Handbeispiel)")
st.markdown(
    f"Das Handbeispiel hat 6 Kunden, Bedienzeit 2, Kapazität 9 und den Horizont H = 40. Der Halbweg M steht in der Seitenleiste (jetzt **{ev.zahl_kurz(h.m)}**). "
    "Der Zeitstrahl zeigt jedes Label: Kreise sind **Vorwärtslabels** (Beginn t), Rauten **Rückwärtslabels** (spätester Beginn T), hohl sind die dominierten oder verdrängten. Die rote Linie ist der Halbweg."
)
st.plotly_chart(V.build_zeitstrahl(inst, h.bidi.vor, h.bidi.rueck, h.m), width="stretch", key="timeline_chart")
t1, t2, t3, t4 = st.columns(4)
t1.metric("Vorwärtslabels", h.bidi.erzeugt_v, delta=f"{h.bidi.lebend_v} leben am Ende", delta_color="off")
t2.metric("Rückwärtslabels", h.bidi.erzeugt_r, delta=f"{h.bidi.lebend_r} leben am Ende", delta_color="off")
t3.metric("Verbindungspaare", h.bidi.paare, delta=f"{h.bidi.kanten} Kanten geprüft", delta_color="off")
t4.metric("Dominanzvergleiche", h.bidi.vergleiche, delta=f"einseitig {h.uni.vergleiche}", delta_color="off")
st.caption(
    f"Am Halbweg endeten {h.bidi.abgeschnitten_v} Vorwärts- und {h.bidi.abgeschnitten_r} Rückwärtsverlängerungen (kein Label: die andere Seite übernimmt). "
    "Ein Beispiel einer Rechnung: Das Label F06 (Kunde 6, Weg 5, 6) entsteht aus F02 (Kunde 5, Beginn 9) über die Kante 5 → 6: Ankunft 9 + 2 + 7 = 18 ≤ 19 (Fensterende), Kosten −1,5 + 7 − 10,5 = −5, Last 2 + 3 = 5."
)
with st.expander("Vorwärtslabels (Beginn t bis M)", expanded=True):
    st.dataframe(_df(ev.label_zeilen(h.bidi.vor)), hide_index=True, width="stretch")
    st.caption("Reihenfolge der Erzeugung; „gesperrt“ ist das Gedächtnis (hier alle besuchten Kunden). Ein Label, das beim Erzeugen von einem bestehenden dominiert wird, kommt nie in die Warteschlange; ein später dominiertes wird verdrängt.")
with st.expander("Rückwärtslabels (spätester Beginn T ab M)", expanded=True):
    st.dataframe(_df(ev.label_zeilen(h.bidi.rueck)), hide_index=True, width="stretch")
    st.caption("B00 ist das Depot-Ende (T = 40). Die Kosten eines Rückwärtslabels enthalten die Kante zum Nachfolger und den Dualpreis des Kunden selbst; „weiter zu“ nennt den Nachfolger.")
paare = ev.paar_zeilen(inst, h.bidi.vor, h.bidi.rueck)
gruende = {g: sum(1 for p in paare if p["_grund"] == g and not p["_uebersprungen"]) for g in ("passt", "Zeit", "Last", "Gedächtnis")}
with st.expander("Verbindung: alle Paare je Kante mit Begründung", expanded=True):
    st.markdown(
        f"Über jede Kante (i, j) mit Labels auf beiden Seiten werden Vorwärtslabels in i und Rückwärtslabels in j zusammengesetzt. **{h.bidi.paare}** Paare wurden geprüft: **{gruende['passt']}** passen, verworfen wegen der Zeit {gruende['Zeit']}, "
        f"wegen der Last {gruende['Last']}, wegen eines gemeinsamen Kunden {gruende['Gedächtnis']}."
    )
    st.dataframe(_df(paare), hide_index=True, width="stretch")
    st.markdown("**Die beste Verbindung je Kante** (nur solche mit negativen reduzierten Kosten):")
    st.dataframe(pd.DataFrame([{"Kante": f"({v.kante[0]}, {v.kante[1]})", "Vorwärts": ev.etikett(True, v.vor), "Rückwärts": ev.etikett(False, v.rueck), "Route": ev.weg_text(v.route), "reduzierte Kosten": ev.zahl_kurz(v.rc)}
                               for v in sorted(h.bidi.verbindungen, key=lambda v: v.rc)]), hide_index=True, width="stretch")
    if h.bidi.paare_alle != h.bidi.paare:
        st.caption(f"Eine Vorprüfung überspringt Kanten, bei denen schon das früheste Vorwärtslabel zu spät für das späteste Rückwärts-T kommt; ohne sie wären es {h.bidi.paare_alle} Paare über {h.bidi.kanten_alle} Kanten. Gezählt werden die geprüften Paare.")
with st.expander("Zum Vergleich: das einseitige Verfahren (alle Labels)"):
    st.dataframe(_df(ev.label_zeilen(h.uni.vor, einseitig=True)), hide_index=True, width="stretch")
    st.caption(f"{h.uni.labels} erzeugte Labels, davon {h.uni.dominiert_v} dominiert, {h.uni.lebend_v} leben am Ende, {h.uni.vergleiche} Dominanzvergleiche. Es findet dieselben negativen Routen: " + "; ".join(f"{ev.weg_text(r)} ({ev.zahl_kurz(rc)})" for rc, r in h.uni.routen) + ".")
st.markdown(f"**Halbweg-Reihe:** dasselbe Beispiel mit anderen Halbwegen (M = 0: nur rückwärts, M = 40: nur vorwärts; einseitig sind es {h.uni.labels} Labels).")
st.dataframe(pd.DataFrame(T.tabelle_hand_reihe(h)), hide_index=True, width="stretch")
st.plotly_chart(V.build_halbweg_kurve([100 * r[0] / inst.H for r in h.reihe], [r[1] for r in h.reihe], [r[2] for r in h.reihe], [r[1] + r[2] for r in h.reihe], h.uni.labels,
                                      marken=[(100.0 * h.m / inst.H, "gewählt", C.COLOR_BAD)]), width="stretch", key="hand_curve_chart")
st.caption("Die Summe zählt beide Starts mit; bei M = 0 und M = 40 besteht eine Seite nur aus ihrem Start (36 gegen 35 einseitige Labels).")
st.markdown(f"**Gegenprobe:** alle zulässigen elementaren Routen des Handbeispiels aufgezählt (Tiefensuche, ohne Labeling): **{len(h.wege)}** Routen, davon **{h.negativ_wege}** mit negativen reduzierten Kosten; die beste ist {ev.weg_text(h.bester_weg[1])} mit {ev.zahl_kurz(h.bester_weg[0])}.")
kind, text = ev.verdict_hand(h)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 2: Kundeninstanz live ----------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Größe und Halbweg an einer Kundeninstanz")
st.markdown(
    f"Eine Kundeninstanz im Stil der Solomon-Benchmarks (selbst erzeugt, nicht die Originalinstanzen): Depot in der Mitte eines Quadrats von 100 × 100, Fahrzeit gleich Entfernung, Bedienzeit {C.BEDIENZEIT}, Horizont {C.HORIZONT}, "
    "Last 5 bis 25 je Kunde. Die Dualpreise kommen aus einer Spaltenerzeugung mit einseitigem Labeling (Runde in der Seitenleiste); beide Verfahren rechnen dann mit denselben Preisen. "
    f"Eine Obergrenze von {ev.zahl(C.LABEL_CAP)} erzeugten Labels je Lauf schützt die Rechenzeit."
)
if a.zu_gross:
    st.warning(f"Zu groß für die Live-Rechnung: {a.zu_gross}. Die Messreihen in Experiment 5 zeigen größere Fälle.")
else:
    hinweis = (f" (die Spaltenerzeugung endet nach {a.runde_tatsaechlich} Runden: es gelten die Preise ihres Endes)" if settings.runde not in (1, C.RUNDE_ENDE) and a.runde_tatsaechlich != settings.runde else "")
    st.caption(f"Dualpreise aus {'dem Ende' if settings.runde == C.RUNDE_ENDE else 'Runde ' + str(settings.runde)}{hinweis}; die Spaltenerzeugung erzeugte dafür {ev.zahl(a.labels_duale)} Labels.")
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Labels einseitig", ev.zahl(a.uni.labels), delta=f"{ev.zahl(a.uni.vergleiche)} Dominanzvergleiche", delta_color="off")
    e2.metric("Labels bidirektional", ev.zahl(a.bidi.labels), delta=f"{ev.zahl(a.bidi.erzeugt_v)} vorwärts + {ev.zahl(a.bidi.erzeugt_r)} rückwärts", delta_color="off")
    e3.metric("Verhältnis", ev.prozent(ev.quote(a.bidi.labels, a.uni.labels)), delta=f"{ev.zahl(a.bidi.vergleiche)} Dominanzvergleiche", delta_color="off")
    e4.metric("Verbindungspaare", ev.zahl(a.bidi.paare), delta=f"{ev.zahl(a.bidi.kanten)} Kanten", delta_color="off")
    gleich_rc, gleich_route = ev.gleiche_route(a.uni, a.bidi)
    st.markdown(f"**Dieselben besten reduzierten Kosten wie einseitig: {'ja' if gleich_rc else 'NEIN'}** "
                + (f"(beste Route einseitig {ev.weg_text(a.uni.beste[1])}, bidirektional {ev.weg_text(a.bidi.beste[1])}, reduzierte Kosten {ev.zahl(a.uni.beste_rc, 2)}; "
                   f"{'dieselbe Route' if gleich_route else 'verschiedene, gleich gute Routen'})." if a.uni.beste else "(beide Verfahren finden keine Route mit negativen reduzierten Kosten)."))
    kind, text = ev.verdict_halbweg_wahl(a, settings.halbweg_pct)
    getattr(st, kind)(text)
    st.caption("Die Rechenzeit steht nicht da: Sekunden hängen von der Last des Rechners ab und sind nicht festgeschrieben; gezählt werden Labels und Paare.")

st.markdown("---")

# --- Experiment 3: bester Halbweg --------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Wo liegt der beste Halbweg?")
st.markdown(
    "Dieselbe Kundeninstanz, nun mit dem Halbweg M von 0 % bis 100 % von H in Schritten von 10 %. Bei 0 % wächst alles rückwärts, bei 100 % alles vorwärts: Das sind einseitige Verfahren. "
    "Zu früh gewählt, wächst die Rückwärtsseite fast über den ganzen Horizont, zu spät die Vorwärtsseite; dazwischen liegt ein Minimum."
)
kurve = None
if a.zu_gross:
    st.info("Ohne Live-Rechnung der Instanz gibt es hier keine Kurve.")
else:
    frei = st.session_state.get("kurve_frei") == repr(kurve_key)
    if a.uni.labels <= C.LIVE_KURVE_LIMIT or frei:
        with st.spinner("Die Halbweg-Kurve wird gerechnet …"):
            kurve = _kurve(kurve_key)
    else:
        st.info(f"Die Kurve braucht elf Läufe; bei {ev.zahl(a.uni.labels)} einseitigen Labels rechnet die App sie nur auf Knopfdruck (Grenze: {ev.zahl(C.LIVE_KURVE_LIMIT)} Labels).")
        if st.button("Kurve trotzdem live rechnen", key="kurve_knopf"):
            st.session_state["kurve_frei"] = repr(kurve_key)
            st.rerun()
if kurve is not None:
    pk = kurve.punkte
    st.plotly_chart(V.build_halbweg_kurve([p.prozent for p in pk], [p.erzeugt_v for p in pk], [p.erzeugt_r for p in pk], [p.summe for p in pk], kurve.uni_labels,
                                          marken=[(kurve.bester.prozent, "bester", C.COLOR_VOR), (50, "H/2", C.COLOR_SUMME)] + ([(100.0 * kurve.dynd.halbweg / C.HORIZONT, "M* von dynD", C.COLOR_RUECK)] if kurve.dynd.halbweg else [])),
                    width="stretch", key="halbweg_chart")
    abbruch = " Läufe über der Obergrenze von " + ev.zahl(C.LABEL_CAP) + " Labels sind abgebrochen und mit ihrem Teilstand gezeichnet." if any(p.abgebrochen for p in pk) else ""
    st.caption(f"Ein Lauf je Punkt. Die Fassung dynD (Experiment 4) wählt ihren Halbweg selbst und erzeugt {ev.zahl(kurve.dynd.labels)} Labels bei M* = {ev.zahl(kurve.dynd.halbweg / C.HORIZONT, 2)} H.{abbruch}")
    kind, text = ev.verdict_kurve(kurve)
    getattr(st, kind)(text)
pool = zus["pool"]
st.markdown("**Feste Messreihe** (30 Kunden, 480 Läufe, siehe Experiment 5): Median der Labels im Verhältnis zum einseitigen Verfahren je fester Halbweg.")
st.plotly_chart(V.build_verhaeltnis([C.VERFAHREN_NAMEN[n] for n in B.FESTE], [("Median der Messreihe", [pool[n]["median"] for n in B.FESTE], C.COLOR_SUMME), ("größter Wert", [pool[n]["max"] for n in B.FESTE], C.COLOR_BAD)],
                                    titel_x="fester Halbweg"), width="stretch", key="band_halbweg_chart")
kind, text = T.verdict_halbweg_band(pool, zus["bester_fester_median"])
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 4: dynamischer Halbweg ---------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Der dynamische Halbweg (ein ehrlicher Kontrast)")
st.markdown(
    "Statt M vorzugeben, kann man beide Seiten abwechselnd wachsen lassen (die mit weniger Labels zuerst), bis sich ihre Fronten in der Zeit kreuzen. Gemessen sind **vier einfache Fassungen**: "
    "**dyn** (nichts gekappt), **dynF** (neue Vorwärtslabels jenseits der Rückwärtsfront werden nicht erzeugt), **dynB** (entsprechend rückwärts) und **dynD** (solche Verlängerungen werden zurückgestellt und erst freigegeben, wenn der Halbweg M* feststeht). "
    "Das ist die einfache Auslegung dieser Demo (gleich viele Labels je Seite als Regel), **nicht das Verfahren von Tilk u. a.**; das Ergebnis sagt nichts über deren Verfahren."
)
dyn = None
if a.zu_gross:
    st.info("Ohne Live-Rechnung der Instanz gibt es hier keinen Vergleich.")
elif a.uni.labels <= C.LIVE_KURVE_LIMIT or st.session_state.get("kurve_frei") == repr(kurve_key):
    with st.spinner("Die dynamischen Fassungen werden gerechnet …"):
        dyn = _dyn(kurve_key)
else:
    st.info("Die vier Fassungen rechnet die App nur auf Knopfdruck (siehe Experiment 3).")
if dyn is not None:
    namen = ["einseitig", "fest H/2"] + [C.VERFAHREN_NAMEN[n] for n, _ in dyn.zeilen]
    werte = [dyn.uni_labels, dyn.halb.labels] + [r.labels for _, r in dyn.zeilen]
    st.plotly_chart(V.build_balken(namen, [("erzeugte Labels", werte)]), width="stretch", key="dyn_chart")
    dz = []
    for key, r in [("fest0.5", dyn.halb)] + [(nm, r) for nm, r in dyn.zeilen]:
        dz.append({"Verfahren": C.VERFAHREN_NAMEN[key], "Labels": ev.zahl(r.labels), "Verhältnis zu einseitig": ev.verhaeltnis_text(ev.quote(r.labels, dyn.uni_labels)), "Verbindungspaare": ev.zahl(r.paare),
                   "Halbweg M* (Anteil von H)": ev.zahl(r.halbweg / C.HORIZONT, 2) if key in ("fest0.5", "dynD") else "-",
                   "Labels jenseits von M*": ev.zahl(r.verschwendet_v + r.verschwendet_r) if key == "dynD" else "-"})
    st.dataframe(pd.DataFrame(dz), hide_index=True, width="stretch")
    kind, text = ev.verdict_dynamisch(dyn)
    getattr(st, kind)(text)
st.markdown("**Feste Messreihe** (30 Kunden, 480 Läufe): Median der Labels im Verhältnis zum einseitigen Verfahren.")
st.plotly_chart(V.build_verhaeltnis([C.VERFAHREN_NAMEN[n] for n in ("fest0.5",) + B.DYNAMISCHE], [("Median der Messreihe", [pool[n]["median"] for n in ("fest0.5",) + B.DYNAMISCHE], C.COLOR_SUMME),
                                                                                                     ("größter Wert", [pool[n]["max"] for n in ("fest0.5",) + B.DYNAMISCHE], C.COLOR_BAD)]),
                width="stretch", key="band_dyn_chart")
kind, text = T.verdict_dynamisch_band(pool, zus["dynd_besser_als_fest"], zus["laeufe"], verschw, mstar)
getattr(st, kind)(text)
st.caption("Ob feinere Zeitschritte oder eine Vorschätzung des Halbwegs das Überschießen verkleinern, ist nicht geprüft. Dass beidseitiges Kappen ohne Zurückstellen unzulässig wäre, ist nicht gezeigt und wird nicht behauptet.")

st.markdown("---")

# --- Experiment 5: Bänder --------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Bänder – 480 Läufe der festen Messreihe")
st.markdown(
    "Feste Messreihe mit dem Kern dieser Demo: 30 Kunden, Kapazität 70 (Gedächtnis k = 5 und 8) und 120 (k = 5), Kunden zufällig und gruppiert, Fensterbreite 40 und 100, je 10 Zufalls-Seeds, "
    "Dualpreise aus den Runden 1, 3, 8 und vom Ende einer Spaltenerzeugung. Je Lauf das einseitige Verfahren und neun bidirektionale Einstellungen; **Kapazität 70 und 120 benutzen dieselben Zufalls-Seeds und sind nicht unabhängig.**"
)
st.markdown("**Alle 480 Läufe zusammen:** Labels im Verhältnis zum einseitigen Verfahren.")
st.dataframe(pd.DataFrame(T.tabelle_pool(pool)), hide_index=True, width="stretch")
kind, text = T.verdict_baender(pool, zus["paare_je_label"], zus["vergleiche"])
getattr(st, kind)(text)
band_runde = st.radio("Dualpreise der Zellen aus", list(B.RUNDEN_NAMEN), index=3, format_func=lambda r: "Ende" if r == "ende" else f"Runde {r}", horizontal=True, key="band_runde")
zeilen_zellen = T.tabelle_zellen(band, band_runde)
st.markdown(f"**Je Zelle** (10 Läufe, Dualpreise aus {'dem Ende' if band_runde == 'ende' else 'Runde ' + band_runde}), fest H/2:")
st.dataframe(pd.DataFrame(zeilen_zellen), hide_index=True, width="stretch")
st.plotly_chart(V.build_verhaeltnis([f"{z['Kapazität']}/{'g' if z['Kunden'].startswith('g') else 'z'}/{z['Fensterbreite']}/k{z['Gedächtnis k']}" for z in zeilen_zellen],
                                    [("Median", [B.zelle(z)["median"] for z in B.zellen_der_runde(band, band_runde)], C.COLOR_SUMME), ("Maximum", [B.zelle(z)["max"] for z in B.zellen_der_runde(band, band_runde)], C.COLOR_BAD)],
                                    titel_x="Kapazität / Lage (z = zufällig, g = gruppiert) / Fensterbreite / Gedächtnis"), width="stretch", key="band_cells_chart")
sz = B.schwaechste_zelle(band, band_runde)
st.caption(f"Schwächste Zelle bei Dualpreisen aus {'dem Ende' if band_runde == 'ende' else 'Runde ' + band_runde}: Kapazität {sz['q']}, {C.TYP_NAMEN[sz['typ']]}, Fensterbreite {sz['breite']}, k = {sz['k']} mit Median {ev.verhaeltnis_text(sz['median'])}.")
st.markdown("**Nach Dualpreis-Runde** (Median von fest H/2, je 40 Läufe):")
st.dataframe(pd.DataFrame(T.tabelle_runden(band)), hide_index=True, width="stretch")
st.markdown("**Nach Größe der Label-Menge** (Labels des einseitigen Laufs; Median von fest H/2):")
st.dataframe(pd.DataFrame(T.tabelle_groessen(band)), hide_index=True, width="stretch")
st.markdown("**Welcher feste Halbweg hat je Lauf die wenigsten Labels?**")
st.dataframe(pd.DataFrame(T.tabelle_bester_fester(band)), hide_index=True, width="stretch")
st.caption("Hinweise: nur 30 Kunden und kurze Routen (Horizont 300, Bedienzeit 10); längere Routen, 50 oder 100 Kunden und Label-Mengen von einigen hunderttausend Labels sind nicht gemessen. "
           "Die Dualpreise der Runde 1 sind die der Einzelfahrten (extrem); am Ende findet das Pricing keine negative Route, dort sind gleiche Kosten ein schwacher Test. "
           f"Die Reihe ist mit {band['umgebung']} gerechnet; Zeiten stehen nicht da.")
with st.expander("Quellen der Zeilen"):
    for z in band["zeilen"]:
        st.markdown(f"- {z['quelle']}")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
f25 = pool["fest0.25"]
st.markdown(
    f"""
| Annahme | Was passiert, wenn sie verletzt ist | Was zeigt es |
|---|---|---|
| **Die Zeit ist die Ressource, an der geteilt wird.** | Der Halbweg teilt den Zeithorizont. Bei mehreren Ressourcen (Zeit, Last, Strecke) ist die Wahl der „Mitte“ eine eigene Frage; sie ist hier nicht gemessen. | Experimente 1 bis 3 |
| **Die Routen sind kurz.** | Gemessen sind 30 Kunden mit Horizont 300 und Bedienzeit 10. Wie sich der Vorteil bei längeren Routen, 50 oder 100 Kunden oder mehreren hunderttausend Labels verhält, ist nicht gemessen. | Experiment 5 |
| **Der Halbweg liegt fest bei einem Anteil von H.** | Zu früh oder zu spät gewählt, kann bidirektional mehr Labels erzeugen als einseitig (fest H/4 in {f25['n'] - f25['weniger']} von {f25['n']} Läufen der Messreihe). | Experimente 2 und 3 |
| **Dynamische Wahl bringt gegenüber fest H/2 keinen Vorteil.** | Gemessen ist nur die einfache Auslegung dieser Demo (gleiche Label-Zahl je Seite), nicht das Verfahren von Tilk u. a. und nicht jede denkbare Fassung. | Experiment 4 |
| **Das Verbinden ist gerechnet, nicht gewogen.** | Es wird als Matrixoperation je Kante ausgeführt und als Zahl der Paare ausgewiesen; ein Gesamtaufwandsmaß aus Labels und Paaren ist nicht festgelegt, Sekunden sind nicht festgeschrieben. | Experimente 2 und 5 |
| **Je Zelle 10 Zufalls-Seeds.** | Die Spanne zwischen Median und Maximum ist groß; Kapazität 70 und 120 benutzen dieselben Zufalls-Seeds. | Experiment 5 |
| **Bidirektional und Eimer zusammen.** | Eimer (eine andere Maßnahme gegen die Label-Zahl) sind nicht kombiniert gemessen. | - |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** *Gegeben:* ein Depot 0, Kunden $1,\dots,n$ mit Last, Zeitfenster und Entfernungen (Entfernung = Fahrzeit = Kosten), Dualpreise $\pi_j$. *Gesucht:* eine Route $0 \to j_1 \to \dots \to j_m \to 0$ mit negativen reduzierten Kosten,
die Last, Fenster und Horizont einhält. *Verfahren:* Labeling mit Dominanz, einseitig oder von beiden Enden mit Verbindung.

| Symbol | Bedeutung |
|---|---|
| $d_{ij}$ | Entfernung (= Fahrzeit = Kosten) von $i$ nach $j$; 0 ist das Depot |
| $\sigma,\ q_j,\ Q$ | Bedienzeit, Last von Kunde $j$, Kapazität |
| $[a_j, b_j],\ H$ | Zeitfenster für den Beginn der Bedienung bei Kunde $j$, Horizont für die Rückkehr |
| $\pi_j$ | Dualpreis von Kunde $j$ ($\pi_0 = 0$) |
| $(t, c, q, S)$ | Vorwärtslabel: frühester Beginn, reduzierte Kosten, Last, Menge $S$ der gesperrten Kunden |
| $(T, c, q, S)$ | Rückwärtslabel: spätester Beginn, reduzierte Kosten ab dem Knoten, Last ab dem Knoten, Menge $S$ der gesperrten Kunden |
| $N_k(j)$ | die $k$ nächsten Kunden von $j$ einschließlich $j$ (Gedächtnis; $k = n$: elementar) |
| $M$ | Halbweg (Zeitpunkt, in der Messreihe feste Anteile von $H$, vor allem $M = H/2$) |

**Reduzierte Kosten** einer Route: $\bar c = \sum_{i=0}^{m} d_{j_i j_{i+1}} - \sum_{i=1}^{m} \pi_{j_i}$ mit $j_0 = j_{m+1} = 0$. Gesucht ist eine zulässige Route mit $\bar c < 0$.

**Vorwärts.** Aus $(t, c, q, S)$ am Knoten $i$ entsteht über $j \notin S$ das Label

$$t' = \max\bigl(t + \sigma_i + d_{ij},\; a_j\bigr), \quad c' = c + d_{ij} - \pi_j, \quad q' = q + q_j, \quad S' = (S \cap N_k(j)) \cup \{j\},$$

nur falls $t + \sigma_i + d_{ij} \le b_j$ und $q' \le Q$ ($\sigma_i = \sigma$ für einen Kunden, $0$ am Depot). Der Start ist $(0, 0, 0, \emptyset)$ am Depot.

**Rückwärts.** Aus $(T, c, q, S)$ am Knoten $j$ entsteht über den Vorgänger $i \notin S$ das Label

$$T' = \min\bigl(b_i,\; T - \sigma - d_{ij}\bigr), \quad c' = c + d_{ij} - \pi_i, \quad q' = q + q_i, \quad S' = (S \cap N_k(i)) \cup \{i\},$$

nur falls $T' \ge a_i$ und $q' \le Q$. Der Start ist $(H, 0, 0, \emptyset)$ am Depot-Ende.

**Halbweg.** Vorwärtslabels werden nur mit $t \le M$, Rückwärtslabels nur mit $T \ge M$ erzeugt.

**Dominanz.** Vorwärts dominiert $(t, c, q, S)$ das Label $(t', c', q', S')$ am selben Knoten, wenn $c \le c'$, $t \le t'$, $q \le q'$ und $S \subseteq S'$. Rückwärts gilt dasselbe mit $T \ge T'$ statt $t \le t'$.

**Verbindung.** Ein Vorwärtslabel $(t, c_F, q_F, S_F)$ am Knoten $i$ und ein Rückwärtslabel $(T, c_B, q_B, S_B)$ am Knoten $j$ ergeben über die Kante $(i, j)$ eine Route, wenn

$$t + \sigma_i + d_{ij} \le T, \qquad q_F + q_B \le Q, \qquad S_F \cap S_B = \emptyset,$$

mit den reduzierten Kosten $c_F + d_{ij} + c_B$. Die beste Verbindung über alle Kanten ist die beste Route; sie stimmt mit dem Ergebnis des einseitigen Verfahrens überein.

**Zählgrößen.** Erzeugte Labels (fester Halbweg): alle Verlängerungen, die Last und Fenster bestehen und am Halbweg nicht enden, auch die sofort dominierten (bidirektional beide Richtungen mit beiden Starts). Verbindungspaare: Vorwärtslabels in $i$ mal Rückwärtslabels in $j$,
summiert über die Kanten, bei denen das früheste Vorwärtslabel zeitlich überhaupt zum spätesten Rückwärts-$T$ passen kann.

**Literatur.** Righini, Salani (2006): *Symmetry helps: bounded bi-directional dynamic programming for the elementary shortest path problem with resource constraints*, Discrete Optimization 3(3), S. 255–273 (von beiden Enden labeln, in der Mitte verbinden);
Tilk, Rothenbächer, Gschwind, Irnich (2017): European Journal of Operational Research 261(2), S. 530–539 (dynamische Wahl der Mitte); Irnich, Desaulniers (2005): *Shortest Path Problems with Resource Constraints*, in: Column Generation, Springer, S. 33–65.
Prüfstand: bei allen nur Abstract oder Zitat gesehen, kein Volltext gelesen. Die Messung hier ist kein Urteil über das Verfahren von Tilk u. a., sondern über die einfache Fassung dieser Demo. Keine Zahl der Demo stammt aus der Literatur.
        """
    )

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(ASSUMPTIONS_MARKDOWN)

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html)."
)
