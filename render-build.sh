#!/usr/bin/env bash

# Exit on error
set -o errexit

# Install WeasyPrint dependencies
apt-get update
apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libxml2 \
    libxslt1.1 \
    libjpeg-dev \
    zlib1g-dev \
    libssl-dev \
    libpq-dev \
    python3-dev \
    curl

echo "✅ System dependencies for WeasyPrint installed"

