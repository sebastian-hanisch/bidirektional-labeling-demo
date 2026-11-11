"""Erzeugt die festen Messreihen der Demo (data/) mit dem Kern der Demo (bdl_algorithm.py, bdl_colgen.py), nicht aus den Dateien der Vormessung.

    python tools/messreihe_baender.py duale      # Dualpreise: 120 Spaltenerzeugungen (Instanz x Gedächtnis), schreibt data/duale_v9.json
    python tools/messreihe_baender.py mess       # 480 Läufe (Instanz x Gedächtnis x Runde), je 10 Verfahren, schreibt data/baender_v9.json
    python tools/messreihe_baender.py abgleich   # Kern gegen die Vormessung (alte Instanzen, alte Dualpreise): alle 4800 Zeilen, nur Ausgabe
    python tools/messreihe_baender.py stichprobe # drei Instanzen der Vormessung (alte Dualpreise, erwartete Zeilen) als data/vormessung_stichprobe.json für den Test
    python tools/messreihe_baender.py frueher    # Zusammenfassung der Rohdateien der Vormessung (nicht neu gerechnet), schreibt data/fruehere_messreihe.json

Raster: 30 Kunden, Fensterbreite 40 und 100, zwei Instanztypen, Zufalls-Seeds 0 bis 9; Kapazität 70 mit Gedächtnis k = 5 und 8, Kapazität 120 mit k = 5; Dualpreise der Runden 1, 3, 8 und
des Endes der Spaltenerzeugung (Überdeckungs-Master, einseitiges Pricing). Die Instanzen kommen aus SplitMix64 (`bdl_scenario.instanz_aus_seed`). `abgleich` braucht die Dateien der
Vormessung (Ordner label-setting-planung/vormessung neben diesem Repo); es läuft nur lokal."""

import json
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import bdl_algorithm as A  # noqa: E402
import bdl_colgen as G  # noqa: E402
import bdl_constants as C  # noqa: E402
import bdl_scenario as S  # noqa: E402

DATA = ROOT / "data"
VORMESSUNG = ROOT.parent / "label-setting-planung" / "vormessung"
FELDER = ["labels", "gF", "gB", "liveF", "liveB", "paare", "kanten", "vergleiche", "rc", "halbweg", "verschwendet", "zurueckgestellt", "paare_alle", "kanten_alle"]
RUNDEN_NAMEN = {1: "1", 3: "3", 8: "8", C.RUNDE_ENDE: "ende"}


def umgebung() -> str:
    import numpy
    import scipy

    return f"Python {platform.python_version()}, numpy {numpy.__version__}, scipy {scipy.__version__}"


def schluessel(typ, breite, seed, k, q) -> str:
    return f"{typ}|{breite}|{seed}|{k}|{q}"


def alle_schluessel() -> list:
    return [(typ, b, seed, k, q) for q, k in C.BAND_ZELLEN for typ in C.TYPEN for b in C.BAND_BREITEN for seed in C.BAND_SEEDS]


def messe_verfahren(inst, pi, k, name, max_labels=10 ** 9) -> list:
    """Ein Lauf eines Verfahrens; Rückgabe: die Felder in der Reihenfolge von FELDER (rc auf 6 Stellen gerundet)."""
    if name == "uni":
        r = A.pricing_einseitig(inst, pi, k, max_routen=1, max_labels=max_labels)
    elif name.startswith("fest"):
        r = A.pricing_bidirektional(inst, pi, k, "fest", halbweg=float(name[4:]) * inst.H, max_routen=1, max_labels=max_labels)
    else:
        r = A.pricing_bidirektional(inst, pi, k, name, max_routen=1, max_labels=max_labels)
    if r.abgebrochen:
        raise RuntimeError(f"Abbruch bei {name}")
    return [r.labels, r.erzeugt_v, r.erzeugt_r, r.lebend_v, r.lebend_r, r.paare, r.kanten, r.vergleiche, round(r.beste_rc, 6),
            round(r.halbweg, 3) if (r.halbweg is not None and name != "uni") else 0.0, r.verschwendet_v + r.verschwendet_r, r.zurueckgestellt, r.paare_alle, r.kanten_alle]


def _job_duale(arg):
    typ, b, seed, k, q = arg
    inst = S.instanz_aus_seed(C.BAND_N, seed, b, typ, Q=q)
    t0 = time.time()
    g = G.duale_der_runden(inst, k, max_labels=10 ** 9)
    d = {RUNDEN_NAMEN.get(r, str(r)): list(pi) for r, pi in g.duale.items()}
    if g.ende is not None:
        d["ende"] = list(g.ende)
    return schluessel(*arg), {"runden": g.runden, "schranke": g.schranke, "spalten": g.spalten, "labels": g.labels, "abgebrochen": g.abgebrochen, "duale": d, "sekunden": round(time.time() - t0, 1)}


def _job_mess(arg):
    (typ, b, seed, k, q), duale = arg
    inst = S.instanz_aus_seed(C.BAND_N, seed, b, typ, Q=q)
    zeilen = {}
    for runde, pi in duale.items():
        zeilen[runde] = {name: messe_verfahren(inst, pi, k, name) for name in C.VERFAHREN}
    return (typ, b, seed, k, q), zeilen


def cmd_duale():
    DATA.mkdir(exist_ok=True)
    res = {}
    with ProcessPoolExecutor(max_workers=4) as ex:
        for key, rec in ex.map(_job_duale, alle_schluessel(), chunksize=1):
            res[key] = rec
            print(key, rec["runden"], round(rec["schranke"], 4), rec["labels"], rec["sekunden"], "s", flush=True)
    (DATA / "duale_v9.json").write_text(json.dumps({"umgebung": umgebung(), "quelle": "tools/messreihe_baender.py duale", "eintraege": res}), encoding="utf-8")


def cmd_mess():
    duale = json.loads((DATA / "duale_v9.json").read_text(encoding="utf-8"))
    auftraege = []
    for sk in alle_schluessel():
        rec = duale["eintraege"][schluessel(*sk)]
        if rec["abgebrochen"]:
            raise SystemExit(f"Spaltenerzeugung {sk} abgebrochen")
        auftraege.append((sk, rec["duale"]))
    zellen = {}
    with ProcessPoolExecutor(max_workers=4) as ex:
        for (typ, b, seed, k, q), zeilen in ex.map(_job_mess, auftraege, chunksize=1):
            for runde, verf in zeilen.items():
                zellen.setdefault((q, typ, b, k, runde), []).append({"seed": seed, "v": verf})
            print(typ, b, seed, k, q, flush=True)
    out = []
    for (q, typ, b, k, runde), laeufe in sorted(zellen.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2], kv[0][3], {"1": 1, "3": 3, "8": 8, "ende": 99}[kv[0][4]])):
        laeufe.sort(key=lambda x: x["seed"])
        out.append({"q": q, "typ": typ, "breite": b, "k": k, "runde": runde, "laeufe": laeufe,
                    "quelle": f"tools/messreihe_baender.py mess: n = 30, Kapazität {q}, {typ}, Fensterbreite {b}, Gedächtnis k = {k}, Dualpreise der Runde {runde}, Zufalls-Seeds 0 bis 9"})
    meta = {"umgebung": umgebung(), "felder": FELDER, "verfahren": list(C.VERFAHREN),
            "beschreibung": "480 Läufe (Instanz x Gedächtnis x Runde), je Lauf das einseitige Labeling und neun bidirektionale Einstellungen, mit dem Kern dieser Demo neu gerechnet. "
                            "Die Dualpreise stammen aus data/duale_v9.json (Spaltenerzeugung mit dem Kern dieser Demo).",
            "zeilen": out}
    (DATA / "baender_v9.json").write_text(json.dumps(meta), encoding="utf-8")


# --- Abgleich mit der Vormessung -----------------------------------------------------------------------------------------------------------------

def _vm_zeilen() -> dict:
    rows = {}
    for typ, q in (("zufall", 70), ("cluster", 70), ("zufall", 120), ("cluster", 120)):
        zeilen = (VORMESSUNG / f"out_v9_mess_{typ}_Q{q}.txt").read_text(encoding="utf-8").splitlines()[1:]
        for line in zeilen:
            p = line.split()
            rows[(typ, int(p[1]), int(p[2]), int(p[3]), q, p[5], p[6])] = p
    return rows


def _job_abgleich(arg):
    from alt_instanz import alte_instanz

    (typ, b, seed, k, q), duale, vm = arg
    inst = alte_instanz(30, seed, b, Q=q, gruppiert=(typ == "cluster"))
    abw = 0
    n = 0
    for runde, pi in duale.items():
        for name in C.VERFAHREN:
            got = messe_verfahren(inst, pi, k, name)
            p = vm[(typ, b, seed, k, q, runde, name)]
            exp = [int(p[7]), int(p[8]), int(p[9]), int(p[10]), int(p[11]), int(p[12]), int(p[13]), int(p[14]), float(p[15]), float(p[19]), None, int(p[20])]
            n += 1
            if [got[i] for i in (0, 1, 2, 3, 4, 5, 6, 7)] != exp[:8] or abs(got[8] - exp[8]) > 1e-5 or abs(got[9] - exp[9]) > 0.06 or got[11] != exp[11]:
                abw += 1
    return n, abw


def cmd_abgleich():
    """Der Kern der Demo auf den alten Instanzen (Pythons random.Random) mit den alten Dualpreisen gegen alle 4800 Zeilen der Vormessung."""
    vm = _vm_zeilen()
    auftraege = []
    for typ, q in (("zufall", 70), ("cluster", 70), ("zufall", 120), ("cluster", 120)):
        duale = json.loads((VORMESSUNG / f"v9_duale_{typ}_Q{q}.json").read_text(encoding="utf-8"))
        for key, rec in duale.items():
            _, b, seed, k = key.split("|")
            runden = {str(r): pi for r, pi in rec["duals"].items()}
            runden["ende"] = rec["ende"]
            auftraege.append(((typ, int(b), int(seed), int(k), q), runden, vm))
    gesamt = abw = 0
    with ProcessPoolExecutor(max_workers=4) as ex:
        for n, a in ex.map(_job_abgleich, auftraege, chunksize=1):
            gesamt += n
            abw += a
    print(f"Abgleich mit der Vormessung: {gesamt} Zeilen, {abw} Abweichungen")


def frueher_zusammenfassung() -> dict:
    """Fasst die Rohdateien der Vormessung mit denselben Funktionen zusammen wie die neue Messreihe (`bdl_baender.zusammenfassung`); die Zahlen sind nicht neu gerechnet."""
    import bdl_baender as B

    zellen = {}
    for p in _vm_zeilen().values():
        typ = "zufaellig" if p[0] == "zufall" else "gruppiert"
        feld = [int(p[7]), int(p[8]), int(p[9]), int(p[10]), int(p[11]), int(p[12]), int(p[13]), int(p[14]), float(p[15]), float(p[19]), None, int(p[20]), None, None]
        zellen.setdefault((int(p[4]), typ, int(p[1]), int(p[3]), p[5]), {}).setdefault(int(p[2]), {})[p[6]] = feld
    band = {"zeilen": [{"q": q, "typ": t, "breite": b, "k": k, "runde": r, "laeufe": [{"seed": s, "v": v} for s, v in sorted(d.items())]} for (q, t, b, k, r), d in zellen.items()]}
    z = B.zusammenfassung(band)
    z["quelle"] = ("Rohdateien out_v9_mess_*.txt der Vormessung (label-setting-planung/vormessung), mit tools/messreihe_baender.py frueher zusammengefasst; "
                   "Instanzen mit Pythons random.Random, andere Dualpreise; nicht neu gerechnet")
    return z


def cmd_frueher():
    z = frueher_zusammenfassung()
    (DATA / "fruehere_messreihe.json").write_text(json.dumps(z, indent=1), encoding="utf-8")


STICHPROBE = (("zufall", 40, 1, 5, 70), ("cluster", 40, 2, 8, 70), ("zufall", 100, 3, 5, 120))


def cmd_stichprobe():
    """Legt drei Instanzen der Vormessung samt ihren alten Dualpreisen und den erwarteten Zeilen der Rohdateien in data/ ab; `tests/test_baender.py` rechnet sie mit dem Kern nach."""
    vm = _vm_zeilen()
    aus = []
    for typ, b, seed, k, q in STICHPROBE:
        duale = json.loads((VORMESSUNG / f"v9_duale_{typ}_Q{q}.json").read_text(encoding="utf-8"))[f"{typ}|{b}|{seed}|{k}"]
        runden = {str(r): pi for r, pi in duale["duals"].items()}
        runden["ende"] = duale["ende"]
        erwartet = {}
        for runde in runden:
            erwartet[runde] = {}
            for name in C.VERFAHREN:
                p = vm[(typ, b, seed, k, q, runde, name)]
                erwartet[runde][name] = {"labels": int(p[7]), "gF": int(p[8]), "gB": int(p[9]), "liveF": int(p[10]), "liveB": int(p[11]), "paare": int(p[12]), "kanten": int(p[13]),
                                         "vergleiche": int(p[14]), "rc": float(p[15]), "halbweg": float(p[19]), "zurueckgestellt": int(p[20])}
        aus.append({"typ": typ, "breite": b, "seed": seed, "k": k, "q": q, "duale": runden, "erwartet": erwartet})
    (DATA / "vormessung_stichprobe.json").write_text(json.dumps({"quelle": "Rohdateien und Dualpreise der Vormessung (label-setting-planung/vormessung: out_v9_mess_*.txt, v9_duale_*.json), "
                                                                          "mit tools/messreihe_baender.py stichprobe ausgezogen; Instanzen mit Pythons random.Random (tests/alt_instanz.py)", "instanzen": aus}), encoding="utf-8")


if __name__ == "__main__":
    {"duale": cmd_duale, "mess": cmd_mess, "abgleich": cmd_abgleich, "frueher": cmd_frueher, "stichprobe": cmd_stichprobe}[sys.argv[1]]()
