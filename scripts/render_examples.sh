#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
sh run.sh --package org.apache.commons:commons-text:1.12.0 \
    --output output/commons-text.png --ascii
sh run.sh --package commons-io:commons-io:2.16.1 \
    --output output/commons-io.png --ascii
sh run.sh --package commons-codec:commons-codec:1.17.1 \
    --output output/commons-codec.png --ascii
