import streamlit as st
import pandas as pd
from utils.data_loader import load_data, build_dag_summary
from utils.charts import duration_histogram, slowest_tasks_bar, duration_by_dag
from utils.theme import (
    apply_theme, kpi_card, section_title, sidebar_shell, page_header,
    styled_column, STATE_FR_COLOR,
)

st.set_page_config(page_title="Performance · Airflow", page_icon="assets/airflow-pin.png", layout="wide")
apply_theme(st)

df          = load_data()
dag_summary = build_dag_summary()

active  = df[(df["Duration_Seconds"] > 0) & (df["Task_State"] == "success")]
all_dur = df[df["Duration_Seconds"] > 0]
# Mediane plutot que moyenne : quelques taches a duree extreme suffisent
# a rendre une moyenne absurde ; la mediane reflete la duree typique.
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
            "Durees d'execution et goulots d'etranglement.")

c1, c2, c3 = st.columns(3, gap="small")
with c1:
    kpi_card(st, "Duree mediane", fmtd(med_min),
             sub=f"par tache reussie · p95 : {fmtd(p95_min)}", color="#05AEEF", icon="clock")
with c2:
    max_val  = max_task["Duration_Minutes"] if max_task is not None else 0
    max_name = max_task["Task_ID"][:22] if max_task is not None else "—"
    kpi_card(st, "Tache la plus longue", fmtd(max_val),
             sub=max_name, color="#F0481C", icon="zap")
with c3:
    kpi_card(st, "Taches mesurees", len(all_dur),
             sub="avec duree > 0", color="#22C55E", icon="activity")

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    section_title(st, "Distribution des durees", color="#F0481C", right="axe X : minutes")
    st.plotly_chart(duration_histogram(df), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

col_l, col_r = st.columns([1.2, 1], gap="medium")
with col_l:
    with st.container(border=True):
        section_title(st, "Taches les plus longues", color="#EF4444")
        top_n = st.slider("Nombre de taches", 5, 30, 15, 5)
        st.plotly_chart(slowest_tasks_bar(df, top_n=top_n), use_container_width=True)
with col_r:
    with st.container(border=True):
        section_title(st, "DAGs les plus consommateurs", color="#05AEEF",
                      right="duree cumulee · top 15")
        st.plotly_chart(duration_by_dag(df), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    section_title(st, "Durees par DAG", color="#F0481C")
    selected = st.selectbox(
        "Choisir un DAG",
        ["— Tous les DAGs —"] + sorted(df["DAG_ID"].unique()),
        key="perf_dag",
    )
    src = df[df["Duration_Seconds"] > 0].copy()
    if selected != "— Tous les DAGs —":
        src = src[src["DAG_ID"] == selected]

    if src.empty:
        st.info("Aucune donnee de duree disponible pour ce DAG.")
    else:
        perf_display = src[[
            "DAG_ID", "Task_ID", "State_FR", "Duration_Display",
            "Duration_Minutes", "Task_Last_Run_Date"
        ]].sort_values("Duration_Minutes", ascending=False).copy()
        perf_display["Task_Last_Run_Date"] = perf_display["Task_Last_Run_Date"].dt.strftime("%Y-%m-%d  %H:%M").fillna("—")
        perf_display.columns = ["DAG", "Tache", "Etat", "Duree", "Min", "Dernier run"]
        st.dataframe(
            styled_column(perf_display.drop(columns=["Min"]), "Etat", STATE_FR_COLOR),
            use_container_width=True,
            height=min(500, 38 * len(perf_display) + 40),
            column_config={
                "DAG":         st.column_config.TextColumn("DAG", width="medium"),
                "Tache":       st.column_config.TextColumn("Tache", width="medium"),
                "Duree":       st.column_config.TextColumn("Duree", width="small"),
                "Dernier run": st.column_config.TextColumn("Dernier run", width="small"),
            },
            hide_index=True,
        )
