import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote
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
.cih-last-run {
    display:inline-flex; align-items:center; gap:8px;
    background:#F5F8FC; border:1px solid #E9E8E8; border-radius:10px;
    padding:8px 14px; font-size:12.5px; color:#4E4B4C;
}
/* ── ligne d'alerte (DAG en echec / upstream_failed) ── */
.cih-alert-row {
    display:flex; align-items:center; gap:12px;
    padding:12px 14px; border-radius:12px; border-left:3px solid;
    margin-bottom:8px;
}
/* Pas de margin-bottom:0 sur :last-child — le conteneur borde ne laisse
   pas toujours une marge interne fiable en bas ; garder la marge sur
   la derniere ligne aussi evite qu'elle touche la bordure de la carte. */
.cih-alert-icon {
    width:34px; height:34px; flex:none; border-radius:9px;
    background:#FFFFFF; display:flex; align-items:center; justify-content:center;
}
.cih-alert-body { min-width:0; flex:1; }
.cih-alert-id {
    font-size:13.5px; font-weight:700; color:#151213;
    font-family:ui-monospace,Menlo,monospace;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
}
.cih-alert-meta { font-size:11.5px; color:#4E4B4C; margin-top:2px; }
.cih-alert-badge {
    font-size:10.5px; font-weight:700; color:#F59E0B; background:#FFFFFF;
    padding:3px 8px; border-radius:999px; flex:none; white-space:nowrap;
}
.cih-alert-go {
    display:flex; align-items:center; justify-content:center; flex:none;
    width:30px; height:30px; border-radius:8px;
    border:1px solid #E9E8E8; background:#FFFFFF;
    text-decoration:none; transition:background .12s, border-color .12s;
}
.cih-alert-go:hover { background:#F5F8FC; border-color:#d8dce4; }
</style>
""", unsafe_allow_html=True)

df          = load_data()
dag_summary = build_dag_summary()
now         = datetime.now()

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

failed_dags   = dag_summary[dag_summary["failed"] > 0].sort_values("failed", ascending=False)
upstream_dags = dag_summary[(dag_summary["upstream_failed"] > 0) & (dag_summary["failed"] == 0)]


def fmt(n):
    if n >= 1e9: return f"{n/1e9:.1f}B"
    if n >= 1e6: return f"{n/1e6:.1f}M"
    if n >= 1e3: return f"{n/1e3:.0f}K"
    return str(int(n))


def render_alert_row(row, kind):
    """Une ligne d'alerte : icone d'etat, DAG, details, badge 'ancien' si
    pertinent, et un bouton qui renvoie vers le detail complet du DAG dans
    DAG Explorer (parametre d'URL repris par la page pour presectionner)."""
    is_failed = kind == "failed"
    last_run_dt = row["Last_Run"]
    last = last_run_dt.strftime("%d/%m  %H:%M") if pd.notna(last_run_dt) else "—"
    age  = (now - last_run_dt.replace(tzinfo=None)).days if pd.notna(last_run_dt) else 9999
    old  = is_failed and age > 7

    if old:
        col, bg = "#F59E0B", "#FFFBEB"
    elif is_failed:
        col, bg = "#EF4444", "#FEF2F2"
    else:
        col, bg = "#F0481C", "#FFF5F0"

    meta = (f"{int(row['failed'])} echec(s) &middot; {int(row['upstream_failed'])} amont"
            if is_failed else f"{int(row['upstream_failed'])} tache(s) bloquee(s)")
    badge = f'<span class="cih-alert-badge">Ancien &middot; {age} j</span>' if old else ""
    dag_href = f"DAG_Explorer?dag={quote(row['DAG_ID'])}"
    state_icon = svg_icon("x" if is_failed else "alert", 16, col)
    chevron_icon = svg_icon("chevron", 15, "#4E4B4C")

    # Construit en une seule ligne HTML (litteraux adjacents concatenes) :
    # une f-string multi-lignes indentee, quand une valeur interpolee est
    # vide (ex: badge=""), produit une ligne blanche que le parseur
    # Markdown lit comme separateur de bloc — ca coupe le HTML en plein
    # milieu et tout le reste (y compris les lignes suivantes) s'affiche
    # en texte brut au lieu d'etre rendu.
    return (
        f'<div class="cih-alert-row" style="background:{bg};border-left-color:{col};">'
        f'<div class="cih-alert-icon">{state_icon}</div>'
        f'<div class="cih-alert-body">'
        f'<div class="cih-alert-id">{row["DAG_ID"]}</div>'
        f'<div class="cih-alert-meta">{meta} &middot; {last}</div>'
        f'</div>'
        f'{badge}'
        f'<a class="cih-alert-go" href="{dag_href}" target="_self" title="Voir le detail du DAG">{chevron_icon}</a>'
        f'</div>'
    )


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
        section_title(st, "DAGs avec le plus d'echecs", color="#EF4444",
                      right=f"{len(failed_dags)} DAG(s) concernes")
        if failed_dags.empty:
            st.success("Aucun DAG en echec.")
        else:
            st.plotly_chart(dag_failures_bar(dag_summary), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Alertes ──────────────────────────────────────────────────────────────
section_title(st, "Alertes actives", color="#EF4444")

if failed_dags.empty and upstream_dags.empty:
    st.success("Aucune alerte — tous les DAGs fonctionnent normalement.")
else:
    col_a, col_b = st.columns([2, 1], gap="medium")
    with col_a:
        with st.container(border=True):
            section_title(st, f"{len(failed_dags)} DAG(s) avec des taches en echec", color="#EF4444")
            if failed_dags.empty:
                st.caption("Aucune tache en echec.")
            else:
                st.markdown(
                    "".join(render_alert_row(row, "failed") for _, row in failed_dags.iterrows()),
                    unsafe_allow_html=True,
                )
    with col_b:
        with st.container(border=True):
            section_title(st, f"{len(upstream_dags)} DAG(s) avec dependances bloquees", color="#F0481C")
            if upstream_dags.empty:
                st.caption("Aucune dependance bloquee.")
            else:
                st.markdown(
                    "".join(render_alert_row(row, "upstream") for _, row in upstream_dags.iterrows()),
                    unsafe_allow_html=True,
                )
