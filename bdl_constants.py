"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Voreinstellungen."""

# --- Annahmen der Kundeninstanzen (Solomon-artig, selbst erzeugt) -----------------------------------------------------------------------------
HORIZONT, KAPAZITAET, BEDIENZEIT = 300, 70, 10   # Rückkehr zum Depot bis 300, Kapazität 70, Bedienzeit 10 je Kunde
KAPAZITAETEN = (70, 120)                         # wählbare Kapazitäten (die Messreihen benutzen beide)
GRID = 100.0                                     # Kantenlänge des Quadrats
TYPEN = ("zufaellig", "gruppiert")
TYP_NAMEN = {"zufaellig": "zufällig verteilt", "gruppiert": "gruppiert (fünf Zentren)"}

# --- Handbeispiel -----------------------------------------------------------------------------------------------------------------------------
HAND_M_MIN, HAND_M_MAX, HAND_M_STEP, DEFAULT_HAND_M = 0, 40, 5, 20       # Halbweg M des Handbeispiels (Horizont 40); 20 = H/2
HAND_M_REIHE = (0, 10, 15, 20, 25, 30, 40)                               # Halbwege der Reihe im Handbeispiel

# --- Regler der Kundeninstanz -------------------------------------------------------------------------------------------------------------
# Komplexität am Regler-Maximum: Das einseitige Labeling erzeugt je Pricing-Aufruf bei n = 30, Breite 100 (gruppiert, Q = 120, Dualpreise der ersten Runde) einige 100 000 Labels
# (Messreihe mit 30 Kunden: bis zu 180 281 Labels je Lauf, Median 5 388); der Kern rechnet je nach Größe etwa 20 000 bis 150 000 Labels je Sekunde. Deshalb gilt LABEL_CAP (erzeugte Labels
# je Pricing-Lauf) und LABEL_CAP_SPALTENERZEUGUNG (Summe aller Pricing-Aufrufe, die die Dualpreise liefern); wird eine Obergrenze erreicht, meldet die App die Größe statt zu hängen.
N_MIN, N_MAX, DEFAULT_N = 5, 30, 15
BREITE_MIN, BREITE_MAX, BREITE_STEP, DEFAULT_BREITE = 40, 100, 20, 100   # Fensterbreite
K_OPTIONEN, DEFAULT_K = (1, 3, 5, 8), 5                                  # Gedächtnis (ng-Routen): Zahl der nächsten Kunden, die im Label gesperrt bleiben
RUNDEN_OPTIONEN, DEFAULT_RUNDE = (1, 3, 8, 99), 3                        # Dualpreise der Spaltenerzeugung: Runde 1, 3, 8 oder das Ende (99)
RUNDE_ENDE = 99
HALBWEG_MIN, HALBWEG_MAX, HALBWEG_STEP, DEFAULT_HALBWEG = 0, 100, 5, 50  # Halbweg in Prozent des Horizonts
SEED_MAX, DEFAULT_SEED = 999999, 7
LABEL_CAP = 150_000                                                      # Abbruch eines Pricing-Laufs nach so vielen erzeugten Labels (Schutz vor Hängern)
LABEL_CAP_SPALTENERZEUGUNG = 800_000                                   # Summe aller Pricing-Aufrufe der Spaltenerzeugung, die die Dualpreise der Runden liefert
MAX_RUNDEN = 400                                                         # Sicherung der Schleife
SPALTEN_JE_RUNDE = 15                                                    # neue Spalten je Runde (wie in den Messreihen)
HALBWEG_PUNKTE = tuple(range(0, 101, 10))                                # Halbwege der Kurve in Experiment 3 (Prozent von H)
FRAKTIONEN_FEST = (0.25, 0.4, 0.5, 0.6, 0.75)                            # feste Halbwege der Messreihe (Anteil von H)

# --- feste Messreihen -----------------------------------------------------------------------------------------------------------------------
BAND_N = 30
BAND_SEEDS = tuple(range(10))                       # Zufalls-Seeds 0 bis 9 je Zelle
BAND_BREITEN = (40, 100)
BAND_RUNDEN = (1, 3, 8, RUNDE_ENDE)
BAND_ZELLEN = ((70, 5), (70, 8), (120, 5))          # (Kapazität, Gedächtnis k)
VERFAHREN = ("uni", "fest0.25", "fest0.4", "fest0.5", "fest0.6", "fest0.75", "dyn", "dynF", "dynB", "dynD")
VERFAHREN_NAMEN = {
    "uni": "einseitig", "fest0.25": "fest H/4", "fest0.4": "fest 0,4 H", "fest0.5": "fest H/2", "fest0.6": "fest 0,6 H", "fest0.75": "fest 0,75 H",
    "dyn": "dynamisch, nichts gekappt", "dynF": "dynamisch, vorwärts gekappt", "dynB": "dynamisch, rückwärts gekappt", "dynD": "dynamisch, zurückgestellt",
}

# --- Darstellung ----------------------------------------------------------------------------------------------------------------------------
COLOR_VOR = "#2F6B65"       # Vorwärtslabels
COLOR_RUECK = "#c0732b"     # Rückwärtslabels
COLOR_SUMME = "#4c78a8"
COLOR_EIN = "#7a7a7a"       # einseitig
COLOR_BAD = "#c0392b"
COLOR_OTHER = "rgba(150,150,150,0.55)"

# --- Voreinstellungen (Schnellstart) -----------------------------------------------------------------------------------------------------
# Jede Voreinstellung nennt alle Regler: Halbweg des Handbeispiels, n, Fensterbreite, Typ, Kapazität, Gedächtnis k, Dualpreis-Runde, Halbweg in Prozent von H, Zufalls-Seed.
PRESETS = {
    "Standard: Handbeispiel und 15 Kunden": {"hand_m": 20, "n": DEFAULT_N, "breite": DEFAULT_BREITE, "typ": "zufaellig", "q": 70, "k": DEFAULT_K, "runde": DEFAULT_RUNDE, "halbweg": DEFAULT_HALBWEG, "seed": DEFAULT_SEED},
    "Handbeispiel: nur rückwärts (M = 0)": {"hand_m": 0, "n": DEFAULT_N, "breite": DEFAULT_BREITE, "typ": "zufaellig", "q": 70, "k": DEFAULT_K, "runde": DEFAULT_RUNDE, "halbweg": DEFAULT_HALBWEG, "seed": DEFAULT_SEED},
    "Halbweg zu früh (25 % von H)": {"hand_m": 20, "n": DEFAULT_N, "breite": DEFAULT_BREITE, "typ": "zufaellig", "q": 70, "k": DEFAULT_K, "runde": DEFAULT_RUNDE, "halbweg": 25, "seed": 3},
    "Gruppiert, weite Fenster, Ende der Spaltenerzeugung": {"hand_m": 20, "n": 20, "breite": 100, "typ": "gruppiert", "q": 70, "k": DEFAULT_K, "runde": RUNDE_ENDE, "halbweg": DEFAULT_HALBWEG, "seed": DEFAULT_SEED},
    "Kapazität 120, 20 Kunden, erste Runde": {"hand_m": 20, "n": 20, "breite": DEFAULT_BREITE, "typ": "zufaellig", "q": 120, "k": DEFAULT_K, "runde": 1, "halbweg": DEFAULT_HALBWEG, "seed": 5},
    "Kleine Instanz (8 Kunden), Ende": {"hand_m": 20, "n": 8, "breite": DEFAULT_BREITE, "typ": "zufaellig", "q": 70, "k": DEFAULT_K, "runde": RUNDE_ENDE, "halbweg": DEFAULT_HALBWEG, "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Standard: Handbeispiel und 15 Kunden": "Das Handbeispiel mit 6 Kunden und dem Halbweg in der Mitte der Zeit (M = 20 bei Horizont 40), dazu eine Kundeninstanz mit 15 Kunden, Fensterbreite 100, Dualpreisen der dritten Runde und dem Halbweg bei der Hälfte des Horizonts.",
    "Handbeispiel: nur rückwärts (M = 0)": "Im Handbeispiel liegt der Halbweg ganz am Anfang: Alle Labels wachsen rückwärts, die Vorwärtsseite besteht nur aus ihrem Start. Das ist wieder ein einseitiges Verfahren, nur in der Gegenrichtung.",
    "Halbweg zu früh (25 % von H)": "Eine Kundeninstanz (Zufalls-Seed 3), bei der der Halbweg bei einem Viertel des Horizonts liegt: Die Rückwärtsseite wächst fast bis zum Anfang und erzeugt mehr Labels als das einseitige Verfahren.",
    "Gruppiert, weite Fenster, Ende der Spaltenerzeugung": "Kunden in fünf Gruppen, Fensterbreite 100, Dualpreise vom Ende der Spaltenerzeugung (das Pricing findet dann keine neue Route mehr): der Fall mit dem kleinsten Vorteil in den Messreihen.",
    "Kapazität 120, 20 Kunden, erste Runde": "Mehr Kapazität und die Dualpreise der ersten Runde, in der fast jede Verlängerung lohnt: viele Labels, an denen der Halbweg viel spart.",
    "Kleine Instanz (8 Kunden), Ende": "Eine kleine Instanz mit den Dualpreisen vom Ende der Spaltenerzeugung: beide Verfahren finden keine Route mit negativen reduzierten Kosten.",
}

LIVE_KURVE_LIMIT = 40_000                                                # Experimente 3 und 4 rechnen von selbst nur, wenn das einseitige Verfahren höchstens so viele Labels erzeugt; sonst auf Knopfdruck
