"""Die Spaltenerzeugung, die die Dualpreise der Runden liefert: Schleife über Master (`bdl_master.loese_master`) und einseitiges Pricing (`bdl_algorithm.pricing_einseitig`).

Start: die Einzelfahrten 0-j-0 als Spalten. Je Runde: Master lösen (Dualpreise), Pricing mit diesen Preisen, die besten neuen Routen als Spalten anhängen; Ende, wenn das Pricing keine
Route mit negativen reduzierten Kosten mehr findet. Die Dualpreise der Runden 1, 3, 8 und des Endes sind die Eingabe der Messreihen: Das bidirektionale Labeling wird später auf genau diesen
Preisen gegen das einseitige gemessen. Das Pricing der Spaltenerzeugung selbst ist das einseitige Labeling (wie in den Messreihen)."""

from dataclasses import dataclass

import bdl_constants as C
from bdl_algorithm import pricing_einseitig
from bdl_master import loese_master
from bdl_scenario import Instanz


@dataclass(frozen=True)
class Spaltenerzeugung:
    duale: dict            # Runde -> Dualpreise (Tuple), für die gewünschten Runden, soweit erreicht
    ende: tuple | None     # Dualpreise der letzten Master-Lösung (das Pricing findet danach keine Route mehr), None bei Abbruch oder wenn nur bis zu einer Runde gerechnet wurde
    runden: int            # Zahl der gelösten Master
    schranke: float | None
    spalten: int
    labels: int            # Summe der erzeugten Labels aller Pricing-Aufrufe
    abgebrochen: bool      # Label-Obergrenze oder Rundengrenze erreicht


def duale_der_runden(inst: Instanz, k: int | None, runden=(1, 3, 8), bis_runde: int | None = None, max_labels: int = C.LABEL_CAP_SPALTENERZEUGUNG,
                     max_runden: int = C.MAX_RUNDEN, spalten_je_runde: int = C.SPALTEN_JE_RUNDE) -> Spaltenerzeugung:
    """Spaltenerzeugung mit Überdeckungs-Master. Gibt die Dualpreise der Runden `runden` zurück (Master der Runde 1 = nur Einzelfahrten) und die am Ende.

    `bis_runde`: bricht nach dem Master dieser Runde ab (spart das Pricing, wenn nur frühe Dualpreise gebraucht werden); `ende` ist dann None.
    Überschreiten die erzeugten Labels `max_labels` (Summe aller Pricing-Aufrufe), bricht die Rechnung ab (`abgebrochen`)."""
    spalten = [(j,) for j in range(1, inst.n + 1)]
    bekannt = set(spalten)
    duale = {}
    labels_ges = 0
    pi = None
    master = None
    for nr in range(1, max_runden + 1):
        master = loese_master(inst, spalten)
        pi = master.pi
        if nr in runden:
            duale[nr] = pi
        if bis_runde is not None and nr >= bis_runde:
            return Spaltenerzeugung(duale, None, nr, master.wert, len(spalten), labels_ges, False)
        erg = pricing_einseitig(inst, pi, k, max_routen=spalten_je_runde, max_labels=max(1, max_labels - labels_ges))
        labels_ges += erg.erzeugt_v
        if erg.abgebrochen:
            return Spaltenerzeugung(duale, None, nr, None, len(spalten), labels_ges, True)
        frisch = [r for _, r in erg.routen if r not in bekannt]
        if not frisch:
            return Spaltenerzeugung(duale, pi, nr, master.wert, len(spalten), labels_ges, False)
        for r in frisch:
            spalten.append(r)
            bekannt.add(r)
    return Spaltenerzeugung(duale, None, max_runden, None, len(spalten), labels_ges, True)

