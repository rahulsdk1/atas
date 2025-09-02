# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=token_server.py
ENV FLASK_RUN_HOST=0.0.0.0

# Create a startup script to run both services
RUN echo '#!/bin/bash\n\
echo "Starting ATAS Voice Assistant..."\n\
\n\
# Start the token server in background\n\
gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 2 token_server:app &\n\
\n\
# Wait for token server to start\n\
sleep 3\n\
echo "Token server started on port 5000"\n\
\n\
# Start the LiveKit agent worker\n\
echo "Starting LiveKit agent worker..."\n\
python agent.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run both services
CMD ["/app/start.sh"]