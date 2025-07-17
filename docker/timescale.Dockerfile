FROM timescale/timescaledb:latest-pg14

RUN apk update && apk add --no-cache \
    build-base \
    postgresql14-dev \
    clang15 \
    llvm15 \
    git \
    wget \
    make

RUN cd /tmp && \
    wget https://github.com/citusdata/pg_cron/archive/refs/tags/v1.6.4.tar.gz && \
    tar -xzf v1.6.4.tar.gz && \
    cd pg_cron-1.6.4 && \
    make && \
    make install && \
    cd / && \
    rm -rf /tmp/pg_cron-1.6.4 /tmp/v1.6.4.tar.gz

RUN apk del build-base postgresql14-dev git wget make

COPY pg_hba.conf /usr/local/share/postgresql/pg_hba.conf.sample
COPY timescaledb_postgresql.conf /etc/postgresql/postgresql.conf