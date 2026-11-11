"""Gemeinsame Fixtures: das Handbeispiel von Hand (DEMO-PLAYBOOK §1b), unabhängig vom Szenario-Modul noch einmal hingeschrieben.

Das Handbeispiel (Tabelle der Aufgabe): Depot bei (5, 5) und 6 Kunden auf einem Gitter, Entfernung = Fahrzeit = Kosten = Manhattan-Abstand (erfüllt die Dreiecksungleichung), Bedienzeit 2,
Kapazität 9, Rückkehr bis 40. Die Reduzierten Kosten einer Route sind die Summe ihrer Abstände (Depot - Kunden - Depot) minus die Summe der Dualpreise ihrer Kunden.
Die erwarteten Werte stehen in den Tests als Rechnung (Summen, Differenzen), nicht als abgeschriebene Ergebnisse des Codes; ein Test prüft, dass das Szenario-Modul dieselben Zahlen enthält."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bdl_scenario import Instanz  # noqa: E402

# Kunde: Lage, Fenster (Beginn der Bedienung), Bedarf, Dualpreis, laut Tabelle der Aufgabe
HAND_TABELLE = {
    1: ((5, 0), (22, 33), 4, 5.0),
    2: ((4, 7), (5, 17), 3, 4.5),
    3: ((0, 3), (22, 31), 2, 9.0),
    4: ((6, 2), (25, 34), 4, 4.5),
    5: ((7, 1), (9, 19), 2, 7.5),
    6: ((1, 0), (9, 19), 3, 10.5),
}
HAND_DEPOT = (5, 5)
HAND_SVC, HAND_Q, HAND_H = 2, 9, 40


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def hand_lage(i):
    return HAND_DEPOT if i == 0 else HAND_TABELLE[i][0]


def hand_d(i, j):
    return manhattan(hand_lage(i), hand_lage(j))


@pytest.fixture
def hand():
    """Das Handbeispiel als Instanz, aus der Tabelle oben gebaut (nicht aus bdl_scenario)."""
    pts = tuple(hand_lage(i) for i in range(7))
    d = tuple(tuple(hand_d(i, j) for j in range(7)) for i in range(7))
    dem = (0,) + tuple(HAND_TABELLE[i][2] for i in range(1, 7))
    ready = (0,) + tuple(HAND_TABELLE[i][1][0] for i in range(1, 7))
    due = (HAND_H,) + tuple(HAND_TABELLE[i][1][1] for i in range(1, 7))
    return Instanz(pts, d, dem, ready, due, HAND_H, HAND_Q, HAND_SVC)


@pytest.fixture
def hand_pi():
    return (0.0,) + tuple(HAND_TABELLE[i][3] for i in range(1, 7))


def mini_instanz(lagen, dem, fenster, H=100, Q=10, svc=1):
    """Kleine Instanz aus Lagen (Index 0 = Depot, Manhattan), Lasten ab Kunde 1 und Fenstern (früh, spät) ab Kunde 1."""
    d = tuple(tuple(manhattan(a, b) for b in lagen) for a in lagen)
    ready = (0,) + tuple(f[0] for f in fenster)
    due = (H,) + tuple(f[1] for f in fenster)
    return Instanz(tuple(lagen), d, (0,) + tuple(dem), ready, due, H, Q, svc)
