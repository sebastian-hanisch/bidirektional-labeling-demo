"""Orakel-Tests (ORACLE-PLAYBOOK §5, DEMO-PLAYBOOK §12): einseitiges und bidirektionales Labeling gegen einen unabhängigen Rechenweg.

Orakel: Tiefensuche über alle zulässigen Routen (`tests/referenz.py`), ohne Labels, ohne Dominanz, ohne Bitmasken; das ng-Gedächtnis nach der Definition aus der Literatur. Das Orakel selbst
wird zuerst am Handbeispiel geprüft (39 zulässige Routen, Handrechnung der besten Route). Verglichen werden die besten reduzierten Kosten, die Menge der gelieferten Routen (jede ist zulässig
und hat richtig bewertete Kosten) und die Gleichheit der Verfahren untereinander (jeder Halbweg, jede dynamische Fassung). Der große Lauf (200 Instanzen) steht nicht im Repo (README, „Tests“)."""

import pytest
import referenz as R

import bdl_algorithm as A
import bdl_scenario as S
from bdl_rng import SplitMix64


def zufalls_preise(n, seed):
    """Dualpreise zwischen 0 und 70, damit die besten reduzierten Kosten meist negativ sind (Index 0 = Depot)."""
    rng = SplitMix64(1000 + seed)
    return (0.0,) + tuple(round(rng.uniform(0, 70), 2) for _ in range(n))


def alle_verfahren(inst, pi, k):
    """Einseitig, bidirektional mit festen Halbwegen (0, H/4, H/2, 3H/4, H) und die vier dynamischen Fassungen."""
    aus = {"uni": A.pricing_einseitig(inst, pi, k)}
    for anteil in (0.0, 0.25, 0.5, 0.75, 1.0):
        aus[f"fest{anteil}"] = A.pricing_bidirektional(inst, pi, k, "fest", anteil * inst.H)
    for modus in ("dyn", "dynF", "dynB", "dynD"):
        aus[modus] = A.pricing_bidirektional(inst, pi, k, modus)
    return aus


def test_oracle_on_the_hand_example(hand, hand_pi):
    """Das Orakel zuerst an der Handrechnung: 39 zulässige Routen, die beste (5, 6, 3) mit 24 - 27 = -3, drei negative."""
    wege = R.alle_routen(hand)
    assert len(wege) == 39
    assert R.rc(hand, hand_pi, (5, 6, 3)) == (6 + 7 + 4 + 7) - (7.5 + 10.5 + 9) == -3
    assert R.beste(hand, hand_pi) == (-3.0, {(5, 6, 3)}) and R.negative(hand, hand_pi) == {(5, 6, 3), (5, 6, 1), (6, 5, 4)}
    for name, e in alle_verfahren(hand, hand_pi, None).items():
        assert e.beste == (-3.0, (5, 6, 3)), name
        assert {r for rc, r in e.routen} <= R.negative(hand, hand_pi), name                    # jede gelieferte negative Route ist zulässig
    assert {r for _, r in A.pricing_einseitig(hand, hand_pi, None).routen} == R.negative(hand, hand_pi)     # das einseitige Verfahren findet alle drei


@pytest.mark.parametrize("breite", [30, 80, 200])
def test_elementary_labeling_matches_the_depth_first_oracle(breite):
    """7 Kunden, 20 Instanzen je Fensterbreite, Dualpreise zufällig: alle Verfahren finden die besten reduzierten Kosten des Orakels, die gelieferten Routen sind unabhängig nachgerechnet."""
    negativ = 0
    for seed in range(20):
        typ = "gruppiert" if seed % 2 else "zufaellig"
        inst = S.instanz_aus_seed(7, seed, breite, typ)
        pi = zufalls_preise(7, seed)
        erwartet, optimal = R.beste(inst, pi)
        negativ += erwartet < 0
        for name, e in alle_verfahren(inst, pi, None).items():
            assert e.beste_rc == pytest.approx(erwartet, abs=1e-6), (breite, seed, name)
            if erwartet < 0:
                assert e.beste[1] in optimal, (breite, seed, name)                              # eine der optimalen Routen
            for rc, route in e.routen:
                assert A.pruefe_route(inst, route)[0] and R.rc(inst, pi, route) == pytest.approx(rc, abs=1e-6), (breite, seed, name, route)
    assert negativ >= 15                                                                         # der Test ist nicht trivial: meist gibt es eine negative Route


def test_ng_memory_matches_the_literature_definition_of_ng_routes():
    """Kleines Gedächtnis (k = 1 und 2): Routen dürfen Kunden wiederholen, wenn zwischen den Besuchen ein Kunde liegt, dessen Nachbarschaft ihn nicht enthält. Fünf Kunden, kurzer Horizont."""
    verschieden = 0
    for k in (1, 2):
        for seed in range(12):
            inst = S.instanz_aus_seed(5, seed, 60, "zufaellig", H=90.0)
            pi = zufalls_preise(5, seed)
            erwartet, _ = R.beste(inst, pi, k)
            for name, e in alle_verfahren(inst, pi, k).items():
                assert e.beste_rc == pytest.approx(erwartet, abs=1e-6), (k, seed, name)
                for rc, route in e.routen:
                    assert A.pruefe_route(inst, route, elementar=False)[0] and R.ng_zulaessig(route, R.nachbarschaften(inst, k)) and R.rc(inst, pi, route) == pytest.approx(rc, abs=1e-6)
            verschieden += erwartet < R.beste(inst, pi, None)[0] - 1e-6                           # das Gedächtnis erlaubt Wiederholungen: bessere Kosten als elementar
    assert verschieden >= 3                                                                      # der Test trifft Fälle, in denen ein kleines Gedächtnis etwas ändert


@pytest.mark.parametrize("k", [5, 3])
def test_bidirectional_equals_one_sided_with_the_same_memory_on_twelve_customers(k):
    """12 Kunden (zu groß für die Aufzählung): jedes Verfahren findet dieselben besten reduzierten Kosten wie das einseitige mit gleichem Gedächtnis."""
    for seed in range(8):
        for breite in (40, 100):
            inst = S.instanz_aus_seed(12, seed, breite, "gruppiert" if seed % 2 else "zufaellig")
            pi = zufalls_preise(12, seed)
            ergebnisse = alle_verfahren(inst, pi, k)
            ref = ergebnisse["uni"].beste_rc
            assert all(e.beste_rc == pytest.approx(ref, abs=1e-6) for e in ergebnisse.values()), (k, seed, breite)


def test_displayed_counts_are_consistent():
    """Auch die gezeigten Kennzahlen: erzeugte Labels = dominierte + lebende (+ Start je Seite zählt als erzeugt), Paare sind nie mehr als das Produkt aller lebenden Labels je Kante."""
    inst = S.instanz_aus_seed(12, 3, 100, "gruppiert")
    pi = zufalls_preise(12, 3)
    for name, e in alle_verfahren(inst, pi, 5).items():
        assert e.erzeugt_v - e.dominiert_v == e.lebend_v and e.erzeugt_r - e.dominiert_r == e.lebend_r, name
        assert e.paare <= e.paare_alle and e.kanten <= e.kanten_alle, name
        if name == "uni":
            assert e.erzeugt_r == 0 and e.paare == 0
