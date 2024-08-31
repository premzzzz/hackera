# FROM python:3.9-alpine   ##Troubleshooting area
FROM python:3.9-slim

# Install build dependencies including swig and cmake  ##Troubleshooting area
# RUN apk add --no-cache \
#     build-base \
#     swig \
#     cmake \
#     python3-dev

# Set the working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --verbose

# Copy application code
COPY static /app/
COPY templates /app/
COPY app.py /app/


# Create upload directory
RUN mkdir -p /app/uploads

# Copy environment variables
COPY .env /app/.env

# Expose port
EXPOSE 5000

# Set the working directory for the Flask app
WORKDIR /app/

# Command to run the Flask app
CMD ["python", "app.py"]