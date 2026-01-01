FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
# ffmpeg is required for demucs/whisper audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (8000 default for uvicorn)
EXPOSE 8000

# Command to run the application
# Assumes the container context is the backend folder, so app.main is local
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
