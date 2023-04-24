FROM postgres:15
COPY scripts/ /docker-entrypoint-initdb.d/
RUN chmod a+r /docker-entrypoint-initdb.d/*
