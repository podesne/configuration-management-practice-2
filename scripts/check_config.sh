#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
sh run.sh --package org.apache.commons:commons-text:1.12.0 \
  --repo https://repo.maven.apache.org/maven2 \
  --output output/text.png --ascii --filter junit
