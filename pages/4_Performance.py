import streamlit as st
import pandas as pd
from utils.data_loader import load_data
from utils.charts import duration_histogram, slowest_tasks_bar, duration_by_operator

st.set_page_config(page_title="Performance · Airflow", page_icon=None, layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 1.2rem !important; }
[data-testid="stSidebar"] { background:#FFFFFF !important; border-right:1px solid #E9E8E8; }
.section-title {
    font-size:0.95rem; font-weight:700; color:#151213;
    border-left:4px solid #F0481C; padding-left:10px; margin:4px 0 14px 0;
}
.kpi-mini {
    background:#FFF; border:1px solid #E9E8E8; border-radius:10px;
    padding:14px 18px; text-align:center;
}
.kpi-mini .val { font-size:1.9rem; font-weight:700; }
.kpi-mini .lbl { font-size:0.70rem; color:#4E4B4C; text-transform:uppercase; letter-spacing:0.06em; }
</style>
""", unsafe_allow_html=True)

df = load_data()

st.markdown("## Performance et Durees")
st.caption("Analyse des temps d'execution des taches Airflow.")

active  = df[(df["Duration_Seconds"] > 0) & (df["Task_State"] == "success")]
all_dur = df[df["Duration_Seconds"] > 0]

avg_min  = active["Duration_Minutes"].mean() if len(active) > 0 else 0
max_task = all_dur.nlargest(1, "Duration_Seconds").iloc[0] if len(all_dur) > 0 else None
p95_min  = active["Duration_Minutes"].quantile(0.95) if len(active) > 0 else 0


def fmtd(minutes):
    h = int(minutes // 60)
    m = int(minutes % 60)
    s = int((minutes * 60) % 60)
    if h > 0:
        return f"{h}h {m:02d}m"
    if m > 0:
        return f"{m}m {s:02d}s"
    return f"{s}s"


c1, c2, c3, c4 = st.columns(4, gap="small")
with c1:
    st.markdown(f"""<div class="kpi-mini">
    <div class="val" style="color:#F0481C;">{fmtd(avg_min)}</div>
    <div class="lbl">Duree moyenne (succes)</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi-mini">
    <div class="val" style="color:#EF4444;">{fmtd(p95_min)}</div>
    <div class="lbl">95e percentile</div></div>""", unsafe_allow_html=True)
with c3:
    max_val  = max_task["Duration_Minutes"] if max_task is not None else 0
    max_name = max_task["Task_ID"][:16] if max_task is not None else "—"
    st.markdown(f"""<div class="kpi-mini">
    <div class="val" style="color:#8B5CF6;">{fmtd(max_val)}</div>
    <div class="lbl">Duree max · {max_name}</div></div>""", unsafe_allow_html=True)
with c4:
    n_with_dur = len(all_dur)
    st.markdown(f"""<div class="kpi-mini">
    <div class="val" style="color:#05AEEF;">{n_with_dur}</div>
    <div class="lbl">Taches avec duree connue</div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col_l, col_r = st.columns([1, 1], gap="medium")
with col_l:
    st.markdown('<div class="section-title">Distribution des durees</div>', unsafe_allow_html=True)
    st.plotly_chart(duration_histogram(df), use_container_width=True)
with col_r:
    st.markdown('<div class="section-title">Duree par type d\'operateur</div>', unsafe_allow_html=True)
    st.plotly_chart(duration_by_operator(df), use_container_width=True)

st.markdown("---")
st.markdown('<div class="section-title">Taches les plus longues</div>', unsafe_allow_html=True)
top_n = st.slider("Nombre de taches", 5, 30, 15, 5)
st.plotly_chart(slowest_tasks_bar(df, top_n=top_n), use_container_width=True)

st.markdown("---")
st.markdown('<div class="section-title">Durees par DAG</div>', unsafe_allow_html=True)

selected = st.selectbox(
    "Choisir un DAG",
    ["— Tous les DAGs —"] + sorted(df["DAG_ID"].unique()),
    key="perf_dag",
)

src = df[df["Duration_Seconds"] > 0].copy()
if selected != "— Tous les DAGs —":
    src = src[src["DAG_ID"] == selected]

if src.empty:
    st.info("Aucune donnee de duree disponible pour ce DAG.")
else:
    perf_display = src[[
        "DAG_ID", "Task_ID", "Task_State", "Duration_Display", "Duration_Minutes", "Task_Last_Run_Date"
    ]].sort_values("Duration_Minutes", ascending=False).copy()
    perf_display["Task_Last_Run_Date"] = perf_display["Task_Last_Run_Date"].dt.strftime("%Y-%m-%d  %H:%M").fillna("—")
    perf_display.columns = ["DAG", "Tache", "Etat", "Duree", "Min", "Dernier run"]

    st.dataframe(
        perf_display.drop(columns=["Min"]),
        use_container_width=True,
        height=min(500, 38 * len(perf_display) + 40),
        column_config={
            "DAG":         st.column_config.TextColumn("DAG", width="medium"),
            "Tache":       st.column_config.TextColumn("Tache", width="medium"),
            "Etat":        st.column_config.TextColumn("Etat", width="small"),
            "Duree":       st.column_config.TextColumn("Duree", width="small"),
            "Dernier run": st.column_config.TextColumn("Dernier run", width="small"),
        },
        hide_index=True,
    )

with st.sidebar:
    st.markdown("**Performance**")
    st.markdown(f"- Duree moyenne : {fmtd(avg_min)}")
    st.markdown(f"- P95 : {fmtd(p95_min)}")
    if max_task is not None:
        st.markdown(f"- Max : {fmtd(max_task['Duration_Minutes'])}")
        st.markdown(f"  ({max_task['Task_ID'][:20]})")
    st.divider()
    op_avg = (
        df[df["Duration_Seconds"] > 0]
        .groupby("Operator_Type")["Duration_Minutes"]
        .mean()
        .sort_values(ascending=False)
    )
    st.markdown("**Duree moy. par operateur**")
    for op, avg in op_avg.items():
        st.markdown(f"- {op} : {fmtd(avg)}")
