"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange) und haben feste Bereiche, damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben und Plotly nie einen leeren
Wertebereich zeichnet. Keine logarithmischen Achsen, keine Text-Spuren: Beschriftungen sind `add_annotation`-Aufrufe (mit Hintergrund), DEMO-PLAYBOOK §3."""

import plotly.graph_objects as go

import bdl_constants as C
from bdl_scenario import Instanz

HINTERGRUND = "rgba(255,255,255,0.88)"


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360, legend=True, oben=10):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=oben, b=10), plot_bgcolor="rgba(0,0,0,0)", showlegend=legend, legend=dict(orientation="h", y=-0.25))
    return lock_axes(fig)


def _zahl(x) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.1f}".replace(".", ",")


def _obergrenze(werte, spielraum: float = 1.12) -> float:
    """Obere Achsengrenze: größter Wert mal Spielraum, mindestens 1 (nie ein leerer Bereich)."""
    m = max([float(w) for w in werte] + [0.0])
    return max(1.0, m * spielraum)


def build_handnetz(inst: Instanz, pi, weg=()):
    """Das Handbeispiel als Lageplan: Depot (Raute) und Kunden mit Last, Zeitfenster und Dualpreis. Grün: die beste Route. Die Linien sind Luftlinien; gerechnet wird mit dem Manhattan-Abstand."""
    fig = go.Figure()
    if weg:
        folge = (0,) + tuple(weg) + (0,)
        fig.add_trace(go.Scatter(x=[inst.pts[i][0] for i in folge], y=[inst.pts[i][1] for i in folge], mode="lines", line=dict(color=C.COLOR_VOR, width=4), name="beste Route", hoverinfo="skip"))
    nummern = [str(i) for i in range(1, inst.n + 1)]
    fig.add_trace(go.Scatter(x=[inst.pts[i][0] for i in range(1, inst.n + 1)], y=[inst.pts[i][1] for i in range(1, inst.n + 1)], mode="markers", marker=dict(size=26, color=C.COLOR_SUMME,
                             line=dict(color="white", width=2)), showlegend=False, customdata=nummern, hovertemplate="Kunde %{customdata}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[inst.pts[0][0]], y=[inst.pts[0][1]], mode="markers", marker=dict(size=30, color="#444", symbol="diamond", line=dict(color="white", width=2)), showlegend=False,
                             hovertemplate="Depot<extra></extra>"))
    for i in range(1, inst.n + 1):
        x, y = inst.pts[i]
        fig.add_annotation(x=x, y=y, text=str(i), showarrow=False, font=dict(color="white", size=13))
        fig.add_annotation(x=x, y=y, text=f"Last {_zahl(inst.dem[i])}, π {_zahl(pi[i])}<br>[{_zahl(inst.ready[i])}, {_zahl(inst.due[i])}]", showarrow=False, yshift=-31, font=dict(size=10), bgcolor=HINTERGRUND, borderpad=1)
    fig.add_annotation(x=inst.pts[0][0], y=inst.pts[0][1], text="D", showarrow=False, font=dict(color="white", size=13))
    xs = [p[0] for p in inst.pts]
    ys = [p[1] for p in inst.pts]
    fig.update_xaxes(range=[min(xs) - 1.5, max(xs) + 1.5], showgrid=False, zeroline=False, showticklabels=False)
    fig.update_yaxes(range=[min(ys) - 1.8, max(ys) + 1.2], showgrid=False, zeroline=False, showticklabels=False)
    return _base(fig, height=420, legend=bool(weg))


def build_zeitstrahl(inst: Instanz, vor, rueck, m: float):
    """Zeitstrahl der Labels des Handbeispiels: waagerecht die Zeit, senkrecht der Knoten. Kreise: Vorwärtslabels (Beginn t), Rauten: Rückwärtslabels (spätester Beginn T); gefüllt = behalten,
    hohl = dominiert oder verdrängt. Die senkrechte Linie ist der Halbweg M. Beschriftet sind alle Labels (F00, B00 ...)."""
    fig = go.Figure()
    h = inst.H
    for seite, farbe, symbol in ((vor, C.COLOR_VOR, "circle"), (rueck, C.COLOR_RUECK, "diamond")):
        for tot in (False, True):
            nrs = [nr for nr in range(len(seite.labels)) if seite.tot[nr] == tot]
            if not nrs:
                continue
            name = ("Vorwärtslabels" if seite.vorwaerts else "Rückwärtslabels") + (" (dominiert oder verdrängt)" if tot else " (behalten)")
            fig.add_trace(go.Scatter(x=[seite.labels[nr][0] for nr in nrs], y=[seite.labels[nr][4] for nr in nrs], mode="markers", name=name,
                                     marker=dict(size=13, symbol=symbol if not tot else symbol + "-open", color=farbe, line=dict(width=2, color=farbe)),
                                     customdata=[f"{'F' if seite.vorwaerts else 'B'}{nr:02d}" for nr in nrs], hovertemplate="%{customdata}: Zeit %{x}, Knoten %{y}<extra></extra>"))
        for nr, lab in enumerate(seite.labels):
            fig.add_annotation(x=lab[0], y=lab[4], text=f"{'F' if seite.vorwaerts else 'B'}{nr:02d}", showarrow=False, yshift=15 if seite.vorwaerts else -15, font=dict(size=9, color=farbe),
                               bgcolor=HINTERGRUND, borderpad=0)
    fig.add_vline(x=m, line=dict(color=C.COLOR_BAD, width=2, dash="dash"), annotation_text="Halbweg M", annotation_position="top")
    fig.update_xaxes(range=[-2, h + 2], title="Zeit", tickmode="linear", tick0=0, dtick=10)
    fig.update_yaxes(range=[-0.7, inst.n + 0.7], tickmode="array", tickvals=list(range(inst.n + 1)), ticktext=["Depot"] + [f"Kunde {i}" for i in range(1, inst.n + 1)])
    return _base(fig, height=470, oben=34)


def build_halbweg_kurve(prozente, vor, rueck, summe, einseitig: int, marken=(), titel_x="Halbweg M in Prozent von H"):
    """Erzeugte Labels über den Halbweg: Vorwärtslabels, Rückwärtslabels und ihre Summe; die waagerechte Linie ist das einseitige Verfahren. `marken`: Liste (x, Text, Farbe) für senkrechte Marken."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(prozente), y=list(vor), mode="lines+markers", name="vorwärts", line=dict(color=C.COLOR_VOR, width=2), marker=dict(size=6)))
    fig.add_trace(go.Scatter(x=list(prozente), y=list(rueck), mode="lines+markers", name="rückwärts", line=dict(color=C.COLOR_RUECK, width=2), marker=dict(size=6)))
    fig.add_trace(go.Scatter(x=list(prozente), y=list(summe), mode="lines+markers", name="Summe", line=dict(color=C.COLOR_SUMME, width=4), marker=dict(size=9)))
    fig.add_trace(go.Scatter(x=[0, 100], y=[einseitig, einseitig], mode="lines", name="einseitig", line=dict(color=C.COLOR_EIN, width=2, dash="dash"), hoverinfo="skip"))
    for x, text, farbe in marken:
        fig.add_vline(x=x, line=dict(color=farbe, width=1, dash="dot"), annotation_text=text, annotation_position="top", annotation_font=dict(color=farbe, size=10))
    fig.update_xaxes(range=[-4, 104], title=titel_x, tickmode="linear", tick0=0, dtick=10)
    fig.update_yaxes(range=[0, _obergrenze(list(summe) + list(vor) + list(rueck) + [einseitig])], title="erzeugte Labels")
    return _base(fig, height=380, oben=34)


def build_balken(kategorien, serien, titel_y="", titel_x="", stapel=False, farben=None, ymax=None):
    """Gruppierte (oder gestapelte) Balken: `serien` = Liste (Name, Werte je Kategorie). Die y-Achse hat einen festen Bereich von 0 bis zum größten Wert (oder `ymax`)."""
    fig = go.Figure()
    farben = farben or [C.COLOR_SUMME, C.COLOR_RUECK, C.COLOR_VOR, C.COLOR_BAD]
    for idx, (name, werte) in enumerate(serien):
        fig.add_trace(go.Bar(x=[str(k) for k in kategorien], y=[float(w) for w in werte], name=name, marker_color=farben[idx % len(farben)]))
    fig.update_layout(barmode="stack" if stapel else "group")
    alle = [float(w) for _, werte in serien for w in werte]
    if stapel:
        alle = [sum(float(s[1][i]) for s in serien) for i in range(len(kategorien))]
    fig.update_xaxes(title=titel_x, type="category")
    fig.update_yaxes(title=titel_y, range=[0, ymax if ymax else _obergrenze(alle)])
    return _base(fig, height=340, legend=len(serien) > 1)


def build_verhaeltnis(kategorien, serien, titel_y="Anteil an den einseitigen Labels", titel_x=""):
    """Linien mit Marken über Kategorien: `serien` = Liste (Name, Werte, Farbe). Die waagerechte Linie bei 1 ist das einseitige Verfahren; y von 0 bis mindestens 1,2."""
    fig = go.Figure()
    for name, werte, farbe in serien:
        fig.add_trace(go.Scatter(x=[str(k) for k in kategorien], y=[float(w) for w in werte], mode="lines+markers", name=name, line=dict(color=farbe, width=3), marker=dict(size=9)))
    fig.add_hline(y=1.0, line=dict(color=C.COLOR_EIN, width=2, dash="dash"))
    alle = [float(w) for _, werte, _ in serien for w in werte]
    fig.update_xaxes(title=titel_x, type="category")
    fig.update_yaxes(title=titel_y, range=[0, max(1.2, _obergrenze(alle, 1.1))])
    return _base(fig, height=340, legend=len(serien) > 1)
