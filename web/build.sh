#!/usr/bin/env bash
# Assemble the static site in _site/: web front end + shared Python core + data.
# Usage: web/build.sh [output_dir]
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
out="${1:-$root/_site}"

rm -rf "$out"
mkdir -p "$out"

cp "$root"/web/index.html "$root"/web/app.js "$root"/web/worker.js "$root"/web/style.css "$out"/
cp "$root"/web/py/webapp.py "$out"/

cd "$root"
files=(webapp.py)

for f in algorithms/*.py models/*.py routing/*.py data/*.csv; do
  mkdir -p "$out/$(dirname "$f")"
  cp "$f" "$out/$f"
  files+=("$f")
done

# Manifest the worker uses to copy the sources into Pyodide's filesystem.
printf '%s\n' "${files[@]}" | python3 -c 'import json, sys; print(json.dumps(sys.stdin.read().split()))' > "$out/files.json"

echo "Built $out (${#files[@]} files)"
