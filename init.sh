#!/bin/bash
set -e

script_dir="$(cd "$(dirname "$0")" && pwd)"
venv_dir="$script_dir/venv"
echo "Using venv directory: $venv_dir"

if [[ ! -d "$venv_dir" ]]; then
  python3 -m venv "$venv_dir"
fi

. "$venv_dir/bin/activate"

"$venv_dir/bin/python" -m pip --require-virtualenv install --upgrade pip
"$venv_dir/bin/python" -m pip --require-virtualenv install --upgrade -r "$script_dir/requirements.txt"
