import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_loader import load_data, build_dag_summary
from utils.charts import failures_timeline
from utils.theme import apply_theme, kpi_card, section_title

st.set_page_config(page_title="Failures · Airflow", page_icon=None, layout="wide")

apply_theme(st)

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
    kpi_card(st, "Taches en echec", len(failed_df), color="#EF4444")
with c2:
    kpi_card(st, "Upstream failed", len(upstream_df), color="#F0481C")
with c3:
    kpi_card(st, "Echecs recents (7j)", len(recent_fails), color="#EF4444")
with c4:
    n_dags_ko = int(dag_summary["Has_Failure"].sum())
    kpi_card(st, "DAGs impactes", n_dags_ko, color="#F59E0B")

st.markdown("<br>", unsafe_allow_html=True)

all_bad = df[df["Task_State"].isin(["failed", "upstream_failed"])].dropna(subset=["Task_Last_Run_Date"])
if not all_bad.empty:
    section_title(st, "Timeline des echecs", color="#EF4444")
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
