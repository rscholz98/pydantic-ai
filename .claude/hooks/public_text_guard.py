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
# GitHub owners (orgs or users) whose repos are Richard's own: a `gh` command targeting one of
# them with `-R`/`--repo` skips the blocked-name check, since those names are not secret there.
# Kept off the repo like the names themselves.
OWN_ORGS_FILE = Path.home() / '.config/pydantic-ai-public-guard/own-orgs.txt'
MENTION = re.compile(r'(?<![\w.`/=<\-])@([A-Za-z0-9][A-Za-z0-9-]{0,38})\b')
# Richard's own handle, allowed in the "on behalf of" attribution line of larger posts.
SELF_HANDLE = 'rscholz98'
FILE_FLAGS = {'-F', '--file', '--body-file', '-b'}


CONTROL = re.compile(r'\|\||&&|\|&|;|\||&|\n|\(|\)|\{|\}')
"""Shell control operators and grouping: a command is checked segment by segment so one own-repo
flag cannot cover a second, public invocation on the same line. A legitimate `&` or `|` inside
quoted text makes a segment unparsable, which fails closed to the name check."""

REPO_REF = re.compile(r'^(?P<owner>[\w.-]+)/[\w.-]+#\d+$')
"""A positional `owner/repo#N` reference. Bare `owner/repo` is never a selector (a `--body-file`
path looks the same), so only the numbered form counts."""


def own_repo_owner(tokens: list[str], own: set[str]) -> bool:
    """One simple `gh pr|issue ...` invocation that targets, by flag and by any positional
    reference, exactly one repo under an own owner. Any flag or target form this does not
    recognise exactly fails closed."""
    if len(tokens) < 3 or tokens[0] != 'gh' or tokens[1] not in {'pr', 'issue'}:
        return False
    flag_owners: list[str] = []
    positional_owners: list[str] = []
    i = 2
    while i < len(tokens):
        tok = tokens[i]
        if tok in {'-R', '--repo'}:
            if i + 1 >= len(tokens):
                return False
            value, i = tokens[i + 1], i + 2
        elif tok.startswith('--repo='):
            value, i = tok[len('--repo='):], i + 1
        elif tok.startswith('-R') or tok.startswith('--repo'):
            return False  # `-Rowner/repo` and other forms pflag accepts but this parser does not
        else:
            lowered = tok.lower()
            if 'github' in lowered or '://' in lowered:
                return False  # a URL target in any spelling; only the flag form is exempted
            if (m := REPO_REF.match(tok)) and not tok.startswith(('-', '.', '/', '~')):
                positional_owners.append(m.group('owner').lower())
            i += 1
            continue
        value = value.removeprefix('https://github.com/')
        flag_owners.append(value.split('/')[0].lower() if '/' in value else '')
    if len(flag_owners) != 1 or flag_owners[0] not in own:
        return False
    return all(owner in own for owner in positional_owners)


def own_repo(command: str) -> bool:
    """True only for the narrowest shape: optional `cd <path> &&` segments, then exactly one
    validated own-repo `gh pr|issue ...` call, and no shell expansion character (`$`, backtick)
    anywhere in the command. Every other shape, including any wrapper, a second command of any
    kind, or a segment that cannot be parsed, fails closed and keeps the blocked-name check."""
    if not OWN_ORGS_FILE.is_file():
        return False
    own = {o.strip().lower() for o in OWN_ORGS_FILE.read_text().splitlines() if o.strip() and not o.startswith('#')}
    if '$' in command or '`' in command:
        return False
    validated = 0
    for seg in CONTROL.split(command):
        if not seg.strip():
            continue
        try:
            tokens = shlex.split(seg)
        except ValueError:
            return False
        if not tokens:
            continue
        if tokens[0] == 'cd' and len(tokens) == 2:
            continue
        if len(PUBLIC.findall(seg)) != 1 or not own_repo_owner(tokens, own):
            return False
        validated += 1
    return validated == 1


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
    if NAMES_FILE.is_file() and not own_repo(command):
        names = [n.strip() for n in NAMES_FILE.read_text().splitlines() if n.strip() and not n.startswith('#')]
        if names:
            checks.append((re.compile(r'\b(?:' + '|'.join(names) + r')\b'), 'blocked company/product/customer name'))
    for text in texts:
        for pattern, label in checks:
            if pattern.search(text) and label not in problems:
                problems.append(label)
        mentions = sorted(set(MENTION.findall(strip_code(text))) - {SELF_HANDLE})
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
