#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p output/comparison
for name in commons-text commons-io commons-codec; do
    mvn -B -f "examples/comparison/$name.xml" \
        org.apache.maven.plugins:maven-dependency-plugin:3.8.1:tree \
        -Dscope=runtime -DoutputType=text \
        -DoutputFile="$PWD/output/comparison/$name.txt"
done
