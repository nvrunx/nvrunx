# syntax=docker/dockerfile:1

FROM python:3.12-slim

LABEL name="nvrunx" \
    maintainer="nvrunx <nvrunxbdueub@gmail.com>" \
    description="Make websites accessible for AI agents. Automate tasks online with ease." \
    homepage="https://github.com/nvrunx/nvrunx"

ARG TARGETPLATFORM
ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT

# Global system-level config
ENV TZ=UTC \
    LANGUAGE=en_US:en \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONIOENCODING=UTF-8 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    IN_DOCKER=True

# User config
ENV NVRUNX_USER="nvrunx" \
    DEFAULT_PUID=911 \
    DEFAULT_PGID=911

# Paths
ENV CODE_DIR=/app \
    DATA_DIR=/data \
    PATH="/app/.venv/bin:$PATH"

# Build shell config
SHELL ["/bin/bash", "-o", "pipefail", "-o", "errexit", "-o", "errtrace", "-o", "nounset", "-c"] 

# Force apt to leave downloaded binaries in /var/cache/apt
RUN echo 'Binary::apt::APT::Keep-Downloaded-Packages "1";' > /etc/apt/apt.conf.d/99keep-cache \
    && echo 'APT::Install-Recommends "0";' > /etc/apt/apt.conf.d/99no-intall-recommends \
    && echo 'APT::Install-Suggests "0";' > /etc/apt/apt.conf.d/99no-intall-suggests \
    && rm -f /etc/apt/apt.conf.d/docker-clean

# Create non-privileged user
RUN echo "[*] Setting up $NVRUNX_USER user uid=${DEFAULT_PUID}..." \
    && groupadd --system $NVRUNX_USER \
    && useradd --system --create-home --gid $NVRUNX_USER --groups audio,video $NVRUNX_USER \
    && usermod -u "$DEFAULT_PUID" "$NVRUNX_USER" \
    && groupmod -g "$DEFAULT_PGID" "$NVRUNX_USER" \
    && mkdir -p /data \
    && mkdir -p /home/$NVRUNX_USER/.config \
    && chown -R $NVRUNX_USER:$NVRUNX_USER /home/$NVRUNX_USER \
    && ln -s $DATA_DIR /home/$NVRUNX_USER/.config/nvrunx

# Install base apt dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked,id=apt-$TARGETARCH$TARGETVARIANT \
    echo "[+] Installing APT base system dependencies for $TARGETPLATFORM..." \
    && mkdir -p /etc/apt/keyrings \
    && apt-get update -qq \
    && apt-get install -qq -y --no-install-recommends \
        apt-transport-https ca-certificates apt-utils gnupg2 unzip curl wget grep \
        nano iputils-ping dnsutils jq \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency manifest
WORKDIR /app
COPY pyproject.toml /app/

# Set up Python environment
RUN echo "[+] Setting up venv using uv..." \
    && uv venv \
    && which python | grep "/app/.venv" \
    && python --version

# Install Chromium browser
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked,id=apt-$TARGETARCH$TARGETVARIANT \
    echo "[+] Installing chromium browser..." \
    && apt-get update -qq \
    && apt-get install -y --no-install-recommends \
        chromium \
        fonts-unifont \
        fonts-liberation \
        fonts-dejavu-core \
        fonts-freefont-ttf \
        fonts-noto-core \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/chromium /usr/bin/chromium-browser \
    && mkdir -p "/home/${NVRUNX_USER}/.config/chromium/Crash Reports/pending/" \
    && chown -R "$NVRUNX_USER:$NVRUNX_USER" "/home/${NVRUNX_USER}/.config" \
    && chromium-browser --version

# Install Python dependencies
RUN echo "[+] Installing nvrunx dependencies..." \
    && uv sync --all-extras --no-dev --no-install-project

# Copy the rest of the codebase
COPY . /app

# Install the nvrunx package
RUN echo "[+] Installing nvrunx from source..." \
    && uv sync --all-extras --no-dev \
    && python -c "import browser_use; print('nvrunx installed successfully')"

# Set up data directory
RUN mkdir -p "$DATA_DIR/profiles/default" \
    && chown -R $NVRUNX_USER:$NVRUNX_USER "$DATA_DIR"

USER "$NVRUNX_USER"
VOLUME "$DATA_DIR"
EXPOSE 9242
EXPOSE 9222

ENTRYPOINT ["python", "-m", "browser_use.cli"]