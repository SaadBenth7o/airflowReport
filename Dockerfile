FROM python:3.12-slim

WORKDIR /app

# Dependances Python (xlrd==1.2.0 est pin car seule version compatible .xls)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code de l'application (voir .dockerignore pour ce qui est exclu)
COPY dashboard.py .
COPY pages/ ./pages/
COPY utils/ ./utils/
COPY assets/ ./assets/
COPY .streamlit/ ./.streamlit/

# Le fichier de donnees source est fourni au runtime via volume
# (voir docker-compose.yml) — le dossier doit exister pour que l'upload
# depuis l'UI puisse y ecrire des le premier lancement.
RUN mkdir -p airflowhistory

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8501/_stcore/health', timeout=3)" || exit 1

ENTRYPOINT ["streamlit", "run", "dashboard.py", \
    "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
