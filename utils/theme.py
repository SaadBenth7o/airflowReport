"""
Charte visuelle CIH Bank — refonte UI complète du dashboard Airflow (V2).
Icônes Lucide-style (SVG inline, identiques au mockup React validé).
"""

import base64
from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.data_loader import (
    render_data_uploader, compute_health, load_data,
    legacy_excluded_count, reference_date, REPORT_PERIOD_START,
)

_LOGO_PATH = Path(__file__).parent.parent / "assets" / "cih-logo.png"


def _load_logo_b64():
    try:
        return base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")
    except Exception:
        return ""


_LOGO_B64 = _load_logo_b64()

# ── Palette ──────────────────────────────────────────────────────────────
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
    "green_dk":    "#16A34A",
    "red":         "#EF4444",
    "red_soft":    "#FEF2F2",
    "red_dk":      "#DC2626",
    "amber":       "#F59E0B",
    "amber_soft":  "#FFFBEB",
    "violet":      "#8B5CF6",
}

STATE_FR = {
    "success":         ("Succes",      CIH["green"],  CIH["green_soft"]),
    "failed":          ("Echec",       CIH["red"],    CIH["red_soft"]),
    "skipped":         ("Ignoree",     CIH["amber"],  CIH["amber_soft"]),
    "upstream_failed": ("Echec amont", CIH["orange"], CIH["orange_soft"]),
    "running":         ("En cours",    CIH["blue"],   CIH["blue_soft"]),
}

# Nom Streamlit "couleur" (:color[texte]) le plus proche de chaque etat —
# utilise pour les boutons de la liste DAG (markdown natif, pas de HTML).
STATE_MD_COLOR = {
    "success": "green", "failed": "red", "skipped": "gray",
    "upstream_failed": "orange", "running": "blue",
}

# Items de navigation — identiques au mockup (id, libelle, icone, route)
NAV_ITEMS = [
    ("overview",    "Vue d'ensemble",     "grid",     ""),
    ("failures",    "Echecs & alertes",   "alert",    "Failures"),
    ("explorer",    "DAG Explorer",       "branch",   "DAG_Explorer"),
    ("volume",      "Volume de donnees",  "database", "Data_Volume"),
    ("performance", "Performance",        "activity", "Performance"),
    ("schedule",    "Planification",      "calendar", "Schedule"),
]

# ── Icônes SVG Lucide (paths identiques au mockup React) ─────────────────
_ICON_PATHS = {
    "grid":     '<rect x="3" y="3" width="7" height="7" rx="1.5"/>'
                '<rect x="14" y="3" width="7" height="7" rx="1.5"/>'
                '<rect x="14" y="14" width="7" height="7" rx="1.5"/>'
                '<rect x="3" y="14" width="7" height="7" rx="1.5"/>',
    "alert":    '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94'
                'a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
                '<line x1="12" y1="9" x2="12" y2="13"/>'
                '<line x1="12" y1="17" x2="12.01" y2="17"/>',
    "branch":   '<line x1="6" y1="3" x2="6" y2="15"/>'
                '<circle cx="18" cy="6" r="3"/>'
                '<circle cx="6" cy="18" r="3"/>'
                '<path d="M18 9a9 9 0 0 1-9 9"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
                '<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>'
                '<path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"/>',
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/>'
                '<line x1="16" y1="2" x2="16" y2="6"/>'
                '<line x1="8" y1="2" x2="8" y2="6"/>'
                '<line x1="3" y1="10" x2="21" y2="10"/>',
    "clock":    '<circle cx="12" cy="12" r="10"/>'
                '<polyline points="12 6 12 12 16 14"/>',
    "zap":      '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "layers":   '<polygon points="12 2 2 7 12 12 22 7 12 2"/>'
                '<polyline points="2 17 12 22 22 17"/>'
                '<polyline points="2 12 12 17 22 12"/>',
    "hash":     '<line x1="4" y1="9" x2="20" y2="9"/>'
                '<line x1="4" y1="15" x2="20" y2="15"/>'
                '<line x1="10" y1="3" x2="8" y2="21"/>'
                '<line x1="16" y1="3" x2="14" y2="21"/>',
    "trend":    '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>'
                '<polyline points="17 6 23 6 23 12"/>',
    "check":    '<polyline points="20 6 9 17 4 12"/>',
    "refresh":  '<path d="M23 4v6h-6"/><path d="M1 20v-6h6"/>'
                '<path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10"/>'
                '<path d="M20.49 15a9 9 0 0 1-14.85 3.36L1 14"/>',
    "user":     '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
                '<circle cx="12" cy="7" r="4"/>',
    "x":        '<line x1="18" y1="6" x2="6" y2="18"/>'
                '<line x1="6" y1="6" x2="18" y2="18"/>',
    "search":   '<circle cx="11" cy="11" r="8"/>'
                '<line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "chevron":  '<polyline points="9 18 15 12 9 6"/>',
}


def svg_icon(name, size=18, color="currentColor", sw=1.9):
    """Retourne un SVG Lucide-style en HTML string."""
    paths = _ICON_PATHS.get(name, "")
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{paths}</svg>'
    )


# ── Helpers publics ───────────────────────────────────────────────────────

def apply_theme(st):
    """Injecte le CSS global. Appeler une fois après set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(st, title, subtitle="", crumb=None):
    """En-tête de page avec breadcrumb, identique au header du mockup.

    ATTENTION : construit en une seule ligne HTML (concatenation de
    litteraux adjacents), jamais en f-string multi-lignes indentee. Une
    ligne qui ne contiendrait QUE une valeur vide (ex: sous-titre absent)
    deviendrait une ligne blanche aux yeux du parseur Markdown, ce qui
    termine prematurement le bloc HTML et fait fuir tout le reste en texte
    brut (bug reel rencontre avec les cartes d'alerte — voir render_alert_row).
    """
    crumb = crumb or title
    sub_html = f'<p class="cih-page-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<div class="cih-page-header">'
        f'<div class="cih-breadcrumb">'
        f'<span>Airflow</span>'
        f'<span style="opacity:.4;margin:0 4px">/</span>'
        f'<span style="color:{CIH["orange"]};font-weight:700;">{crumb}</span>'
        f'</div>'
        f'<h1 class="cih-page-title">{title}</h1>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def data_freshness(data_date):
    """(age_jours, couleur, libelle) de la fraicheur des donnees, par
    rapport a l'horloge murale — pour un rapport quotidien, un export de
    plus d'un jour merite un signal visuel."""
    if pd.isna(data_date):
        return None, CIH["muted"], "date inconnue"
    age = max(0, (datetime.now() - data_date.to_pydatetime()).days)
    if age <= 1:
        return age, CIH["green_dk"], ("aujourd'hui" if age == 0 else "il y a 1 j")
    color = CIH["amber"] if age <= 3 else CIH["red_dk"]
    return age, color, f"il y a {age} j"


def sidebar_shell(st, active):
    """
    Rend la sidebar complete : logo CIH, navigation (icones SVG + libelles
    identiques au mockup), widget sante en bas. `active` = id de page
    (voir NAV_ITEMS : 'overview' | 'failures' | 'explorer' | 'volume' |
    'performance' | 'schedule').

    La sante globale et la fraicheur des donnees sont calculees ici, via
    compute_health() — regle unique, aucune page ne peut afficher un label
    incoherent avec les autres.
    """
    health = compute_health()
    health_label, n_ok, n_ko = health["label"], health["n_ok"], health["n_ko"]
    data_date = reference_date(load_data())
    n_legacy  = legacy_excluded_count()
    logo_html = (
        f'<img src="data:image/png;base64,{_LOGO_B64}" alt="CIH Bank" class="cih-brand-logo-img"/>'
        if _LOGO_B64 else
        '<div class="cih-brand-logo">CIH</div>'
    )
    st.sidebar.markdown(
        f'<div class="cih-brand">'
        f'{logo_html}'
        f'<div class="cih-brand-sub-standalone">Data Platform &middot; Airflow</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    nav_html = '<div class="cih-nav-section-label">Monitoring</div><nav class="cih-navlist">'
    for id_, label, icon_name, route in NAV_ITEMS:
        on = id_ == active
        color = CIH["orange"] if on else CIH["ink2"]
        ico = svg_icon(icon_name, size=18, color=color, sw=2.1 if on else 1.8)
        cls = "cih-navlink active" if on else "cih-navlink"
        href = route if route else "/"
        nav_html += f'<a class="{cls}" href="{href}" target="_self">{ico}<span>{label}</span></a>'
    nav_html += "</nav>"
    st.sidebar.markdown(nav_html, unsafe_allow_html=True)

    hc = (CIH["green"] if health_label == "Sain"
          else CIH["red"] if health_label == "Critique"
          else CIH["amber"])
    n_ko_color = CIH["red_dk"] if n_ko > 0 else CIH["ink"]

    _, fresh_color, fresh_label = data_freshness(data_date)
    date_str = data_date.strftime("%d/%m %H:%M") if pd.notna(data_date) else "—"
    legacy_html = ""
    if n_legacy:
        legacy_html = (
            f'<div style="font-size:10.5px;color:{CIH["muted"]};margin-top:4px;">'
            f'{n_legacy} tache(s) anterieure(s) au '
            f'{REPORT_PERIOD_START.strftime("%d/%m/%Y")} exclue(s)</div>'
        )
    st.sidebar.markdown(
        f'<div class="cih-health-widget">'
        f'<div class="cih-health-row">'
        f'<span class="cih-dot" style="background:{hc};"></span>'
        f'<span style="font-size:13px;font-weight:700;color:{CIH["ink"]};">Sante globale</span>'
        f'<span class="cih-health-badge" style="color:{hc};background:{hc}18;">{health_label}</span>'
        f'</div>'
        f'<div class="cih-health-boxes">'
        f'<div class="cih-health-box">'
        f'<div style="font-size:17px;font-weight:800;color:{CIH["green_dk"]};">{n_ok}</div>'
        f'<div style="font-size:10.5px;color:{CIH["ink2"]};">sains</div>'
        f'</div>'
        f'<div class="cih-health-box">'
        f'<div style="font-size:17px;font-weight:800;color:{n_ko_color};">{n_ko}</div>'
        f'<div style="font-size:10.5px;color:{CIH["ink2"]};">degrades</div>'
        f'</div>'
        f'</div>'
        f'<div style="margin-top:11px;padding-top:9px;border-top:1px solid {CIH["border"]};'
        f'display:flex;align-items:center;gap:7px;">'
        f'<span style="width:8px;height:8px;border-radius:50%;flex:none;background:{fresh_color};"></span>'
        f'<span style="font-size:11px;color:{CIH["ink2"]};">Donnees du <b>{date_str}</b>'
        f' &middot; <span style="color:{fresh_color};font-weight:700;">{fresh_label}</span></span>'
        f'</div>'
        f'{legacy_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

    render_data_uploader(st)


def section_title(st, txt, color=None, right=""):
    """Titre de section avec barre accent. `right` : HTML optionnel aligne a droite."""
    color = color or CIH["orange"]
    right_html = f'<span class="cih-section-right">{right}</span>' if right else ""
    st.markdown(
        f'<div class="cih-section">'
        f'<span class="cih-section-bar" style="background:{color}"></span>'
        f'<span class="cih-section-txt">{txt}</span>{right_html}</div>',
        unsafe_allow_html=True,
    )


def kpi_card(st, label, value, sub="", color=None, icon=None,
             delta=None, delta_up=True):
    """Tuile KPI avec icone Lucide dans un cercle colore (top-right)."""
    color = color or CIH["orange"]

    icon_html = ""
    if icon:
        ico = svg_icon(icon, size=16, color=color, sw=2.0)
        icon_html = (
            f'<div style="width:32px;height:32px;border-radius:9px;'
            f'background:{color}1a;display:flex;align-items:center;'
            f'justify-content:center;flex:none;">{ico}</div>'
        )

    delta_html = ""
    if delta:
        dc = CIH["green_dk"] if delta_up else CIH["red_dk"]
        arrow = "▲" if delta_up else "▼"
        delta_html = (
            f'<span style="font-weight:700;font-size:11.5px;color:{dc};">'
            f'{arrow} {delta}</span>'
        )

    nbsp = "&nbsp;" if delta_html and sub else ""
    st.markdown(
        f'<div class="cih-kpi">'
        f'<div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:10px;">'
        f'<div class="cih-kpi-label">{label}</div>'
        f'{icon_html}'
        f'</div>'
        f'<div class="cih-kpi-value" style="color:{color};">{value}</div>'
        f'<div class="cih-kpi-sub">{delta_html}{nbsp}{sub}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def status_pill(state):
    label, c, bg = STATE_FR.get(state, (state, CIH["muted"], CIH["bg"]))
    return (
        f'<span class="cih-pill" style="color:{c};background:{bg};">'
        f'<i style="background:{c};"></i>{label}</span>'
    )


# Couleur du texte d'etat dans les tableaux — deux variantes selon que la
# colonne contient le code brut (Task_State) ou le libelle FR deja mappe.
STATE_RAW_COLOR = {
    "success": CIH["green"], "failed": CIH["red"], "skipped": CIH["amber"],
    "upstream_failed": CIH["orange"], "running": CIH["blue"], "unknown": CIH["muted"],
}
STATE_FR_COLOR = {
    "Succes": CIH["green"], "Echec": CIH["red"], "Ignoree": CIH["amber"],
    "Upstream": CIH["orange"], "Echec amont": CIH["orange"], "En cours": CIH["blue"],
    "Inconnu": CIH["muted"],
}


def styled_column(df, column, color_map):
    """
    Retourne un pandas Styler colorant le texte de `column` selon
    color_map (valeur exacte -> couleur hex). A passer directement a
    st.dataframe(...) a la place du DataFrame brut (compatible avec
    column_config).
    """
    def _color(val):
        c = color_map.get(val)
        return f"color:{c};font-weight:700;" if c else ""
    return df.style.map(_color, subset=[column])


def donut_legend(st, segments):
    """
    Legende a cote d'un donut chart : point colore + libelle + valeur + %.
    segments : liste de {"label":str, "color":hex, "value":int}
    """
    total = sum(s["value"] for s in segments) or 1
    rows = ""
    for s in segments:
        if s["value"] <= 0:
            continue
        pct = round(s["value"] / total * 100)
        rows += (
            f'<div class="cih-legend-row">'
            f'<span class="cih-legend-dot" style="background:{s["color"]};"></span>'
            f'<span class="cih-legend-label">{s["label"]}</span>'
            f'<span class="cih-legend-value">{s["value"]:,}</span>'
            f'<span class="cih-legend-pct">{pct}%</span>'
            f'</div>'
        )
    st.markdown(f'<div class="cih-legend">{rows}</div>', unsafe_allow_html=True)


def card_open(st):
    """Ouvre un conteneur carte (bordure + radius) — utiliser en `with`."""
    return st.container(border=True)


# ── CSS global ────────────────────────────────────────────────────────────
_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── base ── */
html, body, [class*="css"], .stApp {{
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    color: {CIH['ink']};
    -webkit-font-smoothing: antialiased;
}}
.stApp {{ background: {CIH['bg']}; }}
.block-container {{
    padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1680px;
    animation: cih-fade .28s cubic-bezier(.2,.7,.2,1);
}}

/* ── animations ── */
@keyframes cih-fade {{
    from {{ opacity: 0; transform: translateY(9px); }}
    to   {{ opacity: 1; transform: none; }}
}}
@keyframes cih-spin {{ to {{ transform: rotate(360deg); }} }}
@keyframes cih-pulse {{
    0%   {{ box-shadow: 0 0 0 0 rgba(34,197,94,.50); }}
    70%  {{ box-shadow: 0 0 0 6px rgba(34,197,94,0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(34,197,94,0); }}
}}

/* Cache le chrome Streamlit + la nav multipage par defaut (remplacee par cih-navlist).
   IMPORTANT : le bouton qui rouvre la sidebar repliee (data-testid=
   "stExpandSidebarButton") vit DANS le header, a l'interieur de stToolbar.
   Masquer stHeader ou stToolbar en entier le supprime aussi — on ne cache
   donc que les elements precis (menu hamburger, bouton Deploy, indicateur
   de statut, decoration), jamais leurs conteneurs. */
#MainMenu, footer,
[data-testid="stMainMenu"],
[data-testid="stAppDeployButton"],
[data-testid="stStatusWidget"],
[data-testid="stDecoration"] {{
    visibility:hidden; height:0;
}}
header[data-testid="stHeader"] {{ background:transparent; box-shadow:none; }}
[data-testid="stSidebarNav"] {{ display:none; }}
[data-testid="stExpandSidebarButton"] {{
    visibility: visible !important; display: flex !important; opacity: 1 !important;
}}

/* ── titres ── */
h1 {{ font-weight:800; letter-spacing:-.02em; color:{CIH['ink']}; }}
h2, h3 {{ font-weight:700; letter-spacing:-.01em; color:{CIH['ink']}; }}

/* ── sidebar ── */
[data-testid="stSidebar"] {{
    background: {CIH['surface']};
    border-right: 1px solid {CIH['border']};
}}
[data-testid="stSidebar"] .block-container {{ padding: 0 !important; }}

/* ── brand CIH ── */
.cih-brand {{
    display: flex; flex-direction: column; align-items: flex-start; gap: 9px;
    padding: 20px 20px 16px;
    border-bottom: 1px solid {CIH['border']};
}}
.cih-brand-logo-img {{ width: 100%; max-width: 100%; height: auto; display: block; }}
.cih-brand-logo {{
    width: 38px; height: 38px; flex: none;
    border-radius: 10px; background: {CIH['orange']};
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 3px 10px rgba(240,72,28,.32);
    color: #fff; font-weight: 800; font-size: 13px; letter-spacing: -.01em;
}}
.cih-brand-sub-standalone {{
    font-size: 11px; font-weight: 600; color: {CIH['ink2']}; letter-spacing: .02em;
}}

/* ── nav custom (remplace stSidebarNav) ── */
.cih-nav-section-label {{
    font-size: 10px; font-weight: 700; letter-spacing: .12em;
    color: {CIH['muted']}; text-transform: uppercase;
    padding: 14px 20px 8px;
}}
.cih-navlist {{ display:flex; flex-direction:column; gap:2px; padding: 0 10px; }}
/* Specificite + !important : le CSS par defaut de Streamlit applique une
   couleur bleue et un soulignement aux <a> dans le markdown, avec une
   specificite plus forte que .cih-navlink seul. */
[data-testid="stSidebar"] a.cih-navlink,
[data-testid="stSidebar"] a.cih-navlink:visited {{
    position: relative; display:flex; align-items:center; gap:11px;
    padding:10px 12px; border-radius:10px;
    text-decoration:none !important; font-size:13.5px; font-weight:500;
    color:{CIH['ink2']} !important; transition: background .12s, color .12s;
}}
[data-testid="stSidebar"] a.cih-navlink:hover {{
    background:{CIH['bg']}; text-decoration:none !important;
}}
[data-testid="stSidebar"] a.cih-navlink.active {{
    background:{CIH['orange_soft']}; color:{CIH['orange']} !important; font-weight:700;
}}
.cih-navlink.active::before {{
    content:''; position:absolute; left:0; top:8px; bottom:8px;
    width:3px; border-radius:3px; background:{CIH['orange']};
}}
.cih-navlink svg {{ flex: none; }}

/* ── health widget ── */
.cih-health-widget {{
    background: {CIH['bg']}; border: 1px solid {CIH['border']};
    border-radius: 12px; padding: 13px 14px;
    margin: 16px 12px 12px;
}}
.cih-health-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
.cih-dot {{
    width: 9px; height: 9px; border-radius: 50%; flex: none;
    animation: cih-pulse 2.2s infinite;
}}
.cih-health-badge {{
    margin-left: auto; font-size: 11px; font-weight: 700;
    padding: 2px 9px; border-radius: 999px;
}}
.cih-health-boxes {{ display: flex; gap: 8px; }}
.cih-health-box {{
    flex: 1; text-align: center;
    background: {CIH['surface']}; border: 1px solid {CIH['border']};
    border-radius: 9px; padding: 7px 4px;
}}

/* ── page header (breadcrumb + titre) ── */
.cih-page-header {{
    background: {CIH['surface']};
    border: 1px solid {CIH['border']};
    border-radius: 16px;
    padding: 18px 24px 16px;
    margin-bottom: 22px;
    box-shadow: 0 1px 3px rgba(21,18,19,.05);
}}
.cih-breadcrumb {{
    font-size: 11.5px; font-weight: 600; color: {CIH['muted']};
    margin-bottom: 4px; display: flex; align-items: center;
}}
.cih-page-title {{
    margin: 0 0 2px !important; font-size: 22px !important;
    font-weight: 800 !important; letter-spacing: -.02em !important;
    color: {CIH['ink']} !important;
}}
.cih-page-sub {{
    margin: 0 !important; font-size: 13px !important;
    color: {CIH['ink2']} !important; line-height: 1.4 !important;
}}

/* ── KPI card ── */
.cih-kpi {{
    background: {CIH['surface']}; border: 1px solid {CIH['border']};
    border-radius: 16px; padding: 18px 20px 16px;
    box-shadow: 0 1px 3px rgba(21,18,19,.05);
    transition: box-shadow .18s, transform .18s, border-color .18s;
    height: 100%;
}}
.cih-kpi:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(21,18,19,.09);
    border-color: #d8dce4;
}}
.cih-kpi-label {{
    font-size: 10.5px; font-weight: 700; letter-spacing: .09em;
    text-transform: uppercase; color: {CIH['ink2']};
}}
.cih-kpi-value {{
    font-size: 34px; font-weight: 800; line-height: 1;
    letter-spacing: -.03em; margin: 4px 0 2px;
    font-variant-numeric: tabular-nums;
}}
.cih-kpi-sub {{
    font-size: 11.5px; color: {CIH['ink2']}; margin-top: 7px;
    display: flex; gap: 6px; align-items: center;
}}

/* ── st.metric natif ── */
[data-testid="stMetric"] {{
    background: {CIH['surface']}; border: 1px solid {CIH['border']};
    border-radius: 16px; padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(21,18,19,.05);
}}
[data-testid="stMetricValue"] {{ font-weight:800; letter-spacing:-.02em; }}
[data-testid="stMetricLabel"] {{
    font-size:10.5px; font-weight:700; letter-spacing:.09em;
    text-transform:uppercase; color:{CIH['ink2']};
}}

/* ── conteneurs border=True (nos "cards") ── */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {CIH['surface']}; border: 1px solid {CIH['border']} !important;
    border-radius: 16px; box-shadow: 0 1px 3px rgba(21,18,19,.04);
}}
[data-testid="stVerticalBlockBorderWrapper"] > div > div {{ padding: 20px; }}

/* ── section title ── */
.cih-section {{
    display: flex; align-items: center; gap: 10px;
    font-size: 15px; font-weight: 800; color: {CIH['ink']};
    letter-spacing: -.01em; margin: 10px 0 16px;
}}
.cih-section-bar {{ width: 4px; height: 18px; border-radius: 3px; display: inline-block; flex: none; }}
.cih-section-txt {{ flex: 1; }}
.cih-section-right {{ font-size: 12px; font-weight: 600; color: {CIH['muted']}; }}

/* ── legende donut ── */
.cih-legend {{ display:flex; flex-direction:column; gap:11px; }}
.cih-legend-row {{ display:flex; align-items:center; gap:9px; font-size:13px; }}
.cih-legend-dot {{ width:10px; height:10px; border-radius:3px; flex:none; }}
.cih-legend-label {{ color:{CIH['ink2']}; flex:1; }}
.cih-legend-value {{ font-weight:700; color:{CIH['ink']}; font-variant-numeric: tabular-nums; }}
.cih-legend-pct {{ color:{CIH['muted']}; font-size:11.5px; width:38px; text-align:right; font-variant-numeric: tabular-nums; }}

/* ── status pill ── */
.cih-pill {{
    display: inline-flex; align-items: center; gap: 6px;
    font-weight: 600; font-size: 12px; padding: 3px 10px;
    border-radius: 999px; white-space: nowrap;
}}
.cih-pill i {{ width:6px; height:6px; border-radius:50%; display:inline-block; }}

/* ── boutons ── */
.stButton > button {{
    border-radius: 10px; border: 1px solid {CIH['border']};
    font-weight: 600;
    transition: background .14s, border-color .14s, transform .1s;
}}
.stButton > button:active {{ transform: translateY(1px); }}
.stButton > button[kind="primary"] {{
    border: 1px solid {CIH['orange']};
    background: {CIH['orange']}; color: #fff; font-weight: 700;
    box-shadow: 0 2px 6px rgba(240,72,28,.22);
}}
.stButton > button[kind="primary"]:hover {{ background:{CIH['orange_dk']}; border-color:{CIH['orange_dk']}; }}
.stButton > button[kind="secondary"] {{ background:{CIH['surface']}; color:{CIH['ink']}; }}
.stButton > button[kind="secondary"]:hover {{ background:{CIH['bg']}; border-color:#d8dce4; }}

/* liste DAG explorer : boutons pleine largeur, alignes a gauche */
.cih-daglist .stButton > button {{
    text-align: left; justify-content: flex-start; padding: 10px 12px;
    border-radius: 11px;
}}
.cih-daglist .stButton > button p {{ text-align:left; margin:0; line-height:1.5; }}

/* ── onglets ── */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px; padding: 6px 16px;
    font-weight: 600; color: {CIH['ink2']};
    transition: background .12s, color .12s;
}}
.stTabs [aria-selected="true"] {{
    background: {CIH['orange_soft']}; color: {CIH['orange']};
}}

/* ── tableaux ── */
[data-testid="stDataFrame"] {{
    border: 1px solid {CIH['border']}; border-radius: 14px; overflow: hidden;
}}

/* ── champs de saisie ── */
.stTextInput input,
.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div {{
    border-radius: 10px !important;
    border-color: {CIH['border']} !important;
    background: {CIH['surface']} !important;
}}

/* ── file uploader (mise a jour des donnees) ── */
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
    border-radius: 12px; background: {CIH['bg']}; border: 1px dashed {CIH['border']};
}}
[data-testid="stSidebar"] .stFileUploader {{ padding: 0 12px; margin-bottom: 4px; }}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] span {{
    font-size: 12px; color: {CIH['ink2']};
}}
[data-testid="stSidebar"] .stCaption {{ padding: 0 12px; }}

/* ── scrollbar ── */
::-webkit-scrollbar {{ width:10px; height:10px; }}
::-webkit-scrollbar-thumb {{
    background: #dfe3ea; border-radius: 8px;
    border: 3px solid {CIH['bg']};
}}
::-webkit-scrollbar-thumb:hover {{ background: #c8cdd6; }}
</style>
"""
