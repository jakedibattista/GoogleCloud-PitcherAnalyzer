# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create directory for credentials
RUN mkdir -p /tmp/keys

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/google-credentials.json

# Create non-root user
RUN useradd -m -r app && \
    chown -R app:app /app && \
    chown -R app:app /tmp/keys

# Switch to non-root user
USER app

# Expose port
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# Create and configure Streamlit settings
RUN mkdir -p /root/.streamlit
RUN echo '\
[server]\n\
maxUploadSize = 200\n\
maxMessageSize = 200\n\
\n\
[browser]\n\
serverAddress = "0.0.0.0"\n\
serverPort = 8501\n\
gatherUsageStats = false\n\
' > /root/.streamlit/config.toml

# Create necessary directories
RUN mkdir -p /app/uploads /app/credentials /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
ENV STREAMLIT_SERVER_MAX_MESSAGE_SIZE=200

# Set Google Cloud specific environment variables
ENV GCP_PROJECT_ID=baseball-pitcher-analyzer
ENV GCP_BUCKET_NAME=baseball-pitcher-analyzer-videos
ENV GCP_LOCATION=us-central1
ENV GOOGLE_CLOUD_PROJECT=baseball-pitcher-analyzer

# Add this near the end of your Dockerfile
RUN echo "Checking for GOOGLE_API_KEY during build..."
RUN if [ -z "$GOOGLE_API_KEY" ]; then echo "WARNING: GOOGLE_API_KEY not set"; else echo "GOOGLE_API_KEY is set"; fi

# Add this line to your Dockerfile
# ENV GOOGLE_API_KEY should be provided at runtime

# Add this near the end of your Dockerfile
RUN echo "Checking for GOOGLE_API_KEY during build..."
RUN if [ -z "$GOOGLE_API_KEY" ]; then echo "WARNING: GOOGLE_API_KEY not set"; else echo "GOOGLE_API_KEY is set"; fi 