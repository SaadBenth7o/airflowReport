import streamlit as st
import pandas as pd
from utils.data_loader import load_data, build_dag_summary
from utils.charts import schedule_pie, schedule_hour_bar
from utils.theme import apply_theme, section_title

st.set_page_config(page_title="Schedule · Airflow", page_icon=None, layout="wide")

apply_theme(st)

df          = load_data()
dag_summary = build_dag_summary()

st.markdown("## Schedule")
st.caption("Visualisation des planifications cron de tous les DAGs actifs.")

col_l, col_r = st.columns([1, 1.2], gap="medium")
with col_l:
    section_title(st, "Repartition des frequences")
    st.plotly_chart(schedule_pie(df), use_container_width=True)
with col_r:
    section_title(st, "DAGs par heure de demarrage")
    st.plotly_chart(schedule_hour_bar(df), use_container_width=True)

st.markdown("---")
section_title(st, "Detail des planifications par DAG")

dag_sched = dag_summary[["DAG_ID", "Schedule_Cron", "Schedule_Category", "Total_Tasks", "Success_Rate"]].copy()

CRON_DESC = {
    "None":            "Declenchement manuel uniquement",
    "1 day, 0:00:00": "Tous les jours a minuit",
}


def describe_cron(cron):
    c = str(cron).strip()
    if c in CRON_DESC:
        return CRON_DESC[c]
    if c == "None":
        return "Manuel"
    parts = c.split()
    if len(parts) == 5:
        mins, hour, dom, month, dow = parts
        try:
            if dom == "*" and month == "*" and dow == "*":
                if "/" in hour:
                    step = hour.split("/")[1]
                    return f"Toutes les {step}h"
                if "," in hour:
                    return f"Plusieurs fois par jour ({hour}h)"
                if hour.isdigit():
                    return f"Tous les jours a {int(hour):02d}h{int(mins):02d}"
            if dow != "*":
                if hour.isdigit():
                    return f"Hebdomadaire (j {dow}) a {int(hour):02d}h{int(mins):02d}"
            if dom != "*" and month == "*":
                if "-" in dom:
                    a, b = dom.split("-")
                    return f"Mensuel (j {a} a {b}) a {int(hour):02d}h{int(mins):02d}"
                return f"Mensuel (j {dom}) a {int(hour):02d}h{int(mins):02d}"
            if dom != "*" and month != "*":
                return f"Annuel — j {dom} mois {month} a {int(hour):02d}h{int(mins):02d}"
        except Exception:
            pass
    return c


dag_sched["Description"] = dag_sched["Schedule_Cron"].apply(describe_cron)

cat_filter = st.multiselect(
    "Filtrer par frequence",
    options=sorted(dag_sched["Schedule_Category"].unique()),
)
if cat_filter:
    dag_sched = dag_sched[dag_sched["Schedule_Category"].isin(cat_filter)]

search_sched = st.text_input("Rechercher un DAG", key="sched_search")
if search_sched:
    dag_sched = dag_sched[dag_sched["DAG_ID"].str.contains(search_sched, case=False, na=False)]

dag_sched_display = dag_sched.rename(columns={
    "DAG_ID":           "DAG",
    "Schedule_Category":"Frequence",
    "Schedule_Cron":    "Cron",
    "Description":      "Planification",
    "Total_Tasks":      "Tasks",
    "Success_Rate":     "Succes %",
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

with st.sidebar:
    st.markdown("**Schedule**")
    freq = df.drop_duplicates("DAG_ID")["Schedule_Category"].value_counts()
    for cat, cnt in freq.items():
        st.markdown(f"- {cat} : {cnt} DAG(s)")
    st.divider()
    manual_dags = dag_summary[dag_summary["Schedule_Cron"] == "None"]
    if not manual_dags.empty:
        st.markdown(f"{len(manual_dags)} DAGs sans schedule automatique (manuel).")
