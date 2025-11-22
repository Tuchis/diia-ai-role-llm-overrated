# Use a lightweight Python image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependency file first (caching optimization)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your backend code
COPY . .

# Expose the port FastAPI runs on (HTTPS)
EXPOSE 443

# Command to start the server with SSL
# --host 0.0.0.0 is CRITICAL for Docker containers to be accessible
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "443", \
     "--ssl-keyfile", "/etc/letsencrypt/live/diia-translation.com/privkey.pem", \
     "--ssl-certfile", "/etc/letsencrypt/live/diia-translation.com/fullchain.pem"]