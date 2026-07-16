import streamlit as st
import pandas as pd
from utils.data_loader import load_data, build_dag_summary
from utils.charts import dag_task_composition, success_rate_gauge
from utils.cron_fr import describe_cron
from utils.theme import (
    apply_theme, section_title, sidebar_shell, page_header, svg_icon,
    styled_column, STATE_FR_COLOR, download_button, chart_config, align_right, plotly_export_js,
)

st.set_page_config(page_title="DAG Explorer · Airflow", page_icon="assets/transparent.png", layout="wide")
apply_theme(st)

df          = load_data()
dag_summary = build_dag_summary()


def fmt(n):
    if n >= 1e9: return f"{n/1e9:.2f}B"
    if n >= 1e6: return f"{n/1e6:.1f}M"
    if n >= 1e3: return f"{n/1e3:.0f}K"
    return str(int(n))


with st.sidebar:
    sidebar_shell(st, active="explorer")

page_header(st, "DAG Explorer",
            "Exploration détaillée de chaque pipeline de données.")

# ── Filtres ──────────────────────────────────────────────────────────────
with st.container(border=True):
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1], gap="medium")
    with col_f1:
        search = st.text_input("Rechercher un DAG", placeholder="Nom du DAG…")
    with col_f2:
        sched_options = ["Tous"] + sorted(dag_summary["Schedule_Category"].unique())
        sched_filter  = st.selectbox("Fréquence", sched_options)
    with col_f3:
        sort_map   = {"Échecs": "failed", "Taux de succès": "Success_Rate",
                      "Volume": "Total_Rows", "Tâches": "Total_Tasks", "Nom": "DAG_ID"}
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

sel_id  = st.session_state["dag_explorer_sel"]
dag_row = dag_summary[dag_summary["DAG_ID"] == sel_id].iloc[0]
dag_df  = df[df["DAG_ID"] == sel_id]

# ── Master (liste) / Detail — puis tableau des taches en pleine largeur ──
# La liste est dimensionnee pour se terminer au meme niveau que la rangee
# Composition / Fiabilite ; le tableau "Taches du DAG" occupe ensuite
# toute la largeur de la page au lieu d'etre coince sous le detail.
LIST_HEIGHT = 430

col_list, col_detail = st.columns([1, 2.3], gap="medium")

with col_list:
    with st.container(border=True):
        section_title(st, "DAGs", right=f"{len(list_view)} / {len(dag_summary)}")
        st.markdown('<div class="cih-daglist">', unsafe_allow_html=True)
        with st.container(height=LIST_HEIGHT):
            if list_view.empty:
                st.caption("Aucun DAG ne correspond à ces filtres.")
            for _, d in list_view.iterrows():
                dag_id   = d["DAG_ID"]
                selected = dag_id == st.session_state["dag_explorer_sel"]
                dot = ("red" if d["failed"] > 0 else
                       "orange" if d["upstream_failed"] > 0 else
                       "blue" if d["running"] > 0 else "green")
                rate_c = ("green" if d["Success_Rate"] >= 80 else
                          "orange" if d["Success_Rate"] >= 50 else "red")
                meta = (f"{int(d['Total_Tasks'])} tâches &middot; "
                        f"{d['Schedule_Category']} &middot; ")
                if selected:
                    # Bouton primaire = fond orange, texte blanc : les
                    # directives :couleur[...] y sont illisibles (rouge sur
                    # orange) — texte brut uniquement.
                    label = f"● **{dag_id}**  \n{meta}{d['Success_Rate']:.0f}%"
                else:
                    label = (f":{dot}[●] **{dag_id}**  \n"
                             f"{meta}:{rate_c}[{d['Success_Rate']:.0f}%]")
                if st.button(label, key=f"dagbtn_{dag_id}", width="stretch",
                             type="primary" if selected else "secondary"):
                    st.session_state["dag_explorer_sel"] = dag_id
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with col_detail:
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
            # La planification est affichee en clair (convertie depuis le
            # cron) ; l'expression brute reste accessible au survol.
            sched_txt = describe_cron(dag_row["Schedule_Cron"])
            st.markdown(
                f'<div style="display:flex;gap:16px;margin-top:8px;margin-right:4px;'
                f'margin-bottom:10px;flex-wrap:wrap;max-width:100%;font-size:12.5px;color:#4E4B4C;">'
                f'<span style="display:flex;align-items:center;gap:6px;white-space:nowrap;">'
                f'{owner_icon}{dag_row["Owner"]}</span>'
                f'<span style="display:flex;align-items:center;gap:6px;white-space:nowrap;">'
                f'{calendar_icon}{dag_row["Schedule_Category"]}</span>'
                f'<span title="{dag_row["Schedule_Cron"]}" style="background:#F5F8FC;'
                f'border:1px solid #E9E8E8;border-radius:6px;padding:2px 8px;color:#151213;'
                f'white-space:nowrap;">'
                f'{sched_txt}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_h2:
            st.markdown(
                f'<div style="text-align:right;">'
                f'<div style="font-size:11px;color:#9AA0A8;font-weight:600;">Lignes traitées</div>'
                f'<div style="font-size:22px;font-weight:800;color:#F0481C;'
                f'font-variant-numeric:tabular-nums;">{fmt(dag_row["Total_Rows"])}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Hauteurs 320 : les bas de Composition et Fiabilite s'alignent sur le
    # bas de la carte DAGs (liste de gauche) — valeurs mesurees en reel.
    col_comp, col_gauge = st.columns([1.3, 1], gap="medium")
    with col_comp:
        with st.container(border=True):
            section_title(st, "Composition des tâches", color="#05AEEF")
            st.plotly_chart(dag_task_composition(df, sel_id, height=320), width="stretch",
                            config=chart_config(f"Composition des tâches - {sel_id}"))
    with col_gauge:
        with st.container(border=True):
            section_title(st, "Fiabilité", color="#22C55E")
            st.plotly_chart(success_rate_gauge(dag_row["Success_Rate"], height=320), width="stretch",
                            config=chart_config(f"Fiabilité - {sel_id}"))

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    section_title(st, "Tâches du DAG", color="#F0481C", right=f"{sel_id} &middot; {len(dag_df)} tâches")
    task_display = dag_df[[
        "Task_ID", "Operator_Type", "Bash_Script_Name",
        "State_FR", "Task_Last_Run_Date", "Duration_Display", "Rows_Affected_Total"
    ]].copy()
    task_display["Task_Last_Run_Date"] = task_display["Task_Last_Run_Date"].dt.strftime("%Y-%m-%d  %H:%M").fillna("—")
    task_display["Rows_Affected_Total"] = task_display["Rows_Affected_Total"].apply(lambda n: f"{int(n):,}")
    task_display.columns = ["Tâche", "Opérateur", "Script", "État", "Dernier run", "Durée", "Lignes"]

    with align_right(st, key="align-right-dag-explorer"):
        download_button(st, task_display, title=f"Tâches du DAG {sel_id}", key="dl_dag_explorer")

    st.dataframe(
        styled_column(task_display, "État", STATE_FR_COLOR), width="stretch",
        height=min(500, 38 * len(task_display) + 40),
        hide_index=True,
    )

plotly_export_js(st)
