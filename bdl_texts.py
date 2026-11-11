"""Längere Texte der App an einer Stelle: App und README zeigen denselben Wortlaut (`tests/test_claims.py` sucht den Text der App in der README)."""

ASSUMPTIONS_MARKDOWN = """\
**Annahmen**

- **Handbeispiel:** Depot bei (5, 5) und 6 Kunden auf einem Gitter; Entfernung, Fahrzeit und Kosten sind der Manhattan-Abstand, Bedienzeit 2, Kapazität 9, Rückkehr bis 40; die Dualpreise sind halbzahlig vorgegeben. Das Fenster eines Kunden gilt für den Beginn der Bedienung (früher ankommen heißt warten, später ankommen ist unzulässig).
- **Kundeninstanzen:** selbst erzeugt im Stil der Solomon-Benchmarks (nicht die Originalinstanzen), 5 bis 30 Kunden gleichverteilt im Quadrat 100 × 100 oder gruppiert um fünf Zentren, Fahrzeit gleich Entfernung gleich Kosten, Bedienzeit 10, Horizont 300, Kapazität 70 oder 120, Last 5 bis 25 je Kunde, Fensterbreite 40 bis 100.
- **Dualpreise:** aus einer Spaltenerzeugung mit Überdeckungs-Master (HiGHS über scipy) und einseitigem Labeling als Pricing; Runde 1 (nur Einzelfahrten im Master), Runde 3, Runde 8 oder das Ende (das Pricing findet keine Route mehr). Beide Verfahren rechnen mit denselben Preisen.
- **Gedächtnis:** ng-Routen mit den k nächsten Kunden (k = 1, 3, 5, 8); Kreise sind damit nicht ganz ausgeschlossen. Das Handbeispiel ist elementar (jeder Kunde höchstens einmal).
- **Messgröße:** erzeugte Labels, auch die sofort dominierten; bidirektional Vorwärts plus Rückwärts samt der beiden Starts. Verbindungspaare werden getrennt gezählt. Sekunden stehen nirgends als Ergebnis und sind nicht festgeschrieben.

**Grenzen**

- Die Messreihen haben 30 Kunden, Horizont 300 und Bedienzeit 10 (kurze Routen); längere Routen, 50 oder 100 Kunden und Label-Mengen von einigen hunderttausend Labels sind nicht gemessen.
- Je Zelle der Messreihen stehen 10 Zufalls-Seeds; Kapazität 70 und 120 benutzen dieselben Zufalls-Seeds und sind nicht unabhängig.
- Die dynamischen Fassungen sind die einfache Auslegung dieser Demo (gleich viele Labels je Seite als Regel), nicht das Verfahren von Tilk u. a.; die Aussage „dynamisch ist schlechter als fest H/2“ gilt für diese vier Fassungen und diese Messreihe.
- Ein Gesamtaufwandsmaß aus Labels und Verbindungspaaren ist nicht festgelegt. Das Verbinden ist eine Matrixoperation je Kante; ob ein Paar billiger ist als ein Label, ist nicht gemessen.
- Bidirektionales Labeling zusammen mit Eimern oder mit mehreren Ressourcen (die Wahl der „Mitte“ bei mehreren Größen) ist nicht gemessen.
- Keine Aussage über öffentliche Benchmarks, andere Programmiersprachen, andere LP-Löser oder andere Rechner.

**Bekannte Probleme und Unsicherheiten**

- Die Dualpreise späterer Runden hängen vom LP-Löser ab: Der Master hat oft mehrere gleich gute Dualpreise (Entartung), und HiGHS wählt je nach Version eine davon. Die Messreihe nutzt die in `data/duale_v9.json` gespeicherten Dualpreise; auf diesen sind die Zählungen reproduzierbar, eine neue Spaltenerzeugung kann andere Preise liefern.
- Die Dualpreise der Runde 1 sind die der Einzelfahrten (extrem groß); am Ende der Spaltenerzeugung findet das Pricing keine negative Route, dort sind gleiche Kosten beider Verfahren ein schwacher Test (die Runden 1, 3 und 8 prüfen echte Optima).
- Bei kleinen Instanzen endet die Spaltenerzeugung vor der gewählten Runde; dann gelten die Dualpreise ihres Endes, und die App sagt es.
- Das erste Laden einer Einstellung rechnet die Spaltenerzeugung und mehrere Labeling-Läufe und kann einige Sekunden dauern; große Einstellungen stoßen an eine Obergrenze an Labels, und die App meldet dann die Größe statt zu hängen.
- Die Ansichten wurden mit Streamlits Testwerkzeug und im Browser geprüft (Fenster 1400 und 375 Pixel breit): Die Seite lädt, alle sechs Voreinstellungen laufen ohne Fehlermeldung und ohne Konsolenfehler, auf dem Telefon gibt es kein seitliches Scrollen. Beim allerersten Laden in einem noch nicht dargestellten Browser-Fenster meldete die Konsole achtmal einen Plotly-Fehler („attribute y: Expected length“), die Diagramme waren dort nur 16 Pixel breit gezeichnet; in vier danach frisch geöffneten Fenstern mit richtiger Größe trat er nicht auf. Nicht jede Ansicht wurde als Bild durchgesehen, und die Diagramme sind nicht anklickbar (kein Mausklick auf ein Diagramm getestet).
"""
