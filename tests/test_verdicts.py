"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Ergebnisse, keine Seeds. Damit prüft der Test die Grenzen (Verhältnis genau 1, Gleichstand der Kosten, kein Nenner) und jede genannte Zahl
direkt. Welche Verdikt-Zeile jede Voreinstellung der App zeigt, prüft `tests/test_app.py`."""

import dataclasses


import bdl_algorithm as A
import bdl_constants as C
import bdl_evaluation as ev
import bdl_tabellen as T

NBSP = " "


def erg(v, r, routen=(), paare=0, vergleiche=(0, 0), halbweg=None, **kw):
    """Handgesetztes Pricing-Ergebnis: v und r erzeugte Labels, dazu Routen (rc, Route)."""
    return A.PricingErgebnis("fest" if r else "uni", list(routen), v, r, 0, 0, vergleiche[0], vergleiche[1], v, r, paare, 3, paare, 3, halbweg, **kw)


def live(uni, bidi, halb=None, zu_gross=None):
    return ev.LiveAnalyse(None, (0.0,), 3, 100, uni, bidi, halb or bidi, zu_gross, None)


def norm(text):
    return text.replace(NBSP, " ")


# --- Zahlenformat ------------------------------------------------------------------------------------------------------------------------

def test_number_format_is_german():
    assert norm(ev.zahl(1234567)) == "1 234 567" and norm(ev.zahl(2.5, 1)) == "2,5" and ev.zahl(0.0) == "0" and norm(ev.zahl(-0.0, 2)) == "0,00"
    assert norm(ev.zahl(17120.5)) == "17 120" and ev.zahl(3.0) == "3"
    assert ev.zahl_kurz(-3.0) == "-3" and ev.zahl_kurz(1.5) == "1,50" and ev.zahl_kurz(-0.5) == "-0,50"
    assert norm(ev.prozent(0.2766)) == "28 %" and norm(ev.prozent(1.0)) == "100 %" and ev.verhaeltnis_text(0.27) == "0,27"
    assert ev.weg_text((5, 6, 3)) == "5-6-3" and ev.weg_text(()) == "leer" and ev.menge_text(0b1010) == "{1, 3}" and ev.quote(3, 0) == 0.0


def test_labels_are_named_by_direction_and_their_fate_is_described(hand, hand_pi):
    bidi = A.pricing_bidirektional(hand, hand_pi, None, "fest", 20.0, behalte_seiten=True)
    assert ev.etikett(True, 6) == "F06" and ev.etikett(False, 2) == "B02" and ev.etikett(True, 3, einseitig=True) == "E03"
    assert [ev.status_text(bidi.vor, i) for i in (0, 4, 6)] == ["Start", "dominiert von F02", "behalten"]
    assert ev.status_text(bidi.rueck, 6) == "dominiert von B02"
    uni = A.pricing_einseitig(hand, hand_pi, None, behalte_seiten=True)
    verdraengt = [i for i in range(len(uni.vor.labels)) if uni.vor.tot[i] and uni.vor.dominiert_von[i] > i]
    assert verdraengt == [] or ev.status_text(uni.vor, verdraengt[0], einseitig=True).startswith("verdrängt von E")
    assert sum(1 for z in ev.label_zeilen(uni.vor, einseitig=True) if z["Schicksal"].startswith("dominiert")) == 11


# --- Handbeispiel ----------------------------------------------------------------------------------------------------------------------------

def test_hand_verdict_for_the_middle_names_every_number():
    kind, text = ev.verdict_hand(ev.analyse_hand(20))
    assert kind == "success"
    assert "Halbweg 20: bidirektional **16** Labels (8 vorwärts + 8 rückwärts) gegen **35** einseitig, dazu 48 Verbindungspaare." in text
    assert "aller 39 zulässigen Routen, bei allen 7 Halbwegen der Reihe" in text


def test_hand_verdict_at_the_border_is_a_warning_with_the_one_sided_counts():
    for m, v, r in ((0, 1, 35), (40, 35, 1)):
        kind, text = ev.verdict_hand(ev.analyse_hand(m))
        assert kind == "warning" and f"**36** Labels ({v} vorwärts + {r} rückwärts) gegen **35** einseitig" in text and "**nicht weniger** Labels" in text


def test_hand_verdict_reports_a_difference_in_the_best_route():
    h = dataclasses.replace(ev.analyse_hand(20), gleich=False)
    assert "**Achtung:**" in ev.verdict_hand(h)[1]


# --- Kernfrage an der Kundeninstanz -----------------------------------------------------------------------------------------------------------

def test_label_verdict_names_the_share_and_both_routes():
    uni = erg(1000, 0, [(-4.5, (2, 1))], vergleiche=(500, 0))
    bidi = erg(180, 100, [(-4.5, (2, 1))], paare=3000, vergleiche=(60, 40))
    kind, text = ev.verdict_labels(live(uni, bidi))
    assert kind == "success" and "**28 %** der Labels" in norm(text) and "280 (180 vorwärts + 100 rückwärts) gegen 1 000" in norm(text)
    assert "dieselbe beste Route 2-1 mit reduzierten Kosten -4,50" in text


def test_label_verdict_threshold_is_one_and_names_more_labels():
    uni = erg(1000, 0, [(-1.0, (1,))])
    knapp = erg(500, 499, [(-1.0, (1,))])
    gleich = erg(500, 500, [(-1.0, (1,))])
    assert ev.verdict_labels(live(uni, knapp))[0] == "success" and "**99,9 %**" in norm(ev.verdict_labels(live(uni, knapp))[1])
    kind, text = ev.verdict_labels(live(uni, gleich))                                          # genau 100 %: nicht weniger
    assert kind == "warning" and "**mehr Labels als einseitig**" in text and "100 %" in norm(text)
    kind, text = ev.verdict_labels(live(uni, erg(700, 600, [(-1.0, (1,))])))
    assert kind == "warning" and "1 300 (700 vorwärts + 600 rückwärts) gegen 1 000" in norm(text) and "130 %" in norm(text)


def test_label_verdict_for_ties_missing_routes_and_errors():
    uni = erg(100, 0, [(-2.0, (1, 2))])
    kind, text = ev.verdict_labels(live(uni, erg(30, 20, [(-2.0, (2, 1))])))
    assert kind == "success" and "verschiedenen, gleich guten Routen" in text
    assert ev.verdict_labels(live(erg(100, 0), erg(30, 20)))[1].endswith("Beide Verfahren finden keine Route mit negativen reduzierten Kosten: Das Pricing bestätigt nur, dass keine Spalte mehr lohnt.")
    assert ev.verdict_labels(live(uni, erg(30, 20, [(-1.0, (1, 2))])))[0] == "error"            # verschiedene beste Kosten
    kind, text = ev.verdict_labels(live(None, None, zu_gross="Ein Lauf überschreitet 150 000 erzeugte Labels"))
    assert kind == "warning" and "zu groß" in text and "150 000" in norm(text)


def test_connection_verdict_names_pairs_factor_and_comparisons():
    uni = erg(1000, 0, [(-1.0, (1,))], vergleiche=(8000, 0))
    bidi = erg(200, 100, [(-1.0, (1,))], paare=9800, vergleiche=(1000, 500))
    kind, text = ev.verdict_verbinden(live(uni, bidi))
    assert kind == "info" and "**9 800** Paare" in norm(text) and "**9,8-Fache**" in text and "19 %" in norm(text) and "(1 500 gegen 8 000)" in norm(text)
    assert "keine Zahl" in ev.verdict_verbinden(live(None, None, zu_gross="x"))[1]


def test_halfway_choice_verdict_warns_only_when_the_slider_is_worse_than_half():
    halb = erg(100, 80, [(-1.0, (1,))])
    schlecht = erg(150, 90, [(-1.0, (1,))])
    besser = erg(80, 60, [(-1.0, (1,))])
    gleich = erg(100, 80, [(-1.0, (1,))])
    kind, text = ev.verdict_halbweg_wahl(live(erg(500, 0), schlecht, halb), 25)
    assert kind == "warning" and "**Halbweg ungünstig:**" in text and "25 % von H sind es 240 Labels, bei H/2 nur 180 (133 % der Labels bei H/2)" in norm(text)
    assert ev.verdict_halbweg_wahl(live(erg(500, 0), besser, halb), 40)[0] == "info" and "nicht ungünstiger" in ev.verdict_halbweg_wahl(live(erg(500, 0), besser, halb), 40)[1]
    assert ev.verdict_halbweg_wahl(live(erg(500, 0), gleich, halb), 40)[0] == "info"           # Gleichstand ist nicht ungünstiger
    assert "steht auf H/2" in ev.verdict_halbweg_wahl(live(erg(500, 0), halb, halb), 50)[1]
    assert ev.verdict_halbweg_wahl(live(None, None, zu_gross="x"), 25)[0] == "info"


def punkte(summen):
    return tuple(ev.KurvenPunkt(10 * i, s // 2, s - s // 2, 0, False) for i, s in enumerate(summen))


def test_curve_verdict_is_a_success_only_for_a_u_shape():
    dynd = erg(100, 100, halbweg=150.0)
    u = ev.Kurve(punkte([400, 300, 200, 100, 150, 500, 350, 250, 300, 380, 420]), 450, dynd, ev.KurvenPunkt(30, 50, 50, 0, False), None)
    kind, text = ev.verdict_kurve(u)
    assert kind == "success" and "**30 % von H**: 100 (50 vorwärts + 50 rückwärts)" in text and "einseitig sind es 450" in text and "400 und 420" in text and "**U-förmig**" in text
    rand = ev.Kurve(punkte([100, 120, 150, 200, 250, 300, 350, 400, 420, 430, 440]), 450, dynd, ev.KurvenPunkt(0, 50, 50, 0, False), None)
    kind, text = ev.verdict_kurve(rand)
    assert kind == "info" and "nicht U-förmig" in text


def test_dynamic_verdict_is_a_warning_unless_a_version_beats_half():
    halb = erg(100, 80)
    schlechter = tuple((n, erg(150 + i, 100)) for i, n in enumerate(("dyn", "dynF", "dynB", "dynD")))
    kind, text = ev.verdict_dynamisch(ev.DynAnalyse(schlechter, halb, 500))
    assert kind == "warning" and "**180** Labels" in text and "250, 251, 252, 253" in text and "in allen vier Fassungen schlechter" in text
    mit_besser = (("dyn", erg(150, 100)), ("dynF", erg(90, 80)), ("dynB", erg(180, 0)), ("dynD", erg(100, 80)))      # dynD gleich viele: nicht besser
    kind, text = ev.verdict_dynamisch(ev.DynAnalyse(mit_besser, halb, 500))
    assert kind == "info" and text.endswith("dynF. Die Messreihe zeigt das nicht (siehe unten).")


# --- Messreihen --------------------------------------------------------------------------------------------------------------------------

def pool_von(med):
    return {n: {"n": 480, "median": med.get(n, 0.5), "min": 0.1, "max": 1.2, "weniger": med.get("weniger_" + n, 480)} for n in T.B.BIDI}


def test_band_verdict_for_half_names_counts_extremes_and_the_price():
    p = pool_von({"fest0.5": 0.27})
    p["fest0.5"].update(min=0.11, max=0.79)
    kind, text = T.verdict_baender(p, 9.8, 0.2)
    assert kind == "success" and "**480 von 480** Läufen" in text and "Median **27 %**" in text and "kleinster Wert 11 %, größter 79 %" in text and "9,8-Fache" in text and "20 %" in text
    p["fest0.5"]["weniger"] = 479
    kind, text = T.verdict_baender(p, 9.8, 0.2)
    assert kind == "info" and "**479 von 480**" in text and "(Ausnahme: 1 Läufe mit gleich vielen oder mehr Labels)" in text


def test_halfway_band_verdict_names_the_best_and_the_runs_without_gain():
    p = pool_von({"fest0.25": 0.7, "fest0.4": 0.34, "fest0.5": 0.27, "fest0.6": 0.37, "fest0.75": 0.8, "weniger_fest0.25": 403, "weniger_fest0.4": 479})
    kind, text = T.verdict_halbweg_band(p, 0.26)
    assert kind == "info" and "fest H/4 0,70, fest 0,4 H 0,34, fest H/2 0,27, fest 0,6 H 0,37, fest 0,75 H 0,80" in text and "Am besten ist **fest H/2**" in text and "bei 0,26" in text
    assert "fest H/4 in 77 von 480 Läufen; fest 0,4 H in 1 von 480 Läufen" in text
    assert "Nicht weniger" not in T.verdict_halbweg_band(pool_von({}), 0.5)[1]


def test_dynamic_band_verdict_names_medians_share_beyond_the_halfway_and_the_halfway_itself():
    p = pool_von({"fest0.5": 0.27, "dyn": 1.26, "dynF": 0.79, "dynB": 0.8, "dynD": 0.68, "weniger_dyn": 57})
    kind, text = T.verdict_dynamisch_band(p, 0, 480, {"median": 0.6, "min": 0.4, "max": 0.79}, {"median": 0.48, "min": 0.29, "max": 0.67})
    assert kind == "warning" and "**Dynamisch ist hier schlechter als fest H/2.**" in text
    assert "dynamisch, nichts gekappt 1,26, dynamisch, vorwärts gekappt 0,79, dynamisch, rückwärts gekappt 0,80, dynamisch, zurückgestellt 0,68, fest H/2 dagegen 0,27" in text
    assert "in 0 von 480 Läufen weniger Labels als fest H/2" in text and "423 von 480 Läufen gleich viele oder mehr" in text
    assert "bei 0,48 H (Spanne 0,29 bis 0,67)" in text and "60 % der erzeugten Labels (Spanne 40 % bis 79 %)" in norm(text)


def test_tables_have_one_row_per_method_cell_and_round(band_data=None):
    band = T.B.lade_baender()
    z = T.B.zusammenfassung(band)
    assert len(T.tabelle_pool(z["pool"])) == 9 and len(T.tabelle_zellen(band, "ende")) == 12 and len(T.tabelle_runden(band)) == 3 and len(T.tabelle_groessen(band)) == 5
    assert len(T.tabelle_bester_fester(band)) == 2 and len(T.tabelle_vergleich(z, T.B.lade_fruehere())) == 10
    assert T.markdown_tabelle([{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]) == "| a | b |\n|---|---|\n| 1 | x |\n| 2 | y |"
    assert [r["Halbweg M"] for r in T.tabelle_hand_reihe(ev.analyse_hand(20))] == list(C.HAND_M_REIHE)
