import streamlit as st
import pandas as pd
from utils.data_loader import load_data, build_dag_summary
from utils.charts import dag_task_composition, success_rate_gauge
from utils.theme import (
    apply_theme, section_title, sidebar_shell, page_header, svg_icon,
    styled_column, STATE_RAW_COLOR,
)

st.set_page_config(page_title="DAG Explorer · Airflow", page_icon=None, layout="wide")
apply_theme(st)

df          = load_data()
dag_summary = build_dag_summary()
n_ok        = int((~dag_summary["Has_Failure"]).sum())
n_ko        = int(dag_summary["Has_Failure"].sum())
sante       = "Sain" if n_ko == 0 else ("Critique" if n_ko > 5 else "Degrade")


def fmt(n):
    if n >= 1e9: return f"{n/1e9:.2f}B"
    if n >= 1e6: return f"{n/1e6:.1f}M"
    if n >= 1e3: return f"{n/1e3:.0f}K"
    return str(int(n))


with st.sidebar:
    sidebar_shell(st, active="explorer", health_label=sante, n_ok=n_ok, n_ko=n_ko)

page_header(st, "DAG Explorer",
            "Exploration detaillee de chaque pipeline de donnees.")

# ── Filtres ──────────────────────────────────────────────────────────────
with st.container(border=True):
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1], gap="medium")
    with col_f1:
        search = st.text_input("Rechercher un DAG", placeholder="Nom du DAG…")
    with col_f2:
        sched_options = ["Tous"] + sorted(dag_summary["Schedule_Category"].unique())
        sched_filter  = st.selectbox("Frequence", sched_options)
    with col_f3:
        sort_map   = {"Echecs": "failed", "Taux de succes": "Success_Rate",
                      "Volume": "Total_Rows", "Taches": "Total_Tasks", "Nom": "DAG_ID"}
        sort_label = st.selectbox("Trier par", list(sort_map.keys()))
        sort_by    = sort_map[sort_label]

list_view = dag_summary.copy()
if search:
    list_view = list_view[list_view["DAG_ID"].str.contains(search, case=False, na=False)]
if sched_filter != "Tous":
    list_view = list_view[list_view["Schedule_Category"] == sched_filter]
ascending = sort_by in ("DAG_ID", "Success_Rate")
list_view = list_view.sort_values(sort_by, ascending=ascending)

# Arrivee depuis un lien "voir le detail" (ex: alertes de la Vue
# d'ensemble) : le DAG cible est passe en parametre d'URL et prend
# priorite sur la selection precedente.
qp_dag = st.query_params.get("dag")
if qp_dag and qp_dag in dag_summary["DAG_ID"].values:
    st.session_state["dag_explorer_sel"] = qp_dag
    del st.query_params["dag"]
elif "dag_explorer_sel" not in st.session_state or \
        st.session_state["dag_explorer_sel"] not in dag_summary["DAG_ID"].values:
    st.session_state["dag_explorer_sel"] = (
        list_view.iloc[0]["DAG_ID"] if len(list_view) else dag_summary.iloc[0]["DAG_ID"]
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Master (liste) / Detail ─────────────────────────────────────────────
col_list, col_detail = st.columns([1, 2.3], gap="medium")

with col_list:
    with st.container(border=True):
        section_title(st, "DAGs", right=f"{len(list_view)} / {len(dag_summary)}")
        st.markdown('<div class="cih-daglist">', unsafe_allow_html=True)
        with st.container(height=560):
            if list_view.empty:
                st.caption("Aucun DAG ne correspond a ces filtres.")
            for _, d in list_view.iterrows():
                dag_id   = d["DAG_ID"]
                selected = dag_id == st.session_state["dag_explorer_sel"]
                dot = ("red" if d["failed"] > 0 else
                       "orange" if d["upstream_failed"] > 0 else
                       "blue" if d["running"] > 0 else "green")
                rate_c = ("green" if d["Success_Rate"] >= 80 else
                          "orange" if d["Success_Rate"] >= 50 else "red")
                label = (f":{dot}[●] **{dag_id}**  \n"
                         f"{int(d['Total_Tasks'])} taches &middot; {d['Schedule_Category']} &middot; "
                         f":{rate_c}[{d['Success_Rate']:.0f}%]")
                if st.button(label, key=f"dagbtn_{dag_id}", use_container_width=True,
                             type="primary" if selected else "secondary"):
                    st.session_state["dag_explorer_sel"] = dag_id
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with col_detail:
    sel_id  = st.session_state["dag_explorer_sel"]
    dag_row = dag_summary[dag_summary["DAG_ID"] == sel_id].iloc[0]
    dag_df  = df[df["DAG_ID"] == sel_id]

    with st.container(border=True):
        col_h1, col_h2 = st.columns([2.2, 1])
        with col_h1:
            st.markdown(
                f"<div style='font-size:19px;font-weight:800;"
                f"font-family:ui-monospace,Menlo,monospace;letter-spacing:-.01em;'>{sel_id}</div>",
                unsafe_allow_html=True,
            )
            owner_icon    = svg_icon("user", 14, "#9AA0A8")
            calendar_icon = svg_icon("calendar", 14, "#9AA0A8")
            st.markdown(
                f'<div style="display:flex;gap:16px;margin-top:8px;margin-right:4px;'
                f'flex-wrap:wrap;max-width:100%;font-size:12.5px;color:#4E4B4C;">'
                f'<span style="display:flex;align-items:center;gap:6px;white-space:nowrap;">'
                f'{owner_icon}{dag_row["Owner"]}</span>'
                f'<span style="display:flex;align-items:center;gap:6px;white-space:nowrap;">'
                f'{calendar_icon}{dag_row["Schedule_Category"]}</span>'
                f'<span style="font-family:ui-monospace,Menlo,monospace;background:#F5F8FC;'
                f'border:1px solid #E9E8E8;border-radius:6px;padding:2px 8px;color:#151213;'
                f'white-space:nowrap;">'
                f'{dag_row["Schedule_Cron"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_h2:
            st.markdown(
                f'<div style="text-align:right;">'
                f'<div style="font-size:11px;color:#9AA0A8;font-weight:600;">Lignes traitees</div>'
                f'<div style="font-size:22px;font-weight:800;color:#F0481C;font-variant-numeric:tabular-nums;">'
                f'{fmt(dag_row["Total_Rows"])}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    col_comp, col_gauge = st.columns([1.3, 1], gap="medium")
    with col_comp:
        with st.container(border=True):
            section_title(st, "Composition des taches", color="#05AEEF")
            st.plotly_chart(dag_task_composition(df, sel_id), use_container_width=True)
    with col_gauge:
        with st.container(border=True):
            section_title(st, "Fiabilite", color="#22C55E")
            st.plotly_chart(success_rate_gauge(dag_row["Success_Rate"]), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        section_title(st, "Taches du DAG", color="#F0481C", right=f"{len(dag_df)} taches")
        task_display = dag_df[[
            "Task_ID", "Operator_Type", "Bash_Script_Name",
            "Task_State", "Task_Last_Run_Date", "Duration_Display", "Rows_Affected_Total"
        ]].copy()
        task_display["Task_Last_Run_Date"] = task_display["Task_Last_Run_Date"].dt.strftime("%Y-%m-%d  %H:%M").fillna("—")
        task_display["Rows_Affected_Total"] = task_display["Rows_Affected_Total"].apply(
            lambda n: f"{int(n):,}" if n > 0 else "—"
        )
        task_display.columns = ["Tache", "Operateur", "Script", "Etat", "Dernier run", "Duree", "Lignes"]
        st.dataframe(
            styled_column(task_display, "Etat", STATE_RAW_COLOR), use_container_width=True,
            height=min(500, 38 * len(task_display) + 40),
            column_config={
                "Tache":       st.column_config.TextColumn("Tache", width="medium"),
                "Operateur":   st.column_config.TextColumn("Operateur", width="small"),
                "Script":      st.column_config.TextColumn("Script", width="medium"),
                "Dernier run": st.column_config.TextColumn("Dernier run", width="small"),
                "Duree":       st.column_config.TextColumn("Duree", width="small"),
                "Lignes":      st.column_config.TextColumn("Lignes", width="small"),
            },
            hide_index=True,
        )
