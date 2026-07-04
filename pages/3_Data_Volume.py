import streamlit as st
import pandas as pd
from utils.data_loader import load_data, build_dag_summary
from utils.charts import rows_bar, rows_treemap
from utils.theme import (
    apply_theme, kpi_card, section_title, sidebar_shell, page_header,
    styled_column, STATE_FR_COLOR,
)

st.set_page_config(page_title="Volume de donnees · Airflow", page_icon=None, layout="wide")
apply_theme(st)

df          = load_data()
dag_summary = build_dag_summary()

total_rows      = df["Rows_Affected_Total"].sum()
tasks_with_rows = (df["Rows_Affected_Total"] > 0).sum()
top_task        = df.nlargest(1, "Rows_Affected_Total").iloc[0]
top_dag_rows    = dag_summary.nlargest(1, "Total_Rows").iloc[0]


def fmt(n):
    if n >= 1e9: return f"{n/1e9:.2f}B"
    if n >= 1e6: return f"{n/1e6:.1f}M"
    if n >= 1e3: return f"{n/1e3:.0f}K"
    return str(int(n))


with st.sidebar:
    sidebar_shell(st, active="volume")

page_header(st, "Volume de donnees (connu)",
            "Lignes traitees par tache et par pipeline. Volumes connus uniquement : "
            "les scripts PySpark ne remontent pas leurs comptages (seuls les "
            "traitements SQL le font) — ce que vous voyez ici n'est pas l'exhaustivite.",
            crumb="Volume de donnees")

c1, c2, c3, c4 = st.columns(4, gap="small")
with c1:
    kpi_card(st, "Total lignes traitees", fmt(total_rows),
             sub="volume connu", color="#05AEEF", icon="database")
with c2:
    kpi_card(st, "Taches avec volume connu", tasks_with_rows,
             sub="sur " + str(len(df)) + " taches", color="#151213", icon="layers")
with c3:
    kpi_card(st, "Tache max", fmt(top_task["Rows_Affected_Total"]),
             sub=top_task["Task_ID"][:22], color="#F0481C", icon="trend")
with c4:
    kpi_card(st, "DAG max", fmt(top_dag_rows["Total_Rows"]),
             sub=top_dag_rows["DAG_ID"][:22], color="#22C55E", icon="hash")

st.markdown("<br>", unsafe_allow_html=True)

top_n = st.slider("Nombre de taches a afficher", min_value=5, max_value=40, value=20, step=5)

col_l, col_r = st.columns([1.4, 1], gap="medium")
with col_l:
    with st.container(border=True):
        section_title(st, "Top taches par volume", color="#05AEEF")
        st.plotly_chart(rows_bar(df, top_n=top_n), use_container_width=True)
with col_r:
    with st.container(border=True):
        section_title(st, "Repartition par DAG", color="#F0481C", right="proportionnel")
        st.plotly_chart(rows_treemap(dag_summary), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    section_title(st, "Toutes les taches avec volume connu", color="#05AEEF")

    has_rows = df[df["Rows_Affected_Total"] > 0].sort_values("Rows_Affected_Total", ascending=False).copy()
    has_rows["Rows_fmt"] = has_rows["Rows_Affected_Total"].apply(lambda n: f"{int(n):,}")

    dag_filter = st.multiselect("Filtrer par DAG", sorted(has_rows["DAG_ID"].unique()))
    if dag_filter:
        has_rows = has_rows[has_rows["DAG_ID"].isin(dag_filter)]

    display = has_rows[["DAG_ID", "Task_ID", "Bash_Script_Name", "Rows_fmt", "State_FR", "Task_Last_Run_Date"]].copy()
    display["Task_Last_Run_Date"] = display["Task_Last_Run_Date"].dt.strftime("%Y-%m-%d  %H:%M").fillna("—")
    display.columns = ["DAG", "Tache", "Script", "Lignes traitees", "Etat", "Dernier run"]

    st.dataframe(
        styled_column(display, "Etat", STATE_FR_COLOR), use_container_width=True,
        height=min(580, 38 * len(display) + 40),
        column_config={
            "DAG":             st.column_config.TextColumn("DAG", width="medium"),
            "Tache":           st.column_config.TextColumn("Tache", width="medium"),
            "Script":          st.column_config.TextColumn("Script", width="medium"),
            "Lignes traitees": st.column_config.TextColumn("Lignes traitees", width="small"),
            "Dernier run":     st.column_config.TextColumn("Dernier run", width="small"),
        },
        hide_index=True,
    )
    st.caption(f"{len(display)} tache(s) avec volume connu")
