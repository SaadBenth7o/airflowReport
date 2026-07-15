"""
Conversion d'une expression cron (5 champs) en phrase française lisible.

Couvre tous les motifs présents dans les exports Airflow CIH :
  - horaires fixes           : "0 2 * * *"          -> Tous les jours à 02h00
  - plusieurs heures         : "30 7,19 * * *"      -> Tous les jours à 07h30 et 19h30
  - pas horaire              : "05 */3 * * *"       -> Toutes les 3 heures (00h05, 03h05, ..., 21h05)
  - pas horaire avec départ  : "12 1/4 * * *"       -> Toutes les 4 heures (01h12, 05h12, ..., 21h12)
  - pas minute + plage heure : "*/5 7-19 * * *"     -> Toutes les 5 minutes, de 07h à 19h
  - minutes listées          : "0,19,36,51 7-20 * * *" -> Chaque heure aux minutes 0, 19, 36 et 51, de 07h à 20h
  - hebdomadaire             : "0 0 * * 6"          -> Chaque samedi à 00h00
  - plage de jours           : "0 19 * * 1-6"       -> Du lundi au samedi à 19h00
  - mensuel                  : "0 1 15 * *"         -> Le 15 de chaque mois à 01h00
  - plage mensuelle          : "0 4 16-17 * *"      -> Du 16 au 17 de chaque mois à 04h00
  - annuel                   : "0 4 1 1 *"          -> Le 1er janvier à 04h00 (annuel)
  - timedelta Airflow        : "1 day, 0:00:00"     -> Tous les jours à minuit
  - "None"                   :                      -> Déclenchement manuel

Toute expression non reconnue est renvoyée telle quelle : mieux vaut un
cron brut qu'une description fausse.
"""

import re

_DOW_FR = {
    0: "dimanche", 1: "lundi", 2: "mardi", 3: "mercredi",
    4: "jeudi", 5: "vendredi", 6: "samedi", 7: "dimanche",
}
_MONTH_FR = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
    7: "juillet", 8: "août", 9: "septembre", 10: "octobre",
    11: "novembre", 12: "décembre",
}


def _fmt_time(h, m):
    if h == 0 and m == 0:
        return "minuit"
    if h == 12 and m == 0:
        return "midi"
    return f"{h:02d}h{m:02d}"


def _join_fr(items):
    """['a','b','c'] -> 'a, b et c'"""
    items = list(items)
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " et " + items[-1]


def _ordinal(n):
    return "1er" if n == 1 else str(n)


def _parse_field(spec):
    """Décompose un champ cron en (kind, data).

    kinds : 'any' (*) · 'values' [n, ...] · 'range' (a, b)
            · 'step' (start|None, step) — couvre */n, a/n et a-b/n
    """
    if spec == "*":
        return "any", None
    if "/" in spec:
        base, step = spec.split("/", 1)
        step = int(step)
        if base == "*":
            return "step", (None, step)
        if "-" in base:
            a, _b = base.split("-", 1)
            return "step", (int(a), step)
        return "step", (int(base), step)
    if "-" in spec:
        a, b = spec.split("-", 1)
        return "range", (int(a), int(b))
    if "," in spec:
        return "values", [int(v) for v in spec.split(",")]
    return "values", [int(spec)]


def _describe_days(dom, month, dow):
    """Partie 'quand dans le calendrier' de la phrase."""
    dw_kind, dw = _parse_field(dow)
    dm_kind, dm = _parse_field(dom)
    mo_kind, mo = _parse_field(month)

    if dw_kind != "any":
        if dw_kind == "values":
            names = [_DOW_FR[d % 7] for d in dw]
            return "Chaque " + _join_fr(names) if len(names) == 1 else "Le " + _join_fr(names)
        if dw_kind == "range":
            return f"Du {_DOW_FR[dw[0] % 7]} au {_DOW_FR[dw[1] % 7]}"

    if dm_kind != "any" and mo_kind != "any":
        if dm_kind == "values" and mo_kind == "values" and len(dm) == 1 and len(mo) == 1:
            return f"Le {_ordinal(dm[0])} {_MONTH_FR[mo[0]]}", "annuel"
        return None

    if dm_kind == "values":
        if len(dm) == 1:
            return f"Le {_ordinal(dm[0])} de chaque mois"
        return "Les " + _join_fr(str(d) for d in dm) + " de chaque mois"
    if dm_kind == "range":
        return f"Du {dm[0]} au {dm[1]} de chaque mois"

    return "Tous les jours"


def _hours_of_step(start, step):
    return list(range(start or 0, 24, step))


def _enum_times(hours, minute):
    """Liste d'horaires pour un pas horaire : '00h05, 03h05, ..., 21h05'."""
    times = [f"{h:02d}h{minute:02d}" for h in hours]
    if len(times) <= 4:
        return ", ".join(times)
    return f"{times[0]}, {times[1]}, ..., {times[-1]}"


def _describe_time(minute, hour):
    """Partie horaire. Retourne (texte, est_frequence) — une fréquence
    ('Toutes les 3 heures...') porte la phrase, un horaire ('à 02h00')
    complète la partie calendaire."""
    mi_kind, mi = _parse_field(minute)
    ho_kind, ho = _parse_field(hour)

    def hour_window():
        if ho_kind == "range":
            return f", de {ho[0]:02d}h à {ho[1]:02d}h"
        if ho_kind == "values" and len(ho) == 1:
            return f", entre {ho[0]:02d}h et {ho[0] + 1:02d}h"
        return ""

    # Pas en minutes : "toutes les N minutes"
    if mi_kind == "step":
        start, step = mi
        base = f"Toutes les {step} minutes"
        if start:
            base += f" (à partir de la minute {start})"
        return base + hour_window(), True

    if mi_kind == "any":
        return "Chaque minute" + hour_window(), True

    if mi_kind == "range":
        return f"Chaque minute de {mi[0]} à {mi[1]}" + hour_window(), True

    # Minute(s) fixes
    if mi_kind == "values" and len(mi) > 1:
        base = "Chaque heure aux minutes " + _join_fr(str(m) for m in mi)
        return base + hour_window(), True

    m = mi[0]

    if ho_kind == "step":
        h_start, h_step = ho
        hours = _hours_of_step(h_start, h_step)
        return f"Toutes les {h_step} heures ({_enum_times(hours, m)})", True
    if ho_kind == "any":
        return f"Chaque heure à la minute {m}", True
    if ho_kind == "range":
        return f"Chaque heure à la minute {m}, de {ho[0]:02d}h à {ho[1]:02d}h", True
    # une ou plusieurs heures fixes
    return "à " + _join_fr(_fmt_time(h, m) for h in sorted(ho)), False


_TIMEDELTA_RE = re.compile(r"^(\d+)\s*day s?,?\s*(\d+):(\d+)(?::\d+)?$".replace("day s", "days?"))


def describe_cron(cron):
    """Expression cron -> phrase française. Renvoie l'expression brute si
    elle n'est pas reconnue."""
    c = str(cron).strip()
    if c in ("None", "", "nan", "@once", "None."):
        return "Déclenchement manuel"

    m = _TIMEDELTA_RE.match(c)
    if m:
        days, h, mi = int(m.group(1)), int(m.group(2)), int(m.group(3))
        prefix = "Tous les jours" if days == 1 else f"Tous les {days} jours"
        return f"{prefix} à {_fmt_time(h, mi)}"

    parts = c.split()
    if len(parts) != 5:
        return c

    try:
        minute, hour, dom, month, dow = parts
        days = _describe_days(dom, month, dow)
        if days is None:
            return c
        suffix = ""
        if isinstance(days, tuple):
            days, suffix = days
            suffix = f" ({suffix})"
        time_txt, is_freq = _describe_time(minute, hour)

        if is_freq:
            if days == "Tous les jours":
                return time_txt + suffix
            return f"{time_txt}, {days[0].lower()}{days[1:]}{suffix}"
        return f"{days} {time_txt}{suffix}"
    except Exception:
        return c
