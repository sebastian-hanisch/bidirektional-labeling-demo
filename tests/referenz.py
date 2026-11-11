"""Unabhängiger Rechenweg für die Orakel-Tests: Tiefensuche über alle zulässigen Routen, ohne Labels, ohne Dominanz, ohne Bitmasken und ohne den Kern der Demo.

Eine Route ist eine Kundenfolge. Zulässig heißt: Last höchstens Q, Beginn der Bedienung höchstens am Fensterende (früher ankommen heißt warten), Rückkehr zum Depot bis H.
Für das ng-Gedächtnis gilt die Definition aus der Literatur (ohne Gedächtnisregel des Kerns): ein Kunde darf in einer Route mehrfach vorkommen, wenn zwischen zwei Besuchen
mindestens ein Kunde liegt, dessen Nachbarschaft ihn nicht enthält. Die Nachbarschaft NG(j) besteht aus j und den k nächsten Kunden (bei Gleichstand der kleinere Index)."""

EPS = 1e-9


def nachbarschaften(inst, k):
    """NG(j) als Menge, aus den Entfernungen berechnet (k = None: alle Kunden)."""
    n = inst.n
    aus = {}
    for j in range(1, n + 1):
        if k is None or k >= n:
            aus[j] = set(range(1, n + 1))
        else:
            nah = sorted(range(1, n + 1), key=lambda i: (inst.d[j][i], i))[:k]
            aus[j] = set(nah) | {j}
    return aus


def ng_zulaessig(folge, ng):
    """Definition der ng-Route: für je zwei Besuche p < q desselben Kunden c gibt es einen Besuch r mit p < r < q, dessen Nachbarschaft c nicht enthält."""
    for q, c in enumerate(folge):
        for p in range(q):
            if folge[p] == c and not any(c not in ng[folge[r]] for r in range(p + 1, q)):
                return False
    return True


def alle_routen(inst, k=None, max_laenge=12):
    """Alle zulässigen Routen (Kundenfolgen, mindestens ein Kunde) mit ihren reduzierten Kosten unter `pi` stehen hier nicht; sie werden von `rc` berechnet."""
    ng = nachbarschaften(inst, k)
    aus = []

    def rec(folge, i, zeit, last):
        if folge and zeit + inst.svc + inst.d[i][0] <= inst.H + EPS:
            aus.append(tuple(folge))
        if len(folge) >= max_laenge:
            return
        for j in range(1, inst.n + 1):
            if last + inst.dem[j] > inst.Q:
                continue
            ankunft = zeit + (inst.svc if i != 0 else 0) + inst.d[i][j]
            if ankunft > inst.due[j] + EPS:
                continue
            folge.append(j)
            if ng_zulaessig(folge, ng):
                rec(folge, j, max(ankunft, inst.ready[j]), last + inst.dem[j])
            folge.pop()

    rec([], 0, 0.0, 0)
    return aus


def rc(inst, pi, route):
    """Reduzierte Kosten einer Route: Wegstrecke Depot - Kunden - Depot minus Dualpreise."""
    folge = [0] + list(route) + [0]
    return sum(inst.d[a][b] for a, b in zip(folge, folge[1:])) - sum(pi[j] for j in route)


def beste(inst, pi, k=None):
    """(beste reduzierte Kosten, alle Routen mit diesen Kosten); 0 und leere Menge, wenn keine Route negative reduzierte Kosten hat."""
    wege = alle_routen(inst, k)
    werte = [(rc(inst, pi, w), w) for w in wege]
    kleinster = min((x for x, _ in werte), default=0.0)
    if kleinster >= -1e-7:
        return 0.0, set()
    return kleinster, {w for x, w in werte if abs(x - kleinster) < 1e-7}


def negative(inst, pi, k=None):
    """Alle zulässigen Routen mit negativen reduzierten Kosten (Menge)."""
    return {w for w in alle_routen(inst, k) if rc(inst, pi, w) < -1e-7}
