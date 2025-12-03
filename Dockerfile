ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    QT_QPA_PLATFORM=offscreen \
    MPLBACKEND=Agg \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libxkbcommon-x11-0 \
        libxcb-cursor0 \
        ffmpeg \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements-dev.txt

COPY . .

# Par défaut, lance la suite de tests en mode headless.
CMD ["pytest", "--maxfail=1", "-q"]
