#!/bin/bash
set -ex
bash -c "poetry run python -m pytest $*"
