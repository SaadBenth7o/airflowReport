import pandas as pd
import xlrd
import streamlit as st
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
XLS_PATH = BASE_DIR / "airflowhistory" / "airflow_tasks_2026_stats_V2.xls"

# Seuil (nb de taches failed + upstream_failed) au-dela duquel la sante
# globale passe de "Degrade" a "Critique".
CRITICAL_PROBLEM_THRESHOLD = 10

# Colonnes que le dashboard exploite reellement — un nouvel export doit au
# minimum les contenir (memes noms, ordre libre) pour etre accepte.
REQUIRED_COLUMNS = [
    "DAG_ID", "Task_ID", "Operator_Type", "Bash_Script_Name",
    "Schedule_Cron", "Task_State", "Task_Last_Run_Date",
    "Task_Duration", "Rows_Affected_Total", "Owner",
]

# CIH Bank brand palette
CIH_ORANGE = "#F0481C"
CIH_BLUE   = "#05AEEF"
CIH_TEXT   = "#151213"
CIH_TEXT2  = "#4E4B4C"
CIH_BORDER = "#E9E8E8"
CIH_BG     = "#F5F8FC"

STATE_COLORS = {
    "success":         "#22C55E",
    "failed":          "#EF4444",
    "skipped":         "#F59E0B",
    "upstream_failed": "#F0481C",
    "running":         "#05AEEF",
    "never_run":       "#9CA3AF",
    "unknown":         "#6B7280",
}

STATE_FR = {
    "success":         "Succès",
    "failed":          "Échec",
    "skipped":         "Ignorée",
    "upstream_failed": "Échec amont",
    "running":         "En cours",
    "never_run":       "Jamais exécutée",
    "unknown":         "Inconnu",
}

STATE_BG = {
    "success":         "#F0FDF4",
    "failed":          "#FEF2F2",
    "skipped":         "#FFFBEB",
    "upstream_failed": "#FFF5F0",
    "running":         "#F0F9FF",
    "never_run":       "#F9FAFB",
    "unknown":         "#F9FAFB",
}


def _parse_date(val):
    if isinstance(val, float) and val > 1000:
        try:
            return xlrd.xldate_as_datetime(val, 0)
        except Exception:
            return pd.NaT
    if isinstance(val, str) and val not in ("Never Run", "N/A", ""):
        try:
            return pd.to_datetime(val)
        except Exception:
            return pd.NaT
    return pd.NaT


def _parse_duration_seconds(val):
    if isinstance(val, float) and val > 0:
        return val * 24 * 3600
    if isinstance(val, str) and ":" in val:
        try:
            parts = val.split(":")
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
            return h * 3600 + m * 60 + s
        except Exception:
            return 0.0
    return 0.0


def _format_duration(seconds):
    if seconds <= 0:
        return "—"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}h {m:02d}m {s:02d}s"
    if m > 0:
        return f"{m:02d}m {s:02d}s"
    return f"{s:02d}s"


def _fmt_rows(n):
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(int(n))


def _categorize_schedule(sched):
    s = str(sched).strip()
    if s in ("None", "nan", ""):
        return "Manuel"
    if "1 day" in s:
        return "Journalier"
    parts = s.split()
    if len(parts) != 5:
        return "Personnalisé"
    mins, hour, dom, month, dow = parts
    if "/" in mins or "," in mins or "*" in mins:
        return "Intra-journalier"
    if "/" in hour or "," in hour:
        return "Intra-journalier"
    if month != "*" and dom != "*":
        return "Annuel / Ponctuel"
    if dom != "*" and month == "*":
        return "Mensuel"
    if dow != "*":
        return "Hebdomadaire"
    return "Journalier"


@st.cache_data
def load_data(path=str(XLS_PATH)):
    wb = xlrd.open_workbook(path)
    ws = wb.sheet_by_index(0)
    headers = ws.row_values(0)
    raw = [dict(zip(headers, ws.row_values(i))) for i in range(1, ws.nrows)]
    df = pd.DataFrame(raw)

    # A capturer AVANT le parsing des dates : "Never Run" devient NaT apres.
    never_run = df["Task_Last_Run_Date"].astype(str).str.strip().eq("Never Run")

    df["Task_Last_Run_Date"] = df["Task_Last_Run_Date"].apply(_parse_date)
    df["Duration_Seconds"]   = df["Task_Duration"].apply(_parse_duration_seconds)
    df["Duration_Minutes"]   = df["Duration_Seconds"] / 60
    df["Duration_Display"]   = df["Duration_Seconds"].apply(_format_duration)
    df["Rows_Affected_Total"] = (
        pd.to_numeric(df["Rows_Affected_Total"], errors="coerce").fillna(0).astype(int)
    )
    # Un etat vide dans l'export doit rester visible, pas disparaitre.
    # Si la tache n'a jamais tourne (Task_Last_Run_Date = "Never Run"),
    # Airflow n'a simplement aucun etat a rapporter : on l'affiche
    # "Jamais executee". Un vide sur une tache qui A tourne (cas non
    # rencontre a ce jour) resterait "Inconnu".
    state = df["Task_State"].astype(str).str.strip()
    empty = state.isin(["", "nan"])
    state = state.mask(empty & never_run, "never_run")
    df["Task_State"] = state.replace({"": "unknown", "nan": "unknown"})
    df["State_Color"]        = df["Task_State"].map(STATE_COLORS).fillna("#9CA3AF")
    df["State_BG"]           = df["Task_State"].map(STATE_BG).fillna("#F9FAFB")
    df["State_FR"]           = df["Task_State"].map(STATE_FR).fillna(df["Task_State"])
    df["Schedule_Category"]  = df["Schedule_Cron"].apply(_categorize_schedule)
    df["Rows_Display"]       = df["Rows_Affected_Total"].apply(_fmt_rows)

    return df


def reference_date(df):
    """Date des donnees : le dernier run le plus recent de l'export.

    Toute notion de recence (echecs recents, badge 'Ancien'...) doit se
    calculer par rapport a cette date, jamais a l'horloge murale — sinon
    un export vieux de quelques jours fait croire a zero echec recent.
    """
    return df["Task_Last_Run_Date"].max()


@st.cache_data
def build_dag_summary(path=str(XLS_PATH)):
    df = load_data(path)

    counts = (
        df.groupby(["DAG_ID", "Task_State"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["success", "failed", "skipped", "upstream_failed", "running", "never_run", "unknown"], fill_value=0)
    )
    counts.columns.name = None

    agg = df.groupby("DAG_ID").agg(
        Total_Tasks      = ("Task_ID", "count"),
        Total_Rows       = ("Rows_Affected_Total", "sum"),
        Last_Run         = ("Task_Last_Run_Date", "max"),
        Avg_Duration_Min = ("Duration_Minutes", "mean"),
        Schedule_Cron    = ("Schedule_Cron", "first"),
        Schedule_Category= ("Schedule_Category", "first"),
        Owner            = ("Owner", "first"),
    )

    summary = agg.join(counts).fillna(0)
    for col in ["success", "failed", "skipped", "upstream_failed", "running"]:
        if col not in summary.columns:
            summary[col] = 0
        summary[col] = summary[col].astype(int)

    summary["Success_Rate"] = (summary["success"] / summary["Total_Tasks"] * 100).round(1)
    summary["Has_Failure"]  = (summary["failed"] + summary["upstream_failed"]) > 0

    return summary.reset_index()


def fmt_rows(n):
    return _fmt_rows(n)


@st.cache_data
def compute_health(path=str(XLS_PATH)):
    """Sante globale de la plateforme — regle unique pour toutes les pages.

    Avant : chaque page recalculait son propre label avec des regles
    differentes (voire "Sain" code en dur), et la sidebar se contredisait
    d'une page a l'autre.
    """
    df      = load_data(path)
    summary = build_dag_summary(path)
    n_ok    = int((~summary["Has_Failure"]).sum())
    n_ko    = int(summary["Has_Failure"].sum())
    problems = int(df["Task_State"].isin(["failed", "upstream_failed"]).sum())
    label = ("Sain" if problems == 0
             else "Critique" if problems >= CRITICAL_PROBLEM_THRESHOLD
             else "Dégradé")
    return {"label": label, "n_ok": n_ok, "n_ko": n_ko, "problems": problems}


def _validate_upload_bytes(file_bytes):
    """Verifie que le classeur uploade contient bien les colonnes attendues
    (memes metadonnees de table que le fichier en place). Retourne
    (ok, headers, message)."""
    try:
        wb = xlrd.open_workbook(file_contents=file_bytes)
        ws = wb.sheet_by_index(0)
        headers = [str(h).strip() for h in ws.row_values(0)]
    except Exception as exc:
        return False, [], f"Fichier illisible ({exc})."

    missing = [c for c in REQUIRED_COLUMNS if c not in headers]
    if missing:
        return False, headers, "Colonnes manquantes : " + ", ".join(missing)

    return True, headers, f"{ws.nrows - 1} ligne(s) détectée(s), structure conforme."


def save_uploaded_file(uploaded_file):
    """Valide puis remplace le fichier XLS source par le fichier uploade.
    Vide le cache Streamlit pour forcer le rechargement des donnees.
    Retourne (ok, message)."""
    file_bytes = uploaded_file.getvalue()
    ok, _headers, message = _validate_upload_bytes(file_bytes)
    if not ok:
        return False, message

    XLS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(XLS_PATH, "wb") as f:
        f.write(file_bytes)

    load_data.clear()
    build_dag_summary.clear()
    compute_health.clear()
    return True, f"Nouveau fichier appliqué — {message}"


def render_data_uploader(st):
    """Widget sidebar : depot d'un nouvel export XLS pour rafraichir le
    dashboard sans toucher au systeme de fichiers manuellement. Le fichier
    est rejete s'il ne contient pas les memes colonnes que l'export actuel."""
    st.sidebar.markdown('<div class="cih-nav-section-label">Données</div>', unsafe_allow_html=True)
    uploaded = st.sidebar.file_uploader(
        "Mettre à jour les données",
        type=["xls"],
        key="xls_uploader",
        help="Déposez le dernier export Airflow (.xls) — mêmes colonnes que le fichier actuel.",
    )
    if uploaded is not None:
        sig = (uploaded.name, uploaded.size)
        if st.session_state.get("_xls_upload_sig") != sig:
            st.session_state["_xls_upload_sig"] = sig
            ok, message = save_uploaded_file(uploaded)
            if ok:
                st.toast(message)
                st.rerun()
            else:
                st.sidebar.error(message)

    if XLS_PATH.exists():
        mtime = datetime.fromtimestamp(XLS_PATH.stat().st_mtime)
        st.sidebar.caption(f"Source : {XLS_PATH.name}  ·  maj {mtime.strftime('%d/%m %H:%M')}")
    else:
        st.sidebar.caption("Aucun fichier de données chargé.")
