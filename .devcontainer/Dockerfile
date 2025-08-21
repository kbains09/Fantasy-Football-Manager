# .devcontainer/Dockerfile
FROM mcr.microsoft.com/devcontainers/base:ubuntu
RUN apt-get update && apt-get install -y curl build-essential python3-pip python3-venv
# Go
RUN curl -fsSL https://go.dev/dl/go1.22.5.linux-amd64.tar.gz -o /tmp/go.tgz \
 && tar -C /usr/local -xzf /tmp/go.tgz && ln -s /usr/local/go/bin/go /usr/local/bin/go
# Poetry
RUN pip3 install --no-cache-dir poetry
# Node (optional for Tailwind builds)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs
ENV PATH="/usr/local/go/bin:${PATH}"
