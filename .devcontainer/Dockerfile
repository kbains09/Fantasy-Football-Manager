# .devcontainer/Dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.13

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# ---- OS deps (add libpq-dev for Postgres bindings) ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates git build-essential pkg-config libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# ---- Go 1.22 ----
ARG GO_VERSION=1.22.5
RUN curl -fsSL https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz -o /tmp/go.tgz \
 && tar -C /usr/local -xzf /tmp/go.tgz \
 && ln -sf /usr/local/go/bin/go /usr/local/bin/go \
 && mkdir -p /go/bin \
 && printf 'export GOPATH=/go\nexport PATH=$PATH:/go/bin:/usr/local/go/bin\n' >> /etc/profile

ENV GOPATH=/go
ENV PATH=$PATH:/go/bin:/usr/local/go/bin

# ---- Poetry (global via pipx) ----
RUN pipx install poetry \
 && ln -sf /root/.local/bin/poetry /usr/local/bin/poetry \
 && poetry config virtualenvs.create false

# ---- Node 20 (for Tailwind/asset builds) ----
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get update && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

# ---- Dev user (devcontainers usually already has vscode, but this is safe) ----
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN if ! id -u ${USERNAME} >/dev/null 2>&1; then \
      groupadd --gid ${USER_GID} ${USERNAME} && \
      useradd -s /bin/bash --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME}; \
    fi
USER ${USERNAME}

# Final PATH sanity
ENV PATH="/usr/local/go/bin:${PATH}"
WORKDIR /workspace
