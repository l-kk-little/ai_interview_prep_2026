#!/usr/bin/env python3
"""Check local Markdown targets and explicit exercise paths without executing commands.

Links/inline ./ and ../ paths resolve from their Markdown file. Shell fences and
inline shell commands resolve from repo root, following literal cd per fence.
This is a bounded static audit, not a Markdown renderer or shell interpreter:
anchors, URLs, conceptual API routes and arbitrary pseudocode filenames are not
validated. Shell variables/globs require human review (reported as warnings).
"""
import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import shlex
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[\"\'][^\n]*?[\"\'])?\s*\)')
REF_DEF = re.compile(r'^\s{0,3}\[([^\]]+)\]:\s*(<[^>]+>|\S+)', re.M)
REF_USE = re.compile(r'!?\[([^\]\n]+)\]\[([^\]\n]*)\]')
HTML = re.compile(r'\b(?:href|src)\s*=\s*[\"\']([^\"\']+)[\"\']', re.I)
EXPLICIT = re.compile(r'(?<![\w:/])(?:\.\.?/)+(?:[\w.@%+~-]+/)*[\w.@%+~-]*(?:/)?')
PRIVATE = re.compile(r'(?:/(?:Users|home)/[^\s`\"\'<>，；）)]+|[A-Za-z]:\\Users\\[^\s`]+)')
FENCE = re.compile(r'^\s*(`{3,}|~{3,})([^\n]*)$')
SHELL = re.compile(r'^(?:\$\s*)?(?:(?:[A-Z_]+=[^ ]+)\s+)*(?:cd|python3?|pytest|bash|sh)\s')


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    kind: str
    target: str
    detail: str

    def __str__(self):
        return f'{self.file}:{self.line}: {self.kind}: {self.target} ({self.detail})'


def audit(root=ROOT, repo=None):
    root = Path(root).resolve()
    repo = Path(repo).resolve() if repo else root.parent
    errors, warnings = [], []
    files = sorted(p for p in root.rglob('*.md') if not {'viewer', '.git', '__pycache__'} & set(p.relative_to(root).parts))

    def report(md, n, kind, target, base):
        target = target.strip('<>')
        if urlsplit(target).scheme or target.startswith(('#', '//')):
            return
        path = unquote(target.split('#', 1)[0].split('?', 1)[0])
        if not path:
            return
        dest = (base / path).resolve()
        reason = 'outside repository' if not dest.is_relative_to(repo) else 'missing'
        if not dest.is_relative_to(repo) or not dest.exists():
            errors.append(Finding(str(md.relative_to(root)), n, kind, target, reason))

    def shell(md, n, command, cwd):
        try:
            lexer = shlex.shlex(command, posix=True, punctuation_chars=';&|')
            lexer.whitespace_split = True
            lexer.commenters = '#'
            tokens = list(lexer)
        except ValueError:
            warnings.append(Finding(str(md.relative_to(root)), n, 'review shell', command, 'unparsed quotation'))
            return cwd
        groups, group = [], []
        for tok in tokens + [';']:
            if tok in (';', '&&', '||', '|', '&'):
                if group: groups.append(group)
                group = []
            else: group.append(tok)
        for args in groups:
            while args and ('=' in args[0] or args[0] in ('$', 'env')):
                args = args[1:]
            if not args: continue
            candidates = []
            if args[0] == 'cd' and len(args) > 1:
                candidates = [args[1]]
            elif args[0] in ('python', 'python3', 'bash', 'sh', 'pytest'):
                if len(args) > 1 and not args[1].startswith('-'): candidates.append(args[1])
                for i, arg in enumerate(args[:-1]):
                    if arg in ('-s', '--start-directory'): candidates.append(args[i+1])
                if '-m' in args and 'unittest' in args and 'discover' not in args:
                    candidates.extend(a for a in args[2:] if a.endswith('.py'))
            if 'unittest' in args and 'discover' in args:
                def option(short, long, default):
                    for flag in (short, long):
                        if flag in args and args.index(flag) + 1 < len(args):
                            return args[args.index(flag) + 1]
                    return default
                start = option('-s', '--start-directory', '.')
                pattern = option('-p', '--pattern', 'test*.py')
                if not any(c in start for c in '$~{}') and not list((cwd / start).glob(pattern)):
                    errors.append(Finding(str(md.relative_to(root)), n, 'test pattern', pattern, 'no matching tests'))
            for target in dict.fromkeys(candidates):
                if any(c in target for c in '$*{}~'):
                    warnings.append(Finding(str(md.relative_to(root)), n, 'review shell', target, 'dynamic path'))
                else: report(md, n, 'command path', target, cwd)
            if args[0] == 'cd' and candidates and not any(c in candidates[0] for c in '$*{}~'):
                cwd = (cwd / candidates[0]).resolve()
        return cwd

    for md in files:
        text = md.read_text(encoding='utf-8')
        definitions = {m[1].strip().casefold(): m[2] for m in REF_DEF.finditer(text)}
        fence = None
        language = ''
        cwd = repo
        for n, line in enumerate(text.splitlines(), 1):
            marker = FENCE.match(line)
            if marker:
                if fence is None:
                    fence, language, cwd = marker[1], marker[2].strip().lower(), repo
                elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence): fence = None
                continue
            example = re.search(r'<!-- path-check: example (.+?) -->', line)
            if example:
                warnings.append(Finding(str(md.relative_to(root)), n, 'documented example', example[1], 'not a repository asset'))
                continue
            for m in PRIVATE.finditer(line):
                errors.append(Finding(str(md.relative_to(root)), n, 'machine path', m[0], 'not portable'))
            is_shell = fence is not None and language in ('bash', 'sh', 'shell', 'console')
            if is_shell:
                cwd = shell(md, n, line.strip(), cwd)
                continue
            if fence is None:
                plain = re.sub(r'`[^`]*`', '', line)
                for pattern in (LINK, HTML):
                    for m in pattern.finditer(plain): report(md, n, 'link', m[1], md.parent)
                for m in REF_DEF.finditer(plain): report(md, n, 'reference', m[2], md.parent)
                for m in REF_USE.finditer(plain):
                    key = (m[2] or m[1]).strip().casefold()
                    if key not in definitions:
                        errors.append(Finding(str(md.relative_to(root)), n, 'reference', key, 'undefined'))
                for m in re.finditer(r'`([^`]+)`', line):
                    code = m[1]
                    if SHELL.match(code): shell(md, n, code, repo)
                    else:
                        for match in EXPLICIT.finditer(code): report(md, n, 'inline path', match[0], md.parent)
                # Bare explicit cross-directory paths in prose (not link targets).
                for m in EXPLICIT.finditer(re.sub(LINK, '', plain)):
                    report(md, n, 'prose path', m[0], md.parent)
            else:
                for m in EXPLICIT.finditer(line): report(md, n, 'code path', m[0], md.parent)
    return files, list(dict.fromkeys(errors)), list(dict.fromkeys(warnings))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--repo-root', type=Path)
    args = parser.parse_args()
    files, errors, warnings = audit(args.root, args.repo_root)
    for item in warnings: print(f'WARN: {item}')
    for item in errors: print(f'ERROR: {item}')
    print(f'{"FAIL" if errors else "OK"}: {len(files)} Markdown files, {len(errors)} errors, {len(warnings)} warnings')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
