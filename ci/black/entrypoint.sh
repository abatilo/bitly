#!/bin/bash
set -ex
bash -c "poetry run black $*"
