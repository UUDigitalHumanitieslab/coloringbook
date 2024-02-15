# syntax=docker/dockerfile:1
FROM python:2.7.9

# Copy source files
COPY . /coloringbook

# Change working directory
WORKDIR /coloringbook

# Install dependencies
RUN pip install -r requirements.txt

# Install Gunicorn for production deployment
RUN pip install gunicorn==19.9.0

# Expose port
EXPOSE 5000