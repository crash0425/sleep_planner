#!/usr/bin/env bash

apt-get update && apt-get install -y \
  build-essential \
  libpango1.0-0 \
  libgdk-pixbuf2.0-0 \
  libffi-dev \
  libcairo2 \
  libpangoft2-1.0-0 \
  libpangocairo-1.0-0 \
  libxml2 \
  libxslt1.1 \
  libjpeg-dev \
  zlib1g-dev

pip install -r requirements.txt
