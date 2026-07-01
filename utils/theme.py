"""
Charte visuelle CIH Bank — refonte UI du dashboard Airflow.

Un seul point d'entrée : `apply_theme(st)`, à appeler tout en haut de
`dashboard.py` (après `st.set_page_config`). Injecte le CSS premium qui
aligne l'app Streamlit sur la maquette validée (palette CIH obligatoire :
orange #F0481C, bleu #05AEEF, texte #151213/#4E4B4C, bordure #E9E8E8,
fond #F5F8FC ; rouge réservé aux échecs et alertes).

Helpers fournis :
    apply_theme(st)                     -> injecte le CSS + la police Inter
    kpi_card(st, label, value, ...)     -> tuile KPI stylée
    section_title(st, txt, color=None)  -> titre de section avec barre
    status_pill(state)                  -> HTML d'un badge d'état (à passer
                                           dans st.markdown(..., unsafe_allow_html=True))
"""

# ----------------------------------------------------------------------
# Palette CIH — source unique de vérité côté front
# ----------------------------------------------------------------------
CIH = {
    "orange":      "#F0481C",
    "orange_dk":   "#D63A12",
    "orange_soft": "#FFF1EC",
    "blue":        "#05AEEF",
    "blue_soft":   "#E7F7FE",
    "ink":         "#151213",
    "ink2":        "#4E4B4C",
    "muted":       "#9AA0A8",
    "border":      "#E9E8E8",
    "line":        "#EEF1F5",
    "bg":          "#F5F8FC",
    "surface":     "#FFFFFF",
    "green":       "#22C55E",
    "green_soft":  "#F0FDF4",
    "red":         "#EF4444",
    "red_soft":    "#FEF2F2",
    "amber":       "#F59E0B",
    "amber_soft":  "#FFFBEB",
}

# Couleurs d'état (identiques à utils/data_loader.STATE_COLORS)
STATE_FR = {
    "success":         ("Succès",      CIH["green"], CIH["green_soft"]),
    "failed":          ("Échec",       CIH["red"],   CIH["red_soft"]),
    "skipped":         ("Ignorée",     CIH["amber"], CIH["amber_soft"]),
    "upstream_failed": ("Échec amont", CIH["orange"],CIH["orange_soft"]),
    "running":         ("En cours",    CIH["blue"],  CIH["blue_soft"]),
}


def apply_theme(st):
    """Injecte le CSS global. À appeler une fois, après set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def section_title(st, txt, color=None):
    color = color or CIH["orange"]
    st.markdown(
        f'<div class="cih-section">'
        f'<span style="background:{color}"></span>{txt}</div>',
        unsafe_allow_html=True,
    )


def status_pill(state):
    label, c, bg = STATE_FR.get(state, (state, CIH["muted"], CIH["bg"]))
    return (
        f'<span class="cih-pill" style="color:{c};background:{bg}">'
        f'<i style="background:{c}"></i>{label}</span>'
    )


def kpi_card(st, label, value, sub="", color=None, delta=None, delta_up=True):
    """Tuile KPI. `delta` ex : '+3,2 %' ; `delta_up` colore vert/rouge."""
    color = color or CIH["orange"]
    delta_html = ""
    if delta:
        dc = CIH["green"] if delta_up else CIH["red"]
        arrow = "▲" if delta_up else "▼"
        delta_html = (
            f'<span class="cih-kpi-delta" style="color:{dc}">'
            f'{arrow} {delta}</span>'
        )
    st.markdown(
        f'''<div class="cih-kpi">
              <div class="cih-kpi-label">{label}</div>
              <div class="cih-kpi-value" style="color:{color}">{value}</div>
              <div class="cih-kpi-sub">{delta_html}{sub}</div>
            </div>''',
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------
# CSS — mirroir de la maquette premium
# ----------------------------------------------------------------------
_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ---- base ---- */
html, body, [class*="css"], .stApp {{
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    color: {CIH['ink']};
}}
.stApp {{ background: {CIH['bg']}; }}
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1320px; }}

/* Masque le chrome Streamlit par défaut */
#MainMenu, footer, header[data-testid="stHeader"] {{ visibility: hidden; height: 0; }}

/* ---- titres ---- */
h1 {{ font-weight: 800; letter-spacing: -.02em; color: {CIH['ink']}; }}
h2, h3 {{ font-weight: 700; letter-spacing: -.01em; color: {CIH['ink']}; }}

/* ---- barre latérale ---- */
[data-testid="stSidebar"] {{
    background: {CIH['surface']};
    border-right: 1px solid {CIH['border']};
}}
[data-testid="stSidebar"] .block-container {{ padding-top: 1.4rem; }}

/* ---- boutons de navigation (st.radio / st.page_link) ---- */
[data-testid="stSidebar"] .stRadio > label,
[data-testid="stSidebar"] label {{ font-weight: 600; color: {CIH['ink2']}; }}

/* ---- boutons ---- */
.stButton > button {{
    border-radius: 10px;
    border: 1px solid {CIH['orange']};
    background: {CIH['orange']};
    color: #fff;
    font-weight: 700;
    padding: .5rem 1rem;
    box-shadow: 0 2px 6px rgba(240,72,28,.25);
    transition: background .14s, transform .1s;
}}
.stButton > button:hover {{ background: {CIH['orange_dk']}; color: #fff; border-color: {CIH['orange_dk']}; }}
.stButton > button:active {{ transform: translateY(1px); }}

/* ---- KPI natif st.metric ---- */
[data-testid="stMetric"] {{
    background: {CIH['surface']};
    border: 1px solid {CIH['border']};
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 1px 2px rgba(21,18,19,.04);
}}
[data-testid="stMetricValue"] {{ font-weight: 800; letter-spacing: -.02em; color: {CIH['ink']}; }}
[data-testid="stMetricLabel"] {{
    font-size: 10.5px; font-weight: 700; letter-spacing: .09em;
    text-transform: uppercase; color: {CIH['ink2']};
}}

/* ---- tuile KPI custom (kpi_card) ---- */
.cih-kpi {{
    background: {CIH['surface']};
    border: 1px solid {CIH['border']};
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 1px 2px rgba(21,18,19,.04);
    transition: box-shadow .18s, transform .18s, border-color .18s;
}}
.cih-kpi:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(21,18,19,.08);
    border-color: #dfe3ea;
}}
.cih-kpi-label {{
    font-size: 10.5px; font-weight: 700; letter-spacing: .09em;
    text-transform: uppercase; color: {CIH['ink2']}; margin-bottom: 8px;
}}
.cih-kpi-value {{ font-size: 32px; font-weight: 800; line-height: 1; letter-spacing: -.02em; }}
.cih-kpi-sub {{ font-size: 11.5px; color: {CIH['ink2']}; margin-top: 8px; display: flex; gap: 6px; align-items: center; }}
.cih-kpi-delta {{ font-weight: 700; }}

/* ---- cartes / conteneurs (st.container(border=True)) ---- */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {CIH['surface']};
    border: 1px solid {CIH['border']} !important;
    border-radius: 16px;
    box-shadow: 0 1px 2px rgba(21,18,19,.04);
}}

/* ---- titre de section (section_title) ---- */
.cih-section {{
    display: flex; align-items: center; gap: 9px;
    font-size: 15px; font-weight: 800; color: {CIH['ink']};
    letter-spacing: -.01em; margin: 8px 0 14px;
}}
.cih-section span {{ width: 4px; height: 16px; border-radius: 3px; display: inline-block; }}

/* ---- badge d'état (status_pill) ---- */
.cih-pill {{
    display: inline-flex; align-items: center; gap: 6px;
    font-weight: 600; font-size: 12px; padding: 3px 10px;
    border-radius: 999px; white-space: nowrap;
}}
.cih-pill i {{ width: 6px; height: 6px; border-radius: 6px; display: inline-block; }}

/* ---- onglets ---- */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px; padding: 6px 14px; font-weight: 600; color: {CIH['ink2']};
}}
.stTabs [aria-selected="true"] {{ background: {CIH['orange_soft']}; color: {CIH['orange']}; }}

/* ---- tableaux (st.dataframe) ---- */
[data-testid="stDataFrame"] {{ border: 1px solid {CIH['border']}; border-radius: 12px; }}

/* ---- champs de saisie ---- */
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div {{
    border-radius: 10px !important; border-color: {CIH['border']} !important;
}}
</style>
"""
