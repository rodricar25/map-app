FROM python:3.11-slim

WORKDIR /usr/src/app

# System dependency (optional but useful for networking/debugging)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code + static dataset
COPY map-app.py .
COPY worldcities.csv .
COPY cities.csv .

# Expose Flask port
EXPOSE 5000

# Run the app
CMD ["python", "map-app.py"]