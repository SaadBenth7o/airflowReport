import streamlit as st
import pandas as pd
from utils.data_loader import load_data, build_dag_summary, reference_date
from utils.charts import failures_timeline
from utils.theme import apply_theme, kpi_card, section_title, sidebar_shell, page_header, download_button

st.set_page_config(page_title="Échecs & alertes · Airflow", page_icon="assets/transparent.png", layout="wide")
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

page_header(st, "Échecs & alertes",
            "Tâches en échec et dépendances bloquées.")

c1, c2, c3, c4 = st.columns(4, gap="small")
with c1:
    kpi_card(st, "Tâches en échec", len(failed_df),
             sub="état : failed", color="#EF4444", icon="x")
with c2:
    kpi_card(st, "Échecs amont", len(upstream_df),
             sub="dépendances bloquées", color="#F0481C", icon="alert")
with c3:
    kpi_card(st, "Échecs récents", len(recent_fails),
             sub="7 derniers jours de données", color="#EF4444", icon="clock")
with c4:
    n_ko = int(dag_summary["Has_Failure"].sum())
    n_ok = int((~dag_summary["Has_Failure"]).sum())
    kpi_card(st, "DAGs impactés", n_ko,
             sub=f"{n_ok} sains", color="#05AEEF", icon="branch")

st.markdown("<br>", unsafe_allow_html=True)

all_bad = df[df["Task_State"].isin(["failed", "upstream_failed"])].dropna(subset=["Task_Last_Run_Date"])
if not all_bad.empty:
    with st.container(border=True):
        section_title(st, "Timeline des échecs par DAG", color="#EF4444")
        st.plotly_chart(failures_timeline(df), width="stretch")
    st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    section_title(st, "Détail des tâches en échec", color="#EF4444")
    tab1, tab2 = st.tabs(["Tâches en échec (failed)", "Tâches upstream failed"])

    def show_failure_table(source_df, key_suffix, title_prefix=""):
        if source_df.empty:
            st.success("Aucune tâche dans cet état.")
            return
        display = source_df[[
            "DAG_ID", "Task_ID", "Bash_Script_Name",
            "Task_Last_Run_Date", "Duration_Display", "Schedule_Cron"
        ]].copy()
        display["Task_Last_Run_Date"] = display["Task_Last_Run_Date"].dt.strftime("%Y-%m-%d  %H:%M").fillna("—")
        display.columns = ["DAG", "Tâche", "Script", "Dernier run", "Durée", "Schedule"]

        col_f1, col_f2 = st.columns([3.2, 1])
        with col_f1:
            dag_filter = st.multiselect(
                "Filtrer par DAG", options=sorted(display["DAG"].unique()),
                key=f"filter_{key_suffix}",
            )
        with col_f2:
            st.write("")  # Spacer pour aligner avec l'input
            if dag_filter:
                display_copy = display[display["DAG"].isin(dag_filter)]
            else:
                display_copy = display
            download_button(st, display_copy, title=title_prefix, key=f"dl_{key_suffix}")

        if dag_filter:
            display = display[display["DAG"].isin(dag_filter)]
        st.dataframe(
            display, width="stretch",
            height=min(580, 38 * len(display) + 40),
            column_config={"Script": st.column_config.TextColumn("Script .sh")},
            hide_index=True,
        )
        st.caption(f"{len(display)} tâche(s)")

    with tab1:
        show_failure_table(failed_df, "failed", "Tâches en échec")

    with tab2:
        st.info("Les tâches upstream_failed sont bloquées car une tâche précédente dans le même DAG a échoué.")
        show_failure_table(upstream_df, "upstream", "Tâches upstream failed")
