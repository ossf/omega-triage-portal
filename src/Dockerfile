#FROM nginx:alpine
#COPY .. /usr/share/nginx/html
#COPY ./site/ /usr/share/nginx/html/

FROM docker
COPY --from=docker/buildx-bin /buildx /usr/libexec/docker/cli-plugins/docker-buildx
RUN docker buildx version

# syntax=docker/dockerfile:1
FROM python:3.8-alpine3.17
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# [Choice] Node.js version: none, lts/*, 16, 14, 12, 10
ARG NODE_VERSION="none"
RUN if [ "${NODE_VERSION}" != "none" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

# Install OSS Gadget
# License: MIT
ARG OSSGADGET_VERSION="0.1.307"
RUN cd /opt && \
    wget -q https://github.com/microsoft/OSSGadget/releases/download/v${OSSGADGET_VERSION}/OSSGadget_linux_${OSSGADGET_VERSION}.tar.gz -O OSSGadget.tar.gz && \
    tar zxvf OSSGadget.tar.gz && \
    rm OSSGadget.tar.gz && \
    mv OSSGadget_linux_${OSSGADGET_VERSION} OSSGadget


RUN apk update && apk add python3-dev \
                        gcc \
                        libc-dev \
                        postgresql-dev \
                        musl-dev  \
                        libffi-dev \
                        libmagic

WORKDIR /app
COPY src/requirements.txt .
RUN mkdir .env
RUN mkdir /data
RUN mkdir /logs
# Uncomment below for local dev - during GH workflow this dir already exist
RUN mkdir /tmp
RUN touch /logs/database.log
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /app/

EXPOSE 8001

CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]
