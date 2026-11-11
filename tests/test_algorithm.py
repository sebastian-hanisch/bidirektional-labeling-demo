"""Kern gegen die Handrechnung (DEMO-PLAYBOOK §1b): jede Regel an der Mini-Instanz, das Handbeispiel Label für Label, die Zählungen und die Randfälle des Halbwegs.

Das Handbeispiel (tests/conftest.py): Depot und 6 Kunden, Manhattan-Abstand, Bedienzeit 2, Kapazität 9, Horizont 40, Halbweg M = H/2 = 20. Jedes Label wird in den Tests noch einmal aus der
Definition für seine Route berechnet (`label_vorwaerts`, `label_rueckwaerts`), nicht aus dem Kern abgeschrieben. Die Zählungen (35 einseitig; 8 + 8 bidirektional; 48 Paare) stammen aus
dem von Hand geführten Protokoll der Planung (ein unabhängiges Skript nur mit der Standardbibliothek) und sind hier mit ihrer Rechnung an den einzelnen Labels abgesichert."""

import pytest
from conftest import HAND_Q, HAND_SVC, hand_d, mini_instanz

import bdl_algorithm as A
import bdl_constants as C
import bdl_evaluation as ev
import bdl_scenario as S

H = 40


def label_vorwaerts(inst, pi, route):
    """Vorwärtslabel einer Route aus der Definition: (Beginn t, reduzierte Kosten c, Last q) nach dem letzten Kunden."""
    t, c, q, i = 0, 0, 0, 0
    for j in route:
        t = max(t + (HAND_SVC if i != 0 else 0) + inst.d[i][j], inst.ready[j])
        c += inst.d[i][j] - pi[j]
        q += inst.dem[j]
        i = j
    return t, c, q


def label_rueckwaerts(inst, pi, route):
    """Rückwärtslabel einer Route (Kundenfolge bis zum Depot-Ende): (spätester Beginn T beim ersten Kunden, Kosten c, Last q); c enthält die Kante zum Nachfolger und -pi des ersten Kunden."""
    T, c, q, nach = inst.H, 0, 0, 0
    for j in reversed(route):
        T = min(inst.due[j], T - HAND_SVC - inst.d[j][nach])
        c += inst.d[j][nach] - pi[j]
        q += inst.dem[j]
        nach = j
    return T, c, q


def kette(seite, nr):
    """Kundenfolge eines Labels: bei Vorwärtslabels vom Start bis zum Label, bei Rückwärtslabels vom Label bis zum Depot-Ende."""
    folge = []
    while nr != -1 and seite.labels[nr][A.L_K] != 0:
        folge.append(seite.labels[nr][A.L_K])
        nr = seite.labels[nr][A.L_E]
    return tuple(reversed(folge)) if seite.vorwaerts else tuple(folge)


# --- Szenario und Gedächtnis -------------------------------------------------------------------------------------------------------------------

def test_scenario_module_has_the_hand_table(hand, hand_pi):
    s = S.handbeispiel()
    assert (s.pts, s.d, s.dem, s.ready, s.due, s.H, s.Q, s.svc) == (hand.pts, hand.d, hand.dem, hand.ready, hand.due, hand.H, hand.Q, hand.svc)
    assert S.HAND_DUAL == hand_pi and s.n == 6


def test_hand_distances_follow_the_manhattan_rule(hand):
    assert [hand.d[0][j] for j in range(1, 7)] == [5, 3, 7, 4, 6, 9]
    assert hand.d[5][6] == abs(7 - 1) + abs(1 - 0) == 7 and hand.d[6][3] == abs(1 - 0) + abs(0 - 3) == 4 and hand.d[3][0] == 5 + 2 == 7


def test_ng_masks_elementary_and_small_memory():
    inst = mini_instanz([(0, 0), (1, 0), (2, 0), (5, 0), (9, 0)], [1, 1, 1, 1], [(0, 99)] * 4)
    alle = A.ng_masken(inst, None)
    assert alle[0] == 0 and all(alle[j] == 0b11110 for j in range(1, 5)) and A.ng_masken(inst, 4) == alle
    assert A.menge_aus_maske(0b10110) == (1, 2, 4)
    m1 = A.ng_masken(inst, 1)
    assert m1[1:] == (0b10, 0b100, 0b1000, 0b10000)                      # k = 1: nur der Kunde selbst
    m2 = A.ng_masken(inst, 2)
    assert A.menge_aus_maske(m2[1]) == (1, 2) and A.menge_aus_maske(m2[2]) == (1, 2) and A.menge_aus_maske(m2[3]) == (2, 3) and A.menge_aus_maske(m2[4]) == (3, 4)


# --- Dominanzregeln --------------------------------------------------------------------------------------------------------------------------

def test_forward_dominance_needs_every_condition():
    a = (10.0, 5.0, 3, 0b0010, 1, -1)
    assert A.dominiert_vorwaerts(a, (10.0, 5.0, 3, 0b0010, 1, -1))                   # gleiche Werte: ja
    assert A.dominiert_vorwaerts(a, (11.0, 6.0, 4, 0b0110, 1, -1))                   # überall schlechter, Gedächtnis Obermenge
    assert not A.dominiert_vorwaerts(a, (9.0, 6.0, 4, 0b0110, 1, -1))                # b früher
    assert not A.dominiert_vorwaerts(a, (11.0, 4.0, 4, 0b0110, 1, -1))               # b billiger
    assert not A.dominiert_vorwaerts(a, (11.0, 6.0, 2, 0b0110, 1, -1))               # b mit weniger Last
    assert not A.dominiert_vorwaerts(a, (11.0, 6.0, 4, 0b0100, 1, -1))               # Gedächtnis von a ist keine Teilmenge
    assert A.dominiert_vorwaerts(a, (10.0 + 1e-10, 5.0 + 1e-10, 3, 0b0010, 1, -1))   # innerhalb der Toleranz


def test_backward_dominance_prefers_the_later_latest_start():
    a = (30.0, 5.0, 3, 0b0010, 1, -1)
    assert A.dominiert_rueckwaerts(a, (29.0, 6.0, 4, 0b0110, 1, -1))                 # späteres T ist besser
    assert not A.dominiert_rueckwaerts(a, (31.0, 6.0, 4, 0b0110, 1, -1))             # b darf später beginnen
    assert not A.dominiert_rueckwaerts(a, (29.0, 4.0, 4, 0b0110, 1, -1))
    assert not A.dominiert_rueckwaerts(a, (29.0, 6.0, 2, 0b0110, 1, -1))
    assert not A.dominiert_rueckwaerts(a, (29.0, 6.0, 4, 0b0100, 1, -1))


def test_insertion_drops_a_dominated_label_and_evicts_the_ones_it_dominates(hand):
    s = A.neue_seite(hand, True)
    first = A.fuege_ein(s, (10.0, 5.0, 3, 0b10, 2, 0))
    assert first == 1 and s.lebend[2] == [1]
    assert A.fuege_ein(s, (11.0, 6.0, 3, 0b10, 2, 0)) is None and s.tot[2] and s.dominiert_von[2] == 1          # sofort dominiert, Nummer vergeben
    assert A.fuege_ein(s, (10.0, 5.0, 3, 0b10, 2, 0)) is None and s.dominiert_von[3] == 1                       # gleiche Werte: das frühere bleibt
    best = A.fuege_ein(s, (9.0, 4.0, 3, 0b10, 2, 0))
    assert best == 4 and s.tot[1] and s.dominiert_von[1] == 4 and s.lebend[2] == [4]                             # verdrängt das alte
    assert s.dominiert == 3 and s.erzeugt == 5                                                                  # Start + vier eingefügte


# --- Verlängerungen -----------------------------------------------------------------------------------------------------------------------------

def test_forward_extension_applies_window_wait_load_and_memory(hand, hand_pi):
    ng = A.ng_masken(hand, None)
    ausgang = A.verlaengerungen_vorwaerts(hand, hand_pi, ng, (0.0, 0.0, 0, 0, 0, -1))
    assert [x[0] for x in ausgang] == [1, 2, 3, 4, 5, 6]                                   # vom Depot ist jeder Kunde erreichbar
    assert {x[0]: x[1] for x in ausgang} == {1: 22, 2: 5, 3: 22, 4: 25, 5: 9, 6: 9}       # Beginn = max(Ankunft, Fensteranfang): Kunde 1 wartet von 5 bis 22
    assert [x[2] for x in ausgang if x[0] == 2] == [hand.d[0][2] - 4.5]
    von_5 = A.verlaengerungen_vorwaerts(hand, hand_pi, ng, (9.0, -1.5, 2, 1 << 5, 5, 0))
    assert [x[0] for x in von_5] == [1, 3, 4, 6]                                           # Kunde 2: Ankunft 9 + 2 + 9 = 20 > 17
    assert [x for x in von_5 if x[0] == 6] == [(6, 18, -1.5 + 7 - 10.5, 5, (1 << 5) | (1 << 6))]
    voll = A.verlaengerungen_vorwaerts(hand, hand_pi, ng, (24.0, -6.0, 9, 0b1100010, 1, 0))
    assert voll == []                                                                      # Last 9 + 2 > 9 bei jedem weiteren Kunden


def test_forward_extension_forgets_customers_outside_the_neighbourhood(hand, hand_pi):
    ng = A.ng_masken(hand, 1)                                                              # k = 1: gesperrt bleibt nur der letzte Kunde
    aus = A.verlaengerungen_vorwaerts(hand, hand_pi, ng, (9.0, -1.5, 2, 1 << 5, 5, 0))
    assert all(x[4] == 1 << x[0] for x in aus)


def test_backward_extension_computes_the_latest_start(hand, hand_pi):
    ng = A.ng_masken(hand, None)
    aus = {x[0]: x for x in A.verlaengerungen_rueckwaerts(hand, hand_pi, ng, (float(H), 0.0, 0, 0, 0, -1))}
    assert sorted(aus) == [1, 2, 3, 4, 5, 6]
    assert aus[3][1] == min(31, H - HAND_SVC - hand_d(3, 0)) == 31 and aus[3][2] == hand_d(3, 0) - 9 == -2
    assert aus[1][1] == min(33, H - 2 - 5) == 33 and aus[2][1] == min(17, H - 2 - 3) == 17
    von_4 = {x[0] for x in A.verlaengerungen_rueckwaerts(hand, hand_pi, ng, (34.0, -0.5, 4, 1 << 4, 4, 0))}
    assert von_4 == {1, 2, 3, 5, 6}
    # ein Vorgänger, dessen spätester Beginn vor seinem Fensteranfang liegt, ist unzulässig: Kunde 6 vor Kunde 3 braucht 9 + 2 + 4 = 15 <= T3
    assert 6 not in {x[0] for x in A.verlaengerungen_rueckwaerts(hand, hand_pi, ng, (12.0, 0.0, 2, 1 << 3, 3, 0))}   # T3 = 12: 12 - 2 - 4 = 6 < Fensteranfang 9


# --- Handbeispiel Label für Label -----------------------------------------------------------------------------------------------------------------

@pytest.fixture
def bidi(hand, hand_pi):
    return A.pricing_bidirektional(hand, hand_pi, None, "fest", 20.0, behalte_seiten=True)


def test_hand_forward_labels_are_recomputed_from_their_routes(hand, hand_pi, bidi):
    vor = bidi.vor
    assert [(l[A.L_K]) for l in vor.labels] == [0, 2, 5, 6, 5, 6, 6, 5]                      # F00 bis F07
    for nr, lab in enumerate(vor.labels[1:], 1):
        t, c, q = label_vorwaerts(hand, hand_pi, kette(vor, nr))
        assert (lab[A.L_Z], lab[A.L_C], lab[A.L_Q]) == (t, c, q), nr
        assert t <= 20                                                                         # nur Beginn bis zum Halbweg
    assert kette(vor, 6) == (5, 6) and (vor.labels[6][A.L_Z], vor.labels[6][A.L_C]) == (9 + 2 + 7, -1.5 + 7 - 10.5) == (18, -5)
    assert vor.tot == [False, False, False, False, True, False, False, False] and vor.dominiert_von[4] == 2       # F04 (2, 5) von F02 (5) dominiert


def test_hand_backward_labels_are_recomputed_from_their_routes(hand, hand_pi, bidi):
    rueck = bidi.rueck
    assert [l[A.L_K] for l in rueck.labels] == [0, 1, 3, 4, 1, 3, 3, 4]                      # B00 bis B07
    for nr, lab in enumerate(rueck.labels[1:], 1):
        T, c, q = label_rueckwaerts(hand, hand_pi, kette(rueck, nr))
        assert (lab[A.L_Z], lab[A.L_C], lab[A.L_Q]) == (T, c, q), nr
        assert T >= 20                                                                         # nur spätester Beginn ab dem Halbweg
    assert (rueck.labels[2][A.L_Z], rueck.labels[2][A.L_C]) == (min(31, H - 2 - 7), 7 - 9) == (31, -2)
    assert rueck.tot == [False, False, False, False, False, False, True, False] and rueck.dominiert_von[6] == 2   # B06 {1, 3} von B02 {3} dominiert


def test_hand_connection_finds_the_best_route_over_the_edge_6_3(hand, hand_pi, bidi):
    beste = min(bidi.verbindungen, key=lambda v: v.rc)
    assert beste.kante == (6, 3) and beste.route == (5, 6, 3) and (beste.vor, beste.rueck) == (6, 2)
    f, b = bidi.vor.labels[6], bidi.rueck.labels[2]
    assert f[A.L_Z] + HAND_SVC + hand_d(6, 3) == 18 + 2 + 4 == 24 <= b[A.L_Z] == 31
    assert f[A.L_Q] + b[A.L_Q] == 5 + 2 == 7 <= HAND_Q and not f[A.L_M] & b[A.L_M]
    assert beste.rc == f[A.L_C] + hand_d(6, 3) + b[A.L_C] == -5 + 4 - 2 == -3
    assert ev.pruefe_ergebnis(hand, hand_pi, bidi, True) is None
    assert A.reduzierte_kosten(hand, hand_pi, (5, 6, 3)) == (6 + 7 + 4 + 7) - (7.5 + 10.5 + 9) == -3
    assert A.beste_routen(bidi.verbindungen, 15)[:3] == [(-3.0, (5, 6, 3)), (-1.0, (5, 6, 1)), (-0.5, (6, 5, 4))]


def test_pair_check_names_the_first_violated_rule(hand, bidi):
    f6, f1, b2, b4 = bidi.vor.labels[6], bidi.vor.labels[1], bidi.rueck.labels[2], bidi.rueck.labels[4]
    assert A.paar_pruefung(hand, f6, b2, 6, 3) == ("passt", -3)
    f_spaet = (30.0, 0.0, 0, 0, 5, 0)
    assert A.paar_pruefung(hand, f_spaet, b2, 5, 3) == ("Zeit", None)                         # 30 + 2 + 9 > 31
    f_schwer = (10.0, 0.0, 8, 0, 6, 0)
    assert A.paar_pruefung(hand, f_schwer, b2, 6, 3) == ("Last", None)                        # 8 + 2 > 9 (Zeit 10 + 2 + 4 = 16 passt)
    f_doppelt = (10.0, 0.0, 1, 1 << 3, 6, 0)
    assert A.paar_pruefung(hand, f_doppelt, b2, 6, 3) == ("Gedächtnis", None)                 # Kunde 3 käme zweimal vor
    assert f1[A.L_K] == 2 and b4[A.L_K] == 1


def test_hand_counts_einseitig_and_bidirectional(hand, hand_pi, bidi):
    uni = A.pricing_einseitig(hand, hand_pi, None)
    assert (uni.erzeugt_v, uni.dominiert_v, uni.lebend_v, uni.vergleiche_v) == (35, 11, 24, 102) and uni.erzeugt_v - uni.dominiert_v == uni.lebend_v
    assert uni.routen[:3] == [(-3.0, (5, 6, 3)), (-1.0, (5, 6, 1)), (-0.5, (6, 5, 4))] and len(uni.routen) == 3
    assert (bidi.erzeugt_v, bidi.erzeugt_r, bidi.labels) == (8, 8, 16) and (bidi.lebend_v, bidi.lebend_r) == (7, 7) and bidi.vergleiche == 16
    assert (bidi.paare, bidi.kanten) == (48, 15) and (bidi.paare_alle, bidi.kanten_alle) == (48, 15)
    assert [r for r in bidi.routen if r[0] < 0] == uni.routen                                 # dieselben drei negativen Routen
    assert round(bidi.labels / uni.labels, 2) == 0.46 and bidi.abgeschnitten_v > 0 and bidi.abgeschnitten_r > 0


def test_hand_halfway_series_counts(hand, hand_pi):
    erwartet = {0: (1, 35, 22, 6, 22, 6), 10: (4, 30, 70, 22, 72, 24), 15: (4, 22, 52, 22, 54, 24), 20: (8, 8, 48, 15, 48, 15), 25: (25, 7, 97, 22, 113, 24),
                30: (29, 4, 62, 22, 72, 24), 40: (35, 1, 23, 6, 23, 6)}
    for m, (v, r, paare, kanten, paare_alle, kanten_alle) in erwartet.items():
        e = A.pricing_bidirektional(hand, hand_pi, None, "fest", float(m))
        assert (e.erzeugt_v, e.erzeugt_r, e.paare, e.kanten, e.paare_alle, e.kanten_alle) == (v, r, paare, kanten, paare_alle, kanten_alle), m
        assert e.beste == (-3.0, (5, 6, 3))                                                    # bei jedem Halbweg dieselbe beste Route
    assert [erwartet[m][0] + erwartet[m][1] for m in erwartet] == [36, 34, 26, 16, 32, 33, 36]   # Summe U-förmig, Minimum bei H/2 = 20


def test_halfway_extremes_reduce_to_a_one_sided_labeling(hand, hand_pi):
    uni = A.pricing_einseitig(hand, hand_pi, None)
    rein_rueckwaerts = A.pricing_bidirektional(hand, hand_pi, None, "fest", 0.0)
    rein_vorwaerts = A.pricing_bidirektional(hand, hand_pi, None, "fest", float(H))
    assert rein_rueckwaerts.erzeugt_v == 1 and rein_vorwaerts.erzeugt_r == 1                  # nur der Start der leeren Seite
    assert rein_rueckwaerts.erzeugt_r == 35 and rein_vorwaerts.erzeugt_v == uni.erzeugt_v      # M = H: genau das einseitige Verfahren
    assert rein_vorwaerts.beste == uni.beste == rein_rueckwaerts.beste


def test_connection_matches_a_plain_loop_over_all_pairs(hand, hand_pi, bidi):
    """Die Matrixoperation je Kante findet je Kante dasselbe wie eine einfache Schleife über alle Paare mit `paar_pruefung`."""
    vor, rueck = bidi.vor, bidi.rueck
    von_schleife = {}
    for i in range(7):
        for j in range(7):
            if i == j:
                continue
            for f in vor.lebend[i]:
                for b in rueck.lebend[j]:
                    grund, kosten = A.paar_pruefung(hand, vor.labels[f], rueck.labels[b], i, j)
                    if grund == "passt" and kosten < -1e-7 and ((i, j) not in von_schleife or kosten < von_schleife[(i, j)]):
                        von_schleife[(i, j)] = kosten
    assert {v.kante: v.rc for v in bidi.verbindungen} == von_schleife


def test_dynamic_versions_find_the_same_best_route_on_the_hand_example(hand, hand_pi):
    for modus in ("dyn", "dynF", "dynB", "dynD"):
        e = A.pricing_bidirektional(hand, hand_pi, None, modus)
        assert e.beste == (-3.0, (5, 6, 3)), modus
    assert A.pricing_bidirektional(hand, hand_pi, None, "dynD").halbweg is not None


def test_unknown_mode_and_label_budget(hand, hand_pi):
    with pytest.raises(ValueError):
        A.pricing_bidirektional(hand, hand_pi, None, "schnell")
    for e in (A.pricing_einseitig(hand, hand_pi, None, max_labels=10), A.pricing_bidirektional(hand, hand_pi, None, "fest", 20.0, max_labels=5),
              A.pricing_bidirektional(hand, hand_pi, None, "dynD", max_labels=5), A.pricing_bidirektional(hand, hand_pi, None, "dyn", max_labels=5)):
        assert e.abgebrochen and e.routen == []


# --- Aufzählung und Prüfer -----------------------------------------------------------------------------------------------------------------

def test_hand_enumeration_has_39_routes_and_three_negative(hand, hand_pi):
    wege = A.alle_zulaessigen_wege(hand)
    assert len(wege) == 39 and len(set(wege)) == 39
    rc = sorted((A.reduzierte_kosten(hand, hand_pi, w), w) for w in wege)
    assert rc[0] == (-3.0, (5, 6, 3)) and sum(1 for x, _ in rc if x < -1e-7) == 3
    assert all(A.pruefe_route(hand, w)[0] for w in wege)


def test_route_checker_names_the_violated_rule(hand):
    assert A.pruefe_route(hand, (5, 6, 3)) == (True, "zulässig (Last, Fenster, Rückkehr)")
    assert A.pruefe_route(hand, (1, 4, 5))[1] == "unzulässig bei Kunde 5: Last 10 > 9"
    assert A.pruefe_route(hand, (6, 2))[1] == "unzulässig bei Kunde 2: Ankunft 21 > Fensterende 17"
    assert A.pruefe_route(hand, (5, 5))[1] == "ein Kunde kommt mehrfach vor" and A.pruefe_route(hand, ())[1] == "leere Route"
    assert A.pruefe_route(hand, (5, 5), elementar=False)[0] is True                          # ohne die Elementarität ist der Kunde 5 zweimal zulässig: Last 2 + 2 <= 9, Beginn 11 <= 19, Rückkehr 11 + 2 + 6 = 19 <= 40
    assert A.pruefe_route(hand, (7,))[1] == "Kunde außerhalb von 1 bis n"


def test_worst_case_at_the_slider_maximum_terminates_with_a_result_or_the_size_message():
    """Hänger-Netz (DEMO-PLAYBOOK §1c): alle Regler am Maximum, schwerster Fall der Live-Rechnung; das Ergebnis ist da oder die Rechnung meldet ihre Größe, nie ein Hänger."""
    s = ev.Settings(n=C.N_MAX, breite=C.BREITE_MAX, typ="gruppiert", q=max(C.KAPAZITAETEN), k=max(C.K_OPTIONEN), runde=1, halbweg_pct=C.HALBWEG_MAX, seed=3)
    a = ev.analyse_live(s)
    assert a.zu_gross is not None or (a.uni.routen and a.bidi.routen)
