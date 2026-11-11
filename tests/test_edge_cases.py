"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): ein Kunde, zwei Kunden, Last genau Q, ein Label genau am Halbweg, Kreise über die Naht bei kleinem Gedächtnis,
unerreichbare Kunden, Gleichstände, Halbweg außerhalb von 0 bis H."""

import pytest
from conftest import mini_instanz

import bdl_algorithm as A

H = 100


def beide(inst, pi, k=None, halbweg=None):
    return A.pricing_einseitig(inst, pi, k), A.pricing_bidirektional(inst, pi, k, "fest", halbweg)


def test_single_customer_is_found_when_the_price_pays_for_the_trip():
    """n = 1: Depot (0, 0), Kunde bei (3, 4) im Manhattan-Abstand 7; die Route hat reduzierte Kosten 14 - Dualpreis."""
    inst = mini_instanz([(0, 0), (3, 4)], [2], [(0, 90)])
    for e in beide(inst, (0.0, 20.0)):
        assert e.routen == [(14 - 20.0, (1,))]
    for e in beide(inst, (0.0, 14.0)):
        assert e.routen == [] and e.beste is None                              # Gleichstand: reduzierte Kosten 0 sind nicht negativ
    for e in beide(inst, (0.0, 10.0)):
        assert e.routen == []


def test_exactly_two_customers_in_both_orders():
    """n = 2: beide Reihenfolgen sind zu prüfen; mit Fenstern, die nur eine Reihenfolge erlauben, findet jedes Verfahren genau diese."""
    inst = mini_instanz([(0, 0), (5, 0), (10, 0)], [1, 1], [(0, 6), (12, 40)])
    for e in beide(inst, (0.0, 30.0, 30.0)):
        assert e.beste == (5 + 5 + 10 - 60, (1, 2)) and (2, 1) not in {r for _, r in e.routen}
    inst2 = mini_instanz([(0, 0), (5, 0), (10, 0)], [1, 1], [(0, 90), (0, 90)])
    for e in beide(inst2, (0.0, 30.0, 30.0)):
        assert e.beste[1] in {(1, 2), (2, 1)} and e.beste_rc == pytest.approx(20 - 60)


def test_load_exactly_at_the_capacity_is_allowed():
    """Last genau Q ist zulässig (inklusive Grenze), Last Q + 1 nicht; beide Seiten und die Verbindung halten sich daran."""
    gut = mini_instanz([(0, 0), (4, 0), (8, 0)], [3, 3], [(0, 90), (0, 90)], Q=6)
    schlecht = mini_instanz([(0, 0), (4, 0), (8, 0)], [3, 3], [(0, 90), (0, 90)], Q=5)
    pi = (0.0, 20.0, 20.0)
    for e in beide(gut, pi):
        assert e.beste[1] in {(1, 2), (2, 1)}
    for e in beide(schlecht, pi):
        assert len(e.beste[1]) == 1 and all(len(r) == 1 for _, r in e.routen)


def test_a_label_exactly_at_the_halfway_is_found_for_every_nearby_halfway():
    """Ein Kunde, dessen Beginn genau bei M liegt, geht durch die Verbindung nicht verloren (M gleich, knapp darunter und knapp darüber)."""
    inst = mini_instanz([(0, 0), (30, 0), (30, 10)], [1, 1], [(30, 50), (50, 70)], svc=5)
    # Kunde 1: Beginn 30; Kunde 2 danach: Ankunft 30 + 5 + 10 = 45, Beginn 50 (Warten); Rückkehr 50 + 5 + 40 = 95 <= 100; Wegstrecke 30 + 10 + 40 = 80 gegen Dualpreise 120
    pi = (0.0, 60.0, 60.0)
    ref = A.pricing_einseitig(inst, pi, None).beste
    assert ref == (80 - 120, (1, 2))
    for m in (29.0, 29.999, 30.0, 30.001, 31.0, 45.0, 44.999):
        assert A.pricing_bidirektional(inst, pi, None, "fest", m).beste == ref, m


def test_halfway_outside_zero_to_h_behaves_like_the_nearest_border(hand, hand_pi):
    ref0 = A.pricing_bidirektional(hand, hand_pi, None, "fest", 0.0)
    refh = A.pricing_bidirektional(hand, hand_pi, None, "fest", float(hand.H))
    unten = A.pricing_bidirektional(hand, hand_pi, None, "fest", -5.0)
    oben = A.pricing_bidirektional(hand, hand_pi, None, "fest", hand.H + 5.0)
    assert (unten.erzeugt_v, unten.erzeugt_r, unten.beste) == (ref0.erzeugt_v, ref0.erzeugt_r, ref0.beste)
    assert (oben.erzeugt_v, oben.erzeugt_r, oben.beste) == (refh.erzeugt_v, refh.erzeugt_r, refh.beste)


def test_cycles_across_the_seam_with_memory_one():
    """Gedächtnis k = 1: Kunde 1 darf nach Kunde 2 noch einmal besucht werden (1 liegt nicht in der Nachbarschaft von 2). Auch wenn der erste Besuch vorwärts und der zweite rückwärts liegt
    (Halbweg dazwischen), findet die Verbindung diese Route; mit dem Gedächtnis aller Kunden gibt es sie nicht."""
    inst = mini_instanz([(0, 0), (4, 0), (8, 0)], [1, 1], [(0, 95), (0, 95)], H=H, svc=5, Q=3)          # Kapazität 3: höchstens drei Besuche
    pi = (0.0, 60.0, 4.0)
    ref_ng = A.pricing_einseitig(inst, pi, 1)
    assert ref_ng.beste == (16 - 124, (1, 2, 1)) and A.pruefe_route(inst, (1, 2, 1), elementar=False)[0]
    ref_el = A.pricing_einseitig(inst, pi, None)
    assert len(set(ref_el.beste[1])) == len(ref_el.beste[1]) and ref_el.beste_rc > ref_ng.beste_rc
    for m in (0.0, 20.0, 25.0, 40.0, 50.0, 60.0, 80.0, 100.0):
        e = A.pricing_bidirektional(inst, pi, 1, "fest", m)
        assert e.beste == ref_ng.beste, m
    for modus in ("dyn", "dynF", "dynB", "dynD"):
        assert A.pricing_bidirektional(inst, pi, 1, modus).beste == ref_ng.beste, modus


def test_unreachable_customers_leave_only_the_starts():
    """Fenster, die vor der Fahrzeit enden: keine Verlängerung, nur die beiden Starts, keine Route, kein Fehler."""
    inst = mini_instanz([(0, 0), (30, 0), (0, 30)], [1, 1], [(0, 10), (0, 10)])
    pi = (0.0, 500.0, 500.0)
    uni, bidi = beide(inst, pi)
    assert uni.routen == [] and bidi.routen == [] and uni.erzeugt_v == 1 and (bidi.erzeugt_v, bidi.erzeugt_r) == (1, 1) and bidi.paare == 0


def test_customers_with_identical_position_and_window_give_a_deterministic_result():
    """Gleichstand: zwei Kunden am selben Ort mit gleichem Fenster; das Ergebnis ist bei jedem Lauf dasselbe, und die Route nimmt beide mit."""
    inst = mini_instanz([(0, 0), (5, 5), (5, 5)], [1, 1], [(0, 80), (0, 80)])
    pi = (0.0, 30.0, 30.0)
    erste = beide(inst, pi)
    zweite = beide(inst, pi)
    assert [e.routen for e in erste] == [e.routen for e in zweite]
    assert erste[0].beste[1] in {(1, 2), (2, 1)} and erste[0].beste_rc == pytest.approx(20 - 60) and erste[0].beste == erste[1].beste


def test_window_over_the_whole_horizon_and_late_depot_return():
    """Fenster [0, H] für einen Kunden direkt am Rand: Rückkehr genau zur Zeit H ist zulässig, eine Zeiteinheit später nicht."""
    inst = mini_instanz([(0, 0), (40, 0)], [1], [(0, 100)], H=100, svc=20)           # hin 40, Bedienung 20, zurück 40: Ankunft 100 = H
    assert beide(inst, (0.0, 200.0))[0].beste is not None and beide(inst, (0.0, 200.0))[1].beste is not None
    zu_spaet = mini_instanz([(0, 0), (40, 0)], [1], [(0, 100)], H=99, svc=20)
    assert beide(zu_spaet, (0.0, 200.0))[0].routen == [] and beide(zu_spaet, (0.0, 200.0))[1].routen == []
