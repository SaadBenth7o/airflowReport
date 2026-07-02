<#
.SYNOPSIS
    Lance le dashboard Airflow CIH Bank (Streamlit).

.DESCRIPTION
    Se positionne a la racine du projet, verifie/installe les dependances
    Python listees dans requirements.txt, controle la presence du fichier de
    donnees source, puis demarre le serveur Streamlit sur le port 8501.

.PARAMETER SkipInstall
    Ignore l'etape d'installation des dependances (demarrage plus rapide si
    l'environnement est deja a jour).

.PARAMETER Port
    Port d'ecoute du serveur Streamlit (defaut : 8501).

.EXAMPLE
    .\run.ps1
    .\run.ps1 -SkipInstall
    .\run.ps1 -Port 8502
#>

param(
    [switch]$SkipInstall,
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "==================================================" -ForegroundColor DarkGray
Write-Host "  CIH Bank -- Airflow DAG Report Dashboard" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor DarkGray
Write-Host ""

# 1. Verifier que Python est disponible
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "[ERREUR] Python est introuvable dans le PATH." -ForegroundColor Red
    Write-Host "Installez Python 3.10+ (https://www.python.org/downloads/) puis reessayez." -ForegroundColor Red
    exit 1
}
$pyVersion = (python --version) 2>&1
Write-Host "[OK] $pyVersion detecte" -ForegroundColor Green

# 2. Installer les dependances (sauf si -SkipInstall)
if (-not $SkipInstall) {
    Write-Host "Verification des dependances (requirements.txt)..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt --quiet --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERREUR] Echec de l'installation des dependances." -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Dependances a jour" -ForegroundColor Green
} else {
    Write-Host "[SKIP] Installation des dependances ignoree (-SkipInstall)" -ForegroundColor DarkYellow
}

# 3. Verifier la presence du fichier de donnees source
$xlsPath = Join-Path $PSScriptRoot "airflowhistory\airflow_tasks_2026_stats_V2.xls"
if (-not (Test-Path $xlsPath)) {
    Write-Host ""
    Write-Host "[ATTENTION] Fichier de donnees introuvable :" -ForegroundColor Yellow
    Write-Host "  $xlsPath" -ForegroundColor Yellow
    Write-Host "Placez le dernier export XLS d'Airflow a cet emplacement avant" -ForegroundColor Yellow
    Write-Host "de rafraichir la page, sinon le dashboard ne pourra pas charger de donnees." -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "[OK] Fichier de donnees trouve : $xlsPath" -ForegroundColor Green
}

# 4. Lancer Streamlit
Write-Host ""
Write-Host "Demarrage du dashboard sur http://localhost:$Port ..." -ForegroundColor Cyan
Write-Host "(Ctrl+C dans cette fenetre pour arreter le serveur)" -ForegroundColor DarkGray
Write-Host ""

streamlit run dashboard.py --server.port $Port
