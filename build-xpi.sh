#!/usr/bin/env bash

readonly SCRIPT_DIR=$(dirname $(realpath "$0"))

rm -f "${SCRIPT_DIR}/pap.xpi"
cd "${SCRIPT_DIR}/xpi"
zip -r ../pap.xpi *
mv ../pap.xpi /home/aubin/.thunderbird/q13e01zf.default/extensions/pap.analysis@hpms.org.xpi
thunderbird
