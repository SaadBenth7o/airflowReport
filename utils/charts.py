import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from utils.data_loader import STATE_COLORS, CIH_ORANGE, CIH_BLUE, CIH_BG, CIH_TEXT, CIH_BORDER

_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=CIH_TEXT, size=13),
    margin=dict(l=10, r=10, t=45, b=10),
    hoverlabel=dict(bgcolor="white", bordercolor=CIH_BORDER, font_size=13),
)


def _apply(fig, height=360):
    fig.update_layout(**_LAYOUT, height=height)
    return fig


# ---------- Overview ----------

def state_donut(df):
    counts = df["Task_State"].value_counts().reset_index()
    counts.columns = ["État", "Nombre"]
    fr_map = {"success": "Succès", "failed": "Échec", "skipped": "Ignorée",
               "upstream_failed": "Échec amont", "running": "En cours"}
    counts["Label"] = counts["État"].map(fr_map).fillna(counts["État"])
    colors = [STATE_COLORS.get(s, "#9CA3AF") for s in counts["État"]]

    fig = go.Figure(go.Pie(
        labels=counts["Label"],
        values=counts["Nombre"],
        hole=0.62,
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value} tâches (%{percent})<extra></extra>",
        pull=[0.04 if s == "failed" else 0 for s in counts["État"]],
    ))
    total = counts["Nombre"].sum()
    fig.add_annotation(text=f"<b>{total}</b><br><span style='font-size:11px'>tâches</span>",
                       x=0.5, y=0.5, showarrow=False, font_size=18)
    fig.update_layout(**_LAYOUT, title="Distribution des états", height=360,
                      showlegend=True,
                      legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"))
    return fig


def dag_failures_bar(dag_summary, top_n=10):
    df = dag_summary[dag_summary["failed"] > 0].nlargest(top_n, "failed").copy()
    df["DAG_Short"] = df["DAG_ID"].apply(lambda x: x if len(x) <= 30 else x[:28] + "…")

    fig = px.bar(
        df, x="failed", y="DAG_Short", orientation="h",
        color="failed",
        color_continuous_scale=[[0, "#FBBF24"], [0.5, "#F97316"], [1, "#EF4444"]],
        hover_data={"DAG_ID": True, "failed": True, "Success_Rate": True},
        labels={"failed": "Tâches en échec", "DAG_Short": ""},
        title=f"Top {min(top_n, len(df))} DAGs — Tâches en échec",
    )
    fig.update_coloraxes(showscale=False)
    fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>%{x} échec(s)<br>Taux de succès : %{customdata[2]:.1f}%<extra></extra>")
    return _apply(fig, 380)


# ---------- Failures ----------

def failures_timeline(df):
    target = df[df["Task_State"].isin(["failed", "upstream_failed"])].dropna(subset=["Task_Last_Run_Date"]).copy()
    target["Label"] = target["Task_State"].map({"failed": "Échec", "upstream_failed": "Échec amont"})

    n_dags = target["DAG_ID"].nunique()
    fig = px.scatter(
        target,
        x="Task_Last_Run_Date", y="DAG_ID",
        color="Task_State",
        color_discrete_map=STATE_COLORS,
        symbol="Task_State",
        hover_data={"Task_ID": True, "Bash_Script_Name": True, "Task_Last_Run_Date": True},
        title="Timeline des échecs par DAG",
        labels={"Task_Last_Run_Date": "Date du dernier run", "DAG_ID": ""},
    )
    fig.update_traces(marker_size=13)
    fig.update_layout(**_LAYOUT, height=max(320, n_dags * 38 + 100),
                      legend=dict(title="État", orientation="v"))
    return fig


# ---------- DAG Explorer ----------

def dag_task_composition(df, dag_id):
    dag_df = df[df["DAG_ID"] == dag_id]
    counts = dag_df["Task_State"].value_counts().reset_index()
    counts.columns = ["État", "Nombre"]
    colors = [STATE_COLORS.get(s, "#9CA3AF") for s in counts["État"]]

    fig = px.bar(
        counts, x="État", y="Nombre",
        color="État", color_discrete_map=STATE_COLORS,
        title=f"Composition — {dag_id}",
        labels={"État": "", "Nombre": "Nb tâches"},
    )
    fig.update_layout(**_LAYOUT, height=280, showlegend=False)
    return fig


def success_rate_gauge(rate):
    color = "#22C55E" if rate >= 80 else CIH_ORANGE if rate >= 50 else "#EF4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=rate,
        number={"suffix": "%", "font": {"size": 32, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": CIH_TEXT},
            "bar": {"color": color},
            "bgcolor": "white",
            "steps": [
                {"range": [0, 50],  "color": "#FEE2E2"},
                {"range": [50, 80], "color": "#FEF3C7"},
                {"range": [80, 100],"color": "#DCFCE7"},
            ],
        },
        title={"text": "Taux de succès global", "font": {"size": 14}},
    ))
    fig.update_layout(**_LAYOUT, height=250)
    return fig


# ---------- Data Volume ----------

def rows_bar(df, top_n=20):
    src = df[df["Rows_Affected_Total"] > 0].nlargest(top_n, "Rows_Affected_Total").copy()
    src["Label"] = src["Task_ID"].apply(lambda x: x if len(x) <= 28 else x[:26] + "…")

    fig = px.bar(
        src, x="Rows_Affected_Total", y="Label", orientation="h",
        color_discrete_sequence=[CIH_BLUE],
        hover_data={"DAG_ID": True, "Rows_Affected_Total": ":,"},
        labels={"Rows_Affected_Total": "Lignes traitées", "Label": ""},
        title=f"Top {min(top_n, len(src))} tâches par volume",
    )
    fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>%{y}<br>%{x:,} lignes<extra></extra>")
    return _apply(fig, 520)


def rows_treemap(dag_summary):
    src = dag_summary[dag_summary["Total_Rows"] > 0].copy()
    src["Rows_Label"] = src["Total_Rows"].apply(
        lambda n: f"{n/1e9:.1f}B" if n >= 1e9 else f"{n/1e6:.0f}M" if n >= 1e6 else f"{n/1e3:.0f}K"
    )
    fig = px.treemap(
        src, path=["DAG_ID"], values="Total_Rows",
        color="Total_Rows",
        color_continuous_scale=[[0, "#E0F2FE"], [1, CIH_BLUE]],
        title="Volume total par DAG",
        hover_data={"Total_Rows": ":,"},
    )
    fig.update_traces(hovertemplate="<b>%{label}</b><br>%{value:,} lignes<extra></extra>")
    fig.update_coloraxes(showscale=False)
    return _apply(fig, 400)


# ---------- Performance ----------

def duration_histogram(df):
    src = df[(df["Duration_Minutes"] > 0) & (df["Task_State"] == "success")].copy()
    fig = px.histogram(
        src, x="Duration_Minutes", nbins=35,
        color_discrete_sequence=[CIH_ORANGE],
        labels={"Duration_Minutes": "Durée (minutes)", "count": "Nb tâches"},
        title="Distribution des durées — tâches réussies",
    )
    fig.update_layout(**_LAYOUT, height=340,
                      bargap=0.05,
                      xaxis=dict(gridcolor=CIH_BORDER),
                      yaxis=dict(gridcolor=CIH_BORDER))
    return fig


def slowest_tasks_bar(df, top_n=15):
    src = df[df["Duration_Seconds"] > 0].nlargest(top_n, "Duration_Seconds").copy()
    src["Label"] = src["DAG_ID"].str[:12] + " / " + src["Task_ID"].str[:20]

    fig = px.bar(
        src, x="Duration_Minutes", y="Label", orientation="h",
        color="Task_State", color_discrete_map=STATE_COLORS,
        hover_data={"DAG_ID": True, "Task_ID": True, "Duration_Display": True},
        labels={"Duration_Minutes": "Durée (min)", "Label": "", "Task_State": "État"},
        title=f"Top {min(top_n, len(src))} tâches les plus longues",
    )
    fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>Durée : %{customdata[2]}<extra></extra>")
    return _apply(fig, 520)


def duration_by_operator(df):
    src = df[df["Duration_Minutes"] > 0].copy()
    fig = px.box(
        src, x="Operator_Type", y="Duration_Minutes",
        color="Operator_Type",
        color_discrete_sequence=[CIH_ORANGE, CIH_BLUE, "#22C55E", "#8B5CF6"],
        labels={"Operator_Type": "Opérateur", "Duration_Minutes": "Durée (min)"},
        title="Durée par type d'opérateur",
        points="outliers",
    )
    fig.update_layout(**_LAYOUT, height=340, showlegend=False,
                      yaxis=dict(gridcolor=CIH_BORDER))
    return fig


# ---------- Schedule ----------

def schedule_pie(df):
    src = df.drop_duplicates("DAG_ID")[["DAG_ID", "Schedule_Category"]].copy()
    counts = src["Schedule_Category"].value_counts().reset_index()
    counts.columns = ["Fréquence", "Nombre"]

    fig = go.Figure(go.Pie(
        labels=counts["Fréquence"],
        values=counts["Nombre"],
        hole=0.55,
        marker=dict(
            colors=[CIH_ORANGE, CIH_BLUE, "#22C55E", "#F59E0B", "#8B5CF6", "#EC4899"],
            line=dict(color="white", width=2),
        ),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value} DAGs<extra></extra>",
    ))
    fig.update_layout(**_LAYOUT, title="Fréquence de planification des DAGs",
                      height=360, showlegend=True,
                      legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"))
    return fig


def schedule_hour_bar(df):
    src = df.drop_duplicates("DAG_ID").copy()
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
        title="DAGs par heure de démarrage",
    )
    fig.update_layout(**_LAYOUT, height=320,
                      xaxis=dict(tickmode="linear", tick0=0, dtick=1, gridcolor=CIH_BORDER),
                      yaxis=dict(gridcolor=CIH_BORDER))
    return fig
