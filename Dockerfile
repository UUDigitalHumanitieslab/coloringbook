# syntax=docker/dockerfile:1
FROM python:2.7.9

# Copy source files
COPY . /coloringbook

# Change working directory
WORKDIR /coloringbook

# Install dependencies
RUN pip install -r requirements.txt

# Expose port
EXPOSE 5000

# Start server
CMD python manage.py -A -c CONFIG.py db upgrade && python manage.py -c CONFIG.py runserver -dr --host 0.0.0.0

