#!/bin/bash
# Pushes this project to GitHub. Create an EMPTY repo on github.com first (no README/.gitignore/license).
set -e
cd "$(dirname "$0")/.."
echo "Paste your GitHub repo URL (e.g. https://github.com/yourname/text-to-sql-rag.git):"
read -r URL
[ -z "$URL" ] && { echo "No URL given."; exit 1; }
if git remote get-url origin >/dev/null 2>&1; then git remote set-url origin "$URL"; else git remote add origin "$URL"; fi
git add -A
git diff --cached --quiet || git commit -m "chore: add GitHub push helper"
echo
echo "Pushing... When asked: Username = your GitHub username, Password = a personal access token (not your password)."
git push -u origin main
echo
echo "Done: ${URL%.git}"
