# syntax=docker/dockerfile:1

# We only need the node modules for the frontend build
# We don't need to install npm within the final image
FROM node:19 AS node-install
WORKDIR /node-build/
COPY .yarnrc .
COPY package.json .
RUN yarn

# This is the final image that will be used in production
FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install OSS Gadget
# License: MIT
ARG OSSGADGET_VERSION="0.1.307"
RUN cd /opt
ADD https://github.com/microsoft/OSSGadget/releases/download/v${OSSGADGET_VERSION}/OSSGadget_linux_${OSSGADGET_VERSION}.tar.gz OSSGadget.tar.gz
RUN    tar zxvf OSSGadget.tar.gz && \
    rm OSSGadget.tar.gz && \
    mv OSSGadget_linux_${OSSGADGET_VERSION} OSSGadget


RUN apt-get update && apt-get install -y --no-install-recommends \
                        build-essential \
                        libmagic-dev \
                        postgresql \
                        postgresql-contrib \
                        musl-dev \
                        && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir .env && mkdir /data && mkdir /logs
# Uncomment below for local dev - during GH workflow this dir already exist
# RUN mkdir /tmp
RUN touch /logs/database.log

# Run this last to prevent cache invalidation when dependencies change
COPY requirements.txt .
# Run pip install upgrade to support any updates not caught by the requirements.txt
RUN pip install --upgrade pip
# Run pip install before copying the rest of the code to prevent cache invalidation
RUN pip install -r requirements.txt
# Copy the frontend build from the node-install stage.
# We don't need to have npm installed within the final image
COPY --from=node-install /node-build/triage/static/triage/resources /app/triage/static/triage/resources/

# Now, finally, copy the rest of the code
# This will invalidate the cache if any of the code changes, so we want to do this last
COPY . /app/

EXPOSE 8001

CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]
