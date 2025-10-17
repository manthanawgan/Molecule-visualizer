# syntax=docker/dockerfile:1.5
FROM mambaorg/micromamba:1.5.3

ARG MAMBA_DOCKERFILE_ACTIVATE=1

WORKDIR /app

COPY backend/environment.yml /tmp/environment.yml
RUN micromamba create -y -f /tmp/environment.yml \
    && micromamba clean --all --yes

COPY backend/app /app/app

ENV PYTHONPATH=/app
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000
EXPOSE 8000

CMD ["micromamba", "run", "-n", "rdkit-env", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
