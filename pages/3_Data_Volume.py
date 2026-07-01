import streamlit as st
import pandas as pd
from utils.data_loader import load_data, build_dag_summary
from utils.charts import rows_bar, rows_treemap

st.set_page_config(page_title="Data Volume · Airflow", page_icon=None, layout="wide")

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
    st.markdown(f"""<div class="kpi-mini">
    <div class="val" style="color:#05AEEF;">{fmt(total_rows)}</div>
    <div class="lbl">Total lignes traitees</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi-mini">
    <div class="val" style="color:#151213;">{tasks_with_rows}</div>
    <div class="lbl">Taches avec donnees</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi-mini">
    <div class="val" style="color:#F0481C;">{fmt(top_task['Rows_Affected_Total'])}</div>
    <div class="lbl">Tache max · {top_task['Task_ID'][:18]}</div></div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="kpi-mini">
    <div class="val" style="color:#22C55E;">{fmt(top_dag_rows['Total_Rows'])}</div>
    <div class="lbl">DAG max · {top_dag_rows['DAG_ID'][:18]}</div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

top_n = st.slider("Nombre de taches a afficher", min_value=5, max_value=40, value=20, step=5)

col_l, col_r = st.columns([1.4, 1], gap="medium")
with col_l:
    st.markdown('<div class="section-title">Top taches par volume</div>', unsafe_allow_html=True)
    st.plotly_chart(rows_bar(df, top_n=top_n), use_container_width=True)
with col_r:
    st.markdown('<div class="section-title">Repartition par DAG</div>', unsafe_allow_html=True)
    st.plotly_chart(rows_treemap(dag_summary), use_container_width=True)

st.markdown("---")
st.markdown('<div class="section-title">Toutes les taches avec donnees (lignes > 0)</div>', unsafe_allow_html=True)

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
        "DAG":            st.column_config.TextColumn("DAG", width="medium"),
        "Tache":          st.column_config.TextColumn("Tache", width="medium"),
        "Script":         st.column_config.TextColumn("Script", width="medium"),
        "Lignes traitees":st.column_config.TextColumn("Lignes traitees", width="small"),
        "Etat":           st.column_config.TextColumn("Etat", width="small"),
        "Dernier run":    st.column_config.TextColumn("Dernier run", width="small"),
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
