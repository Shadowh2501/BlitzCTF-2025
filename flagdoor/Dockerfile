FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y sqlite3 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files except the app/ directory
COPY templates/ templates/
COPY static/ static
COPY app.py .

# Initialize database and set permissions
RUN touch users.db && \
    chmod a+rw users.db && \
    sqlite3 users.db "VACUUM;"

CMD ["python", "app.py"]
