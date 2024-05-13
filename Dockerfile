FROM python:3.12-slim

# Define a build-time variable
ARG APP_DIR=/app
ENV APP_DIR=${APP_DIR}

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH $APP_DIR
# ENV DJANGO_SETTINGS_MODULE=backend.settings

# Set work directory
WORKDIR $APP_DIR

# Install system dependencies for mysqlclient
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY ./requirements.txt $APP_DIR
COPY $APP_DIR $APP_DIR
# Install any needed packages specified in requirements.txt
# RUN pip install uv && uv venv
RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r $APP_DIR/requirements.txt

EXPOSE 8008
# Run migrations on startup
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8008"]

# COPY ./entrypoint.sh /entrypoint.sh
# RUN chmod +x /entrypoint.sh
# ENTRYPOINT ["/entrypoint.sh"]
