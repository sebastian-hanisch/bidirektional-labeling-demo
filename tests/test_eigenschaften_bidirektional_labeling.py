"""Eigenschaftstests (ORACLE-PLAYBOOK §5.2): Aussagen, die für das Verfahren gelten müssen, ohne dass man das richtige Ergebnis kennt.

Je Eigenschaft 10 bis 20 Instanzen mit festem Zufalls-Seed. Belegt sind sie durch die Definition des Verfahrens: Das Ergebnis darf nicht an der Wahl des Halbwegs, an der Nummerierung der Kunden
oder an der Einheit von Strecke und Zeit hängen, und ohne Gewinn in den Dualpreisen gibt es keine negative Route."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

import bdl_algorithm as A
import bdl_scenario as S
from bdl_rng import SplitMix64
from bdl_scenario import Instanz

ROOT = Path(__file__).resolve().parent.parent


def preise(n, seed):
    rng = SplitMix64(2000 + seed)
    return (0.0,) + tuple(round(rng.uniform(0, 70), 2) for _ in range(n))


def umnummeriert(inst: Instanz, pi, perm):
    """Dieselbe Instanz mit anderer Kundennummerierung: Kunde j heißt danach perm[j - 1] (perm ist eine Permutation von 1 bis n)."""
    n = inst.n
    neu = {0: 0}
    for j in range(1, n + 1):
        neu[j] = perm[j - 1]
    umgekehrt = {v: k for k, v in neu.items()}
    ordnung = [umgekehrt[i] for i in range(n + 1)]            # neue Nummer i war früher Kunde ordnung[i]
    d = tuple(tuple(inst.d[a][b] for b in ordnung) for a in ordnung)
    return (Instanz(tuple(inst.pts[a] for a in ordnung), d, tuple(inst.dem[a] for a in ordnung), tuple(inst.ready[a] for a in ordnung), tuple(inst.due[a] for a in ordnung), inst.H, inst.Q, inst.svc),
            tuple(pi[a] for a in ordnung))


def test_best_cost_does_not_depend_on_the_halfway():
    """Jeder Halbweg von 0 bis H (21 Werte, auch die beiden Ränder) liefert dieselben besten reduzierten Kosten wie das einseitige Verfahren."""
    for seed in range(12):
        inst = S.instanz_aus_seed(10, seed, 80, "gruppiert" if seed % 2 else "zufaellig")
        pi = preise(10, seed)
        for k in (None, 5):
            ref = A.pricing_einseitig(inst, pi, k).beste_rc
            for schritt in range(21):
                e = A.pricing_bidirektional(inst, pi, k, "fest", inst.H * schritt / 20)
                assert e.beste_rc == pytest.approx(ref, abs=1e-6), (seed, k, schritt)


def test_result_does_not_depend_on_the_numbering_of_the_customers():
    """Elementar: andere Nummerierung der Kunden, dieselben besten reduzierten Kosten (einseitig und bidirektional); die gefundene Route heißt dann anders, hat aber dieselben Kosten."""
    for seed in range(10):
        inst = S.instanz_aus_seed(9, seed, 80, "zufaellig")
        pi = preise(9, seed)
        rng = SplitMix64(seed)
        perm = list(range(1, 10))
        for i in range(8, 0, -1):                                # Mischen mit dem übergebenen Generator
            j = rng.wahl(i + 1)
            perm[i], perm[j] = perm[j], perm[i]
        inst2, pi2 = umnummeriert(inst, pi, perm)
        for verfahren in (lambda i, p: A.pricing_einseitig(i, p, None), lambda i, p: A.pricing_bidirektional(i, p, None, "fest", i.H / 2)):
            a, b = verfahren(inst, pi), verfahren(inst2, pi2)
            assert a.beste_rc == pytest.approx(b.beste_rc, abs=1e-6), seed
            if b.beste:
                assert A.pruefe_route(inst2, b.beste[1])[0] and A.reduzierte_kosten(inst2, pi2, b.beste[1]) == pytest.approx(b.beste_rc, abs=1e-6)


def test_zero_prices_give_no_negative_route():
    """Ohne Dualpreise sind die reduzierten Kosten jeder Route die Wegstrecke, also nicht negativ: kein Verfahren findet eine Spalte."""
    for seed in range(10):
        inst = S.instanz_aus_seed(12, seed, 100, "gruppiert" if seed % 2 else "zufaellig")
        pi = (0.0,) * 13
        for e in (A.pricing_einseitig(inst, pi, 5), A.pricing_bidirektional(inst, pi, 5, "fest"), A.pricing_bidirektional(inst, pi, 5, "dynD")):
            assert e.routen == [] and e.beste_rc == 0.0 and e.beste is None


def test_scaling_distances_times_and_prices_scales_the_cost_and_keeps_the_label_counts():
    """Alle Strecken, Zeiten (Fenster, Bedienzeit, Horizont) und Dualpreise mit 2 multipliziert: die Kosten verdoppeln sich, die Label-Zahlen bleiben (die Reihenfolge der Vergleiche ändert sich nicht)."""
    for seed in range(8):
        inst = S.instanz_aus_seed(10, seed, 80, "zufaellig")
        pi = preise(10, seed)
        zwei = Instanz(inst.pts, tuple(tuple(2 * x for x in z) for z in inst.d), inst.dem, tuple(2 * x for x in inst.ready), tuple(2 * x for x in inst.due), 2 * inst.H, inst.Q, 2 * inst.svc)
        pi2 = tuple(2 * p for p in pi)
        for modus in ("fest", "dynD"):
            a = A.pricing_bidirektional(inst, pi, 5, modus, halbweg=inst.H / 2 if modus == "fest" else None)
            b = A.pricing_bidirektional(zwei, pi2, 5, modus, halbweg=zwei.H / 2 if modus == "fest" else None)
            assert (a.erzeugt_v, a.erzeugt_r, a.paare, a.kanten) == (b.erzeugt_v, b.erzeugt_r, b.paare, b.kanten), (seed, modus)
            assert b.beste_rc == pytest.approx(2 * a.beste_rc, abs=1e-6)
        u, u2 = A.pricing_einseitig(inst, pi, 5), A.pricing_einseitig(zwei, pi2, 5)
        assert (u.erzeugt_v, u.vergleiche_v) == (u2.erzeugt_v, u2.vergleiche_v)


def test_dominance_never_changes_the_best_cost(monkeypatch):
    """Ohne Dominanz (beide Regeln immer falsch) und mit ihr dieselben besten Kosten, aber ohne Dominanz mehr Labels: die Regeln streichen nur Überflüssiges (6 Kunden, elementar)."""
    for seed in range(10):
        inst = S.instanz_aus_seed(6, seed, 100, "zufaellig")
        pi = preise(6, seed)
        mit = [A.pricing_einseitig(inst, pi, None), A.pricing_bidirektional(inst, pi, None, "fest")]
        with monkeypatch.context() as m:
            m.setattr(A, "dominiert_vorwaerts", lambda a, b: False)
            m.setattr(A, "dominiert_rueckwaerts", lambda a, b: False)
            ohne = [A.pricing_einseitig(inst, pi, None), A.pricing_bidirektional(inst, pi, None, "fest")]
        for x, y in zip(mit, ohne):
            assert x.beste_rc == pytest.approx(y.beste_rc, abs=1e-6), seed
            assert y.labels >= x.labels and y.dominiert_v == 0 and y.dominiert_r == 0
    assert ohne[0].labels > mit[0].labels                        # in der letzten Instanz streicht die Dominanz wirklich Labels


def test_same_input_gives_the_same_counts_in_two_processes_with_different_hash_seeds():
    """Kein Ergebnis hängt von der Reihenfolge einer Menge oder eines Wörterbuchs ab (DEMO-PLAYBOOK §1d): gleiche Eingabe, zwei Prozesse mit PYTHONHASHSEED 1 und 2, gleiche Zählungen."""
    code = ("import sys; sys.path.insert(0, %r); import bdl_algorithm as A, bdl_scenario as S;"
            "i = S.instanz_aus_seed(14, 4, 100, 'gruppiert'); pi = S.einzelfahrt_preise(i);"
            "r = [A.pricing_einseitig(i, pi, 5), A.pricing_bidirektional(i, pi, 5, 'fest'), A.pricing_bidirektional(i, pi, 5, 'dynD')];"
            "print([(e.erzeugt_v, e.erzeugt_r, e.paare, e.vergleiche, e.beste) for e in r])" % str(ROOT))
    aus = []
    for hashseed in ("1", "2"):
        p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120, env={**os.environ, "PYTHONHASHSEED": hashseed})
        assert p.returncode == 0, p.stderr[-400:]
        aus.append(p.stdout.strip())
    assert aus[0] == aus[1] and aus[0]
