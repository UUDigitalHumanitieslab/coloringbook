# syntax=docker/dockerfile:1
FROM python:2.7.9

# Install GIT
RUN apt install -y git

# Clone repository
RUN git clone https://github.com/UUDigitalHumanitieslab/coloringbook.git

# Change working directory
WORKDIR /coloringbook

# Install dependencies
RUN pip install -r requirements.txt

# Copy the config file
COPY CONFIG.py coloringbook/CONFIG.py

# Expose port
EXPOSE 5000

# Start server
CMD ["python",  "manage.py",  "-c", "CONFIG.py", "runserver", "-d"]
