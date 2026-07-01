import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_loader import load_data, build_dag_summary
from utils.charts import failures_timeline

st.set_page_config(page_title="Failures · Airflow", page_icon=None, layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 1.2rem !important; }
[data-testid="stSidebar"] { background:#FFFFFF !important; border-right:1px solid #E9E8E8; }
.section-title {
    font-size:0.95rem; font-weight:700; color:#151213;
    border-left:4px solid #EF4444; padding-left:10px; margin:4px 0 14px 0;
}
.kpi-mini {
    background:#FFF; border:1px solid #E9E8E8; border-radius:10px;
    padding:14px 18px; text-align:center;
}
.kpi-mini .val { font-size:1.9rem; font-weight:700; }
.kpi-mini .lbl { font-size:0.70rem; color:#4E4B4C; text-transform:uppercase; letter-spacing:0.06em; }
</style>
""", unsafe_allow_html=True)

df          = load_data()
dag_summary = build_dag_summary()
now         = datetime.now()

st.markdown("## Failures et Incidents")
st.caption("Vue consolidee de toutes les taches en etat d'echec ou bloquees.")

failed_df     = df[df["Task_State"] == "failed"]
upstream_df   = df[df["Task_State"] == "upstream_failed"]
recent_cutoff = pd.Timestamp(now - pd.Timedelta(days=7))
recent_fails  = failed_df[failed_df["Task_Last_Run_Date"] >= recent_cutoff]
old_fails     = failed_df[failed_df["Task_Last_Run_Date"] < recent_cutoff]

c1, c2, c3, c4 = st.columns(4, gap="small")
with c1:
    st.markdown(f"""<div class="kpi-mini">
    <div class="val" style="color:#EF4444;">{len(failed_df)}</div>
    <div class="lbl">Taches en echec</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi-mini">
    <div class="val" style="color:#F0481C;">{len(upstream_df)}</div>
    <div class="lbl">Upstream failed</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi-mini">
    <div class="val" style="color:#EF4444;">{len(recent_fails)}</div>
    <div class="lbl">Echecs recents (7j)</div></div>""", unsafe_allow_html=True)
with c4:
    n_dags_ko = int(dag_summary["Has_Failure"].sum())
    st.markdown(f"""<div class="kpi-mini">
    <div class="val" style="color:#F59E0B;">{n_dags_ko}</div>
    <div class="lbl">DAGs impactes</div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

all_bad = df[df["Task_State"].isin(["failed", "upstream_failed"])].dropna(subset=["Task_Last_Run_Date"])
if not all_bad.empty:
    st.markdown('<div class="section-title">Timeline des echecs</div>', unsafe_allow_html=True)
    st.plotly_chart(failures_timeline(df), use_container_width=True)

tab1, tab2 = st.tabs(["Taches en echec (failed)", "Upstream failed"])


def show_failure_table(source_df, key_suffix):
    if source_df.empty:
        st.success("Aucune tache dans cet etat.")
        return

    display = source_df[[
        "DAG_ID", "Task_ID", "Bash_Script_Name",
        "Task_Last_Run_Date", "Duration_Display", "Schedule_Cron"
    ]].copy()
    display["Task_Last_Run_Date"] = display["Task_Last_Run_Date"].dt.strftime("%Y-%m-%d  %H:%M").fillna("—")
    display.columns = ["DAG", "Tache", "Script", "Dernier run", "Duree", "Schedule"]

    dag_filter = st.multiselect(
        "Filtrer par DAG",
        options=sorted(display["DAG"].unique()),
        key=f"filter_{key_suffix}",
    )
    if dag_filter:
        display = display[display["DAG"].isin(dag_filter)]

    st.dataframe(
        display,
        use_container_width=True,
        height=min(580, 38 * len(display) + 40),
        column_config={
            "DAG":         st.column_config.TextColumn("DAG", width="medium"),
            "Tache":       st.column_config.TextColumn("Tache", width="medium"),
            "Script":      st.column_config.TextColumn("Script .sh", width="medium"),
            "Dernier run": st.column_config.TextColumn("Dernier run", width="small"),
            "Duree":       st.column_config.TextColumn("Duree", width="small"),
            "Schedule":    st.column_config.TextColumn("Schedule", width="small"),
        },
        hide_index=True,
    )
    st.caption(f"{len(display)} tache(s) affichee(s)")


with tab1:
    if not failed_df.empty:
        st.markdown("**DAGs les plus impactes**")
        dag_fail_counts = (
            failed_df.groupby("DAG_ID")
            .agg(Echecs=("Task_ID", "count"), Dernier_run=("Task_Last_Run_Date", "max"))
            .sort_values("Echecs", ascending=False)
            .reset_index()
        )
        dag_fail_counts["Dernier_run"] = dag_fail_counts["Dernier_run"].dt.strftime("%d/%m  %H:%M").fillna("—")
        st.dataframe(
            dag_fail_counts.rename(columns={"DAG_ID": "DAG", "Echecs": "Nb echecs", "Dernier_run": "Dernier run"}),
            use_container_width=True, hide_index=True, height=220,
        )
        st.markdown("---")
    show_failure_table(failed_df, "failed")

with tab2:
    st.info("Les taches upstream_failed sont bloquees car une tache precedente dans le meme DAG a echoue.")
    show_failure_table(upstream_df, "upstream")

with st.sidebar:
    st.markdown("**Failures**")
    st.markdown(f"- {len(failed_df)} taches en echec")
    st.markdown(f"- {len(upstream_df)} upstream failed")
    st.markdown(f"- {len(recent_fails)} echecs recents (7j)")
    st.divider()
    if not old_fails.empty:
        st.warning(f"{len(old_fails)} tache(s) en echec depuis plus de 7 jours.")
        for dag in old_fails["DAG_ID"].unique():
            st.markdown(f"  - {dag}")
