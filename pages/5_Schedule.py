import streamlit as st
import pandas as pd
from utils.data_loader import load_data, build_dag_summary
from utils.charts import schedule_pie, schedule_hour_bar, schedule_distribution_segments
from utils.theme import apply_theme, kpi_card, section_title, sidebar_shell, page_header, donut_legend

st.set_page_config(page_title="Planification · Airflow", page_icon=None, layout="wide")
apply_theme(st)

df          = load_data()
dag_summary = build_dag_summary()
n_ok        = int((~dag_summary["Has_Failure"]).sum())
n_ko        = int(dag_summary["Has_Failure"].sum())

uniq   = df.drop_duplicates("DAG_ID")
by_cat = uniq["Schedule_Category"].value_counts()

with st.sidebar:
    sidebar_shell(st, active="schedule", health_label="Sain", n_ok=n_ok, n_ko=n_ko)

page_header(st, "Planification",
            "Frequences et fenetres de demarrage des DAGs.")

c1, c2, c3 = st.columns(3, gap="small")
with c1:
    kpi_card(st, "DAGs planifies", len(uniq), sub="tous actifs", color="#05AEEF", icon="calendar")
with c2:
    kpi_card(st, "Journaliers", int(by_cat.get("Journalier", 0)),
             sub="execution quotidienne", color="#F0481C", icon="clock")
with c3:
    kpi_card(st, "Intra-journaliers", int(by_cat.get("Intra-journalier", 0)),
             sub="plusieurs fois par jour", color="#22C55E", icon="refresh")

st.markdown("<br>", unsafe_allow_html=True)

col_l, col_r = st.columns([1, 1.3], gap="medium")
with col_l:
    with st.container(border=True):
        section_title(st, "Frequence de planification", color="#F0481C")
        c_donut, c_legend = st.columns([1, 1])
        with c_donut:
            st.plotly_chart(schedule_pie(df), use_container_width=True)
        with c_legend:
            st.markdown("<div style='padding-top:20px;'></div>", unsafe_allow_html=True)
            donut_legend(st, schedule_distribution_segments(df))
with col_r:
    with st.container(border=True):
        section_title(st, "DAGs par heure de demarrage (UTC)", color="#05AEEF")
        st.plotly_chart(schedule_hour_bar(df), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    section_title(st, "Planning des DAGs", color="#F0481C")

    dag_sched = dag_summary[["DAG_ID", "Schedule_Cron", "Schedule_Category", "Total_Tasks", "Success_Rate"]].copy()

    CRON_DESC = {
        "None":            "Declenchement manuel uniquement",
        "1 day, 0:00:00": "Tous les jours a minuit",
    }

    def describe_cron(cron):
        c = str(cron).strip()
        if c in CRON_DESC: return CRON_DESC[c]
        if c == "None": return "Manuel"
        parts = c.split()
        if len(parts) == 5:
            mins, hour, dom, month, dow = parts
            try:
                if dom == "*" and month == "*" and dow == "*":
                    if "/" in hour:
                        return f"Toutes les {hour.split('/')[1]}h"
                    if "," in hour:
                        return f"Plusieurs fois par jour ({hour}h)"
                    if hour.isdigit():
                        return f"Tous les jours a {int(hour):02d}h{int(mins):02d}"
                if dow != "*" and hour.isdigit():
                    return f"Hebdomadaire (j {dow}) a {int(hour):02d}h{int(mins):02d}"
                if dom != "*" and month == "*":
                    if "-" in dom:
                        a, b = dom.split("-")
                        return f"Mensuel (j {a}-{b}) a {int(hour):02d}h{int(mins):02d}"
                    return f"Mensuel (j {dom}) a {int(hour):02d}h{int(mins):02d}"
                if dom != "*" and month != "*":
                    return f"Annuel — j {dom} mois {month} a {int(hour):02d}h{int(mins):02d}"
            except Exception:
                pass
        return c

    dag_sched["Description"] = dag_sched["Schedule_Cron"].apply(describe_cron)

    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        cat_filter = st.multiselect(
            "Filtrer par frequence",
            options=sorted(dag_sched["Schedule_Category"].unique()),
        )
    with col_f2:
        search_sched = st.text_input("Rechercher un DAG", key="sched_search")

    if cat_filter:
        dag_sched = dag_sched[dag_sched["Schedule_Category"].isin(cat_filter)]
    if search_sched:
        dag_sched = dag_sched[dag_sched["DAG_ID"].str.contains(search_sched, case=False, na=False)]

    dag_sched_display = dag_sched.rename(columns={
        "DAG_ID": "DAG", "Schedule_Category": "Frequence",
        "Schedule_Cron": "Cron", "Description": "Planification",
        "Total_Tasks": "Tasks", "Success_Rate": "Succes %",
    })
    st.dataframe(
        dag_sched_display[["DAG", "Frequence", "Cron", "Planification", "Tasks", "Succes %"]],
        use_container_width=True,
        height=min(620, 38 * len(dag_sched_display) + 40),
        column_config={
            "DAG":           st.column_config.TextColumn("DAG", width="large"),
            "Frequence":     st.column_config.TextColumn("Frequence", width="small"),
            "Cron":          st.column_config.TextColumn("Expression Cron", width="medium"),
            "Planification": st.column_config.TextColumn("Planification lisible", width="large"),
            "Tasks":         st.column_config.NumberColumn("Tasks", format="%d", width="small"),
            "Succes %":      st.column_config.ProgressColumn("Succes %", min_value=0, max_value=100,
                                                              format="%.1f%%", width="medium"),
        },
        hide_index=True,
    )
    st.caption(f"{len(dag_sched_display)} DAG(s) affiches")
