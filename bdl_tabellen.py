"""Tabellen und Verdikte der festen Messreihen (Bänder) und des Handbeispiels als reine Funktionen.

Die Tabellen sind Listen gleichartiger Wörterbücher; die App zeigt sie mit `st.dataframe`, die README erzeugt ihre Messtabellen mit `markdown_tabelle` aus denselben Daten
(`tools/readme_tabellen.py`, `tests/test_claims.py` prüft, dass sie dort stehen). Jedes Verdikt ist `(Art, Text)` und nennt jede Zahl aus den übergebenen Kennzahlen."""

import bdl_baender as B
import bdl_constants as C
import bdl_evaluation as ev
from bdl_evaluation import NBSP, HandAnalyse, prozent, verhaeltnis_text, weg_text, zahl, zahl_kurz
from bdl_scenario import HAND_DUAL, handbeispiel


def markdown_tabelle(zeilen: list) -> str:
    """Markdown-Tabelle aus einer Liste gleichartiger Wörterbücher (Spaltenköpfe = Schlüssel)."""
    kopf = list(zeilen[0])
    aus = ["| " + " | ".join(kopf) + " |", "|" + "|".join("---" for _ in kopf) + "|"]
    aus += ["| " + " | ".join(str(z[k]) for k in kopf) + " |" for z in zeilen]
    return "\n".join(aus)


def tabelle_pool(pool: dict) -> list:
    """Alle Läufe zusammen: je Verfahren Median, Minimum bis Maximum des Verhältnisses der Labels zum einseitigen Lauf und Läufe mit weniger Labels."""
    return [{"Verfahren": C.VERFAHREN_NAMEN[n], "Median": verhaeltnis_text(p["median"]), "Minimum bis Maximum": f"{verhaeltnis_text(p['min'])} bis {verhaeltnis_text(p['max'])}",
             "Läufe mit weniger Labels als einseitig": f"{zahl(p['weniger'])} von {zahl(p['n'])}"} for n, p in pool.items()]


def zellen_name(z: dict) -> tuple:
    return z["q"], C.TYP_NAMEN[z["typ"]], z["breite"], z["k"]


def tabelle_zellen(band: dict, runde: str) -> list:
    """Je Zelle einer Dualpreis-Runde (10 Läufe): Labels des einseitigen Verfahrens (Median), Verhältnis von fest H/2 (Median, Mittel, Maximum), Läufe mit weniger Labels,
    Verbindungspaare je einseitigem Label (Median)."""
    aus = []
    for z in B.zellen_der_runde(band, runde):
        s = B.zelle(z)
        q, typ, breite, k = zellen_name(z)
        aus.append({"Kapazität": q, "Kunden": typ, "Fensterbreite": breite, "Gedächtnis k": k, "Läufe": s["n"], "einseitige Labels (Median)": zahl(s["uni_labels"]),
                    "fest H/2: Median": verhaeltnis_text(s["median"]), "Mittel": verhaeltnis_text(s["mittel"]), "Maximum": verhaeltnis_text(s["max"]),
                    "weniger Labels": f"{s['weniger']} von {s['n']}", "Paare je einseitigem Label (Median)": zahl(s["paare_je_label"], 1)})
    return aus


def tabelle_runden(band: dict) -> list:
    """Median des Verhältnisses von fest H/2 je Dualpreis-Runde, getrennt nach Kapazität und Gedächtnis (je 40 Läufe)."""
    aus = []
    for q, k in C.BAND_ZELLEN:
        r = B.je_runde(band, q, k)
        aus.append({"Kapazität": q, "Gedächtnis k": k, **{("Ende" if n == "ende" else f"Runde {n}"): verhaeltnis_text(r[n]["median"]) for n in B.RUNDEN_NAMEN}})
    return aus


def klasse_text(lo: int, hi: int) -> str:
    return f"ab {zahl(lo)}" if hi >= 10 ** 9 else f"{zahl(lo)} bis unter {zahl(hi)}"


def tabelle_groessen(band: dict) -> list:
    """Median des Verhältnisses von fest H/2 nach der Label-Zahl des einseitigen Laufs in Klassen."""
    return [{"Labels des einseitigen Laufs": klasse_text(lo, hi), "Läufe": n, "Median von fest H/2": "keine Läufe" if med is None else verhaeltnis_text(med)}
            for lo, hi, n, med in B.nach_groesse(band)]


def tabelle_bester_fester(band: dict) -> list:
    """Wie oft ein fester Halbweg je Lauf die wenigsten Labels hat (getrennt nach Kapazität; bei Gleichstand der kleinere Anteil von H)."""
    aus = []
    for q in C.KAPAZITAETEN:
        h = B.haeufigkeit_bester_fester(band, q)
        aus.append({"Kapazität": q, "Läufe": h["n"], **{C.VERFAHREN_NAMEN[n]: f"{h[n]} ({zahl(100 * h[n] / h['n'])}{NBSP}%)" for n in B.FESTE}})
    return aus


def tabelle_vergleich(neu: dict, frueher: dict) -> list:
    """Dieselben Kennzahlen: diese Demo (neu gerechnet) gegen die frühere Messreihe der Planung (aus deren Rohdateien übernommen, nicht neu gerechnet)."""
    zeilen = []
    for n in B.BIDI:
        a, b = neu["pool"][n], frueher["pool"][n]
        zeilen.append({"Verfahren": C.VERFAHREN_NAMEN[n], "Median diese Demo": verhaeltnis_text(a["median"]), "Median frühere Reihe": verhaeltnis_text(b["median"]),
                       "weniger Labels diese Demo": f"{a['weniger']} von {a['n']}", "weniger Labels frühere Reihe": f"{b['weniger']} von {b['n']}"})
    zeilen.append({"Verfahren": "Verbindungspaare je einseitigem Label (fest H/2, Median)", "Median diese Demo": zahl(neu["paare_je_label"], 1), "Median frühere Reihe": zahl(frueher["paare_je_label"], 1),
                   "weniger Labels diese Demo": "-", "weniger Labels frühere Reihe": "-"})
    return zeilen


def tabelle_hand_netz() -> list:
    """Die Tabelle des Handbeispiels: Kunde, Ort, Fenster, Bedarf, Dualpreis."""
    inst = handbeispiel()
    return [{"Kunde": j, "Ort": f"({inst.pts[j][0]}, {inst.pts[j][1]})", "Fenster [früh, spät]": f"[{inst.ready[j]:g}, {inst.due[j]:g}]", "Bedarf": inst.dem[j], "Dualpreis π": zahl_kurz(HAND_DUAL[j])}
            for j in range(1, inst.n + 1)]


def tabelle_hand_reihe(h: HandAnalyse, ohne_vorpruefung: bool = False) -> list:
    """Das Handbeispiel bei den Halbwegen der Reihe: Labels vorwärts, rückwärts, Summe, Verbindungspaare, Kanten und beste Route. `ohne_vorpruefung`: Paare und Kanten ohne die Vorprüfung der Zeit."""
    zeilen = []
    for mx, v, r, paare, kanten, paare_alle, kanten_alle, b in h.reihe:
        z = {"Halbweg M": mx, "Vorwärtslabels": v, "Rückwärtslabels": r, "Summe": v + r, "Verbindungspaare": paare_alle if ohne_vorpruefung else paare, "Kanten": kanten_alle if ohne_vorpruefung else kanten,
             "beste Route": f"{weg_text(b[1])}, {zahl_kurz(b[0])}"}
        zeilen.append(z)
    return zeilen


def tabelle_presets() -> list:
    """Je Voreinstellung die Live-Rechnung: einseitige und bidirektionale Labels (vorwärts + rückwärts), Anteil und Verbindungspaare."""
    zeilen = []
    for name, p in C.PRESETS.items():
        s = ev.settings_aus_preset(p)
        a = ev.analyse_live(s)
        zeilen.append({"Voreinstellung": name, "Kunden": f"{s.n}, {C.TYP_NAMEN[s.typ]}, Breite {s.breite}, Kapazität {s.q}, k = {s.k}, Zufalls-Seed {s.seed}",
                       "Dualpreise aus": ev.runde_label(s.runde), "Halbweg in % von H": s.halbweg_pct, "Labels einseitig": zahl(a.uni.labels),
                       "Labels bidirektional": f"{zahl(a.bidi.labels)} ({zahl(a.bidi.erzeugt_v)} + {zahl(a.bidi.erzeugt_r)})", "Anteil": ev.prozent_genau(ev.quote(a.bidi.labels, a.uni.labels)),
                       "Verbindungspaare": zahl(a.bidi.paare)})
    return zeilen


def verdict_baender(pool: dict, paare_je_label: float, vergleiche: float) -> tuple:
    """Verdikt der festen Messreihe für fest H/2: in wie vielen Läufen weniger Labels als einseitig, Median, kleinster und größter Wert, und der Preis des Verbindens."""
    p = pool["fest0.5"]
    ausnahme = f" (Ausnahme: {p['n'] - p['weniger']} Läufe mit gleich vielen oder mehr Labels)" if p["weniger"] < p["n"] else ""
    text = (f"Fest H/2 erzeugt in **{zahl(p['weniger'])} von {zahl(p['n'])}** Läufen weniger Labels als das einseitige Verfahren{ausnahme}: Median **{prozent(p['median'])}** der einseitigen Label-Zahl, "
            f"kleinster Wert {prozent(p['min'])}, größter {prozent(p['max'])}. Das Verbinden prüft im Median das {zahl(paare_je_label, 1)}-Fache der einseitigen Label-Zahl an Paaren; "
            f"die Dominanzvergleiche der Labels betragen im Median {prozent(vergleiche)} der einseitigen.")
    return ("success" if p["weniger"] == p["n"] else "info"), text


def verdict_halbweg_band(pool: dict, bester_median: float) -> tuple:
    """Verdikt der festen Halbwege der Messreihe: Median je Halbweg, Läufe ohne Vorteil, und was ein im Rückblick je Lauf gewählter bester Halbweg erreichte."""
    meds = ", ".join(f"{C.VERFAHREN_NAMEN[n]} {verhaeltnis_text(pool[n]['median'])}" for n in B.FESTE)
    schlecht = [f"{C.VERFAHREN_NAMEN[n]} in {pool[n]['n'] - pool[n]['weniger']} von {pool[n]['n']} Läufen" for n in B.FESTE if pool[n]["weniger"] < pool[n]["n"]]
    best = min(B.FESTE, key=lambda n: pool[n]["median"])
    text = (f"Median der Labels im Verhältnis zum einseitigen Verfahren: {meds}. Am besten ist **{C.VERFAHREN_NAMEN[best]}**; wäre je Lauf im Rückblick der beste feste Halbweg gewählt worden, "
            f"läge der Median bei {verhaeltnis_text(bester_median)}. ")
    if schlecht:
        text += "Nicht weniger Labels als einseitig erzeugt " + "; ".join(schlecht) + ". "
    text += "Die Summe der Labels ist über den Halbweg U-förmig."
    return "info", text


def verdict_dynamisch_band(pool: dict, dynd_besser: int, n_laeufe: int, verschwendet: dict, mstar: dict) -> tuple:
    """Verdikt der dynamischen Fassungen in der Messreihe: schlechter als fest H/2, und wie viele der Labels von dynD jenseits des endgültigen Halbwegs liegen."""
    fest = pool["fest0.5"]["median"]
    meds = ", ".join(f"{C.VERFAHREN_NAMEN[n]} {verhaeltnis_text(pool[n]['median'])}" for n in B.DYNAMISCHE)
    ohne = pool["dyn"]["n"] - pool["dyn"]["weniger"]
    text = (f"**Dynamisch ist hier schlechter als fest H/2.** Median der Labels im Verhältnis zum einseitigen Verfahren: {meds}, fest H/2 dagegen {verhaeltnis_text(fest)}. Die Fassung dynD erzeugt in "
            f"{zahl(dynd_besser)} von {zahl(n_laeufe)} Läufen weniger Labels als fest H/2; ohne Kappen (dyn) sind es in {zahl(ohne)} von {zahl(pool['dyn']['n'])} Läufen gleich viele oder mehr Labels als einseitig. "
            f"Der Halbweg von dynD landet bei den Dualpreisen am Ende im Median bei {zahl(mstar['median'], 2)} H (Spanne {zahl(mstar['min'], 2)} bis {zahl(mstar['max'], 2)}), also in der Gegend des besten festen Halbwegs; "
            f"in diesen Läufen liegen im Median {prozent(verschwendet['median'])} der erzeugten Labels (Spanne {prozent(verschwendet['min'])} bis {prozent(verschwendet['max'])}) jenseits des endgültigen Halbwegs und sind für die beste Route nicht nötig (sie können zusätzliche Verbindungen liefern).")
    return "warning", text
