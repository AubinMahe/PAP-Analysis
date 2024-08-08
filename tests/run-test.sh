#!/usr/bin/env bash

readonly SCRIPT_DIR=$(readlink -f $(dirname "$0"))
# readonly TEST_FILE="2024 04 18 - Vehicules de loisirs Horizon.pdf"
readonly TEST_FILE="2024 07 15 - ECF.pdf"
readonly COMMAND='\x55\x0\x0\x0{"action":"extract-text","path":"'"/tmp/${TEST_FILE}"'"}'

cp "${SCRIPT_DIR}/${TEST_FILE}" /tmp/
cd "${SCRIPT_DIR}/../native"
(echo -e "${COMMAND}" ; cat) | python3 analyse.py
