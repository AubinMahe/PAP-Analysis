#!/usr/bin/env bash

readonly SCRIPT_DIR=$(dirname $(realpath "$0"))

rm -f "${SCRIPT_DIR}/pap.xpi"
cd "${SCRIPT_DIR}/xpi"
zip -r ../pap.xpi *
