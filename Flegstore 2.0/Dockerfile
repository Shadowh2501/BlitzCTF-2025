# Use a slim Python base
FROM python:3.10.14-slim-bullseye

# Update system packages to reduce vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get clean

# Set working directory
WORKDIR /usr/src/app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .

# Expose whatever port Flask is listening on (default 5000)
EXPOSE 5000

# Default env vars (can be overridden at runtime)
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# You *must* pass PRICE and FLAG when you run
CMD ["flask", "run"]
