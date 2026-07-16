import streamlit as st
import pandas as pd
from utils.data_loader import load_data, build_dag_summary
from utils.charts import (
    schedule_pie, schedule_hour_bar, schedule_distribution_segments, SCHEDULE_COLORS,
)
from utils.cron_fr import describe_cron
from utils.theme import (
    apply_theme, kpi_card, section_title, sidebar_shell, page_header, donut_legend,
)

st.set_page_config(page_title="Planification · Airflow", page_icon="assets/transparent.png", layout="wide")
apply_theme(st)

df          = load_data()
dag_summary = build_dag_summary()

uniq   = df.drop_duplicates("DAG_ID")
by_cat = uniq["Schedule_Category"].value_counts()

with st.sidebar:
    sidebar_shell(st, active="schedule")

page_header(st, "Planification",
            "Fréquences et fenêtres de démarrage des DAGs.")

c1, c2, c3 = st.columns(3, gap="small")
with c1:
    kpi_card(st, "DAGs planifiés", len(uniq), sub="tous actifs", color="#05AEEF", icon="calendar")
with c2:
    kpi_card(st, "Journaliers", int(by_cat.get("Journalier", 0)),
             sub="exécution quotidienne", color="#F0481C", icon="clock")
with c3:
    kpi_card(st, "Intra-journaliers", int(by_cat.get("Intra-journalier", 0)),
             sub="plusieurs fois par jour", color="#22C55E", icon="refresh")

st.markdown("<br>", unsafe_allow_html=True)

col_l, col_r = st.columns([1, 1.3], gap="medium")
with col_l:
    with st.container(border=True):
        section_title(st, "Fréquence de planification", color="#F0481C")
        c_donut, c_legend = st.columns([1, 1])
        with c_donut:
            # height=300 : aligne le bas de cette carte sur "DAGs par
            # heure de demarrage" (mesure reelle).
            st.plotly_chart(schedule_pie(df, height=300), use_container_width=True)
        with c_legend:
            st.markdown("<div style='padding-top:20px;'></div>", unsafe_allow_html=True)
            donut_legend(st, schedule_distribution_segments(df))
with col_r:
    with st.container(border=True):
        section_title(st, "DAGs (journaliers) par heure de démarrage (UTC)", color="#05AEEF")
        st.plotly_chart(schedule_hour_bar(df), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    section_title(st, "Planning des DAGs", color="#F0481C")

    dag_sched = dag_summary[["DAG_ID", "Schedule_Cron", "Schedule_Category", "Total_Tasks", "Success_Rate"]].copy()
    # Conversion cron -> phrase francaise (utils/cron_fr) ; l'expression
    # brute reste en derniere colonne pour verification.
    dag_sched["Description"] = dag_sched["Schedule_Cron"].apply(describe_cron)

    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        cat_filter = st.multiselect(
            "Filtrer par fréquence",
            options=sorted(dag_sched["Schedule_Category"].unique()),
        )
    with col_f2:
        search_sched = st.text_input("Rechercher un DAG", key="sched_search")

    if cat_filter:
        dag_sched = dag_sched[dag_sched["Schedule_Category"].isin(cat_filter)]
    if search_sched:
        dag_sched = dag_sched[dag_sched["DAG_ID"].str.contains(search_sched, case=False, na=False)]

    dag_sched_display = dag_sched.rename(columns={
        "DAG_ID": "DAG", "Schedule_Category": "Fréquence",
        "Schedule_Cron": "Expression cron", "Description": "Planification lisible",
        "Total_Tasks": "Tâches", "Success_Rate": "Succès %",
    })[["DAG", "Fréquence", "Planification lisible", "Tâches", "Succès %", "Expression cron"]].copy()
    # Succes % : pourcentage colore sur un gradient divergent rouge ->
    # ambre -> vert, a la place de la barre de progression.
    dag_sched_display["Succès %"] = dag_sched_display["Succès %"].map(lambda v: f"{v:.1f} %")

    def _lerp(a, b, t):
        return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))

    def _pct_style(val):
        try:
            v = float(str(val).replace("%", "").strip())
        except ValueError:
            return ""
        if v <= 50:
            rgb = _lerp((239, 68, 68), (245, 158, 11), v / 50)
        else:
            rgb = _lerp((245, 158, 11), (22, 163, 74), (v - 50) / 50)
        return f"color:rgb{rgb};font-weight:700;"

    def _freq_style(val):
        c = SCHEDULE_COLORS.get(val)
        return f"color:{c};font-weight:700;" if c else ""

    # Expression cron : petit rectangle monospace, comme l'ancienne puce
    # du header de DAG Explorer. (#F5F8FC etait invisible sur fond blanc.)
    _CRON_CSS = ("font-family:ui-monospace,Menlo,monospace;"
                 "background-color:#EEF1F5;color:#151213;")

    sty = (
        dag_sched_display.style
        .map(_freq_style, subset=["Fréquence"])
        .map(_pct_style, subset=["Succès %"])
        .map(lambda _v: _CRON_CSS, subset=["Expression cron"])
    )
    st.dataframe(
        sty,
        use_container_width=True,
        height=min(620, 38 * len(dag_sched_display) + 40),
        hide_index=True,
    )
    st.caption(f"{len(dag_sched_display)} DAG(s) affichés")
