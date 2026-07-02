# Airflow DAG Report — CIH Bank

Dashboard de reporting Streamlit pour le monitoring des DAGs Apache Airflow
de la plateforme de donnees CIH Bank. Genere une vue exhaustive et intuitive
(etat des taches, echecs, volumetrie, performance, planification) a partir
d'un export XLS produit par le script de reporting Airflow.

![Statut](https://img.shields.io/badge/statut-actif-22C55E)
![Python](https://img.shields.io/badge/python-3.10%2B-05AEEF)
![Streamlit](https://img.shields.io/badge/streamlit-%3E%3D1.35-F0481C)

---

## Sommaire

- [Apercu](#apercu)
- [Pages du dashboard](#pages-du-dashboard)
- [Prerequis](#prerequis)
- [Installation et lancement](#installation-et-lancement)
- [Mettre a jour les donnees](#mettre-a-jour-les-donnees)
- [Structure du projet](#structure-du-projet)
- [Charte graphique CIH Bank](#charte-graphique-cih-bank)
- [Depannage](#depannage)

---

## Apercu

Le dashboard lit un fichier **`airflow_tasks_2026_stats_V2.xls`** (genere par
le script de reporting Airflow) et construit automatiquement :

- des indicateurs cles (KPI) par etat de tache (succes / echec / ignoree /
  echec amont / en cours),
- des graphiques interactifs (Plotly) pour la repartition des etats, les
  volumes traites, les durees d'execution et la planification,
- une exploration detaillee DAG par DAG (maitre-detail),
- des tables filtrables et triables pour l'investigation d'incidents.

Aucune base de donnees n'est requise : il suffit de deposer un nouvel export
XLS pour rafraichir l'ensemble du dashboard.

## Pages du dashboard

| Page | Route | Contenu |
|---|---|---|
| **Vue d'ensemble** | `/` | KPIs globaux, repartition des etats (donut), top DAGs en echec, alertes actives |
| **Echecs & alertes** | `/Failures` | Timeline des echecs par DAG, tables `failed` / `upstream_failed` filtrables |
| **DAG Explorer** | `/DAG_Explorer` | Liste des DAGs (recherche, filtre, tri) + detail complet du DAG selectionne |
| **Volume de donnees** | `/Data_Volume` | Top taches par volume, repartition par DAG (treemap), table des lignes traitees |
| **Performance** | `/Performance` | Distribution des durees, taches les plus lentes, duree par operateur |
| **Planification** | `/Schedule` | Repartition des frequences cron, heures de demarrage, planning complet |

## Prerequis

- **Python 3.10+**
- **Windows** avec PowerShell (le script `run.ps1` cible cet environnement ;
  le lancement manuel fonctionne sur toute plateforme)
- Le fichier source `airflow_tasks_2026_stats_V2.xls`, place dans
  `airflowhistory/` a la racine du projet

## Installation et lancement

### Option 1 — Script PowerShell (recommande)

```powershell
.\run.ps1
```

Le script verifie que Python est installe, installe/actualise les
dependances (`requirements.txt`), controle la presence du fichier de
donnees, puis demarre le serveur sur **http://localhost:8501**.

Options disponibles :

```powershell
.\run.ps1 -SkipInstall      # ne pas reinstaller les dependances (demarrage plus rapide)
.\run.ps1 -Port 8502        # changer le port d'ecoute
```

### Option 2 — Lancement manuel

```powershell
pip install -r requirements.txt
streamlit run dashboard.py
```

L'application s'ouvre automatiquement dans le navigateur par defaut. Sinon,
ouvrez manuellement **http://localhost:8501**.

## Mettre a jour les donnees

Le dashboard est concu pour un usage recurrent : a chaque nouvelle
execution du script de reporting Airflow, deux methodes sont possibles.

### Option A — Depuis l'interface (recommande)

Un bloc **Donnees** en bas de la sidebar (visible sur toutes les pages)
permet de deposer directement le nouvel export `.xls` :

1. Cliquez sur la zone de depot et selectionnez le nouveau fichier.
2. Le fichier est **valide automatiquement** : ses colonnes doivent
   correspondre aux memes metadonnees de table que l'export actuel
   (`DAG_ID`, `Task_ID`, `Operator_Type`, `Bash_Script_Name`,
   `Schedule_Cron`, `Task_State`, `Task_Last_Run_Date`, `Task_Duration`,
   `Rows_Affected_Total`, `Owner`).
   - **Conforme** → le fichier remplace l'ancien, le cache est vide et le
     dashboard se rafraichit automatiquement avec les nouvelles donnees.
   - **Non conforme** (colonne manquante ou fichier illisible) → le fichier
     est **rejete**, l'ancien export reste actif, un message precise les
     colonnes manquantes.
3. La date de derniere mise a jour du fichier source est affichee sous la
   zone de depot.

### Option B — Remplacement manuel du fichier

1. Remplacez `airflowhistory/airflow_tasks_2026_stats_V2.xls` par le
   nouvel export (memes colonnes).
2. Rafraichissez la page du navigateur (ou relancez `run.ps1`).

Dans les deux cas, les donnees sont mises en cache par Streamlit
(`@st.cache_data`) pour des temps de chargement rapides ; le cache est
invalide automatiquement des qu'un nouveau fichier est applique.

> Le format `.xls` (ancien format Excel binaire) requiert la bibliotheque
> `xlrd==1.2.0` — c'est la seule version qui le supporte encore (les
> versions plus recentes de `xlrd` ne gerent que `.xlsx`). Ne pas mettre a
> jour ce paquet sans adapter `utils/data_loader.py`.

## Structure du projet

```
AIRFLOW_MISSION/
├── run.ps1                     # Script de lancement (Windows/PowerShell)
├── dashboard.py                 # Page principale — Vue d'ensemble
├── pages/
│   ├── 1_Failures.py            # Echecs & alertes
│   ├── 2_DAG_Explorer.py        # DAG Explorer (maitre-detail)
│   ├── 3_Data_Volume.py         # Volume de donnees
│   ├── 4_Performance.py         # Performance
│   └── 5_Schedule.py            # Planification
├── utils/
│   ├── data_loader.py           # Lecture XLS, nettoyage, agregation par DAG
│   ├── charts.py                # Graphiques Plotly (donuts, barres, gauges...)
│   └── theme.py                 # Charte CSS CIH, navigation, composants (KPI, icones SVG)
├── .streamlit/
│   └── config.toml              # Theme Streamlit (couleurs CIH)
├── docs/
│   └── mockup.html              # Maquette de reference (visuel valide)
├── airflowhistory/               # Donnees source (non versionnees, voir .gitignore)
│   └── airflow_tasks_2026_stats_V2.xls
└── requirements.txt
```

## Charte graphique CIH Bank

Palette obligatoire, appliquee sur l'ensemble de l'interface (voir
`utils/theme.py`) :

| Role | Couleur |
|---|---|
| Action principale / importance | Orange `#F0481C` |
| Action secondaire / info / volume | Bleu `#05AEEF` |
| Texte principal | `#151213` |
| Texte secondaire | `#4E4B4C` |
| Bordure | `#E9E8E8` |
| Fond | `#F5F8FC` |
| Succes | Vert `#22C55E` |
| Echec / alerte (reserve aux erreurs) | Rouge `#EF4444` |
| Ignoree | Ambre `#F59E0B` |

Interface volontairement **sobre et formelle** : pas d'emojis, pas de logo
decoratif, icones SVG (style Lucide) uniquement, coins arrondis pour un
rendu doux et professionnel.

## Depannage

**`ModuleNotFoundError: No module named 'xlrd'`**
→ `pip install xlrd==1.2.0` (voir note ci-dessus sur la version imposee).

**Le dashboard affiche des donnees perimees apres mise a jour du XLS**
→ Rafraichissez completement la page (`Ctrl+F5`). Le cache Streamlit peut
etre vide manuellement via le menu ⋮ → *Clear cache*, ou en relancant le
serveur.

**Le port 8501 est deja utilise**
→ `.\run.ps1 -Port 8502` (ou tout autre port libre).

**Erreur de lecture du fichier `.xls`**
→ Verifiez que le fichier n'est pas ouvert dans Excel (verrou de fichier)
et qu'il s'agit bien du format `.xls` binaire (pas `.xlsx`).

**L'upload depuis la sidebar est rejete ("Colonnes manquantes")**
→ Le fichier depose n'a pas exactement les memes en-tetes de colonnes que
l'export de reference (voir liste dans [Mettre a jour les donnees](#mettre-a-jour-les-donnees)).
Verifiez que le script de reporting Airflow n'a pas ete modifie (colonne
renommee/supprimee) avant de reessayer.
