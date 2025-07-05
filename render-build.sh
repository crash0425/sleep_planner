#!/usr/bin/env bash

# Download the wkhtmltopdf Linux binary
curl -L https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.linux-generic-amd64.tar.xz > wkhtmltox.tar.xz

# Extract it
tar -xf wkhtmltox.tar.xz

# Move the binary to a place Render can access
mv wkhtmltox/bin/wkhtmltopdf /usr/local/bin/
chmod +x /usr/local/bin/wkhtmltopdf
