# Bidirektionales Labeling – von beiden Enden rechnen, in der Mitte verbinden – Streamlit-Demo

Demo der Reihe „Ressourcenwege und Spaltenerzeugung“ in der „Konzepte“-Reihe der Website „Sebastian Hanisch – Operations Research und Machine Learning“. Sie zeigt, was die zweite Richtung am **Labeling** des Pricings ändert: Neben dem Vorwärtslabeling vom Depot aus (mit Zeit, Last und Dominanz, wie in den früheren Demos der Reihe) wachsen Labels vom **Ende des Zeithorizonts rückwärts**, beide Seiten nur bis zu einem **Halbweg** in der Zeit, und in der Mitte werden passende Hälften **verbunden**. Gefragt ist, wie viele Labels das spart, wo der beste Halbweg liegt, was das Verbinden kostet und warum eine einfache dynamische Wahl des Halbwegs gegenüber dem festen Halbweg H/2 hier nichts gewinnt. Als Anwendung im Pricing einer Tourenplanung mit einseitigem Labeling siehe [crew-pairing-demo](https://github.com/sebastian-hanisch/crew-pairing-demo).

Von `hub-labeling-demo` (Kürzeste-Wege-Linie, Hub-Labels für Abstandsabfragen) und von `bidirectional-demo` (bidirektionale Dijkstra-Suche ohne Ressourcen; dort geht es um den Abbruch der Suche) ist diese Demo verschieden: Hier gibt es Ressourcengrenzen (Zeit, Last), negative Längen aus Dualpreisen, Dominanz in beiden Richtungen und eine Verbindung mit getrennten Gedächtnissen. Keine Zahl der beiden Demos wird hier verwendet.

## Kernfrage

Wie viele Labels spart man, wenn man nicht nur vom Depot aus vorwärts rechnet, sondern zusätzlich vom Depot-Ende aus rückwärts, und beide Hälften in der Mitte der Zeit verbindet, und was kostet das Verbinden? Gemessen wird in **erzeugten Labels** (auch den sofort dominierten; bidirektional Vorwärts plus Rückwärts samt der beiden Starts); die **Verbindungspaare** stehen getrennt daneben. Sekunden sind nicht Ergebnis und nicht festgeschrieben.

## Befunde und Korrekturen gegenüber dem Plan

- **Neu gerechnete Messreihe mit den Instanzen dieser Demo.** Der Plan nannte Zahlen einer früheren Messreihe, deren Instanzen mit Pythons `random.Random` erzeugt wurden. Diese Demo erzeugt ihre Instanzen mit SplitMix64 (plattformunabhängig), erzeugt die Dualpreise mit einer eigenen Spaltenerzeugung und rechnet **jede Messreihe, die sie als Band zeigt, mit ihrem eigenen Kern neu**. Die Zahlen weichen deshalb ab (Tabelle „Vergleich mit der früheren Messreihe“ unten); die früheren Zahlen stehen dort nur aus der Rohdatei und sind nicht neu gerechnet.
- **Kern gegen die frühere Implementierung geprüft.** Auf den Instanzen der Vormessung (Pythons `random.Random`) und mit deren Dualpreisen liefert der Kern dieser Demo in **allen 4800 Zeilen** der früheren Messreihe dieselben erzeugten Labels, Verbindungspaare, Kanten, Dominanzvergleiche, besten Kosten und (bei der dynamischen Fassung) Halbwege und zurückgestellten Verlängerungen (Messung dieser README mit `tools/messreihe_baender.py abgleich`, nicht im Test; im Test eine Stichprobe von 120 Läufen).
- **Verbindungspaare mit Vorprüfung der Kanten.** Der Plan nannte für die Halbweg-Reihe des Handbeispiels Paarzahlen ohne Vorprüfung (72, 54, 113, 72 bei M = 10, 15, 25, 30). Der Kern (wie die Messreihe) überspringt Kanten, bei denen schon das früheste Vorwärtslabel zu spät für das späteste Rückwärts-T kommt, und zählt nur geprüfte Paare (70, 52, 97, 62). Beide Zählungen stehen in der Tabelle unten; bei M = 20 sind sie gleich (48).
- **Fünf Experimente wie im Plan**, dazu die Paartabelle mit Begründung bei jedem verworfenen Paar (Zeit, Last oder gemeinsamer Kunde) und eine Kennzeichnung des Schicksals jedes Labels (behalten, beim Erzeugen dominiert, später verdrängt).
- **Live-Rechnung nur bis zu einer Obergrenze.** Die Kundenzahl der Live-Instanz geht bis 30; ein Pricing-Lauf bricht bei 150 000 erzeugten Labels ab (die Spaltenerzeugung für die Dualpreise bei 800 000 Labels), und die App meldet dann die Größe. Die Halbweg-Kurve (11 Läufe) und die vier dynamischen Fassungen rechnet die App von selbst nur, wenn das einseitige Verfahren höchstens 40 000 Labels erzeugt; sonst auf Knopfdruck.
- **Offen aus dem Plan:** Die Messung auf langen Routen (Horizont 500) und mit 50 Kunden wurde nicht nachgeholt; die Aussagen bleiben auf 30 Kunden und kurze Routen beschränkt. Die Literatur (Righini und Salani, Tilk u. a.) wurde für den Bau nicht erneut angesehen; der Prüfstand ist unverändert „nur Abstract oder Zitat gesehen“.

## Modell

- **Handbeispiel:** Depot bei (5, 5) und 6 Kunden auf einem Gitter, Entfernung = Fahrzeit = Kosten = Manhattan-Abstand (erfüllt die Dreiecksungleichung), Bedienzeit 2, Kapazität 9, Rückkehr bis H = 40. Das Fenster eines Kunden gilt für den Beginn der Bedienung (früher ankommen heißt warten, später ankommen ist unzulässig). Die reduzierten Kosten einer Route sind die Summe ihrer Abstände (Depot, Kunden, Depot) minus die Summe der Dualpreise ihrer Kunden.

<!-- tabelle:hand_netz -->
| Kunde | Ort | Fenster [früh, spät] | Bedarf | Dualpreis π |
|---|---|---|---|---|
| 1 | (5, 0) | [22, 33] | 4 | 5 |
| 2 | (4, 7) | [5, 17] | 3 | 4,50 |
| 3 | (0, 3) | [22, 31] | 2 | 9 |
| 4 | (6, 2) | [25, 34] | 4 | 4,50 |
| 5 | (7, 1) | [9, 19] | 2 | 7,50 |
| 6 | (1, 0) | [9, 19] | 3 | 10,50 |
<!-- /tabelle -->

- **Kundeninstanzen:** selbst erzeugt im Stil der Solomon-Benchmarks (nicht die Originalinstanzen): Depot in der Mitte eines Quadrats von 100 × 100, 5 bis 30 Kunden gleichverteilt oder um fünf Zentren gruppiert, Fahrzeit gleich Entfernung gleich Kosten, Bedienzeit 10, Horizont 300, Kapazität 70 oder 120, Last 5 bis 25, Fensterbreite 40 bis 100, Zufalls-Seed als Regler.
- **Dualpreise:** aus einer Spaltenerzeugung (Überdeckungs-Master mit HiGHS, einseitiges Labeling als Pricing, die 15 besten neuen Routen je Runde) in Runde 1 (nur Einzelfahrten im Master: der Dualpreis eines Kunden ist die Hin-und-zurück-Fahrt zu ihm), Runde 3, Runde 8 oder am Ende (das Pricing findet keine Route mehr).
- **Gedächtnis:** ng-Routen mit den k nächsten Kunden (k = 1, 3, 5, 8); im Handbeispiel elementar.
- **Verfahren:** Die Formeln stehen im Expander **📐 Mathematische Formulierung** der App mit Lesehilfe und Symboltabelle.

## Methodik

- **Einseitig:** Label-Setting nach Zeit; das offene Label mit dem kleinsten Beginn wird über jeden Kunden verlängert; ein neues Label, das von einem lebenden Label desselben Kunden dominiert wird (Kosten, Beginn, Last höchstens so groß, Gedächtnis eine Teilmenge), ist sofort tot, ein neues Label, das lebende dominiert, verdrängt sie.
- **Bidirektional, fester Halbweg M:** erst alle Vorwärtslabels mit Beginn bis M, dann alle Rückwärtslabels mit spätestem Beginn ab M (der späteste Beginn ist so gewählt, dass der Rest der Route bis zum Ende des Horizonts zulässig bleibt; Dominanz mit „spätester Beginn mindestens so groß“). Verbindung über jede Kante (i, j): Vorwärtslabel in i, Rückwärtslabel in j; ein Paar passt, wenn Beginn + Bedienzeit + Fahrzeit höchstens der späteste Beginn ist, die Lasten zusammen höchstens Q sind und die Gedächtnisse keinen gemeinsamen Kunden haben (das erkennt jeden Kreis über die Naht). Je Kante bleibt die beste Verbindung mit negativen reduzierten Kosten; die Verbindung ist je Kante eine numpy-Matrixoperation.
- **Dynamischer Halbweg (eigene Auslegung, nicht das Verfahren von Tilk u. a.):** beide Richtungen wachsen abwechselnd, die mit weniger erzeugten Labels zuerst, bis der kleinste offene Vorwärtsbeginn größer ist als der größte offene Rückwärts-T. **dyn** kappt nichts, **dynF** erzeugt keine Vorwärtslabels jenseits der Rückwärtsfront, **dynB** keine Rückwärtslabels jenseits der Vorwärtsfront, **dynD** stellt solche Verlängerungen zurück, legt dann den Halbweg M* in die Lücke zwischen den Fronten, gibt die passenden zurückgestellten Verlängerungen frei und rechnet beide Seiten bis M* zu Ende.
- **Fünf Experimente in der App:** (1) das Handbeispiel Schritt für Schritt mit Zeitstrahl, Label-Tabellen, Paartabelle und Halbweg-Reihe, (2) eine Kundeninstanz live (Größe, Halbweg), (3) die Halbweg-Kurve mit der Messreihe daneben, (4) die dynamischen Fassungen, (5) die 480 Läufe der festen Messreihe als Bänder.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an festen Instanzen oder Rechnungen am Handbeispiel. Die Zahl-zu-Test-Tabelle am Ende dieses Abschnitts nennt für jede Zahl den Test.

**Handbeispiel** (6 Kunden, Halbweg M = H/2 = 20):

- Das **einseitige Verfahren** erzeugt **35 Labels** (davon 11 dominiert, 24 leben am Ende) mit 102 Dominanzvergleichen und findet die drei Routen mit negativen reduzierten Kosten: 5-6-3 mit −3, 5-6-1 mit −1 und 6-5-4 mit −0,5.
- **Bidirektional** mit M = 20 erzeugt **8 Vorwärtslabels und 8 Rückwärtslabels, zusammen 16 Labels** (16 von 35, also 0,46 der einseitigen Label-Zahl; 7 + 7 leben am Ende, 16 Dominanzvergleiche), dazu **48 Verbindungspaare** über 15 Kanten. Die beste Verbindung ist die Kante (6, 3) mit dem Vorwärtslabel F06 (Weg 5-6: Beginn 18, Kosten −5) und dem Rückwärtslabel B02 (Kunde 3: spätester Beginn 31, Kosten −2): 18 + 2 + 4 = 24 ≤ 31, Last 5 + 2 = 7 ≤ 9, getrennte Kunden, Kosten −5 + 4 − 2 = −3. Das ist die Route 5-6-3 (Abstände 6 + 7 + 4 + 7 = 24, Dualpreise 7,5 + 10,5 + 9 = 27, Differenz −3). F04 wird von F02 dominiert, B06 von B02.
- Die **Aufzählung** aller zulässigen elementaren Routen (Tiefensuche ohne Labeling) findet 39 Routen, drei davon mit negativen reduzierten Kosten, und dieselbe beste Route 5-6-3 mit −3. **Bei allen 7 Halbwegen der Reihe ist die beste Route dieselbe.**

Das Handbeispiel bei verschiedenen Halbwegen (die Summe zählt beide Starts mit; bei M = 0 und M = 40 besteht eine Seite nur aus ihrem Start, das Verfahren ist dann einseitig: 36 Labels gegen 35). Verbindungspaare und Kanten **mit Vorprüfung der Kanten** (so zählen Kern und Messreihen):

<!-- tabelle:hand_reihe -->
| Halbweg M | Vorwärtslabels | Rückwärtslabels | Summe | Verbindungspaare | Kanten | beste Route |
|---|---|---|---|---|---|---|
| 0 | 1 | 35 | 36 | 22 | 6 | 5-6-3, -3 |
| 10 | 4 | 30 | 34 | 70 | 22 | 5-6-3, -3 |
| 15 | 4 | 22 | 26 | 52 | 22 | 5-6-3, -3 |
| 20 | 8 | 8 | 16 | 48 | 15 | 5-6-3, -3 |
| 25 | 25 | 7 | 32 | 97 | 22 | 5-6-3, -3 |
| 30 | 29 | 4 | 33 | 62 | 22 | 5-6-3, -3 |
| 40 | 35 | 1 | 36 | 23 | 6 | 5-6-3, -3 |
<!-- /tabelle -->

Dieselbe Reihe **ohne Vorprüfung** (Paare und Kanten über alle Kanten mit Labels auf beiden Seiten; so zählte der Plan):

<!-- tabelle:hand_reihe_ohne -->
| Halbweg M | Vorwärtslabels | Rückwärtslabels | Summe | Verbindungspaare | Kanten | beste Route |
|---|---|---|---|---|---|---|
| 0 | 1 | 35 | 36 | 22 | 6 | 5-6-3, -3 |
| 10 | 4 | 30 | 34 | 72 | 24 | 5-6-3, -3 |
| 15 | 4 | 22 | 26 | 54 | 24 | 5-6-3, -3 |
| 20 | 8 | 8 | 16 | 48 | 15 | 5-6-3, -3 |
| 25 | 25 | 7 | 32 | 113 | 24 | 5-6-3, -3 |
| 30 | 29 | 4 | 33 | 72 | 24 | 5-6-3, -3 |
| 40 | 35 | 1 | 36 | 23 | 6 | 5-6-3, -3 |
<!-- /tabelle -->

Die Summe ist U-förmig mit dem Minimum bei M = 20 = H/2. Das gilt für dieses Beispiel mit 6 Kunden; die Messreihe unten nennt den besten festen Halbweg für 30 Kunden.

**Kundeninstanz live, die Voreinstellungen** (Live-Rechnung der App, jeweils eine Instanz an einem festen Zufalls-Seed, kein Befund über viele Instanzen; die Zeile „Handbeispiel: nur rückwärts“ ändert nur das Handbeispiel und hat dieselbe Kundeninstanz wie der Standard):

<!-- tabelle:presets -->
| Voreinstellung | Kunden | Dualpreise aus | Halbweg in % von H | Labels einseitig | Labels bidirektional | Anteil | Verbindungspaare |
|---|---|---|---|---|---|---|---|
| Standard: Handbeispiel und 15 Kunden | 15, zufällig verteilt, Breite 100, Kapazität 70, k = 5, Zufalls-Seed 7 | Runde 3 | 50 | 520 | 189 (121 + 68) | 36 % | 1 277 |
| Handbeispiel: nur rückwärts (M = 0) | 15, zufällig verteilt, Breite 100, Kapazität 70, k = 5, Zufalls-Seed 7 | Runde 3 | 50 | 520 | 189 (121 + 68) | 36 % | 1 277 |
| Halbweg zu früh (25 % von H) | 15, zufällig verteilt, Breite 100, Kapazität 70, k = 5, Zufalls-Seed 3 | Runde 3 | 25 | 748 | 889 (6 + 883) | 119 % | 1 111 |
| Gruppiert, weite Fenster, Ende der Spaltenerzeugung | 20, gruppiert (fünf Zentren), Breite 100, Kapazität 70, k = 5, Zufalls-Seed 7 | Ende | 50 | 1 887 | 1 059 (544 + 515) | 56 % | 21 848 |
| Kapazität 120, 20 Kunden, erste Runde | 20, zufällig verteilt, Breite 100, Kapazität 120, k = 5, Zufalls-Seed 5 | Runde 1 | 50 | 3 438 | 679 (359 + 320) | 20 % | 40 261 |
| Kleine Instanz (8 Kunden), Ende | 8, zufällig verteilt, Breite 100, Kapazität 70, k = 5, Zufalls-Seed 7 | Ende | 50 | 58 | 29 (11 + 18) | 50 % | 65 |
<!-- /tabelle -->

Bei dem Zufalls-Seed 3 mit dem Halbweg bei 25 % von H erzeugt bidirektional **mehr** Labels als einseitig (889 gegen 748); das ist ein Beispiel einer Instanz, kein Anteil über viele Instanzen. In der Zeile „Ende“ findet das Pricing weder einseitig noch bidirektional eine Route mit negativen reduzierten Kosten (am Ende einer Spaltenerzeugung gibt es keine); beide Verfahren bestätigen das, und gezählt werden die Labels dieser Prüfung.

**Feste Messreihe, alle 480 Läufe** (30 Kunden; Kapazität 70 mit k = 5 und k = 8, Kapazität 120 mit k = 5; zufällig und gruppiert; Fensterbreite 40 und 100; je 10 Zufalls-Seeds 0 bis 9; Dualpreise aus den Runden 1, 3, 8 und vom Ende, also 2 mal 2 mal 10 mal 3 mal 4 = 480 Läufe; je Lauf das einseitige Verfahren und neun bidirektionale Einstellungen, 4800 Zeilen). Verhältnis der erzeugten Labels zum einseitigen Lauf:

<!-- tabelle:pool -->
| Verfahren | Median | Minimum bis Maximum | Läufe mit weniger Labels als einseitig |
|---|---|---|---|
| fest H/4 | 0,70 | 0,23 bis 1,73 | 403 von 480 |
| fest 0,4 H | 0,34 | 0,12 bis 1,11 | 479 von 480 |
| fest H/2 | 0,27 | 0,11 bis 0,79 | 480 von 480 |
| fest 0,6 H | 0,37 | 0,12 bis 0,88 | 480 von 480 |
| fest 0,75 H | 0,80 | 0,35 bis 0,99 | 480 von 480 |
| dynamisch, nichts gekappt | 1,26 | 0,64 bis 1,81 | 57 von 480 |
| dynamisch, vorwärts gekappt | 0,79 | 0,40 bis 1,41 | 398 von 480 |
| dynamisch, rückwärts gekappt | 0,80 | 0,35 bis 1,43 | 398 von 480 |
| dynamisch, zurückgestellt | 0,68 | 0,29 bis 1,31 | 442 von 480 |
<!-- /tabelle -->

- **Fest H/2** erzeugt in **480 von 480** Läufen weniger Labels als das einseitige Verfahren: Median 0,27, kleinster Wert 0,11, größter 0,79. Fest H/4 (403 von 480) und fest 0,4 H (479 von 480, die Ausnahme ist ein Lauf mit Kapazität 70, gruppiert, Breite 100, k = 8, Dualpreisen der Runde 3 und dem Zufalls-Seed 5) erzeugen nicht in allen Läufen weniger. Die dynamischen Fassungen erzeugen im Median mehr Labels als fest H/2 (0,68 bis 1,26 gegen 0,27); ohne Kappen (dyn) sind es in 423 von 480 Läufen gleich viele oder mehr Labels als einseitig.
- **Wäre je Lauf im Rückblick der beste feste Halbweg gewählt worden**, läge der Median bei 0,26. Je Lauf hat fest H/2 am häufigsten die wenigsten Labels (siehe Tabelle „Welcher feste Halbweg“).
- **Das Verbinden ist nicht gratis:** Die Verbindungspaare von fest H/2 betragen im Median das 9,8-Fache der einseitigen Label-Zahl; die Dominanzvergleiche der Labels betragen im Median 20 % der Vergleiche des einseitigen Laufs. Das Verbinden ist je Kante eine Matrixoperation; ob ein Paar billiger ist als ein Label, ist nicht gemessen, und ein Gesamtaufwandsmaß ist nicht festgelegt.
- **Dynamisch ist schlechter als fest H/2:** dynD erzeugt in 0 von 480 Läufen weniger Labels als fest H/2 (gegen die ungünstigeren festen Halbwege H/4 und 0,75 H liegt dynD im Median niedriger: 0,68 gegen 0,70 und 0,80). Der Halbweg M* von dynD liegt bei den Dualpreisen vom Ende im Median bei 0,48 H (Spanne 0,29 bis 0,67 H, 120 Läufe), also in der Gegend des besten festen Halbwegs. Trotzdem liegen in diesen 120 Läufen im Median 60 % der von dynD erzeugten Labels (Spanne 40 % bis 79 %) jenseits des endgültigen M* und sind für die beste Route nicht nötig; sie können zusätzliche Verbindungen liefern (Deutung, nicht gemessen: Die Front der Gegenrichtung ist beim frühen Wachsen noch weit weg).

**Je Zelle, Dualpreise vom Ende** (10 Läufe je Zelle; fest H/2; Mittel und Maximum sind aus den Einzelwerten berechnet):

<!-- tabelle:zellen_ende -->
| Kapazität | Kunden | Fensterbreite | Gedächtnis k | Läufe | einseitige Labels (Median) | fest H/2: Median | Mittel | Maximum | weniger Labels | Paare je einseitigem Label (Median) |
|---|---|---|---|---|---|---|---|---|---|---|
| 70 | gruppiert (fünf Zentren) | 40 | 5 | 10 | 4 592 | 0,29 | 0,29 | 0,37 | 10 von 10 | 6,9 |
| 70 | gruppiert (fünf Zentren) | 40 | 8 | 10 | 5 587 | 0,24 | 0,25 | 0,30 | 10 von 10 | 7,3 |
| 70 | gruppiert (fünf Zentren) | 100 | 5 | 10 | 12 997 | 0,58 | 0,56 | 0,69 | 10 von 10 | 26,8 |
| 70 | gruppiert (fünf Zentren) | 100 | 8 | 10 | 17 120 | 0,47 | 0,47 | 0,63 | 10 von 10 | 34,5 |
| 70 | zufällig verteilt | 40 | 5 | 10 | 1 352 | 0,25 | 0,25 | 0,31 | 10 von 10 | 2,5 |
| 70 | zufällig verteilt | 40 | 8 | 10 | 1 476 | 0,25 | 0,24 | 0,32 | 10 von 10 | 2,9 |
| 70 | zufällig verteilt | 100 | 5 | 10 | 4 298 | 0,34 | 0,32 | 0,38 | 10 von 10 | 10,6 |
| 70 | zufällig verteilt | 100 | 8 | 10 | 4 778 | 0,30 | 0,29 | 0,35 | 10 von 10 | 12,4 |
| 120 | gruppiert (fünf Zentren) | 40 | 5 | 10 | 5 494 | 0,21 | 0,21 | 0,30 | 10 von 10 | 5,0 |
| 120 | gruppiert (fünf Zentren) | 100 | 5 | 10 | 27 118 | 0,32 | 0,34 | 0,49 | 10 von 10 | 20,8 |
| 120 | zufällig verteilt | 40 | 5 | 10 | 1 168 | 0,23 | 0,26 | 0,36 | 10 von 10 | 1,6 |
| 120 | zufällig verteilt | 100 | 5 | 10 | 5 166 | 0,23 | 0,25 | 0,41 | 10 von 10 | 5,2 |
<!-- /tabelle -->

Der Median von fest H/2 liegt in den zwölf Zellen zwischen 0,21 und 0,58. Der schwächste Fall ist gruppiert, Breite 100, Kapazität 70, k = 5 (0,58); mit den Dualpreisen der ersten Runde ist es dieselbe Zelle mit 0,50 (siehe Tabelle „Zellen, Dualpreise der ersten Runde“).

**Zellen, Dualpreise der ersten Runde** (derselbe Aufbau):

<!-- tabelle:zellen_1 -->
| Kapazität | Kunden | Fensterbreite | Gedächtnis k | Läufe | einseitige Labels (Median) | fest H/2: Median | Mittel | Maximum | weniger Labels | Paare je einseitigem Label (Median) |
|---|---|---|---|---|---|---|---|---|---|---|
| 70 | gruppiert (fünf Zentren) | 40 | 5 | 10 | 6 252 | 0,27 | 0,27 | 0,34 | 10 von 10 | 12,1 |
| 70 | gruppiert (fünf Zentren) | 40 | 8 | 10 | 7 632 | 0,25 | 0,24 | 0,31 | 10 von 10 | 15,6 |
| 70 | gruppiert (fünf Zentren) | 100 | 5 | 10 | 24 894 | 0,50 | 0,51 | 0,70 | 10 von 10 | 62,5 |
| 70 | gruppiert (fünf Zentren) | 100 | 8 | 10 | 32 258 | 0,45 | 0,46 | 0,68 | 10 von 10 | 80,4 |
| 70 | zufällig verteilt | 40 | 5 | 10 | 2 465 | 0,19 | 0,19 | 0,22 | 10 von 10 | 4,5 |
| 70 | zufällig verteilt | 40 | 8 | 10 | 3 054 | 0,17 | 0,16 | 0,20 | 10 von 10 | 5,3 |
| 70 | zufällig verteilt | 100 | 5 | 10 | 9 908 | 0,23 | 0,23 | 0,30 | 10 von 10 | 20,8 |
| 70 | zufällig verteilt | 100 | 8 | 10 | 12 666 | 0,20 | 0,20 | 0,25 | 10 von 10 | 26,1 |
| 120 | gruppiert (fünf Zentren) | 40 | 5 | 10 | 12 885 | 0,16 | 0,17 | 0,25 | 10 von 10 | 9,8 |
| 120 | gruppiert (fünf Zentren) | 100 | 5 | 10 | 74 612 | 0,26 | 0,29 | 0,46 | 10 von 10 | 58,2 |
| 120 | zufällig verteilt | 40 | 5 | 10 | 3 258 | 0,15 | 0,15 | 0,20 | 10 von 10 | 3,8 |
| 120 | zufällig verteilt | 100 | 5 | 10 | 17 078 | 0,14 | 0,15 | 0,21 | 10 von 10 | 13,6 |
<!-- /tabelle -->

**Nach Dualpreis-Runde** (Median von fest H/2 je 40 Läufe):

<!-- tabelle:runden -->
| Kapazität | Gedächtnis k | Runde 1 | Runde 3 | Runde 8 | Ende |
|---|---|---|---|---|---|
| 70 | 5 | 0,25 | 0,33 | 0,34 | 0,32 |
| 70 | 8 | 0,22 | 0,28 | 0,28 | 0,28 |
| 120 | 5 | 0,16 | 0,25 | 0,27 | 0,24 |
<!-- /tabelle -->

Der Vorteil ist in Runde 1 am größten und bleibt bis zum Ende bestehen.

**Nach Größe der Label-Menge** (Labels des einseitigen Laufs; Median von fest H/2):

<!-- tabelle:klassen -->
| Labels des einseitigen Laufs | Läufe | Median von fest H/2 |
|---|---|---|
| 0 bis unter 1 000 | 10 | 0,30 |
| 1 000 bis unter 5 000 | 220 | 0,25 |
| 5 000 bis unter 20 000 | 191 | 0,28 |
| 20 000 bis unter 100 000 | 55 | 0,40 |
| ab 100 000 | 4 | 0,29 |
<!-- /tabelle -->

In der gepoolten Tabelle liegt der Anteil in der Klasse von 20 000 bis unter 100 000 Labels höher als in den Klassen davor; die Klassen sind aber mit Instanztyp und Fensterbreite vermengt, die Tabelle zeigt deshalb nicht, wie sich der Anteil bei gleicher Instanzart mit der Label-Zahl ändert. Die Klasse ab 100 000 hat nur 4 Läufe. Der größte einseitige Lauf der Messreihe erzeugt 180 281 Labels, der Median aller Läufe liegt bei 5 388.

**Welcher feste Halbweg hat je Lauf die wenigsten Labels?** (bei Gleichstand der kleinere Anteil von H):

<!-- tabelle:bester_fester -->
| Kapazität | Läufe | fest H/4 | fest 0,4 H | fest H/2 | fest 0,6 H | fest 0,75 H |
|---|---|---|---|---|---|---|
| 70 | 320 | 1 (0 %) | 70 (22 %) | 199 (62 %) | 50 (16 %) | 0 (0 %) |
| 120 | 160 | 0 (0 %) | 28 (18 %) | 107 (67 %) | 25 (16 %) | 0 (0 %) |
<!-- /tabelle -->

### Vergleich mit der früheren Messreihe

Die frühere Messreihe der Planung benutzte andere Instanzen (Pythons `random.Random`) und andere Dualpreise. Ihre Zahlen stehen in `data/fruehere_messreihe.json` **aus den Rohdateien übernommen und nicht neu gerechnet**; die Spalte „diese Demo“ ist neu gerechnet.

<!-- tabelle:vergleich -->
| Verfahren | Median diese Demo | Median frühere Reihe | weniger Labels diese Demo | weniger Labels frühere Reihe |
|---|---|---|---|---|
| fest H/4 | 0,70 | 0,65 | 403 von 480 | 404 von 480 |
| fest 0,4 H | 0,34 | 0,31 | 479 von 480 | 480 von 480 |
| fest H/2 | 0,27 | 0,28 | 480 von 480 | 480 von 480 |
| fest 0,6 H | 0,37 | 0,41 | 480 von 480 | 480 von 480 |
| fest 0,75 H | 0,80 | 0,82 | 480 von 480 | 480 von 480 |
| dynamisch, nichts gekappt | 1,26 | 1,25 | 57 von 480 | 89 von 480 |
| dynamisch, vorwärts gekappt | 0,79 | 0,77 | 398 von 480 | 414 von 480 |
| dynamisch, rückwärts gekappt | 0,80 | 0,79 | 398 von 480 | 408 von 480 |
| dynamisch, zurückgestellt | 0,68 | 0,66 | 442 von 480 | 451 von 480 |
| Verbindungspaare je einseitigem Label (fest H/2, Median) | 9,8 | 8,6 | - | - |
<!-- /tabelle -->

Die Befunde stimmen in der Richtung überein (fest H/2 in allen 480 Läufen mit weniger Labels, dynamisch schlechter als fest H/2, unter den gemessenen festen Halbwegen H/2 im Median am besten); die Werte weichen ab (zum Beispiel fest 0,4 H: 479 gegen 480 von 480 Läufen, Verbindungspaare 9,8 gegen 8,6 je Label).

### Zahl → Test

| Zahl | Test |
|---|---|
| Handbeispiel: 35, 11, 24, 102; 8 + 8, 16, 48 Paare, 15 Kanten, 16 Vergleiche; Labels F00 bis F07 und B00 bis B07 (jedes aus der Definition neu berechnet), F04 und B06 dominiert; Verbindung (6, 3) mit −3; die drei negativen Routen | `tests/test_algorithm.py` (`test_hand_*`), `tests/test_claims.py::test_hand_example_sentences_follow_from_the_kernel` |
| Halbweg-Reihe (Labels, Paare mit und ohne Vorprüfung, Kanten, 36 gegen 35 an den Rändern) | `tests/test_algorithm.py::test_hand_halfway_series_counts`, `test_halfway_extremes_reduce_to_a_one_sided_labeling`; `tests/test_claims.py::test_hand_pair_counts_with_and_without_the_precheck_named_in_the_readme`; die Tabellen: `test_readme_tables_are_generated_from_the_data_and_the_kernel` |
| 39 zulässige Routen, 3 negative, beste Route 5-6-3 mit −3 bei allen Halbwegen und gegen die Tiefensuche | `tests/test_oracle_bidirektional_labeling.py::test_oracle_on_the_hand_example`, `tests/test_algorithm.py::test_hand_enumeration_has_39_routes_and_three_negative` |
| Tabelle der Voreinstellungen (Labels, Anteile, Paare), 889 gegen 748 | `tests/test_claims.py::test_readme_tables_are_generated_from_the_data_and_the_kernel`, `test_preset_sentences_follow_from_the_live_rechnung`; `tests/test_app.py::test_each_preset_runs_and_shows_its_expected_verdict` |
| Alle Tabellen der Messreihe (alle 480 Läufe, Zellen, Runden, Größen, bester fester Halbweg) | `tests/test_claims.py::test_readme_tables_are_generated_from_the_data_and_the_kernel` (aus den Einzelwerten erzeugt), `tests/test_baender.py` (Zusammenfassungen aus den Einzelwerten, Stichproben neu gerechnet) |
| 480 von 480, Median 0,27, kleinster 0,11, größter 0,79; 403 und 479 von 480; die Ausnahme von fest 0,4 H; dyn 423 von 480; bester fester Halbweg im Rückblick 0,26; 9,8-Fache Paare, 20 % Vergleiche; dynD in 0 von 480 besser als fest H/2, im Median niedriger als fest H/4 und fest 0,75 H (0,68 gegen 0,70 und 0,80); M* im Median 0,48 H (0,29 bis 0,67); 60 % (40 % bis 79 %) jenseits von M* | `tests/test_claims.py::test_measured_sentences_follow_from_the_data` |
| Zellen: Spanne 0,21 bis 0,58; schwächster Fall 0,58 (Ende) und 0,50 (Runde 1); Vorteil in Runde 1 am größten; größter einseitiger Lauf 180 281 Labels, Median 5 388; fest H/2 am häufigsten der beste feste Halbweg | `tests/test_claims.py::test_cell_and_size_sentences_follow_from_the_data` |
| Vergleich mit der früheren Messreihe (die früheren Zahlen nur aus der Datei) | `tests/test_claims.py::test_comparison_table_follows_from_the_data_and_the_named_differences`, `tests/test_baender.py::test_the_earlier_series_file_equals_the_summary_of_the_raw_files_if_they_are_there` (nur lokal, mit den Rohdateien) |
| Kern trifft die Zeilen der früheren Messreihe auf deren Instanzen (Stichprobe von 120 Läufen) | `tests/test_baender.py::test_the_kernel_hits_the_rows_of_the_earlier_series_on_the_earlier_instances` |
| Zählungen der Messreihe exakt nachgerechnet (4 Zellen, je 10 Verfahren), Dualpreise der Runde 1 und des Endes geprüft, Schranke der Spaltenerzeugung | `tests/test_baender.py` |
| Obergrenzen (150 000, 800 000, 40 000 Labels), Kundenzahl bis 30 | `tests/test_claims.py::test_limits_named_in_the_readme_are_the_constants` |
| Text der Annahmen in App und README gleich; Testzahl; keine verbotenen Wörter | `tests/test_claims.py` |
| Nicht im Test, nur Messung dieser README (Scratch-Lauf, nicht im Repo): der Abgleich aller 4800 Zeilen mit der Vormessung (0 Abweichungen) und die Orakel-Läufe unter „Tests“ | – |

## Ehrliche Grenzen

Die Grenzen stehen auch in der App im Expander „⚠️ Annahmen, Grenzen und bekannte Probleme“; der Wortlaut ist derselbe.

<!-- annahmen -->
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
<!-- /annahmen -->

- **Negativer Befund, gleichrangig:** Die einfache dynamische Wahl des Halbwegs ist in dieser Messreihe in keinem Lauf besser als der feste Halbweg H/2; ungekappt erzeugt sie im Median mehr Labels als das einseitige Verfahren. Das ist eine Aussage über diese vier Fassungen, nicht über das Verfahren von Tilk u. a.
- **Aussagen nur mit Voraussetzungen:** „weniger Labels“ gilt für 30 Kunden, Python, die eigenen Solomon-artigen Instanzen, Entfernungskosten und den festen Halbweg H/2 in dieser Messreihe; eine Aussage „bidirektional ist besser“ ohne diese Voraussetzungen macht die Demo nicht.

## Tests

- **Kern gegen die Handrechnung** (`tests/test_algorithm.py`): jede Regel (Dominanz vorwärts und rückwärts, Verlängerungen, Gedächtnis, Paarprüfung mit Begründung) an der Mini-Instanz, das Handbeispiel Label für Label, die Zählungen und die Randfälle des Halbwegs; die Verbindung als Matrixoperation gegen eine einfache Schleife.
- **Orakel** (`tests/test_oracle_bidirektional_labeling.py`): einseitiges und bidirektionales Labeling (feste Halbwege 0, H/4, H/2, 3H/4, H und die vier dynamischen Fassungen) gegen eine Tiefensuche über alle zulässigen Routen (`tests/referenz.py`, ohne Labels und Dominanz, das ng-Gedächtnis nach der Definition der Literatur), gegen das einseitige Verfahren mit gleichem Gedächtnis bei 12 Kunden, und die gelieferten Routen unabhängig nachgerechnet. Im Scratch-Lauf (nicht im Repo) 210 Instanzen mit 7 Kunden elementar und 200 Instanzen mit 5 Kunden bei k = 1 und 2, zusammen 4100 Läufe: 0 Abweichungen; der Test ist nicht trivial (in 194 von 210 Instanzen ist die beste Route negativ, in 12 von 200 ändert das kleine Gedächtnis das Optimum).
- **Eigenschaften** (`tests/test_eigenschaften_bidirektional_labeling.py`): gleiche besten Kosten bei jedem Halbweg von 0 bis H, bei anderer Nummerierung der Kunden, ohne Dualpreise keine negative Route, Skalierung von Strecken, Zeiten und Preisen, Dominanz ändert nie das Ergebnis, gleiche Zählungen in zwei Prozessen mit verschiedenem Hash-Seed.
- **Randfälle** (`tests/test_edge_cases.py`): ein und zwei Kunden, Last genau Q, ein Label genau am Halbweg, Halbweg außerhalb von 0 bis H, Kreise über die Naht bei k = 1, unerreichbare Kunden, Gleichstände, Rückkehr genau zur Zeit H.
- **Messreihen** (`tests/test_baender.py`): Raster, Quellen, Schlüssigkeit aller 4800 Zeilen, Zusammenfassungen aus den Einzelwerten, vier Zeilen neu gerechnet (je 10 Verfahren), Dualpreise und Schranken, die Gegenprobe gegen die frühere Implementierung.
- **Verdikte** (`tests/test_verdicts.py`): jede Schwelle und jede Zahl im Text an handgesetzten Werten; je Voreinstellung die erwartete Verdikt-Zeile (`tests/test_app.py`).
- **Oberfläche und Layout:** AppTest-Rauchtest (jeder Knopf, jeder Regler am Minimum und Maximum, alle Optionen, Worst-Case aller Regler am Maximum), Permalink, Footer; Schnellstart oben in der Seitenleiste, fester Kopf, aktive Voreinstellung hervorgehoben (`tests/test_layout.py`).
- **Claims** (`tests/test_claims.py`): jede Zahl dieser README, die Tabellen aus den Daten, der Text der Annahmen.

<!-- testzahl -->
Die Suite hat 147 Tests (`pytest --collect-only -q tests`).
<!-- /testzahl -->

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App (fünf Experimente, Grenzen, Formeln) |
| `bdl_algorithm.py` | Kern: Dominanzregeln, Verlängerungen, Verbindung, einseitiges und bidirektionales Labeling (fest und vier dynamische Fassungen), Prüfer, Aufzählung |
| `bdl_baender.py` | Auswertung der festen Messreihen (reine Funktionen auf den Einzelwerten) |
| `bdl_colgen.py`, `bdl_master.py` | Spaltenerzeugung und Master (HiGHS), die die Dualpreise liefern |
| `bdl_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Voreinstellungen |
| `bdl_evaluation.py` | Analysen der Live-Ansichten, Zahlenformat, Verdikte |
| `bdl_layout.py` | Fester Kopf (Stylesheet) |
| `bdl_presets.py` | Permalink (Begrenzen, Einrasten), Voreinstellungen (Schnellstart in der Seitenleiste, aktive hervorgehoben), Zufalls-Seed-Button |
| `bdl_rng.py` | SplitMix64-Zufallsgenerator (plattformunabhängig) |
| `bdl_scenario.py` | Handbeispiel und Solomon-artige Kundeninstanzen |
| `bdl_tabellen.py` | Tabellen und Verdikte der Messreihen |
| `bdl_texts.py` | Text der Annahmen (App und README gleich) |
| `bdl_visualization.py` | Plotly-Abbildungen (Achsen fest und gesperrt) |
| `data/baender_v9.json` | die feste Messreihe: 480 Läufe, je 10 Verfahren, Einzelwerte mit Quelle je Zelle, Umgebung |
| `data/duale_v9.json` | die Dualpreise der Runden 1, 3, 8 und des Endes (aus der Spaltenerzeugung mit dem Kern der Demo) |
| `data/fruehere_messreihe.json` | Zusammenfassung der früheren Messreihe aus deren Rohdateien (nicht neu gerechnet) |
| `data/vormessung_stichprobe.json` | drei Instanzen der Vormessung mit ihren Dualpreisen und den erwarteten Zeilen (für den Test) |
| `tools/messreihe_baender.py` | erzeugt die Dateien in `data/` und gleicht mit der Vormessung ab |
| `tools/readme_tabellen.py`, `tools/readme_fuellen.py` | erzeugen die Tabellen der README aus den Daten und füllen die Marken der README |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Handrechnung, Orakel, Eigenschaften, Randfälle, Messreihen, Verdikte, Claims, Voreinstellungen, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Eimer** (eine andere Maßnahme gegen die Label-Zahl) und die Kombination von bidirektional mit Eimern.
- **Mehrere Ressourcen**: Die Wahl der „Mitte“ bei Zeit und Last zugleich ist eine eigene Frage.
- **Längere Routen, 50 oder 100 Kunden:** nicht gemessen (siehe „Befunde und Korrekturen“).
- **Das Verfahren von Tilk u. a.** (dynamische Mitte): Gebaut sind nur die vier einfachen Fassungen dieser Demo.
- **Ein Gesamtaufwandsmaß** aus Labels und Verbindungspaaren und Rechenzeiten.
- **Pricing mit Heuristiken, Kantenstreichung, Branch-and-Price:** gehören nicht zu dieser Demo.

## Lokal ausführen

Die Cloud-Version von Streamlit stellt ihre Python-Version selbst ein; die CI testet mit Python 3.12.

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Das erste Laden einer Einstellung rechnet die Spaltenerzeugung und mehrere Labeling-Läufe und kann einige Sekunden dauern.

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Die Messreihen neu erzeugen (dauert einige Minuten): `python tools/messreihe_baender.py duale`, dann `mess` (die Dateien in `data/` werden überschrieben; danach die Tabellen dieser README mit `python tools/readme_fuellen.py` erneuern).

Gebaut mit Streamlit, Plotly, NumPy, pandas und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html).
