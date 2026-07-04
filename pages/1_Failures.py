import streamlit as st
import pandas as pd
from utils.data_loader import load_data, build_dag_summary, reference_date
from utils.charts import failures_timeline
from utils.theme import apply_theme, kpi_card, section_title, sidebar_shell, page_header

st.set_page_config(page_title="Echecs & alertes · Airflow", page_icon=None, layout="wide")
apply_theme(st)

df          = load_data()
dag_summary = build_dag_summary()

failed_df     = df[df["Task_State"] == "failed"]
upstream_df   = df[df["Task_State"] == "upstream_failed"]
# Recence calculee par rapport a la date des donnees (dernier run de
# l'export), pas a l'horloge murale : avec un export date de quelques
# jours, "0 echec recent" s'affichait alors que des echecs dataient du
# jour meme de l'export.
recent_cutoff = reference_date(df) - pd.Timedelta(days=7)
recent_fails  = failed_df[failed_df["Task_Last_Run_Date"] >= recent_cutoff]
old_fails     = failed_df[failed_df["Task_Last_Run_Date"] < recent_cutoff]

with st.sidebar:
    sidebar_shell(st, active="failures")

page_header(st, "Echecs & alertes",
            "Taches en echec et dependances bloquees.")

c1, c2, c3, c4 = st.columns(4, gap="small")
with c1:
    kpi_card(st, "Taches en echec", len(failed_df),
             sub="etat : failed", color="#EF4444", icon="x")
with c2:
    kpi_card(st, "Echecs amont", len(upstream_df),
             sub="dependances bloquees", color="#F0481C", icon="alert")
with c3:
    kpi_card(st, "Echecs recents", len(recent_fails),
             sub="7 derniers jours de donnees", color="#EF4444", icon="clock")
with c4:
    n_ko = int(dag_summary["Has_Failure"].sum())
    n_ok = int((~dag_summary["Has_Failure"]).sum())
    kpi_card(st, "DAGs impactes", n_ko,
             sub=f"{n_ok} sains", color="#05AEEF", icon="branch")

st.markdown("<br>", unsafe_allow_html=True)

all_bad = df[df["Task_State"].isin(["failed", "upstream_failed"])].dropna(subset=["Task_Last_Run_Date"])
if not all_bad.empty:
    with st.container(border=True):
        section_title(st, "Timeline des echecs par DAG", color="#EF4444")
        st.plotly_chart(failures_timeline(df), use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    section_title(st, "Detail des taches en echec", color="#EF4444")
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
            "Filtrer par DAG", options=sorted(display["DAG"].unique()),
            key=f"filter_{key_suffix}",
        )
        if dag_filter:
            display = display[display["DAG"].isin(dag_filter)]
        st.dataframe(
            display, use_container_width=True,
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
        st.caption(f"{len(display)} tache(s)")

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
