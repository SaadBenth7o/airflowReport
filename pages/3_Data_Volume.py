import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from utils.data_loader import load_data, build_dag_summary
from utils.charts import tasks_treemap, rows_treemap
from utils.theme import (
    apply_theme, kpi_card, section_title, sidebar_shell, page_header,
    styled_column, STATE_FR_COLOR, download_button, align_bottom_row, chart_config,
)

st.set_page_config(page_title="Volume de données · Airflow", page_icon="assets/transparent.png", layout="wide")
apply_theme(st)

df          = load_data()
dag_summary = build_dag_summary()

total_rows      = df["Rows_Affected_Total"].sum()
tasks_with_rows = (df["Rows_Affected_Total"] > 0).sum()
top_task        = df.nlargest(1, "Rows_Affected_Total").iloc[0]
top_dag_rows    = dag_summary.nlargest(1, "Total_Rows").iloc[0]


def fmt(n):
    if n >= 1e9: return f"{n/1e9:.2f}B"
    if n >= 1e6: return f"{n/1e6:.1f}M"
    if n >= 1e3: return f"{n/1e3:.0f}K"
    return str(int(n))


with st.sidebar:
    sidebar_shell(st, active="volume")

page_header(st, "Volume de données")

c1, c2, c3, c4 = st.columns(4, gap="small")
with c1:
    kpi_card(st, "Total lignes traitées", fmt(total_rows),
             sub="volume connu", color="#05AEEF", icon="database")
with c2:
    kpi_card(st, "DAG max", fmt(top_dag_rows["Total_Rows"]),
             sub=top_dag_rows["DAG_ID"][:22], color="#22C55E", icon="hash")
with c3:
    kpi_card(st, "Tâche max", fmt(top_task["Rows_Affected_Total"]),
             sub=top_task["Task_ID"][:22], color="#F0481C", icon="trend")
with c4:
    kpi_card(st, "Tâches avec volume", tasks_with_rows,
             sub="sur " + str(len(df)) + " tâches", color="#151213", icon="layers")

st.markdown("<br>", unsafe_allow_html=True)

# Lecture du general vers le granulaire : le DAG d'abord.
n_dags_vol = int((dag_summary["Total_Rows"] > 0).sum())

with st.container(border=True):
    section_title(st, "Répartition par DAG", color="#05AEEF",
                  right="proportionnel · cliquer un DAG pour voir ses tâches")
    with st.container(key="slider-blue-volume"):
        top_dags = st.slider("Nombre de DAGs à afficher", min_value=5, max_value=n_dags_vol,
                             value=n_dags_vol, step=1, key="vol_top_dags")
    st.plotly_chart(rows_treemap(df, top_n=top_dags), width="stretch",
                    config=chart_config("Répartition par DAG"))

# Comportements de clic des deux treemaps (retour false depuis
# plotly_treemapclick = annule le zoom par defaut de plotly) :
#  - "cih-treemap-static" (Top taches, plat) : clic inerte — zoomer sur
#    une tuile ne ferait que la faire remplir l'ecran ;
#  - "cih-treemap-drill" (Repartition par DAG) : clic sur un DAG = zoom
#    normal vers ses taches ; clic sur une TACHE = retour a la vue de
#    tous les DAGs (via Plotly.restyle si le bundle est expose, sinon en
#    re-cliquant le pathbar racine).
# Relance a chaque rerun Streamlit (les graphiques sont alors recrees).
components.html(
    """
    <script>
    const bind = () => {
        const plots = window.parent.document.querySelectorAll('.js-plotly-plot');
        let nStatic = 0, nDrill = 0;
        plots.forEach(p => {
            const meta = p._fullLayout && p._fullLayout.meta;
            if (meta === 'cih-treemap-static') {
                nStatic++;
                if (!p.__cihBound) {
                    p.on('plotly_treemapclick', () => false);
                    p.__cihBound = true;
                }
            } else if (meta === 'cih-treemap-drill') {
                nDrill++;
                if (!p.__cihBound) {
                    p.on('plotly_treemapclick', ev => {
                        const pt = ev.points && ev.points[0];
                        if (!pt) return;
                        const id = String(pt.id || '');
                        const parent = String(pt.parent || '');
                        const isTask = parent && parent !== '__root__' && id !== '__root__';
                        if (!isTask) return;  // DAG ou racine : zoom par defaut
                        const PL = window.parent.Plotly || window.Plotly;
                        if (PL && PL.restyle) {
                            PL.restyle(p, {level: '__root__'});
                        } else {
                            const root = p.querySelector('.trace.treemap .pathbar path.surface');
                            if (root) ['mousedown', 'mouseup', 'click'].forEach(t =>
                                root.dispatchEvent(new MouseEvent(t, {bubbles: true, cancelable: true})));
                        }
                        return false;
                    });
                    p.__cihBound = true;
                }
            }
        });
        return nStatic > 0 && nDrill > 0;
    };
    const iv = setInterval(() => { if (bind()) clearInterval(iv); }, 400);
    setTimeout(() => clearInterval(iv), 20000);
    </script>
    """,
    height=0,
)

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    section_title(st, "Toutes les tâches avec volume", color="#05AEEF")

    has_rows = df[df["Rows_Affected_Total"] > 0].sort_values("Rows_Affected_Total", ascending=False).copy()
    has_rows["Rows_fmt"] = has_rows["Rows_Affected_Total"].apply(lambda n: f"{int(n):,}")

    with align_bottom_row(st, key="align-bottom-vol"):
        col_f1, col_f2 = st.columns([3.2, 1])
        with col_f1:
            dag_filter = st.multiselect("Filtrer par DAG", sorted(has_rows["DAG_ID"].unique()))
        with col_f2:
            if dag_filter:
                display_copy = has_rows[has_rows["DAG_ID"].isin(dag_filter)]
            else:
                display_copy = has_rows
            download_button(st, display_copy[["DAG_ID", "Task_ID", "Bash_Script_Name", "Rows_fmt", "State_FR", "Task_Last_Run_Date"]].copy(),
                            title="Toutes les tâches avec volume", key="dl_vol_table")

    if dag_filter:
        has_rows = has_rows[has_rows["DAG_ID"].isin(dag_filter)]

    display = has_rows[["DAG_ID", "Task_ID", "Bash_Script_Name", "Rows_fmt", "State_FR", "Task_Last_Run_Date"]].copy()
    display["Task_Last_Run_Date"] = display["Task_Last_Run_Date"].dt.strftime("%Y-%m-%d  %H:%M").fillna("—")
    display.columns = ["DAG", "Tâche", "Script", "Lignes traitées", "État", "Dernier run"]

    # Pas de width= force : les colonnes s'auto-dimensionnent sur leur
    # contenu, plus de va-et-vient horizontal a la souris.
    st.dataframe(
        styled_column(display, "État", STATE_FR_COLOR), width="stretch",
        height=min(580, 38 * len(display) + 40),
        hide_index=True,
    )
    st.caption(f"{len(display)} tâche(s) avec volume")
