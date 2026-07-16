import streamlit as st
import pandas as pd
from utils.data_loader import load_data, build_dag_summary
from utils.charts import duration_histogram, slowest_tasks_bar, duration_by_dag
from utils.theme import (
    apply_theme, kpi_card, section_title, sidebar_shell, page_header,
    styled_column, STATE_FR_COLOR,
)

st.set_page_config(page_title="Performance · Airflow", page_icon="assets/transparent.png", layout="wide")
apply_theme(st)

df          = load_data()
dag_summary = build_dag_summary()

active  = df[(df["Duration_Seconds"] > 0) & (df["Task_State"] == "success")]
all_dur = df[df["Duration_Seconds"] > 0]
# p95 en indicateur principal : 95 % des taches reussies durent moins que
# ca — plus representatif du "pire cas courant" que la moyenne, que
# quelques durees extremes suffisent a rendre absurde. La mediane (duree
# typique) reste affichee en sous-titre.
med_min = active["Duration_Minutes"].median() if len(active) > 0 else 0
p95_min = active["Duration_Minutes"].quantile(0.95) if len(active) > 0 else 0
max_task = all_dur.nlargest(1, "Duration_Seconds").iloc[0] if len(all_dur) > 0 else None


def fmtd(minutes):
    h = int(minutes // 60);  m = int(minutes % 60);  s = int((minutes * 60) % 60)
    if h > 0:  return f"{h}h {m:02d}m"
    if m > 0:  return f"{m}m {s:02d}s"
    return f"{s}s"


with st.sidebar:
    sidebar_shell(st, active="performance")

page_header(st, "Performance",
            "Durées d'exécution et goulots d'étranglement.")

c1, c2, c3 = st.columns(3, gap="small")
with c1:
    kpi_card(st, "Durée p95", fmtd(p95_min),
             sub=f"médiane : {fmtd(med_min)} · tâches réussies", color="#05AEEF", icon="clock")
with c2:
    max_val  = max_task["Duration_Minutes"] if max_task is not None else 0
    max_name = max_task["Task_ID"][:22] if max_task is not None else "—"
    kpi_card(st, "Tâche la plus longue", fmtd(max_val),
             sub=max_name, color="#F0481C", icon="zap")
with c3:
    kpi_card(st, "Tâches mesurées", len(all_dur),
             sub="avec durée > 0", color="#22C55E", icon="activity")

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    section_title(st, "Distribution des durées", color="#F0481C", right="tâches réussies")
    scale_label = st.radio(
        "Échelle",
        ["Échelle par classe", "Échelle logarithmique"],
        horizontal=True,
        label_visibility="collapsed",
    )
    scale = {"Échelle par classe": "classes",
             "Échelle logarithmique": "log"}[scale_label]
    st.plotly_chart(duration_histogram(df, scale=scale), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Le DAG d'abord (vision globale), ses taches ensuite (detail granulaire).
col_l, col_r = st.columns([1, 1.2], gap="medium")
with col_l:
    with st.container(border=True):
        section_title(st, "DAGs les plus longs", color="#05AEEF", right="durée cumulée")
        with st.container(key="slider-blue-perf"):
            top_dags = st.slider("Nombre de DAGs", 5, 30, 15, 5, key="perf_top_dags")
        st.plotly_chart(duration_by_dag(df, top_n=top_dags), use_container_width=True)
with col_r:
    with st.container(border=True):
        section_title(st, "Tâches les plus longues", color="#EF4444")
        with st.container(key="slider-red-perf"):
            top_n = st.slider("Nombre de tâches", 5, 30, 15, 5, key="perf_top_tasks")
        st.plotly_chart(slowest_tasks_bar(df, top_n=top_n), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    section_title(st, "Durées par DAG", color="#F0481C")
    selected = st.selectbox(
        "Choisir un DAG",
        ["— Tous les DAGs —"] + sorted(df["DAG_ID"].unique()),
        key="perf_dag",
    )
    src = df[df["Duration_Seconds"] > 0].copy()
    if selected != "— Tous les DAGs —":
        src = src[src["DAG_ID"] == selected]

    if src.empty:
        st.info("Aucune donnée de durée disponible pour ce DAG.")
    else:
        perf_display = src[[
            "DAG_ID", "Task_ID", "State_FR", "Duration_Display",
            "Duration_Minutes", "Task_Last_Run_Date"
        ]].sort_values("Duration_Minutes", ascending=False).copy()
        perf_display["Task_Last_Run_Date"] = perf_display["Task_Last_Run_Date"].dt.strftime("%Y-%m-%d  %H:%M").fillna("—")
        perf_display.columns = ["DAG", "Tâche", "État", "Durée", "Min", "Dernier run"]
        st.dataframe(
            styled_column(perf_display.drop(columns=["Min"]), "État", STATE_FR_COLOR),
            use_container_width=True,
            height=min(500, 38 * len(perf_display) + 40),
            hide_index=True,
        )
