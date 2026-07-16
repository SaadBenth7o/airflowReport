import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from utils.data_loader import STATE_COLORS, CIH_ORANGE, CIH_BLUE, CIH_BG, CIH_TEXT, CIH_BORDER

# Fond blanc plutot que transparent : les cartes ont deja un fond blanc a
# l'ecran (aucun changement visuel), mais un PNG exporte avec un fond
# transparent s'affiche noir/damier dans la plupart des visionneuses —
# le blanc explicite reste correct dans tous les cas.
_LAYOUT = dict(
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    font=dict(family="Inter, sans-serif", color=CIH_TEXT, size=13),
    margin=dict(l=10, r=10, t=20, b=10),
    hoverlabel=dict(bgcolor="white", bordercolor=CIH_BORDER, font_size=13),
)

_BAR_RADIUS = 7

STATE_ORDER = ["success", "failed", "skipped", "upstream_failed", "running", "never_run", "unknown"]
STATE_LABELS_FR = {
    "success": "Succès", "failed": "Échec", "skipped": "Ignorée",
    "upstream_failed": "Échec amont", "running": "En cours",
    "never_run": "Jamais exécutée", "unknown": "Inconnu",
}
# Libelle FR -> couleur, pour les graphiques dont la legende affiche l'etat.
STATE_FR_COLORS = {STATE_LABELS_FR[k]: STATE_COLORS[k] for k in STATE_LABELS_FR}

# Palette qualitative pour les tuiles TACHES du treemap drill-down :
# teintes franches et bien separees, lisibles meme sur de tres petites
# tuiles (texte blanc). Attribuees en rotation au sein de chaque DAG.
TASK_PALETTE = [
    "#05AEEF",  # bleu CIH
    "#F0481C",  # orange CIH
    "#8B5CF6",  # violet
    "#22C55E",  # vert
    "#EC4899",  # rose
    "#F59E0B",  # ambre
    "#14B8A6",  # sarcelle
    "#6366F1",  # indigo
    "#A16207",  # brun
    "#0284C7",  # bleu fonce
]


def _apply(fig, height=360):
    fig.update_layout(**_LAYOUT, height=height)
    return fig


def _round_bars(fig, radius=_BAR_RADIUS):
    try:
        fig.update_traces(marker_cornerradius=radius, selector=dict(type="bar"))
    except Exception:
        pass
    return fig


def _donut(labels, values, colors, center_top, center_bottom, height=260, hole=0.68):
    """Donut sans texte sur les tranches ni legende native — total au centre.
    La legende (couleur + libelle + valeur + %) est rendue a part via
    utils.theme.donut_legend, a cote du graphique."""
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=hole,
        marker=dict(colors=colors, line=dict(color="white", width=3)),
        textinfo="none",
        hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>",
        sort=False,
        showlegend=False,
    ))
    fig.add_annotation(
        text=f"<b style='font-size:26px'>{center_top}</b><br>"
             f"<span style='font-size:11.5px;color:{CIH_TEXT}99'>{center_bottom}</span>",
        x=0.5, y=0.5, showarrow=False, font=dict(size=26, color=CIH_TEXT),
    )
    layout = {**_LAYOUT, "margin": dict(l=10, r=10, t=10, b=10)}
    # meta="cih-donut-export" : marqueur consomme par utils.theme.plotly_export_js
    # (ajoute une legende native uniquement au moment du telechargement PNG,
    # sans dupliquer la legende HTML CIH affichee a l'ecran).
    fig.update_layout(**layout, height=height, showlegend=False, meta="cih-donut-export")
    return fig


# ---------- Overview ----------

def state_distribution_segments(df):
    """Segments (label, couleur, valeur) pour la legende du donut d'etats."""
    counts = df["Task_State"].value_counts()
    return [
        {"label": STATE_LABELS_FR[s], "color": STATE_COLORS[s], "value": int(counts.get(s, 0))}
        for s in STATE_ORDER
    ]


def state_donut(df, height=260):
    segs = [s for s in state_distribution_segments(df) if s["value"] > 0]
    total = sum(s["value"] for s in segs)
    return _donut(
        labels=[s["label"] for s in segs],
        values=[s["value"] for s in segs],
        colors=[s["color"] for s in segs],
        center_top=total, center_bottom="tâches", height=height,
    )


def dag_failures_bar(dag_summary, top_n=10):
    df = dag_summary[dag_summary["failed"] > 0].nlargest(top_n, "failed").copy()
    df["DAG_Short"] = df["DAG_ID"].apply(lambda x: x if len(x) <= 30 else x[:28] + "…")

    fig = px.bar(
        df, x="failed", y="DAG_Short", orientation="h",
        color="failed",
        color_continuous_scale=[[0, "#FBBF24"], [0.5, "#F97316"], [1, "#EF4444"]],
        hover_data={"DAG_ID": True, "failed": True, "Success_Rate": True},
        labels={"failed": "Tâches en échec", "DAG_Short": ""},
    )
    fig.update_coloraxes(showscale=False)
    fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>%{x} échec(s)<br>Taux de succès : %{customdata[2]:.1f}%<extra></extra>")
    # Le DAG le plus en echec (1ere ligne, deja triee par nlargest) doit
    # apparaitre EN HAUT du graphique — sans ce reversed, Plotly place les
    # barres horizontales de bas en haut par defaut (ordre inverse).
    fig.update_yaxes(autorange="reversed")
    return _round_bars(_apply(fig, 340))


# ---------- Failures ----------

def failures_timeline(df):
    """Un point = un run (DAG + horodatage + etat), PAS une tache : quand
    plusieurs taches du meme DAG echouent au meme run, leurs points se
    superposaient et le survol ne montrait qu'un Task_ID arbitraire —
    trompeur. Le tooltip donne desormais le nombre de taches concernees
    (le DAG, lui, se lit deja sur l'axe Y)."""
    target = df[df["Task_State"].isin(["failed", "upstream_failed"])].dropna(subset=["Task_Last_Run_Date"]).copy()
    target["Label"] = target["Task_State"].map({"failed": "Échec", "upstream_failed": "Échec amont"})

    grouped = (
        target.groupby(["DAG_ID", "Task_Last_Run_Date", "Label"])
        .size()
        .reset_index(name="Nb")
    )

    n_dags = grouped["DAG_ID"].nunique()
    fig = px.scatter(
        grouped,
        x="Task_Last_Run_Date", y="DAG_ID",
        color="Label",
        color_discrete_map=STATE_FR_COLORS,
        symbol="Label",
        size="Nb", size_max=22,
        custom_data=["Nb", "Label"],
        labels={"Task_Last_Run_Date": "Date du dernier run", "DAG_ID": "", "Label": "État"},
    )
    fig.update_traces(
        hovertemplate="%{x|%d/%m/%Y %H:%M}<br>"
                      "<b>%{customdata[0]} tâche(s)</b> · %{customdata[1]}<extra></extra>",
        marker=dict(sizemin=9),
    )
    fig.update_layout(**_LAYOUT, height=max(320, n_dags * 38 + 60),
                      legend=dict(title="État", orientation="v"))
    return fig


# ---------- DAG Explorer ----------

def dag_task_composition(df, dag_id, height=260):
    dag_df = df[df["DAG_ID"] == dag_id]
    counts = dag_df["State_FR"].value_counts().reset_index()
    counts.columns = ["État", "Nombre"]

    fig = px.bar(
        counts, x="État", y="Nombre",
        color="État", color_discrete_map=STATE_FR_COLORS,
        labels={"État": "", "Nombre": "Nb tâches"},
    )
    fig.update_layout(**_LAYOUT, height=height, showlegend=False)
    return _round_bars(fig)


def success_rate_gauge(rate, height=230):
    color = "#22C55E" if rate >= 80 else CIH_ORANGE if rate >= 50 else "#EF4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=rate,
        number={"suffix": "%", "font": {"size": 32, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": CIH_TEXT},
            "bar": {"color": color},
            "bgcolor": "white",
            "shape": "angular",
            "steps": [
                {"range": [0, 50],  "color": "#FEE2E2"},
                {"range": [50, 80], "color": "#FEF3C7"},
                {"range": [80, 100],"color": "#DCFCE7"},
            ],
        },
        title={"text": "Taux de succès", "font": {"size": 13}},
    ))
    fig.update_layout(**_LAYOUT, height=height)
    return fig


# ---------- Data Volume ----------

def tasks_treemap(df, top_n=20):
    """Top des taches par volume, en surfaces proportionnelles (meme
    lecture que la repartition par DAG) — degrade rouge du template.
    go.Treemap plutot que px.treemap : Task_ID n'est pas unique entre
    DAGs, il faut des ids DAG/tache pour ne pas fusionner les homonymes.

    Treemap plat : le zoom au clic n'apporte rien (une tuile qui remplit
    l'ecran). layout.meta le marque pour le script de la page Volume qui
    supprime ce zoom (retour false sur plotly_treemapclick)."""
    src = df[df["Rows_Affected_Total"] > 0].nlargest(top_n, "Rows_Affected_Total").copy()
    fig = go.Figure(go.Treemap(
        ids=src["DAG_ID"] + " / " + src["Task_ID"],
        labels=src["Task_ID"],
        parents=[""] * len(src),
        values=src["Rows_Affected_Total"],
        customdata=src[["DAG_ID"]],
        marker=dict(
            colors=src["Rows_Affected_Total"],
            colorscale=[[0, "#FEE2E2"], [1, "#EF4444"]],
            cornerradius=6,
            line=dict(color="white", width=2),
        ),
        tiling=dict(pad=0),
        textinfo="label",
        textposition="middle center",
        hovertemplate="<b>%{label}</b><br>DAG : %{customdata[0]}<br>%{value:,} lignes<extra></extra>",
    ))
    fig.update_layout(meta="cih-treemap-static")
    return _apply(fig, 380)


def rows_treemap(df, top_n=None):
    """Repartition du volume par DAG, avec drill-down : la vue initiale
    montre les DAGs en tuiles proportionnelles ; un clic sur un DAG zoome
    et revele ses TACHES, elles aussi proportionnelles ; un clic sur le
    bandeau superieur (pathbar) revient a la vue DAGs.

    Construit en go.Treemap a deux niveaux (DAG -> taches) : px.treemap
    colorerait les parents par moyenne ponderee, alors qu'on veut garder
    'plus fonce = plus de volume' pour les DAGs (leur total). Les TACHES,
    elles, recoivent des couleurs franches qui alternent : un degrade
    bleu unique rendait les petites tuiles indistinctes les unes des
    autres au niveau drill-down."""
    src = df[df["Rows_Affected_Total"] > 0].copy()
    dag_totals = src.groupby("DAG_ID")["Rows_Affected_Total"].sum().sort_values(ascending=False)
    if top_n:
        dag_totals = dag_totals.head(top_n)
        src = src[src["DAG_ID"].isin(dag_totals.index)]
    # Au sein d'un DAG, les grosses taches d'abord : les tuiles voisines
    # prennent ainsi des couleurs successives de la palette.
    src = src.sort_values(["DAG_ID", "Rows_Affected_Total"], ascending=[True, False])

    # Racine EXPLICITE : sans elle, la racine implicite n'a ni libelle ni
    # valeur — le pathbar (bandeau de retour) s'affiche gris fonce #444 et
    # son survol montre le hovertemplate brut ("%{label}...") faute de
    # donnees a interpoler.
    ROOT = "__root__"
    ids     = [ROOT] + list(dag_totals.index) + (src["DAG_ID"] + "/" + src["Task_ID"]).tolist()
    labels  = ["Tous les DAGs"] + list(dag_totals.index) + src["Task_ID"].tolist()
    parents = [""] + [ROOT] * len(dag_totals) + src["DAG_ID"].tolist()
    values  = [int(dag_totals.sum())] + [int(v) for v in dag_totals.values] + src["Rows_Affected_Total"].tolist()

    # Couleurs explicites (chaines hex) plutot que colorscale numerique,
    # pour melanger deux logiques :
    #  - DAGs : degrade bleu 'plus fonce = plus de volume' (vue initiale) ;
    #  - taches : palette qualitative en rotation dans chaque DAG, afin que
    #    chaque tuile se distingue de ses voisines meme minuscule.
    def _blend(t):
        lo, hi = (0xE0, 0xF2, 0xFE), (0x05, 0xAE, 0xEF)
        return "#%02X%02X%02X" % tuple(round(lo[i] + (hi[i] - lo[i]) * t) for i in range(3))

    vmax = float(dag_totals.max()) or 1.0
    dag_colors = [_blend(v / vmax) for v in dag_totals.values]
    task_rank = src.groupby("DAG_ID").cumcount()
    task_colors = [TASK_PALETTE[i % len(TASK_PALETTE)] for i in task_rank]
    colors = ["#FFFFFF"] + dag_colors + task_colors

    fig = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values,
        branchvalues="total",
        # Niveau d'entree = la racine explicite (sinon la vue initiale
        # n'est que la tuile racine elle-meme) ; maxdepth=2 = le niveau
        # courant + ses enfants directs — la vue initiale ne montre que
        # les DAGs, la subdivision en taches n'apparait qu'apres le clic
        # sur un DAG (le niveau courant devient alors ce DAG).
        level=ROOT,
        maxdepth=2,
        marker=dict(
            colors=colors,
            cornerradius=6,
            line=dict(color="white", width=2),
        ),
        tiling=dict(pad=0),
        pathbar=dict(thickness=26),
        textinfo="label",
        textposition="middle center",
        hovertemplate="<b>%{label}</b><br>%{value:,} lignes<extra></extra>",
    ))
    # Marqueur pour le script de la page Volume : au niveau taches, un
    # clic sur une tache RAMENE a la vue de tous les DAGs (au lieu de
    # zoomer sur la tache, sans interet).
    fig.update_layout(meta="cih-treemap-drill")
    # Hauteur augmentee (380 -> 480) : la carte occupe desormais toute la
    # largeur de la page (le treemap des taches a ete retire a cote), plus
    # de hauteur donne plus de place aux tuiles les plus petites.
    return _apply(fig, 480)


# ---------- Performance ----------

# Classes de duree (echelle "par classe") : bornes en minutes, libelles FR.
DURATION_CLASSES = [
    (0,      1,            "< 1 min"),
    (1,      5,            "1 – 5 min"),
    (5,      15,           "5 – 15 min"),
    (15,     30,           "15 – 30 min"),
    (30,     60,           "30 – 60 min"),
    (60,     240,          "1 – 4 h"),
    (240,    1440,         "4 – 24 h"),
    (1440,   float("inf"), "> 24 h"),
]


def duration_histogram(df, scale="log"):
    """Distribution des durees des taches reussies, selon 3 echelles :
      - "log"     : binning en log10 — les durees s'etalent de quelques
                    secondes a des milliers d'heures, en lineaire tout
                    s'ecrase dans le premier bin ;
      - "linear"  : echelle standard (minutes brutes) — utile pour voir
                    a quel point les extremes dominent ;
      - "classes" : effectifs par classe de duree (< 1 min, 1-5 min...),
                    lecture immediate sans notion d'echelle.
    """
    src = df[(df["Duration_Minutes"] > 0) & (df["Task_State"] == "success")].copy()

    if scale == "classes":
        edges  = [c[0] for c in DURATION_CLASSES] + [float("inf")]
        labels = [c[2] for c in DURATION_CLASSES]
        src["Classe"] = pd.cut(src["Duration_Minutes"], bins=edges, labels=labels, right=False)
        counts = src["Classe"].value_counts().reindex(labels, fill_value=0).reset_index()
        counts.columns = ["Classe", "Nb"]
        fig = px.bar(
            counts, x="Classe", y="Nb",
            color_discrete_sequence=[CIH_ORANGE],
            labels={"Classe": "Classe de durée", "Nb": "Nb tâches"},
        )
        fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y} tâche(s)<extra></extra>")
        fig.update_layout(**_LAYOUT, height=320,
                          bargap=0.25,
                          xaxis=dict(gridcolor=CIH_BORDER),
                          yaxis=dict(gridcolor=CIH_BORDER))
        return _round_bars(fig, radius=4)

    if scale == "linear":
        fig = px.histogram(
            src, x="Duration_Minutes", nbins=60,
            color_discrete_sequence=[CIH_ORANGE],
            labels={"Duration_Minutes": "Durée (minutes)"},
        )
        fig.update_traces(hovertemplate="%{y} tâche(s)<extra></extra>")
    else:
        src["Log_Minutes"] = np.log10(src["Duration_Minutes"])
        fig = px.histogram(
            src, x="Log_Minutes", nbins=40,
            color_discrete_sequence=[CIH_ORANGE],
            labels={"Log_Minutes": "Durée (minutes, échelle log)"},
        )
        ticks = list(range(-2, 6))
        fig.update_xaxes(
            tickvals=ticks,
            ticktext=["0,01", "0,1", "1", "10", "100", "1 000", "10 000", "100 000"],
        )
        fig.update_traces(hovertemplate="%{y} tâche(s)<extra></extra>")

    # px.histogram nomme l'axe Y "count" quoi qu'on mette dans labels.
    fig.update_yaxes(title_text="Nb tâches")
    fig.update_layout(**_LAYOUT, height=320,
                      bargap=0.12,
                      xaxis=dict(gridcolor=CIH_BORDER),
                      yaxis=dict(gridcolor=CIH_BORDER))
    return _round_bars(fig, radius=4)


def slowest_tasks_bar(df, top_n=15):
    src = df[df["Duration_Seconds"] > 0].nlargest(top_n, "Duration_Seconds").copy()
    src["Label"] = src["DAG_ID"].str[:12] + " / " + src["Task_ID"].str[:20]

    fig = px.bar(
        src, x="Duration_Minutes", y="Label", orientation="h",
        color="State_FR", color_discrete_map=STATE_FR_COLORS,
        hover_data={"DAG_ID": True, "Task_ID": True, "Duration_Display": True},
        labels={"Duration_Minutes": "Durée (min)", "Label": "", "State_FR": "État"},
    )
    fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>Durée : %{customdata[2]}<extra></extra>")
    fig.update_yaxes(autorange="reversed")
    return _round_bars(_apply(fig, 480))


def duration_by_dag(df, top_n=15):
    """Duree cumulee par DAG : quels pipelines consomment le plus de temps
    machine. Remplace l'ancien box plot par operateur, sans interet ici :
    toutes les taches avec duree mesuree sont des BashOperator (une seule
    categorie a comparer = aucun insight)."""
    src = df[df["Duration_Seconds"] > 0]
    agg = (
        src.groupby("DAG_ID")
        .agg(Total_Min=("Duration_Minutes", "sum"), Nb=("Task_ID", "count"))
        .nlargest(top_n, "Total_Min")
        .reset_index()
    )

    def fmt_min(m):
        h, mn = int(m // 60), int(m % 60)
        return f"{h}h {mn:02d}m" if h else f"{mn}m"

    agg["Duree_fmt"] = agg["Total_Min"].apply(fmt_min)
    agg["Label"] = agg["DAG_ID"].apply(lambda x: x if len(x) <= 28 else x[:26] + "…")

    fig = px.bar(
        agg, x="Total_Min", y="Label", orientation="h",
        color_discrete_sequence=[CIH_BLUE],
        custom_data=["DAG_ID", "Duree_fmt", "Nb"],
        labels={"Total_Min": "Durée cumulée (min)", "Label": ""},
    )
    fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>"
                                    "%{customdata[1]} cumulées<br>"
                                    "%{customdata[2]} tâche(s) mesurée(s)<extra></extra>")
    fig.update_yaxes(autorange="reversed")
    return _round_bars(_apply(fig, 480))


# ---------- Schedule ----------

SCHEDULE_COLORS = {
    "Journalier": CIH_ORANGE, "Intra-journalier": CIH_BLUE, "Hebdomadaire": "#22C55E",
    "Mensuel": "#F59E0B", "Manuel": "#8B5CF6", "Annuel / Ponctuel": "#EC4899",
    "Personnalisé": "#9CA3AF",
}


def schedule_distribution_segments(df):
    src = df.drop_duplicates("DAG_ID")
    counts = src["Schedule_Category"].value_counts()
    return [
        {"label": cat, "color": SCHEDULE_COLORS.get(cat, "#9CA3AF"), "value": int(n)}
        for cat, n in counts.items()
    ]


def schedule_pie(df, height=260):
    segs = [s for s in schedule_distribution_segments(df) if s["value"] > 0]
    total = sum(s["value"] for s in segs)
    return _donut(
        labels=[s["label"] for s in segs],
        values=[s["value"] for s in segs],
        colors=[s["color"] for s in segs],
        center_top=total, center_bottom="DAGs", height=height,
    )


def schedule_hour_bar(df):
    # Uniquement les DAGs JOURNALIERS : melanger les heures de demarrage
    # d'hebdomadaires/mensuels avec les quotidiens n'a pas de sens (ils ne
    # tournent pas les memes jours).
    src = df.drop_duplicates("DAG_ID").copy()
    src = src[src["Schedule_Category"] == "Journalier"]
    src = src[src["Schedule_Cron"] != "None"]

    def extract_hour(cron):
        parts = str(cron).split()
        if len(parts) == 5:
            h = parts[1]
            if h.isdigit():
                return int(h)
        return None

    src["Hour"] = src["Schedule_Cron"].apply(extract_hour)
    src = src.dropna(subset=["Hour"])
    hour_counts = src.groupby("Hour").size().reset_index(name="DAGs")

    fig = px.bar(
        hour_counts, x="Hour", y="DAGs",
        color_discrete_sequence=[CIH_BLUE],
        labels={"Hour": "Heure de démarrage (UTC)", "DAGs": "Nombre de DAGs"},
    )
    fig.update_layout(**_LAYOUT, height=300,
                      xaxis=dict(tickmode="linear", tick0=0, dtick=1, tickangle=0, gridcolor=CIH_BORDER),
                      yaxis=dict(gridcolor=CIH_BORDER))
    return _round_bars(fig, radius=4)
