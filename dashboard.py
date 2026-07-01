import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_loader import load_data, build_dag_summary
from utils.charts import state_donut, dag_failures_bar
from utils.theme import apply_theme, kpi_card, section_title

st.set_page_config(
    page_title="CIH Bank · Airflow Report",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme(st)

st.markdown("""
<style>
.dash-header {
    background:linear-gradient(135deg,#FFFFFF 0%,#F5F8FC 100%);
    border:1px solid #E9E8E8; border-radius:12px;
    padding:20px 28px; margin-bottom:22px;
    display:flex; align-items:center; justify-content:space-between;
}
.dash-title { font-size:1.5rem; font-weight:800; color:#151213; margin:0; letter-spacing:-.02em; }
.dash-sub   { font-size:0.82rem; color:#4E4B4C; margin:4px 0 0 0; }
.dash-badge {
    background:#F5F8FC; border:1px solid #E9E8E8; border-radius:10px;
    padding:10px 16px; font-size:0.82rem; color:#4E4B4C; text-align:right;
}
.alert-card {
    background:#FEF2F2; border-left:4px solid #EF4444;
    border-radius:8px; padding:12px 16px; margin-bottom:8px;
}
.alert-card.upstream { background:#FFF5F0; border-left-color:#F0481C; }
.alert-card.old      { background:#FFFBEB; border-left-color:#F59E0B; }
.alert-title { font-weight:600; font-size:0.90rem; color:#151213; }
.alert-meta  { font-size:0.78rem; color:#4E4B4C; margin-top:2px; }
</style>
""", unsafe_allow_html=True)

df          = load_data()
dag_summary = build_dag_summary()

last_run     = df["Task_Last_Run_Date"].max()
last_run_str = last_run.strftime("%d/%m/%Y  %H:%M") if pd.notna(last_run) else "N/A"

st.markdown(f"""
<div class="dash-header">
  <div>
    <p class="dash-title">Airflow DAG Report &mdash; 2026</p>
    <p class="dash-sub">CIH Bank &middot; Data Platform Monitoring</p>
  </div>
  <div class="dash-badge">
    Derniere execution<br>
    <strong style="font-size:1rem;color:#151213;">{last_run_str}</strong>
  </div>
</div>
""", unsafe_allow_html=True)

total_dags     = df["DAG_ID"].nunique()
total_tasks    = len(df)
total_success  = (df["Task_State"] == "success").sum()
total_failed   = (df["Task_State"] == "failed").sum()
total_upstream = (df["Task_State"] == "upstream_failed").sum()
total_skipped  = (df["Task_State"] == "skipped").sum()
total_running  = (df["Task_State"] == "running").sum()
success_rate   = round(total_success / total_tasks * 100, 1)
total_rows     = df["Rows_Affected_Total"].sum()


def fmt(n):
    if n >= 1e9: return f"{n/1e9:.1f}B"
    if n >= 1e6: return f"{n/1e6:.1f}M"
    if n >= 1e3: return f"{n/1e3:.0f}K"
    return str(int(n))


c1, c2, c3, c4, c5 = st.columns(5, gap="small")
with c1:
    kpi_card(st, "DAGs actifs", total_dags,
             sub=f"{total_tasks} taches au total", color="#05AEEF")
with c2:
    kpi_card(st, "Taux de succes", f"{success_rate}%",
             sub=f"{total_success} taches reussies", color="#22C55E")
with c3:
    kpi_card(st, "Echecs", total_failed,
             sub=f"{total_upstream} upstream failed", color="#EF4444")
with c4:
    kpi_card(st, "Ignorees / En cours", total_skipped,
             sub=f"{total_running} en cours d'execution", color="#F59E0B")
with c5:
    kpi_card(st, "Lignes traitees", fmt(total_rows),
             sub="depuis le 01/01/2026", color="#F0481C")

st.markdown("<br>", unsafe_allow_html=True)

col_l, col_r = st.columns([1, 1.45], gap="medium")
with col_l:
    st.plotly_chart(state_donut(df), use_container_width=True)
with col_r:
    st.plotly_chart(dag_failures_bar(dag_summary), use_container_width=True)

section_title(st, "Alertes actives", color="#EF4444")

failed_dags   = dag_summary[dag_summary["failed"] > 0].sort_values("failed", ascending=False)
upstream_dags = dag_summary[(dag_summary["upstream_failed"] > 0) & (dag_summary["failed"] == 0)]
now           = datetime.now()

if failed_dags.empty and upstream_dags.empty:
    st.success("Aucune alerte — tous les DAGs fonctionnent normalement.")
else:
    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        st.markdown(f"**{len(failed_dags)} DAG(s) avec des taches en echec**")
        for _, row in failed_dags.iterrows():
            last = row["Last_Run"].strftime("%d/%m  %H:%M") if pd.notna(row["Last_Run"]) else "—"
            age  = (now - row["Last_Run"].replace(tzinfo=None)).days if pd.notna(row["Last_Run"]) else 9999
            cls  = "old" if age > 7 else ""
            note = f"<span style='color:#F59E0B;font-size:0.75rem;'> Echec ancien ({age}j)</span>" if age > 7 else ""
            st.markdown(f"""
            <div class="alert-card {cls}">
              <div class="alert-title">{row['DAG_ID']} {note}</div>
              <div class="alert-meta">{int(row['failed'])} echec(s) &middot; {int(row['upstream_failed'])} upstream &middot; Dernier run : {last}</div>
            </div>""", unsafe_allow_html=True)

    with col_b:
        if not upstream_dags.empty:
            st.markdown(f"**{len(upstream_dags)} DAG(s) avec upstream_failed**")
            for _, row in upstream_dags.iterrows():
                last = row["Last_Run"].strftime("%d/%m  %H:%M") if pd.notna(row["Last_Run"]) else "—"
                st.markdown(f"""
                <div class="alert-card upstream">
                  <div class="alert-title">{row['DAG_ID']}</div>
                  <div class="alert-meta">{int(row['upstream_failed'])} tache(s) bloquee(s) en amont &middot; {last}</div>
                </div>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("**Airflow Dashboard**")
    st.caption("CIH Bank · Data Platform")
    st.divider()
    total_problems = total_failed + total_upstream
    sante = "Sain" if total_problems == 0 else ("Degrade" if total_problems < 10 else "Critique")
    st.markdown(f"**Sante globale :** {sante}")
    st.markdown(f"**DAGs :** {total_dags} actifs")
    st.markdown(f"**Taches :** {total_tasks} ({total_failed + total_upstream} en erreur)")
    st.markdown(f"**Derniere maj :** {last_run_str}")
    st.divider()
    st.markdown("**Navigation**")
    st.markdown("- Vue d'ensemble\n- Failures\n- DAG Explorer\n- Data Volume\n- Performance\n- Schedule")
