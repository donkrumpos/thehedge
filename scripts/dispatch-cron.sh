#!/bin/sh
# Cron wrapper for The Hedge daily dispatch.
# Sources the API key from a non-committed env file, runs the generator,
# publishes, and logs. Secret lives in ~/.config/thehedge/dispatch.env (chmod 600),
# never in git. Installed via crontab: see scripts/README or `crontab -l`.

export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

ENV_FILE="$HOME/.config/thehedge/dispatch.env"
LOG="$HOME/.config/thehedge/dispatch.log"

[ -f "$ENV_FILE" ] && . "$ENV_FILE"
export OPENAI_MODEL="${OPENAI_MODEL:-gpt-5.1}"

echo "===== $(date) =====" >> "$LOG"
cd "$HOME/Documents/Projects/thehedge" || { echo "cd failed" >> "$LOG"; exit 1; }
/opt/homebrew/bin/python3 scripts/dispatch.py --publish >> "$LOG" 2>&1
echo "exit: $?" >> "$LOG"
