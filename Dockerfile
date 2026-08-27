FROM python:3.12-slim

WORKDIR /app

# Installe les dépendances d'abord pour profiter du cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie le reste du code applicatif
COPY . .

EXPOSE 5000

# En production, remplacez par un vrai serveur WSGI :
#   RUN pip install gunicorn
#   CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]
CMD ["python", "run.py"]