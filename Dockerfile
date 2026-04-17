FROM php:8.2-apache

# Instalace systémových knihoven pro ODBC
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    odbcinst \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Instalace a zapnutí PHP ODBC rozšíření
RUN docker-php-ext-configure odbc --with-unixODBC=shared,/usr \
    && docker-php-ext-install odbc

# Stažení DuckDB ODBC driveru (Linux x64)
RUN wget https://github.com/duckdb/duckdb/releases/download/v0.10.1/duckdb_odbc-linux-amd64.zip \
    && unzip duckdb_odbc-linux-amd64.zip -d /usr/local/lib \
    && rm duckdb_odbc-linux-amd64.zip

# Kopírování ODBC konfigurace do kontejneru
COPY odbcinst.ini /etc/odbcinst.ini
COPY odbc.ini /etc/odbc.ini

# Zapnutí Apache mod_rewrite (pro hezké URL, volitelné)
RUN a2enmod rewrite

WORKDIR /var/www/html