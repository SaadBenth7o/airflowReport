"""
Charte visuelle CIH Bank — refonte UI complète du dashboard Airflow (V2).
Icônes Lucide-style (SVG inline, identiques au mockup React validé).
"""

import base64
import io
from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.data_loader import (
    render_data_uploader, compute_health, load_data, reference_date,
    STATE_COLORS as _STATE_COLORS, STATE_FR as _STATE_FR_LABELS,
)

_ASSETS = Path(__file__).parent.parent / "assets"


def _load_b64(filename):
    try:
        return base64.b64encode((_ASSETS / filename).read_bytes()).decode("ascii")
    except Exception:
        return ""


# Favicon volontairement VIDE (assets/transparent.png, pixel transparent)
# via page_icon de st.set_page_config sur chaque page : aucun logo dans
# l'onglet — le pinwheel Airflow pretait a confusion, et sans page_icon
# Streamlit remettrait son propre logo.
_LOGO_B64 = _load_b64("cih-logo.png")

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
    "success":         ("Succès",          CIH["green"],  CIH["green_soft"]),
    "failed":          ("Échec",           CIH["red"],    CIH["red_soft"]),
    "skipped":         ("Ignorée",         CIH["amber"],  CIH["amber_soft"]),
    "upstream_failed": ("Échec amont",     CIH["orange"], CIH["orange_soft"]),
    "running":         ("En cours",        CIH["blue"],   CIH["blue_soft"]),
    "never_run":       ("Jamais exécutée", CIH["muted"],  CIH["bg"]),
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
    ("failures",    "Échecs & alertes",   "alert",    "Failures"),
    ("explorer",    "DAG Explorer",       "branch",   "DAG_Explorer"),
    ("volume",      "Volume de données",  "database", "Data_Volume"),
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


def _snapshot_str():
    """Horodatage du snapshot de donnees (date + heure + minute), utilise
    dans les noms de fichiers exportes (tableaux Excel, graphes PNG)."""
    data_date = reference_date(load_data())
    if pd.notna(data_date):
        return data_date.strftime("%Y-%m-%d_%Hh%M")
    return datetime.now().strftime("%Y-%m-%d_%Hh%M")


def align_bottom_row(st, key):
    """Conteneur de ligne (filtres + bouton telecharger) dont les colonnes
    s'alignent sur leur BAS plutot que sur leur haut (comportement par
    defaut de st.columns). Un bouton sans label colle ainsi exactement
    au bas d'un input avec label (text_input, multiselect...), quelle
    que soit la hauteur exacte du label — pas de mesure en pixels a
    deviner, juste du flexbox standard (align-items: flex-end)."""
    return st.container(key=key)


def download_button(st, dataframe, title="Tableau", key="dl_btn"):
    """Bouton de téléchargement Excel d'un DataFrame.
    `title` : nom de la table/graphe (apparaît dans le nom du fichier).
    Affiche en haut à côté des filtres, avec l'icône Material 'download'
    (formelle, pas d'emoji) fournie nativement par st.download_button."""
    file_name = f"{title} - Snapshot {_snapshot_str()}.xlsx"

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, sheet_name="Données", index=False)
    buffer.seek(0)

    st.download_button(
        label="Télécharger",
        icon=":material/download:",
        data=buffer.getvalue(),
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=key,
    )


def copy_button(st, dataframe, key="copy_btn"):
    """Alias pour download_button (pour compatibilité). Télécharge un DataFrame en Excel."""
    download_button(st, dataframe, title="Tableau", key=key)


# Boutons du modebar Plotly a retirer : on ne garde que 'toImage'
# (telecharger en PNG). Les DAGs/taches se filtrent via les widgets
# Streamlit (sliders, multiselect) — zoom/pan/lasso/axes n'apportent
# rien ici et encombrent la barre d'outils.
_MODEBAR_REMOVE = [
    "zoom2d", "pan2d", "select2d", "lasso2d",
    "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d",
    "hoverClosestCartesian", "hoverCompareCartesian",
    "hoverClosestPie", "hoverClosestGl2d", "hoverClosest3d", "hoverClosestGeo",
    "toggleHover", "toggleSpikelines", "resetViews", "resetViewMapbox",
    "zoomInMapbox", "zoomOutMapbox", "sendDataToCloud",
]


def chart_config(title, export_width=None):
    """Config Plotly a passer a st.plotly_chart(fig, config=...) :
    - le bouton 'Telecharger en PNG' du modebar exporte sous un nom de
      fichier significatif (titre de la section + horodatage du snapshot)
      au lieu du defaut generique 'newplot' ;
    - modebar reduit au seul bouton telechargement (zoom/pan/axes retires,
      redondants avec les widgets Streamlit) et toujours visible (pas
      seulement au survol) ;
    - `export_width` : largeur (px) forcee pour l'image exportee, utile
      pour les donuts qui gagnent une legende native au moment de
      l'export (cih-donut-export, voir plotly_export_js)."""
    img_opts = {
        "format": "png",
        "filename": f"{title} - Snapshot {_snapshot_str()}",
    }
    if export_width:
        img_opts["width"] = export_width
    return {
        "toImageButtonOptions": img_opts,
        "displaylogo": False,
        "displayModeBar": True,
        "modeBarButtonsToRemove": _MODEBAR_REMOVE,
    }


def plotly_export_js(st):
    """Injecte un script partage par toutes les pages a graphiques Plotly :
    1. Remplace le bouton natif 'telecharger en PNG' de Plotly par un
       CLONE VISUELLEMENT IDENTIQUE (meme icone camera d'origine, garde
       telle quelle) dont le clic est pris en charge par notre propre
       gestionnaire — necessaire pour le point 2 : le clic natif ne
       laisse aucun moyen d'attendre la fin d'un redessin avant la
       capture de l'image.
    2. Pour les graphiques marques meta='cih-donut-export' (donuts sans
       legende native a l'ecran, cf. utils.charts._donut) : le clic sur
       'telecharger' active la legende (Plotly.restyle POUR LA TRACE +
       Plotly.relayout POUR LE LAYOUT — les deux niveaux sont necessaires,
       showlegend=false au niveau layout bloque toute legende quel que
       soit le reglage de la trace), ATTEND la fin du redessin (promesse),
       capture l'image (Plotly.downloadImage), puis desactive a nouveau
       la legende. L'evenement natif plotly_beforeexport ne convient pas
       ici : il se declenche de facon synchrone et Plotly capture l'image
       avant la fin du redessin declenche par notre restyle — d'ou la
       prise de controle complete du clic.

    Le bouton 'plein ecran' n'est PAS gere ici : ce n'est pas un calque
    HTML separe comme suppose au premier essai, mais un second bouton
    NATIF DU MODEBAR PLOTLY LUI-MEME, ajoute par Streamlit via
    config.modeBarButtonsToAdd = [{{name: "Fullscreen", ...}}] (confirme
    en lisant le bundle JS de Streamlit installe). Il vit donc DEJA dans
    le meme conteneur .modebar que le bouton telecharger, aligne par
    Plotly lui-meme — inutile de le cloner ou de masquer quoi que ce
    soit : il suffit de ne PAS le retirer de modeBarButtonsToRemove (cf.
    chart_config). Le clone qu'on avait ajoute ici avant provoquait
    justement le doublon signale.

    VERIFIE EN NAVIGATEUR REEL (Chrome headless + CDP, 16/07/2026) sur
    une instance Streamlit separee (port 8510, sans toucher a celle de
    l'utilisateur) : un seul bouton telecharger + un seul bouton plein
    ecran dans le modebar (plus de doublon) ; clic reel sur le bouton
    telecharger d'un donut -> fichier PNG telecharge et ouvert, legende
    bien presente a droite ; clic sur un graphique non-donut -> fichier
    telecharge normalement, sans regression.
    """
    st.components.v1.html(
        f"""
        <script>
        const bind = () => {{
            const plots = window.parent.document.querySelectorAll('.js-plotly-plot');
            plots.forEach(p => {{
                try {{
                    const meta = p._fullLayout && p._fullLayout.meta;
                    const isDonut = meta === 'cih-donut-export';
                    let dlBtn = p.querySelector('.modebar-btn[data-title*="Download plot"]');
                    if (!dlBtn || dlBtn.__cihReplaced) return;

                    // Remplace le bouton telecharger natif par un clone : on y
                    // attache notre propre clic (le clic natif ne peut pas
                    // etre mis en pause pour attendre un redessin de legende).
                    // L'icone (camera Plotly d'origine) est volontairement
                    // conservee telle quelle — cloneNode() la recopie deja.
                    const freshBtn = dlBtn.cloneNode(true);
                    freshBtn.__cihReplaced = true;
                    freshBtn.addEventListener('click', async (e) => {{
                        e.preventDefault();
                        e.stopPropagation();
                        const PL = window.parent.Plotly || window.Plotly;
                        if (!PL || !PL.downloadImage) return;
                        const opts = (p._context && p._context.toImageButtonOptions) || {{}};
                        const imgOpts = {{format: opts.format || 'png', filename: opts.filename || 'plot'}};
                        if (opts.width)  imgOpts.width  = opts.width;
                        if (opts.height) imgOpts.height = opts.height;
                        try {{
                            if (isDonut) {{
                                // showlegend doit basculer aux DEUX niveaux : la
                                // trace (_donut() la met a false individuellement)
                                // ET le layout (false = interrupteur general qui
                                // bloque toute legende quel que soit le reglage
                                // de la trace) — verifie en navigateur, le
                                // legend DOM ne se cree pas sans le second.
                                await PL.restyle(p, {{showlegend: true}}, [0]);
                                await PL.relayout(p, {{
                                    showlegend: true,
                                    'legend.x': 1.02, 'legend.y': 0.5, 'legend.xanchor': 'left',
                                    margin: {{l: 10, r: 170, t: 32, b: 10}},
                                }});
                            }}
                            await PL.downloadImage(p, imgOpts);
                        }} finally {{
                            if (isDonut) {{
                                await PL.restyle(p, {{showlegend: false}}, [0]);
                                await PL.relayout(p, {{showlegend: false, margin: {{l: 10, r: 10, t: 32, b: 10}}}});
                            }}
                        }}
                    }});
                    dlBtn.parentNode.replaceChild(freshBtn, dlBtn);
                }} catch (e) {{}}
            }});
        }};
        setInterval(bind, 400);
        </script>
        """,
        height=0,
    )


def align_right(st, key):
    """Conteneur alignant son contenu (ex: un seul bouton, sans filtre
    voisin a aligner) sur le bord droit reel — flexbox justify-content,
    plutot qu'une colonne etroite ou le bouton reste colle a gauche de
    sa colonne (position qui paraît flottante, ni centree ni a droite)."""
    return st.container(key=key)


def page_header(st, title, subtitle="", crumb=None, right_html=""):
    """En-tête de page avec breadcrumb, identique au header du mockup.
    `right_html` : bloc optionnel (spans uniquement) aligne a droite dans
    la carte — ex: badge "Donnees du ..." de la vue d'ensemble.

    ATTENTION : construit en une seule ligne HTML (concatenation de
    litteraux adjacents), jamais en f-string multi-lignes indentee. Une
    ligne qui ne contiendrait QUE une valeur vide (ex: sous-titre absent)
    deviendrait une ligne blanche aux yeux du parseur Markdown, ce qui
    termine prematurement le bloc HTML et fait fuir tout le reste en texte
    brut (bug reel rencontre avec les cartes d'alerte — voir render_alert_row).
    """
    crumb = crumb or title
    sub_html = f'<p class="cih-page-sub">{subtitle}</p>' if subtitle else ""
    right_block = (
        f'<div style="flex:none;align-self:center;">{right_html}</div>' if right_html else ""
    )
    st.markdown(
        f'<div class="cih-page-header" style="display:flex;align-items:flex-start;'
        f'justify-content:space-between;gap:16px;">'
        f'<div style="min-width:0;">'
        f'<div class="cih-breadcrumb">'
        f'<span>Airflow</span>'
        f'<span style="opacity:.4;margin:0 4px">/</span>'
        f'<span style="color:{CIH["orange"]};font-weight:700;">{crumb}</span>'
        f'</div>'
        f'<h1 class="cih-page-title">{title}</h1>'
        f'{sub_html}'
        f'</div>'
        f'{right_block}'
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
    logo_html = (
        f'<img src="data:image/png;base64,{_LOGO_B64}" alt="CIH Bank" class="cih-brand-logo-img"/>'
        if _LOGO_B64 else
        '<div class="cih-brand-logo">CIH</div>'
    )
    # Le bloc marque est un lien vers la vue d'ensemble — meme cible que
    # le bouton de navigation. Uniquement des <span> a l'interieur : le
    # parseur re-parente les elements bloc (<div>) HORS de l'ancre, qui
    # se retrouve vide.
    st.sidebar.markdown(
        f'<a class="cih-brand-link" href="/" target="_self" title="Vue d\'ensemble">'
        f'<span class="cih-brand">'
        f'{logo_html}'
        f'<span class="cih-brand-sub-standalone">Data Platform &middot; Airflow</span>'
        f'</span>'
        f'</a>',
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
    st.sidebar.markdown(
        f'<div class="cih-health-widget">'
        f'<div class="cih-health-row">'
        f'<span class="cih-dot" style="background:{hc};"></span>'
        f'<span style="font-size:13px;font-weight:700;color:{CIH["ink"]};">Santé globale</span>'
        f'</div>'
        f'<div class="cih-health-boxes">'
        f'<div class="cih-health-box">'
        f'<div style="font-size:17px;font-weight:800;color:{CIH["green_dk"]};">{n_ok}</div>'
        f'<div style="font-size:10.5px;color:{CIH["ink2"]};">sains</div>'
        f'</div>'
        f'<div class="cih-health-box">'
        f'<div style="font-size:17px;font-weight:800;color:{n_ko_color};">{n_ko}</div>'
        f'<div style="font-size:10.5px;color:{CIH["ink2"]};">dégradés</div>'
        f'</div>'
        f'</div>'
        f'<div style="margin-top:11px;padding-top:9px;border-top:1px solid {CIH["border"]};'
        f'display:flex;align-items:center;gap:7px;">'
        f'<span style="width:8px;height:8px;border-radius:50%;flex:none;background:{fresh_color};"></span>'
        f'<span style="font-size:11px;color:{CIH["ink2"]};">Données du <b>{date_str}</b>'
        f' &middot; <span style="color:{fresh_color};font-weight:700;">{fresh_label}</span></span>'
        f'</div>'
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
# colonne contient le code brut (Task_State) ou le libelle FR (State_FR).
# Derivees des maps canoniques du data_loader : une seule source de verite
# pour les libelles ET les couleurs.
STATE_RAW_COLOR = dict(_STATE_COLORS)
STATE_FR_COLOR  = {_STATE_FR_LABELS[k]: _STATE_COLORS[k] for k in _STATE_FR_LABELS}


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
/* Le bloc entier est un lien vers la vue d'ensemble : neutraliser le
   style d'ancre par defaut de Streamlit (bleu + soulignement). */
[data-testid="stSidebar"] a.cih-brand-link,
[data-testid="stSidebar"] a.cih-brand-link:visited {{
    display: block; text-decoration: none !important; color: inherit !important;
    cursor: pointer;
}}
[data-testid="stSidebar"] a.cih-brand-link:hover .cih-brand {{ background: {CIH['bg']}; }}
.cih-brand {{
    display: flex; flex-direction: column; align-items: flex-start; gap: 9px;
    padding: 4px 20px 16px;
    border-bottom: 1px solid {CIH['border']};
    transition: background .12s;
}}
.cih-brand-logo-img {{ width: 75%; max-width: 75%; height: auto; display: block; border-radius: 10px; }}
.cih-brand-logo {{
    width: 38px; height: 38px; flex: none;
    border-radius: 10px; background: {CIH['orange']};
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 3px 10px rgba(240,72,28,.32);
    color: #fff; font-weight: 800; font-size: 13px; letter-spacing: -.01em;
}}
.cih-brand-sub-standalone {{
    display: flex; align-items: center; gap: 7px;
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
/* Streamlit <=1.4x : wrapper dedie stVerticalBlockBorderWrapper.
   Streamlit 1.52 : plus de wrapper, la bordure est portee par le
   stVerticalBlock lui-meme via la classe emotion st-emotion-cache-s8chrg
   (hash stable pour une version donnee — A REVERIFIER apres tout upgrade
   de Streamlit : si les cartes perdent leur ombre/rayon, ce hash a change). */
[data-testid="stVerticalBlockBorderWrapper"],
.stVerticalBlock.st-emotion-cache-s8chrg {{
    background: {CIH['surface']}; border: 1px solid {CIH['border']} !important;
    border-radius: 16px; box-shadow: 0 1px 3px rgba(21,18,19,.04);
}}
[data-testid="stVerticalBlockBorderWrapper"] > div > div {{ padding: 20px; }}
.stVerticalBlock.st-emotion-cache-s8chrg {{ padding: 20px; }}

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

/* ── sliders recolores par carte ── */
/* Streamlit colore le slider avec primaryColor (orange) via des styles
   inline (gradient de la piste) : impossible a surcharger proprement en
   CSS. hue-rotate decale la teinte de tout le widget — l'orange CIH
   (~12deg) devient rouge template (~0deg) ou bleu CIH (~197deg), et les
   gris de la piste, non satures, ne bougent pas. Cible : la classe
   st-key-* posee par st.container(key="slider-red-...") autour du widget. */
[class*="st-key-slider-red"] [data-testid="stSlider"] {{ filter: hue-rotate(-14deg) saturate(1.15); }}
[class*="st-key-slider-blue"] [data-testid="stSlider"] {{ filter: hue-rotate(185deg); }}

/* ── alignement bas d'une ligne filtres + bouton telecharger ── */
/* st.container(key="align-bottom-...") autour d'un st.columns() : les
   colonnes s'alignent sur leur bas (au lieu du defaut stretch, qui les
   rend toutes egales en hauteur mais aligne leur CONTENU sur le haut).
   Un bouton (pas de label) colle ainsi exactement au bas d'un input
   voisin qui, lui, a un label au-dessus. */
[class*="st-key-align-bottom"] div[data-testid="stHorizontalBlock"] {{
    align-items: flex-end;
}}

/* ── alignement a droite d'un bouton seul (sans filtre voisin) ── */
[class*="st-key-align-right"] {{
    display: flex;
    justify-content: flex-end;
}}

/* ── barre d'outils native Streamlit des graphiques (plein ecran...) ── */
/* Masquee par defaut, visible seulement au survol : on la force visible
   en permanence, comme demande pour le bouton plein ecran. */
[data-testid="stElementToolbar"] {{
    opacity: 1 !important;
}}

/* ── treemap plotly ── */
/* La tuile racine implicite reste gris fonce (#444) : le plotly.js
   embarque par Streamlit ignore root.color. On la repeint en blanc —
   c'est toujours le premier slice du trace treemap. */
.trace.treemap > g.slice:first-child > path.surface {{
    fill: #FFFFFF !important;
}}

/* ── champs de saisie ── */
.stTextInput input {{
    border-radius: 10px !important;
    border: 1px solid {CIH['border']} !important;
    background: {CIH['surface']} !important;
}}
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
