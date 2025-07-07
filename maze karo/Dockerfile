# Use Python slim image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /usr/src/app

# Install gcc dependencies (if needed for any libraries)
RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose Flask port
EXPOSE 5000

# Set default environment variables for CTF
# These can be overridden at runtime with docker flags or .env file
ENV FLAG="Blitz{Cl3ar_Th3_W4y_4nd_1t_W1ll_B3_Cl34r3d}" \
    FLASK_ENV=production

# Run the application
CMD ["python", "app.py"]