# syntax=docker/dockerfile:1
FROM python:2.7.9

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy source files
COPY . /coloringbook

# Change working directory
WORKDIR /coloringbook

# Install dependencies
RUN pip install -r requirements.txt --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org

# Install Gunicorn for production deployment
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org gunicorn==19.9.0

# Expose port
EXPOSE 5000
