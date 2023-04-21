FROM postgres:15
ADD scripts/ /docker-entrypoint-initdb.d
RUN chmod a+r /docker-entrypoint-initdb.d/*
