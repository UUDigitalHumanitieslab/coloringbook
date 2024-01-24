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

# Set build-time variables
ARG DEVELOPMENT=0
ARG CONFIG_FILE

# Start server. If DEVELOPMENT is set with value 1, then the flag -dr is added.
CMD if [ "$DEVELOPMENT" = "1" ]; then python manage.py -A -c "${CONFIG_FILE}" db upgrade && python manage.py -c "${CONFIG_FILE}" runserver --host 0.0.0.0 -dr; else python manage.py -A -c "${CONFIG_FILE}" db upgrade && python manage.py -c "${CONFIG_FILE}" runserver --host 0.0.0.0; fi
