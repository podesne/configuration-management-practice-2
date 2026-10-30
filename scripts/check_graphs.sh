#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
for name in single chain basic cycle self reverse; do
    sh run.sh --package A --test --repo "examples/$name.json"
done
sh run.sh --package A --test --repo examples/basic.json --filter B
