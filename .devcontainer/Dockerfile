ARG VARIANT=3.13-bookworm

FROM mcr.microsoft.com/vscode/devcontainers/python:${VARIANT}

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends swig graphviz ffmpeg texlive-xetex texlive-fonts-recommended texlive-plain-generic

# Microsoft SQL Server ODBC Driver for Linux
RUN apt-get update && \
    apt-get -y install curl && \
    apt-get update && \
    curl https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc && \
    curl https://packages.microsoft.com/config/debian/12/prod.list | tee /etc/apt/sources.list.d/mssql-release.list && \
    sed -i 's/ signed-by=\/usr\/share\/keyrings\/microsoft-prod.gpg//' /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get -q -y install msodbcsql18 && \
    apt-get update && \
    apt-get -y install unixodbc-dev