#!/usr/bin/env python3
"""PreToolUse guard for text that leaves the machine under Richard's name.

Scans `git commit` messages and `gh` issue/PR/comment/review bodies (inline or from a
file) and denies the call when the text carries a Claude attribution trailer, an em
dash, a name listed in NAMES_FILE, or an `@` mention outside code. Everything
else passes untouched.
"""

from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path

PUBLIC = re.compile(
    r'\bgit\s+(?:-C\s+\S+\s+)?commit\b'
    r'|\bgh\s+(?:pr|issue)\s+(?:create|edit|comment|review|close)\b'
    r'|\bgh\s+api\b[^|;&]*(?:comments|replies|reviews|issues|pulls)'
)
CHECKS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r'(?i)co-authored-by:[^\n]*(?:claude|anthropic)|claude-session:'), 'Claude attribution trailer'),
    (re.compile('\u2014'), 'em dash'),
]
# One regex per line, kept off the repo so the names themselves stay private.
NAMES_FILE = Path.home() / '.config/pydantic-ai-public-guard/blocked-names.txt'
MENTION = re.compile(r'(?<![\w.`/=<\-])@([A-Za-z0-9][A-Za-z0-9-]{0,38})\b')
FILE_FLAGS = {'-F', '--file', '--body-file', '-b'}


def referenced_files(command: str) -> list[str]:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return []
    files: list[str] = []
    for i, tok in enumerate(tokens):
        if '=@' in tok:
            files.append(tok.split('=@', 1)[1])
        elif tok in FILE_FLAGS and i + 1 < len(tokens) and tokens[i + 1] != '-':
            files.append(tokens[i + 1])
        elif tok.startswith('--body-file='):
            files.append(tok.split('=', 1)[1])
    return files


def strip_code(text: str) -> str:
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    return re.sub(r'`[^`\n]*`', '', text)


def main() -> None:
    payload = json.load(sys.stdin)
    command = payload.get('tool_input', {}).get('command', '')
    if not PUBLIC.search(command):
        return
    texts = [command]
    cwd = Path(payload.get('cwd') or '.')
    for name in referenced_files(command):
        path = Path(name).expanduser()
        path = path if path.is_absolute() else cwd / path
        if path.is_file():
            texts.append(path.read_text(errors='replace'))
    problems: list[str] = []
    checks = list(CHECKS)
    if NAMES_FILE.is_file():
        names = [n.strip() for n in NAMES_FILE.read_text().splitlines() if n.strip() and not n.startswith('#')]
        if names:
            checks.append((re.compile(r'\b(?:' + '|'.join(names) + r')\b'), 'blocked company/product/customer name'))
    for text in texts:
        for pattern, label in checks:
            if pattern.search(text) and label not in problems:
                problems.append(label)
        mentions = sorted(set(MENTION.findall(strip_code(text))))
        if mentions:
            problems.append('@ mention of ' + ', '.join(mentions))
    if not problems:
        return
    reason = (
        'Public text for pydantic-ai breaks Richard\'s rules: ' + '; '.join(problems) + '. '
        'Remove it and retry (no Claude trailers, no em dashes, no blocked names, '
        'no @ mentions outside backticks).'
    )
    print(json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': reason,
    }}))


if __name__ == '__main__':
    main()
