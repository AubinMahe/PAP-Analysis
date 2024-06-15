#!/usr/bin/env bash

readonly COMMAND='\x55\x0\x0\x0{"action":"extract-text","path":"/tmp/2024 04 18 - Vehicules de loisirs Horizon.pdf"}'

(echo -e "${COMMAND}" ; cat) | python3 analyse.py
