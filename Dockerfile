FROM php:8.2-apache

# Install system packages including Python and dev tools
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    libpq-dev \
    wget \
    unzip \
    git \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install PHP ODBC extension (not needed - using PostgreSQL + DuckDB directly)
# RUN docker-php-ext-configure odbc --with-unixODBC=shared,/usr \
#     && docker-php-ext-install odbc

# Download DuckDB ODBC driver (optional, not needed for this project)
# RUN wget https://github.com/duckdb/duckdb/releases/download/v0.10.1/duckdb_odbc-linux-amd64.zip \
#     && unzip duckdb_odbc-linux-amd64.zip -d /usr/local/lib \
#     && rm duckdb_odbc-linux-amd64.zip

# ODBC configuration (not needed for PostgreSQL + DuckDB)
# COPY odbcinst.ini /etc/odbcinst.ini
# COPY odbc.ini /etc/odbc.ini

# Enable Apache mod_rewrite
RUN a2enmod rewrite

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Create Python symlink for convenience
RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /var/www/html