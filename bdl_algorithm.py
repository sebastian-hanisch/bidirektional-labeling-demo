"""Kern der Demo: Labeling mit Dominanz und ng-Gedächtnis, einseitig (vorwärts) und bidirektional (vorwärts und rückwärts, in der Mitte der Zeit verbunden).

Jede Regel ist eine eigene Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK §1b); es gibt keinen versteckten Zustand und keinen Zufall. Der Zustand einer Richtung steht
in einer `Seite`, die den Funktionen übergeben wird. Die Steuerung (`pricing_einseitig`, `pricing_bidirektional`) ruft nur der Reihe nach auf.

**Label.** Ein Tupel `(z, c, q, m, knoten, eltern)`:
- `z`: Vorwärts der **früheste** Beginn der Bedienung `t` am Knoten, rückwärts der **späteste** Beginn `T`, so dass der Rest der Route bis zum Ende des Horizonts zulässig bleibt;
- `c`: reduzierte Kosten (Entfernungen minus Dualpreise der besuchten Kunden). Rückwärts enthält `c` die Kante zum Nachfolger und den Dualpreis des Knotens selbst, vorwärts den Weg bis zum Knoten;
- `q`: Last bis zum Knoten (vorwärts) bzw. ab dem Knoten (rückwärts);
- `m`: Gedächtnis als Bitmaske der gesperrten Kunden (ng-Menge; mit dem Gedächtnis aller Kunden ist die Route elementar);
- `eltern`: Nummer des Vorgängers (vorwärts) bzw. Nachfolgers (rückwärts), -1 am Start.

**Dominanz.** Vorwärts dominiert ein Label ein anderes am selben Knoten, wenn Kosten, Beginn und Last höchstens so groß sind und sein Gedächtnis eine Teilmenge ist.
Rückwärts gilt dasselbe, nur dass der späteste Beginn `T` mindestens so groß sein muss. Gleiche Werte: das früher erzeugte Label bleibt.

**Halbweg.** Beim festen Halbweg `M` wachsen die Vorwärtslabels nur bis zum Beginn `t <= M`, die Rückwärtslabels nur bis `T >= M`. Die dynamischen Fassungen wählen die Mitte aus der
Zahl der Labels (eigene Auslegung, nicht das Verfahren von Tilk u. a.). Die **Verbindung** über die Kante (i, j) setzt ein Vorwärtslabel in i und ein Rückwärtslabel in j zusammen,
wenn Zeit, Last und Gedächtnis passen.

Gezählt werden **erzeugte Labels** (auch die sofort dominierten), bei bidirektional Vorwärts plus Rückwärts samt der beiden Starts; die Verbindungspaare werden getrennt gezählt."""

import heapq
from dataclasses import dataclass, field

import numpy as np

import bdl_constants as C
from bdl_scenario import Instanz

EPS = 1e-9
INF = float("inf")
L_Z, L_C, L_Q, L_M, L_K, L_E = range(6)       # Positionen im Label-Tupel
FEHLSCHLAG = 1e-7                              # reduzierte Kosten unter -FEHLSCHLAG gelten als negativ (eine neue Spalte)
MODI = ("fest", "dyn", "dynF", "dynB", "dynD")


# --- Gedächtnis ---------------------------------------------------------------------------------------------------------------------------------

def ng_masken(inst: Instanz, k: int | None) -> tuple:
    """Gedächtnismenge je Kunde als Bitmaske: die `k` nächsten Kunden von j einschließlich j (bei Gleichstand der kleinere Index). `k = None` oder `k >= n`: alle Kunden (elementar)."""
    n = inst.n
    if k is None or k >= n:
        return (0,) + (((1 << (n + 1)) - 2),) * n
    masken = [0] * (n + 1)
    for j in range(1, n + 1):
        nah = sorted(range(1, n + 1), key=lambda i: inst.d[j][i])[:k]
        m = 1 << j
        for i in nah:
            m |= 1 << i
        masken[j] = m
    return tuple(masken)


def menge_aus_maske(m: int) -> tuple:
    """Die Kunden einer Bitmaske, aufsteigend."""
    return tuple(i for i in range(1, m.bit_length()) if (m >> i) & 1)


# --- Dominanzregeln -----------------------------------------------------------------------------------------------------------------------------

def dominiert_vorwaerts(a: tuple, b: tuple) -> bool:
    """Das Vorwärtslabel a dominiert b (gleicher Knoten): Kosten, Beginn und Last höchstens so groß, Gedächtnis von a Teilmenge von b."""
    return a[L_C] <= b[L_C] + EPS and a[L_Z] <= b[L_Z] + EPS and a[L_Q] <= b[L_Q] and (a[L_M] & ~b[L_M]) == 0


def dominiert_rueckwaerts(a: tuple, b: tuple) -> bool:
    """Das Rückwärtslabel a dominiert b (gleicher Knoten): Kosten und Last höchstens so groß, der späteste Beginn mindestens so groß, Gedächtnis von a Teilmenge von b."""
    return a[L_C] <= b[L_C] + EPS and a[L_Z] >= b[L_Z] - EPS and a[L_Q] <= b[L_Q] and (a[L_M] & ~b[L_M]) == 0


# --- Zustand einer Richtung ------------------------------------------------------------------------------------------------------------------------

@dataclass
class Seite:
    """Alle Labels einer Richtung. `labels[nr]` ist das Label mit der Nummer `nr` (Reihenfolge der Erzeugung, auch sofort dominierte); `tot[nr]` heißt dominiert oder verdrängt,
    `dominiert_von[nr]` nennt das dominierende Label (-1: keins). `lebend[knoten]` hält die Nummern der lebenden Labels je Knoten in der Reihenfolge des Einfügens."""
    vorwaerts: bool
    labels: list = field(default_factory=list)
    tot: list = field(default_factory=list)
    dominiert_von: list = field(default_factory=list)
    lebend: list = field(default_factory=list)
    heap: list = field(default_factory=list)
    vergleiche: int = 0
    dominiert: int = 0
    abgeschnitten: int = 0     # Verlängerungen, die am Halbweg endeten (kein Label)

    @property
    def erzeugt(self) -> int:
        return len(self.labels)

    @property
    def anzahl_lebend(self) -> int:
        return sum(len(x) for x in self.lebend)


def neue_seite(inst: Instanz, vorwaerts: bool) -> Seite:
    """Eine Richtung mit ihrem Start: vorwärts das Depot bei Zeit 0, rückwärts das Depot-Ende bei Zeit H (der späteste Beginn ist hier das Ende des Horizonts)."""
    s = Seite(vorwaerts)
    start = (0.0, 0.0, 0, 0, 0, -1) if vorwaerts else (float(inst.H), 0.0, 0, 0, 0, -1)
    s.labels.append(start)
    s.tot.append(False)
    s.dominiert_von.append(-1)
    s.lebend = [[] for _ in range(inst.n + 1)]
    s.lebend[0].append(0)
    s.heap = [(schluessel(s, start), 0)]
    return s


def schluessel(seite: Seite, label: tuple) -> float:
    """Reihenfolge der Bearbeitung: vorwärts der kleinste Beginn zuerst, rückwärts der größte späteste Beginn zuerst."""
    return label[L_Z] if seite.vorwaerts else -label[L_Z]


def fuege_ein(seite: Seite, label: tuple) -> int | None:
    """Dominanzregel beim Einfügen. Wird das neue Label von einem lebenden Label am selben Knoten dominiert, ist es sofort tot (Rückgabe None, die Nummer steht trotzdem vergeben).
    Sonst verdrängt es alle lebenden Labels, die es dominiert, und kommt in die Warteschlange. Rückgabe: die Nummer des Labels oder None."""
    dom = dominiert_vorwaerts if seite.vorwaerts else dominiert_rueckwaerts
    labels = seite.labels
    nr = len(labels)
    labels.append(label)
    seite.tot.append(False)
    seite.dominiert_von.append(-1)
    lst = seite.lebend[label[L_K]]
    for oi in lst:
        seite.vergleiche += 1
        if dom(labels[oi], label):
            seite.tot[nr] = True
            seite.dominiert_von[nr] = oi
            seite.dominiert += 1
            return None
    ueberlebende = []
    for oi in lst:
        seite.vergleiche += 1
        if dom(label, labels[oi]):
            seite.tot[oi] = True
            seite.dominiert_von[oi] = nr
            seite.dominiert += 1
        else:
            ueberlebende.append(oi)
    ueberlebende.append(nr)
    seite.lebend[label[L_K]] = ueberlebende
    heapq.heappush(seite.heap, (schluessel(seite, label), nr))
    return nr


# --- Verlängerungen -----------------------------------------------------------------------------------------------------------------------------

def verlaengerungen_vorwaerts(inst: Instanz, pi, ng: tuple, label: tuple) -> list:
    """Alle zulässigen Verlängerungen eines Vorwärtslabels um einen weiteren Kunden j (j nicht im Gedächtnis, Last höchstens Q, Ankunft höchstens am Fensterende).
    Rückgabe: Liste (j, Beginn, Kosten, Last, Gedächtnis). Der Beginn ist die Ankunft oder, wenn sie früher ist, das Fensteranfang (Warten)."""
    t, c, q, mem, i = label[L_Z], label[L_C], label[L_Q], label[L_M], label[L_K]
    s = inst.svc if i != 0 else 0.0
    d_i = inst.d[i]
    aus = []
    for j in range(1, inst.n + 1):
        if j == i or (mem >> j) & 1:
            continue
        q2 = q + inst.dem[j]
        if q2 > inst.Q:
            continue
        ankunft = t + s + d_i[j]
        if ankunft > inst.due[j] + EPS:
            continue
        aus.append((j, max(ankunft, inst.ready[j]), c + d_i[j] - pi[j], q2, (mem & ng[j]) | (1 << j)))
    return aus


def verlaengerungen_rueckwaerts(inst: Instanz, pi, ng: tuple, label: tuple) -> list:
    """Alle zulässigen Verlängerungen eines Rückwärtslabels um einen Vorgänger i. Der späteste Beginn bei i ist das Fensterende oder, wenn der Nachfolger früher beginnen muss,
    sein spätester Beginn minus Bedienzeit minus Fahrzeit; liegt er vor dem Fensteranfang, ist der Vorgänger unzulässig. Rückgabe: Liste (i, T, Kosten, Last, Gedächtnis)."""
    T, c, q, mem, j = label[L_Z], label[L_C], label[L_Q], label[L_M], label[L_K]
    aus = []
    for i in range(1, inst.n + 1):
        if i == j or (mem >> i) & 1:
            continue
        q2 = q + inst.dem[i]
        if q2 > inst.Q:
            continue
        T2 = min(inst.due[i], T - inst.svc - inst.d[i][j])
        if T2 < inst.ready[i] - EPS:
            continue
        aus.append((i, T2, c + inst.d[i][j] - pi[i], q2, (mem & ng[i]) | (1 << i)))
    return aus


@dataclass
class Aufschub:
    """Zurückgestellte Verlängerungen (nur die Fassung dynD): Warteschlange je Richtung, Schlüssel wie `schluessel`."""
    heap: list = field(default_factory=list)
    folge: int = 0
    anzahl: int = 0


def erweitere(seite: Seite, inst: Instanz, pi, ng: tuple, nr: int, halbweg: float | None = None, front: float | None = None, aufschub: Aufschub | None = None) -> None:
    """Verlängert das Label `nr` einer Richtung und fügt die Ergebnisse ein.

    `halbweg`: Vorwärts kein Label mit Beginn > halbweg, rückwärts keins mit spätestem Beginn < halbweg (die andere Richtung übernimmt).
    `front`: Grenze durch die Front der Gegenrichtung (dynamische Fassungen); Verlängerungen jenseits werden mit `aufschub` zurückgestellt, sonst verworfen."""
    vorz = 1.0 if seite.vorwaerts else -1.0
    label = seite.labels[nr]
    kandidaten = (verlaengerungen_vorwaerts if seite.vorwaerts else verlaengerungen_rueckwaerts)(inst, pi, ng, label)
    grenze_h = INF if halbweg is None else vorz * halbweg
    grenze_f = INF if front is None else vorz * front
    for k, z2, c2, q2, m2 in kandidaten:
        u = vorz * z2
        if u > grenze_h + EPS:
            seite.abgeschnitten += 1
            continue
        if u > grenze_f + EPS:
            if aufschub is not None:
                aufschub.folge += 1
                aufschub.anzahl += 1
                heapq.heappush(aufschub.heap, (u, aufschub.folge, c2, q2, m2, k, nr, z2))
            continue
        fuege_ein(seite, (z2, c2, q2, m2, k, nr))


def gib_frei(seite: Seite, aufschub: Aufschub, halbweg: float) -> None:
    """Gibt die zurückgestellten Verlängerungen frei, die am Halbweg noch gebraucht werden, in der Reihenfolge ihres Schlüssels, und fügt sie ein."""
    vorz = 1.0 if seite.vorwaerts else -1.0
    while aufschub.heap and aufschub.heap[0][0] <= vorz * halbweg + EPS:
        _, _, c2, q2, m2, k, eltern, z2 = heapq.heappop(aufschub.heap)
        fuege_ein(seite, (z2, c2, q2, m2, k, eltern))


def bereinige(seite: Seite) -> None:
    """Entfernt tote Labels vom Kopf der Warteschlange."""
    while seite.heap and seite.tot[seite.heap[0][1]]:
        heapq.heappop(seite.heap)


# --- Verbindung ---------------------------------------------------------------------------------------------------------------------------------

def paar_pruefung(inst: Instanz, f: tuple, b: tuple, i: int, j: int) -> tuple:
    """Prüft ein Paar: Vorwärtslabel f in i, Rückwärtslabel b in j, verbunden durch die Kante (i, j). Rückgabe ("passt", Gesamtkosten) oder ("Zeit" | "Last" | "Gedächtnis", None)
    mit dem ersten verletzten Grund. Zeit: Beginn in i plus Bedienzeit (außer am Depot) plus Fahrzeit muss höchstens der späteste Beginn des Rückwärtslabels sein. Last: Summe höchstens Q.
    Gedächtnis: die beiden Gedächtnisse dürfen keinen gemeinsamen Kunden haben (sonst käme ein Kunde zweimal vor)."""
    s = inst.svc if i != 0 else 0.0
    if f[L_Z] + s + inst.d[i][j] > b[L_Z] + EPS:
        return "Zeit", None
    if f[L_Q] + b[L_Q] > inst.Q:
        return "Last", None
    if f[L_M] & b[L_M]:
        return "Gedächtnis", None
    return "passt", f[L_C] + inst.d[i][j] + b[L_C]


@dataclass(frozen=True)
class Verbindung:
    rc: float
    kante: tuple          # (i, j)
    vor: int              # Nummer des Vorwärtslabels
    rueck: int            # Nummer des Rückwärtslabels
    route: tuple


@dataclass(frozen=True)
class Verbunden:
    beste: tuple          # je Kante die beste Verbindung mit negativen reduzierten Kosten (Verbindung, ...)
    paare: int            # geprüfte Paare (Kanten, bei denen die Zeiten sich überhaupt treffen können)
    kanten: int           # Kanten mit Labels auf beiden Seiten, die zeitlich passen können
    paare_alle: int       # alle Paare über alle Kanten mit Labels auf beiden Seiten (ohne Vorprüfung der Zeit)
    kanten_alle: int


def route_aus_paar(vor: Seite, rueck: Seite, fi: int, bi: int) -> tuple:
    """Die Route eines Paares: die Kunden der Vorwärtskette (ohne Depot) und danach die der Rückwärtskette bis zum Depot-Ende."""
    route = []
    x = fi
    while x != -1:
        route.append(vor.labels[x][L_K])
        x = vor.labels[x][L_E]
    route = list(reversed(route))[1:]
    x = bi
    while x != -1 and rueck.labels[x][L_K] != 0:
        route.append(rueck.labels[x][L_K])
        x = rueck.labels[x][L_E]
    return tuple(route)


def _feld(seite: Seite, nrs: list) -> tuple:
    """Zeit, Kosten, Last und Gedächtnis der Labels `nrs` als Arrays (Gedächtnis als int64)."""
    ls = [seite.labels[x] for x in nrs]
    return (np.array([x[L_Z] for x in ls]), np.array([x[L_C] for x in ls]), np.array([x[L_Q] for x in ls]), np.array([x[L_M] for x in ls], dtype=np.int64))


def verbinde(inst: Instanz, vor: Seite, rueck: Seite) -> Verbunden:
    """Verbindet die lebenden Labels beider Richtungen über jede Kante (i, j): je Kante eine Matrixoperation über alle Paare (Vorwärtslabel in i, Rückwärtslabel in j).

    Eine Kante wird übersprungen, wenn schon das früheste Vorwärtslabel in i zu spät für das späteste Rückwärts-T in j kommt (Vorprüfung; gezählt werden nur geprüfte Kanten und Paare).
    Je Kante bleibt die Verbindung mit den kleinsten Gesamtkosten, falls sie negativ ist."""
    n = inst.n
    fa = [(lst, *_feld(vor, lst)) if lst else None for lst in vor.lebend]
    ba = [(lst, *_feld(rueck, lst)) if lst else None for lst in rueck.lebend]
    beste, paare, kanten, paare_alle, kanten_alle = [], 0, 0, 0, 0
    for i in range(n + 1):
        if fa[i] is None:
            continue
        fl, Ft, Fc, Fq, Fm = fa[i]
        s = inst.svc if i != 0 else 0.0
        tmin = float(Ft.min())
        for j in range(n + 1):
            if i == j or ba[j] is None:
                continue
            bl, Bt, Bc, Bq, Bm = ba[j]
            paare_alle += len(fl) * len(bl)
            kanten_alle += 1
            dij = inst.d[i][j]
            if tmin + s + dij > float(Bt.max()) + EPS:
                continue
            kanten += 1
            paare += len(fl) * len(bl)
            ok = (Ft[:, None] + (s + dij) <= Bt[None, :] + EPS)
            ok &= (Fq[:, None] + Bq[None, :] <= inst.Q)
            ok &= ((Fm[:, None] & Bm[None, :]) == 0)
            gesamt = np.where(ok, Fc[:, None] + dij + Bc[None, :], INF)
            a, b = divmod(int(gesamt.argmin()), gesamt.shape[1])
            v = float(gesamt[a, b])
            if v < -FEHLSCHLAG:
                beste.append(Verbindung(v, (i, j), fl[a], bl[b], route_aus_paar(vor, rueck, fl[a], bl[b])))
    return Verbunden(tuple(beste), paare, kanten, paare_alle, kanten_alle)


def beste_routen(verbindungen, max_routen: int) -> list:
    """Aus den Verbindungen die besten verschiedenen Routen: (rc, route), aufsteigend nach rc; dieselbe Route aus mehreren Kanten zählt mit ihrem kleinsten rc."""
    res = {}
    for v in verbindungen:
        if v.route not in res or v.rc < res[v.route]:
            res[v.route] = v.rc
    return sorted(((rc, r) for r, rc in res.items()))[:max_routen]


# --- Ergebnis -----------------------------------------------------------------------------------------------------------------------------------

@dataclass
class PricingErgebnis:
    modus: str                       # "uni", "fest", "dyn", "dynF", "dynB", "dynD"
    routen: list                     # [(reduzierte Kosten, Route)] mit negativen reduzierten Kosten, die beste zuerst (höchstens max_routen)
    erzeugt_v: int                   # erzeugte Vorwärtslabels (mit Start)
    erzeugt_r: int                   # erzeugte Rückwärtslabels (mit Start), 0 beim einseitigen Verfahren
    dominiert_v: int
    dominiert_r: int
    vergleiche_v: int
    vergleiche_r: int
    lebend_v: int
    lebend_r: int
    paare: int = 0
    kanten: int = 0
    paare_alle: int = 0
    kanten_alle: int = 0
    halbweg: float | None = None     # M (fest) bzw. M* (dynD) in Zeiteinheiten
    verschwendet_v: int = 0          # nur dynD: Vorwärtslabels mit Beginn > M*, für die beste Route nicht nötig
    verschwendet_r: int = 0          # nur dynD: Rückwärtslabels mit spätestem Beginn < M*
    zurueckgestellt: int = 0         # nur dynD
    abgeschnitten_v: int = 0
    abgeschnitten_r: int = 0
    abgebrochen: bool = False        # Label-Obergrenze erreicht: das Ergebnis ist unvollständig
    verbindungen: tuple = ()         # die besten Verbindungen je Kante
    vor: Seite | None = None
    rueck: Seite | None = None

    @property
    def labels(self) -> int:
        return self.erzeugt_v + self.erzeugt_r

    @property
    def vergleiche(self) -> int:
        return self.vergleiche_v + self.vergleiche_r

    @property
    def beste(self) -> tuple | None:
        return self.routen[0] if self.routen else None

    @property
    def beste_rc(self) -> float:
        """Beste reduzierte Kosten; 0, wenn keine Route negative reduzierte Kosten hat (dann lohnt keine neue Spalte)."""
        return self.routen[0][0] if self.routen else 0.0


def _ergebnis(modus, vor, rueck, routen, verb, halbweg, abgebrochen, behalte, **zusatz) -> PricingErgebnis:
    return PricingErgebnis(
        modus, routen, vor.erzeugt, rueck.erzeugt if rueck else 0, vor.dominiert, rueck.dominiert if rueck else 0, vor.vergleiche, rueck.vergleiche if rueck else 0,
        vor.anzahl_lebend, rueck.anzahl_lebend if rueck else 0, verb.paare if verb else 0, verb.kanten if verb else 0, verb.paare_alle if verb else 0, verb.kanten_alle if verb else 0,
        halbweg, abgeschnitten_v=vor.abgeschnitten, abgeschnitten_r=rueck.abgeschnitten if rueck else 0, abgebrochen=abgebrochen,
        verbindungen=verb.beste if verb else (), vor=vor if behalte else None, rueck=rueck if behalte else None, **zusatz)


# --- Steuerung: einseitig ---------------------------------------------------------------------------------------------------------------------

def pricing_einseitig(inst: Instanz, pi, k: int | None, max_routen: int = C.SPALTEN_JE_RUNDE, max_labels: int = C.LABEL_CAP, behalte_seiten: bool = False) -> PricingErgebnis:
    """Einseitiges Labeling nach Zeit (Label-Setting), vorwärts vom Depot, mit Dominanz. Jedes lebende Label am Kunden i, von dem aus das Depot rechtzeitig erreichbar ist, beendet eine Route.
    Rückgabe: die besten Routen mit negativen reduzierten Kosten. Überschreitet die Zahl der erzeugten Labels `max_labels`, bricht der Lauf ab (`abgebrochen`)."""
    ng = ng_masken(inst, k)
    vor = neue_seite(inst, True)
    enden = []
    abgebrochen = False
    while vor.heap:
        _, nr = heapq.heappop(vor.heap)
        if vor.tot[nr]:
            continue
        if len(vor.labels) > max_labels:
            abgebrochen = True
            break
        i = vor.labels[nr][L_K]
        if i != 0 and vor.labels[nr][L_Z] + inst.svc + inst.d[i][0] <= inst.H:
            enden.append((vor.labels[nr][L_C] + inst.d[i][0], nr))
        erweitere(vor, inst, pi, ng, nr)
    res = {}
    if not abgebrochen:
        for rc, nr in enden:
            if rc < -FEHLSCHLAG:
                route = []
                x = nr
                while x != -1:
                    route.append(vor.labels[x][L_K])
                    x = vor.labels[x][L_E]
                route = tuple(reversed(route))[1:]
                if route not in res:
                    res[route] = rc
    routen = sorted(((rc, r) for r, rc in res.items()))[:max_routen]
    return _ergebnis("uni", vor, None, routen, None, None, abgebrochen, behalte_seiten)


# --- Steuerung: bidirektional ---------------------------------------------------------------------------------------------------------------

def _hat_budget(vor: Seite, rueck: Seite, max_labels: int) -> bool:
    return vor.erzeugt + rueck.erzeugt <= max_labels


def _lauf_fest(inst, pi, ng, vor, rueck, halbweg, max_labels) -> bool:
    """Fester Halbweg: erst alle Vorwärtslabels bis Beginn <= halbweg, dann alle Rückwärtslabels bis spätester Beginn >= halbweg. Rückgabe: abgebrochen?"""
    for seite, grenze in ((vor, halbweg), (rueck, halbweg)):
        while seite.heap:
            _, nr = heapq.heappop(seite.heap)
            if seite.tot[nr]:
                continue
            if not _hat_budget(vor, rueck, max_labels):
                return True
            erweitere(seite, inst, pi, ng, nr, halbweg=grenze)
    return False


def _naechste_seite(vor: Seite, rueck: Seite) -> Seite:
    """Dynamische Fassungen: es wächst die Richtung mit den bisher weniger erzeugten Labels (bei Gleichstand vorwärts)."""
    return vor if vor.erzeugt <= rueck.erzeugt else rueck


def _fronten(vor: Seite, rueck: Seite) -> tuple:
    """Kleinster offener Beginn der Vorwärtslabels und größter offener spätester Beginn der Rückwärtslabels (INF bzw. -INF, wenn eine Seite nichts mehr offen hat)."""
    bereinige(vor)
    bereinige(rueck)
    return (vor.heap[0][0] if vor.heap else INF), (-rueck.heap[0][0] if rueck.heap else -INF)


def _lauf_dyn(inst, pi, ng, vor, rueck, kappen, max_labels) -> bool:
    """Dynamischer Halbweg ohne Zurückstellen: beide Richtungen wachsen abwechselnd (die mit weniger Labels), bis die Fronten sich kreuzen (kleinster offener Vorwärtsbeginn
    größer als der größte offene Rückwärts-T). `kappen`: None (nichts gekappt), "F" (neue Vorwärtslabels jenseits der Rückwärtsfront werden nicht erzeugt) oder
    "B" (neue Rückwärtslabels jenseits der Vorwärtsfront werden nicht erzeugt). Rückgabe: abgebrochen?"""
    front_v = front_r = None
    while True:
        tv, tr = _fronten(vor, rueck)
        if not vor.heap or not rueck.heap or tv > tr:
            return False
        if kappen == "F":
            front_v = tr
        if kappen == "B":
            front_r = tv
        if not _hat_budget(vor, rueck, max_labels):
            return True
        seite = _naechste_seite(vor, rueck)
        _, nr = heapq.heappop(seite.heap)
        erweitere(seite, inst, pi, ng, nr, front=front_v if seite.vorwaerts else front_r)


def _lauf_dyn_zurueckgestellt(inst, pi, ng, vor, rueck, max_labels) -> tuple:
    """Dynamischer Halbweg mit zurückgestellten Verlängerungen (dynD). Phase 1 wie `_lauf_dyn`, aber Verlängerungen jenseits der Front der Gegenrichtung werden nicht eingefügt
    (kein Dominanztest, kein Label), sondern zurückgestellt. Kreuzen sich die Fronten, wird M* in die Lücke gelegt, die zurückgestellten Verlängerungen mit Beginn <= M* bzw.
    T >= M* werden freigegeben, und beide Seiten wachsen bis M* zu Ende. Rückgabe: (abgebrochen, M*, Zahl der zurückgestellten Verlängerungen)."""
    auf_v, auf_r = Aufschub(), Aufschub()
    while True:
        tv, tr = _fronten(vor, rueck)
        if tv > tr:
            break
        if not _hat_budget(vor, rueck, max_labels):
            return True, None, auf_v.anzahl + auf_r.anzahl
        if vor.erzeugt <= rueck.erzeugt:
            _, nr = heapq.heappop(vor.heap)
            erweitere(vor, inst, pi, ng, nr, front=tr, aufschub=auf_v)
        else:
            _, nr = heapq.heappop(rueck.heap)
            erweitere(rueck, inst, pi, ng, nr, front=tv, aufschub=auf_r)
    if tv < INF and tr > -INF:
        mstar = (tv + tr) / 2.0
    elif tv == INF and tr > -INF:
        mstar = tr + 1e-6
    elif tr == -INF and tv < INF:
        mstar = tv - 1e-6
    else:
        mstar = inst.H / 2.0
    gib_frei(vor, auf_v, mstar)
    gib_frei(rueck, auf_r, mstar)
    while True:
        tv, tr = _fronten(vor, rueck)
        if not _hat_budget(vor, rueck, max_labels):
            return True, mstar, auf_v.anzahl + auf_r.anzahl
        if vor.heap and tv <= mstar + EPS:
            _, nr = heapq.heappop(vor.heap)
            erweitere(vor, inst, pi, ng, nr, halbweg=mstar)
        elif rueck.heap and tr >= mstar - EPS:
            _, nr = heapq.heappop(rueck.heap)
            erweitere(rueck, inst, pi, ng, nr, halbweg=mstar)
        else:
            return False, mstar, auf_v.anzahl + auf_r.anzahl


def verschwendete_labels(vor: Seite, rueck: Seite, mstar: float) -> tuple:
    """Erzeugte Labels jenseits des endgültigen Halbwegs M*: Vorwärtslabels mit Beginn > M*, Rückwärtslabels mit spätestem Beginn < M* (die beiden Starts zählen nicht).
    Für die beste Route sind sie nicht nötig; sie können zusätzliche Verbindungen liefern."""
    v = sum(1 for lab in vor.labels[1:] if lab[L_Z] > mstar + EPS)
    r = sum(1 for lab in rueck.labels[1:] if lab[L_Z] < mstar - EPS)
    return v, r


def pricing_bidirektional(inst: Instanz, pi, k: int | None, modus: str = "fest", halbweg: float | None = None, max_routen: int = C.SPALTEN_JE_RUNDE,
                          max_labels: int = C.LABEL_CAP, behalte_seiten: bool = False) -> PricingErgebnis:
    """Bidirektionales Labeling: Vorwärts- und Rückwärtslabels, in der Mitte der Zeit verbunden.

    `modus` "fest": Halbweg `halbweg` (Standard H/2). "dyn", "dynF", "dynB", "dynD": dynamische Fassungen (`_lauf_dyn`, `_lauf_dyn_zurueckgestellt`). Die Zahl `max_labels` begrenzt
    die Summe der erzeugten Vorwärts- und Rückwärtslabels; bei Überschreitung bricht der Lauf ab und das Ergebnis ist leer (`abgebrochen`)."""
    if modus not in MODI:
        raise ValueError(f"unbekannter Modus {modus!r}")
    ng = ng_masken(inst, k)
    vor, rueck = neue_seite(inst, True), neue_seite(inst, False)
    mstar, zurueck, verschwendet = None, 0, (0, 0)
    if modus == "fest":
        mstar = inst.H / 2.0 if halbweg is None else float(halbweg)
        abgebrochen = _lauf_fest(inst, pi, ng, vor, rueck, mstar, max_labels)
    elif modus == "dynD":
        abgebrochen, mstar, zurueck = _lauf_dyn_zurueckgestellt(inst, pi, ng, vor, rueck, max_labels)
        if not abgebrochen:
            verschwendet = verschwendete_labels(vor, rueck, mstar)
    else:
        abgebrochen = _lauf_dyn(inst, pi, ng, vor, rueck, {"dyn": None, "dynF": "F", "dynB": "B"}[modus], max_labels)
    verb = None if abgebrochen else verbinde(inst, vor, rueck)
    routen = [] if abgebrochen else beste_routen(verb.beste, max_routen)
    return _ergebnis(modus, vor, rueck, routen, verb, mstar, abgebrochen, behalte_seiten, verschwendet_v=verschwendet[0], verschwendet_r=verschwendet[1], zurueckgestellt=zurueck)


# --- Prüfer und Aufzählung (unabhängig vom Labeling) ----------------------------------------------------------------------------------------------

def reduzierte_kosten(inst: Instanz, pi, route) -> float:
    """Reduzierte Kosten einer Route: Entfernungen Depot - Kunden - Depot minus die Dualpreise der Kunden."""
    folge = (0,) + tuple(route) + (0,)
    return sum(inst.d[a][b] for a, b in zip(folge, folge[1:])) - sum(pi[j] for j in route)


def route_kosten(inst: Instanz, route) -> float:
    """Kosten (Entfernungen) einer Route Depot - Kunden - Depot."""
    folge = (0,) + tuple(route) + (0,)
    return sum(inst.d[a][b] for a, b in zip(folge, folge[1:]))


def pruefe_route(inst: Instanz, route, elementar: bool = True) -> tuple:
    """Unabhängiger Prüfer: fährt die Route ab und prüft Last, Fenster und Rückkehr. Rückgabe (zulässig, Text); der Text nennt bei Verletzung die erste verletzte Regel."""
    route = tuple(route)
    if not route:
        return False, "leere Route"
    if any(not (1 <= j <= inst.n) for j in route):
        return False, "Kunde außerhalb von 1 bis n"
    if elementar and len(set(route)) != len(route):
        return False, "ein Kunde kommt mehrfach vor"
    zeit, last, i = 0.0, 0, 0
    for j in route:
        ankunft = zeit + (inst.svc if i != 0 else 0.0) + inst.d[i][j]
        if inst.dem[j] + last > inst.Q:
            return False, f"unzulässig bei Kunde {j}: Last {last + inst.dem[j]} > {inst.Q}"
        if ankunft > inst.due[j] + EPS:
            return False, f"unzulässig bei Kunde {j}: Ankunft {ankunft:g} > Fensterende {inst.due[j]:g}"
        zeit, last, i = max(ankunft, inst.ready[j]), last + inst.dem[j], j
    if zeit + inst.svc + inst.d[i][0] > inst.H + EPS:
        return False, f"unzulässig: Rückkehr {zeit + inst.svc + inst.d[i][0]:g} > {inst.H:g}"
    return True, "zulässig (Last, Fenster, Rückkehr)"


def alle_zulaessigen_wege(inst: Instanz) -> list:
    """Alle zulässigen elementaren Routen (Last, Fenster, Rückkehr) durch Tiefensuche, als Kundenfolgen in der Reihenfolge der Suche. Nur für kleine n (6 Kunden: 39 Routen)."""
    wege = []

    def rec(weg, i, zeit, last, besucht):
        if weg and zeit + inst.svc + inst.d[i][0] <= inst.H + EPS:
            wege.append(tuple(weg))
        for j in range(1, inst.n + 1):
            if (besucht >> j) & 1 or last + inst.dem[j] > inst.Q:
                continue
            ankunft = zeit + (inst.svc if i != 0 else 0.0) + inst.d[i][j]
            if ankunft > inst.due[j] + EPS:
                continue
            weg.append(j)
            rec(weg, j, max(ankunft, inst.ready[j]), last + inst.dem[j], besucht | (1 << j))
            weg.pop()

    rec([], 0, 0.0, 0, 0)
    return wege
