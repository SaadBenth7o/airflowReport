import streamlit as st
import pandas as pd
from utils.data_loader import load_data, build_dag_summary
from utils.charts import dag_task_composition, success_rate_gauge

st.set_page_config(page_title="DAG Explorer · Airflow", page_icon=None, layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 1.2rem !important; }
[data-testid="stSidebar"] { background:#FFFFFF !important; border-right:1px solid #E9E8E8; }
.section-title {
    font-size:0.95rem; font-weight:700; color:#151213;
    border-left:4px solid #05AEEF; padding-left:10px; margin:4px 0 14px 0;
}
.dag-header {
    background:linear-gradient(135deg,#FFFFFF,#F5F8FC);
    border:1px solid #E9E8E8; border-radius:12px;
    padding:18px 22px; margin-bottom:20px;
}
</style>
""", unsafe_allow_html=True)

df          = load_data()
dag_summary = build_dag_summary()

st.markdown("## DAG Explorer")
st.caption("Vue agregee de tous les DAGs avec filtres et drilldown par DAG.")

col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1.5, 1.5, 1.5], gap="small")

with col_f1:
    search = st.text_input("Rechercher un DAG", placeholder="Nom du DAG...")
with col_f2:
    sched_options = ["Tous"] + sorted(dag_summary["Schedule_Category"].unique())
    sched_filter  = st.selectbox("Frequence", sched_options)
with col_f3:
    health_opts   = ["Tous", "Sain", "Degrade"]
    health_filter = st.selectbox("Sante", health_opts)
with col_f4:
    sort_by = st.selectbox("Trier par", ["DAG_ID", "failed", "Success_Rate", "Total_Rows", "Last_Run"])

summary_view = dag_summary.copy()
if search:
    summary_view = summary_view[summary_view["DAG_ID"].str.contains(search, case=False, na=False)]
if sched_filter != "Tous":
    summary_view = summary_view[summary_view["Schedule_Category"] == sched_filter]
if health_filter == "Sain":
    summary_view = summary_view[~summary_view["Has_Failure"]]
elif health_filter == "Degrade":
    summary_view = summary_view[summary_view["Has_Failure"]]

ascending    = sort_by not in ["failed", "Total_Rows"]
summary_view = summary_view.sort_values(sort_by, ascending=ascending)

st.markdown('<div class="section-title">Tableau recapitulatif — tous les DAGs</div>', unsafe_allow_html=True)
st.caption(f"{len(summary_view)} DAG(s) affiches sur {len(dag_summary)}")


def health_badge(row):
    if row["failed"] > 0:
        return "Degrade"
    if row["upstream_failed"] > 0:
        return "Partiel"
    if row["running"] > 0:
        return "En cours"
    return "Sain"


display = summary_view.copy()
display["Sante"]        = display.apply(health_badge, axis=1)
display["Last_Run_fmt"] = display["Last_Run"].dt.strftime("%Y-%m-%d  %H:%M").fillna("—")
display["Total_Rows_fmt"] = display["Total_Rows"].apply(
    lambda n: f"{n/1e9:.1f}B" if n >= 1e9 else f"{n/1e6:.1f}M" if n >= 1e6 else f"{n/1e3:.0f}K" if n >= 1e3 else str(int(n))
)

table_cols = {
    "DAG_ID":           "DAG",
    "Schedule_Category":"Frequence",
    "Total_Tasks":      "Tasks",
    "Success_Rate":     "Succes %",
    "failed":           "Echecs",
    "upstream_failed":  "Upstream",
    "Total_Rows_fmt":   "Lignes",
    "Last_Run_fmt":     "Dernier run",
    "Sante":            "Sante",
}
show_df = display[list(table_cols)].rename(columns=table_cols)

st.dataframe(
    show_df,
    use_container_width=True,
    height=420,
    column_config={
        "DAG":        st.column_config.TextColumn("DAG", width="large"),
        "Frequence":  st.column_config.TextColumn("Frequence", width="small"),
        "Tasks":      st.column_config.NumberColumn("Tasks", format="%d", width="small"),
        "Succes %":   st.column_config.ProgressColumn("Succes %", min_value=0, max_value=100, format="%.1f%%", width="medium"),
        "Echecs":     st.column_config.NumberColumn("Echecs", format="%d", width="small"),
        "Upstream":   st.column_config.NumberColumn("Upstream", format="%d", width="small"),
        "Lignes":     st.column_config.TextColumn("Lignes", width="small"),
        "Dernier run":st.column_config.TextColumn("Dernier run", width="small"),
        "Sante":      st.column_config.TextColumn("Sante", width="small"),
    },
    hide_index=True,
)

st.markdown("---")
st.markdown('<div class="section-title">Drilldown — detail d\'un DAG</div>', unsafe_allow_html=True)

selected_dag = st.selectbox(
    "Choisir un DAG a explorer",
    options=["— Selectionner un DAG —"] + sorted(df["DAG_ID"].unique()),
)

if selected_dag != "— Selectionner un DAG —":
    dag_df  = df[df["DAG_ID"] == selected_dag]
    dag_row = dag_summary[dag_summary["DAG_ID"] == selected_dag].iloc[0]

    st.markdown(f"""
    <div class="dag-header">
      <strong style="font-size:1.1rem;">{selected_dag}</strong><br>
      <span style="font-size:0.85rem;color:#4E4B4C;">
        Schedule : <code>{dag_row['Schedule_Cron']}</code> &nbsp;&middot;&nbsp;
        {int(dag_row['Total_Tasks'])} taches &nbsp;&middot;&nbsp;
        Succes : <strong>{dag_row['Success_Rate']:.1f}%</strong> &nbsp;&middot;&nbsp;
        Lignes : <strong>{int(dag_row['Total_Rows']):,}</strong>
      </span>
    </div>
    """, unsafe_allow_html=True)

    col_chart, col_gauge = st.columns([2, 1], gap="medium")
    with col_chart:
        st.plotly_chart(dag_task_composition(df, selected_dag), use_container_width=True)
    with col_gauge:
        st.plotly_chart(success_rate_gauge(dag_row["Success_Rate"]), use_container_width=True)

    task_display = dag_df[[
        "Task_ID", "Operator_Type", "Bash_Script_Name",
        "Task_State", "Task_Last_Run_Date", "Duration_Display", "Rows_Affected_Total"
    ]].copy()
    task_display["Task_Last_Run_Date"] = task_display["Task_Last_Run_Date"].dt.strftime("%Y-%m-%d  %H:%M").fillna("—")
    task_display["Rows_Affected_Total"] = task_display["Rows_Affected_Total"].apply(
        lambda n: f"{int(n):,}" if n > 0 else "—"
    )
    task_display.columns = ["Tache", "Operateur", "Script", "Etat", "Dernier run", "Duree", "Lignes"]

    st.dataframe(
        task_display,
        use_container_width=True,
        height=min(550, 38 * len(task_display) + 40),
        column_config={
            "Tache":       st.column_config.TextColumn("Tache", width="medium"),
            "Operateur":   st.column_config.TextColumn("Operateur", width="small"),
            "Script":      st.column_config.TextColumn("Script", width="medium"),
            "Etat":        st.column_config.TextColumn("Etat", width="small"),
            "Dernier run": st.column_config.TextColumn("Dernier run", width="small"),
            "Duree":       st.column_config.TextColumn("Duree", width="small"),
            "Lignes":      st.column_config.TextColumn("Lignes", width="small"),
        },
        hide_index=True,
    )

with st.sidebar:
    st.markdown("**DAG Explorer**")
    total_ok = int((~dag_summary["Has_Failure"]).sum())
    total_ko = int(dag_summary["Has_Failure"].sum())
    st.markdown(f"- {total_ok} DAGs sains")
    st.markdown(f"- {total_ko} DAGs degrades")
    st.divider()
    st.markdown("**Frequences**")
    freq = dag_summary["Schedule_Category"].value_counts()
    for cat, cnt in freq.items():
        st.markdown(f"- {cat} : {cnt}")
