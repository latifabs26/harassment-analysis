# Dockerfile pour les applications Python
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier le fichier requirements.txt
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier les fichiers de l'application
COPY . .

# Exposer le port pour FastAPI
EXPOSE 8000

# Commande par défaut (peut être surchargée)
CMD ["python", "app.py"]