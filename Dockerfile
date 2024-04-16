# Dockerfile is based on the following tutorial:
# https://www.erraticbits.ca/post/2021/fastapi/

FROM python:3.11-slim-bookworm

RUN apt-get update -y && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=app.settings

# Install poetry for packages management
RUN  pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Use /app as the working directory
WORKDIR /app

# Copy poetry files & install the dependencies
COPY ./pyproject.toml /app
COPY ./poetry.lock /app
COPY --from=build-step /app/dist /app/static

RUN poetry install --no-interaction --no-ansi --no-root --without dev
RUN python -c 'from fastembed.embedding import DefaultEmbedding; DefaultEmbedding("sentence-transformers/all-MiniLM-L6-v2")'

# Finally copy the application source code and install root
COPY /app/ /app/

EXPOSE 8000
CMD ["sh", "-c", "python manage.py createsuperuser admin && python manage.py runserver 0.0.0.0:8000"]

