#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
expect_error() {
    if sh run.sh "$@"; then
        echo "Ожидалась ошибка" >&2
        exit 1
    fi
}
expect_error --package bad
expect_error --package g:a:1 --repo ftp://host
expect_error --package A --test --repo missing.json
expect_error --package g:a:1 --output a.jpg
expect_error --package g:a:1 --ascii yes
expect_error --package g:a:1 --filter a
expect_error --package g:a:1 --test no
