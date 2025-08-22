# .devcontainer/Dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.13

ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates git build-essential pkg-config libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# ---- Go (auto-detect arch) ----
ARG GO_VERSION=1.22.5
RUN ARCH="$(dpkg --print-architecture)"; \
    case "$ARCH" in \
      amd64) GOARCH=amd64 ;; \
      arm64) GOARCH=arm64 ;; \
      *) echo "Unsupported arch: $ARCH" && exit 1 ;; \
    esac; \
    curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-${GOARCH}.tar.gz" -o /tmp/go.tgz && \
    tar -C /usr/local -xzf /tmp/go.tgz && \
    ln -sf /usr/local/go/bin/go /usr/local/bin/go

# ---- Poetry via pipx; ----
RUN pipx install poetry \
 && ln -sf /root/.local/bin/poetry /usr/local/bin/poetry \
 && poetry config virtualenvs.create false

# ---- Node 20 (optional, for assets) ----
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get update && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

# Ensure 'vscode' user exists
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN if ! id -u ${USERNAME} >/dev/null 2>&1; then \
      groupadd --gid ${USER_GID} ${USERNAME} && \
      useradd -s /bin/bash --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME}; \
    fi

# ---- Make GOPATH user-writable and on PATH ----
USER root
RUN mkdir -p /home/${USERNAME}/go/bin && chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}/go
USER ${USERNAME}
ENV GOPATH=/home/${USERNAME}/go
ENV GOBIN=/home/${USERNAME}/go/bin
ENV GOMODCACHE=/home/${USERNAME}/go/pkg/mod
ENV PATH=${PATH}:/usr/local/go/bin:${GOBIN}

WORKDIR /workspace
