import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_loader import load_data, build_dag_summary
from utils.charts import state_donut, dag_failures_bar, state_distribution_segments
from utils.theme import (
    apply_theme, kpi_card, section_title, sidebar_shell, page_header,
    svg_icon, donut_legend,
)

st.set_page_config(
    page_title="CIH Bank · Airflow Report",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme(st)

st.markdown("""
<style>
.alert-card {
    background:#FEF2F2; border-left:4px solid #EF4444;
    border-radius:12px; padding:13px 16px; margin-bottom:8px;
}
.alert-card.upstream { background:#FFF5F0; border-left-color:#F0481C; }
.alert-card.old      { background:#FFFBEB; border-left-color:#F59E0B; }
.alert-title { font-weight:700; font-size:13px; color:#151213; }
.alert-meta  { font-size:12px; color:#4E4B4C; margin-top:3px; line-height:1.4; }
.cih-last-run {
    display:inline-flex; align-items:center; gap:8px;
    background:#F5F8FC; border:1px solid #E9E8E8; border-radius:10px;
    padding:8px 14px; font-size:12.5px; color:#4E4B4C;
}
</style>
""", unsafe_allow_html=True)

df          = load_data()
dag_summary = build_dag_summary()

last_run     = df["Task_Last_Run_Date"].max()
last_run_str = last_run.strftime("%d/%m/%Y  %H:%M") if pd.notna(last_run) else "N/A"

total_dags     = df["DAG_ID"].nunique()
total_tasks    = len(df)
total_success  = (df["Task_State"] == "success").sum()
total_failed   = (df["Task_State"] == "failed").sum()
total_upstream = (df["Task_State"] == "upstream_failed").sum()
total_skipped  = (df["Task_State"] == "skipped").sum()
total_running  = (df["Task_State"] == "running").sum()
success_rate   = round(total_success / total_tasks * 100, 1)
total_rows     = df["Rows_Affected_Total"].sum()
total_problems = total_failed + total_upstream
n_ok           = int((~dag_summary["Has_Failure"]).sum())
n_ko           = int(dag_summary["Has_Failure"].sum())
sante          = "Sain" if total_problems == 0 else ("Critique" if total_problems >= 10 else "Degrade")


def fmt(n):
    if n >= 1e9: return f"{n/1e9:.1f}B"
    if n >= 1e6: return f"{n/1e6:.1f}M"
    if n >= 1e3: return f"{n/1e3:.0f}K"
    return str(int(n))


# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    sidebar_shell(st, active="overview", health_label=sante, n_ok=n_ok, n_ko=n_ko)

# ── Header ───────────────────────────────────────────────────────────────
col_hdr, col_badge = st.columns([4, 1])
with col_hdr:
    page_header(
        st,
        title="Vue d'ensemble",
        subtitle="Supervision en temps reel de la plateforme de donnees CIH Bank.",
    )
with col_badge:
    st.markdown(
        f'<div class="cih-last-run" style="margin-top:10px;">'
        f'{svg_icon("clock", 14, "#4E4B4C")}'
        f'<div><div style="font-size:10px;color:#9AA0A8;font-weight:600;">Derniere execution</div>'
        f'<div style="font-weight:700;color:#151213;">{last_run_str}</div></div></div>',
        unsafe_allow_html=True,
    )

# ── KPI cards ────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5, gap="small")
with c1:
    kpi_card(st, "DAGs actifs", total_dags,
             sub=f"{total_tasks} taches au total",
             color="#05AEEF", icon="branch")
with c2:
    kpi_card(st, "Taux de succes", f"{success_rate}%",
             sub=f"{total_success} reussies",
             color="#22C55E", icon="check")
with c3:
    kpi_card(st, "Echecs", total_failed,
             sub=f"{total_upstream} upstream failed",
             color="#EF4444", icon="alert")
with c4:
    kpi_card(st, "Ignorees", total_skipped,
             sub=f"{total_running} en cours",
             color="#F59E0B", icon="zap")
with c5:
    kpi_card(st, "Lignes traitees", fmt(total_rows),
             sub="depuis le 01/01/2026",
             color="#F0481C", icon="database")

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ───────────────────────────────────────────────────────────────
col_l, col_r = st.columns([1, 1.45], gap="medium")
with col_l:
    with st.container(border=True):
        section_title(st, "Distribution des etats", color="#05AEEF")
        c_donut, c_legend = st.columns([1, 1])
        with c_donut:
            st.plotly_chart(state_donut(df), use_container_width=True)
        with c_legend:
            st.markdown("<div style='padding-top:24px;'></div>", unsafe_allow_html=True)
            donut_legend(st, state_distribution_segments(df))
with col_r:
    with st.container(border=True):
        section_title(st, "DAGs avec le plus d'echecs", color="#EF4444")
        st.plotly_chart(dag_failures_bar(dag_summary), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Alertes ──────────────────────────────────────────────────────────────
section_title(st, "Alertes actives", color="#EF4444")

failed_dags   = dag_summary[dag_summary["failed"] > 0].sort_values("failed", ascending=False)
upstream_dags = dag_summary[(dag_summary["upstream_failed"] > 0) & (dag_summary["failed"] == 0)]
now           = datetime.now()

if failed_dags.empty and upstream_dags.empty:
    st.success("Aucune alerte — tous les DAGs fonctionnent normalement.")
else:
    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        if not failed_dags.empty:
            st.markdown(f"**{len(failed_dags)} DAG(s) en echec**")
            for _, row in failed_dags.iterrows():
                last = row["Last_Run"].strftime("%d/%m  %H:%M") if pd.notna(row["Last_Run"]) else "—"
                age  = (now - row["Last_Run"].replace(tzinfo=None)).days if pd.notna(row["Last_Run"]) else 9999
                cls  = "old" if age > 7 else ""
                note = f'<span style="color:#F59E0B;font-size:11px;"> · Echec ancien ({age}j)</span>' if age > 7 else ""
                st.markdown(f"""
                <div class="alert-card {cls}">
                  <div class="alert-title">{row['DAG_ID']}{note}</div>
                  <div class="alert-meta">{int(row['failed'])} echec(s) &middot; {int(row['upstream_failed'])} upstream &middot; {last}</div>
                </div>""", unsafe_allow_html=True)
    with col_b:
        if not upstream_dags.empty:
            st.markdown(f"**{len(upstream_dags)} DAG(s) upstream_failed**")
            for _, row in upstream_dags.iterrows():
                last = row["Last_Run"].strftime("%d/%m  %H:%M") if pd.notna(row["Last_Run"]) else "—"
                st.markdown(f"""
                <div class="alert-card upstream">
                  <div class="alert-title">{row['DAG_ID']}</div>
                  <div class="alert-meta">{int(row['upstream_failed'])} tache(s) bloquee(s) en amont &middot; {last}</div>
                </div>""", unsafe_allow_html=True)
