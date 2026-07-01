import streamlit as st
import pandas as pd
from utils.data_loader import load_data, build_dag_summary
from utils.charts import rows_bar, rows_treemap
from utils.theme import apply_theme, kpi_card, section_title

st.set_page_config(page_title="Data Volume · Airflow", page_icon=None, layout="wide")

apply_theme(st)

df          = load_data()
dag_summary = build_dag_summary()

st.markdown("## Data Volume")
st.caption("Analyse des volumes de donnees traites par les taches Airflow depuis le 01/01/2026.")

total_rows      = df["Rows_Affected_Total"].sum()
tasks_with_rows = (df["Rows_Affected_Total"] > 0).sum()
top_task        = df.nlargest(1, "Rows_Affected_Total").iloc[0]
top_dag_rows    = dag_summary.nlargest(1, "Total_Rows").iloc[0]


def fmt(n):
    if n >= 1e9: return f"{n/1e9:.2f}B"
    if n >= 1e6: return f"{n/1e6:.1f}M"
    if n >= 1e3: return f"{n/1e3:.0f}K"
    return str(int(n))


c1, c2, c3, c4 = st.columns(4, gap="small")
with c1:
    kpi_card(st, "Total lignes traitees", fmt(total_rows), color="#05AEEF")
with c2:
    kpi_card(st, "Taches avec donnees", tasks_with_rows, color="#151213")
with c3:
    kpi_card(st, "Tache max", fmt(top_task["Rows_Affected_Total"]),
             sub=top_task["Task_ID"][:20], color="#F0481C")
with c4:
    kpi_card(st, "DAG max", fmt(top_dag_rows["Total_Rows"]),
             sub=top_dag_rows["DAG_ID"][:20], color="#22C55E")

st.markdown("<br>", unsafe_allow_html=True)

top_n = st.slider("Nombre de taches a afficher", min_value=5, max_value=40, value=20, step=5)

col_l, col_r = st.columns([1.4, 1], gap="medium")
with col_l:
    section_title(st, "Top taches par volume", color="#05AEEF")
    st.plotly_chart(rows_bar(df, top_n=top_n), use_container_width=True)
with col_r:
    section_title(st, "Repartition par DAG", color="#05AEEF")
    st.plotly_chart(rows_treemap(dag_summary), use_container_width=True)

st.markdown("---")
section_title(st, "Toutes les taches avec donnees (lignes > 0)", color="#05AEEF")

has_rows = df[df["Rows_Affected_Total"] > 0].sort_values("Rows_Affected_Total", ascending=False).copy()
has_rows["Rows_fmt"] = has_rows["Rows_Affected_Total"].apply(lambda n: f"{int(n):,}")
has_rows["Etat_FR"]  = has_rows["Task_State"].map({
    "success":         "Succes",
    "failed":          "Echec",
    "skipped":         "Ignoree",
    "upstream_failed": "Upstream",
    "running":         "En cours",
}).fillna(has_rows["Task_State"])

dag_filter = st.multiselect("Filtrer par DAG", sorted(has_rows["DAG_ID"].unique()))
if dag_filter:
    has_rows = has_rows[has_rows["DAG_ID"].isin(dag_filter)]

display = has_rows[["DAG_ID", "Task_ID", "Bash_Script_Name", "Rows_fmt", "Etat_FR", "Task_Last_Run_Date"]].copy()
display["Task_Last_Run_Date"] = display["Task_Last_Run_Date"].dt.strftime("%Y-%m-%d  %H:%M").fillna("—")
display.columns = ["DAG", "Tache", "Script", "Lignes traitees", "Etat", "Dernier run"]

st.dataframe(
    display,
    use_container_width=True,
    height=min(580, 38 * len(display) + 40),
    column_config={
        "DAG":             st.column_config.TextColumn("DAG", width="medium"),
        "Tache":           st.column_config.TextColumn("Tache", width="medium"),
        "Script":          st.column_config.TextColumn("Script", width="medium"),
        "Lignes traitees": st.column_config.TextColumn("Lignes traitees", width="small"),
        "Etat":            st.column_config.TextColumn("Etat", width="small"),
        "Dernier run":     st.column_config.TextColumn("Dernier run", width="small"),
    },
    hide_index=True,
)
st.caption(f"{len(display)} tache(s) avec donnees")

with st.sidebar:
    st.markdown("**Data Volume**")
    st.markdown(f"- Total : {fmt(total_rows)} lignes")
    st.markdown(f"- Taches actives : {tasks_with_rows}")
    st.divider()
    st.markdown("**Top 5 DAGs par volume**")
    top5 = dag_summary.nlargest(5, "Total_Rows")[["DAG_ID", "Total_Rows"]]
    for _, r in top5.iterrows():
        st.markdown(f"- {r['DAG_ID'][:22]} · {fmt(r['Total_Rows'])}")
