"""Repository-wide relative Markdown link check (review VN-15, FP-15). CAD-free, read-only.

Scans every Markdown file git knows about (tracked, plus untracked files that are not ignored) and resolves each
relative link target from the file's folder. A target counts only if git knows it (tracked, or untracked and not
ignored) or it is a folder holding such a file: a git-ignored local file, or a path outside the repository, is a broken
link even when it exists on this machine (review 2026-10-13 R-18). A broken link is allowed only when its file is one of:
  inherited  byte-identical to the upstream r7 commit (UPSTREAM, d38468e): r7 content carried unchanged; its links are
             r7's own and are not rewritten here (the r7 release audit binds some of these files);
  frozen     a declared frozen copy (FROZEN below: copied history and snapshot records whose bytes are kept, several of
             them hash-bound) that carries the frozen-links banner, either in the file itself or in a FROZEN-LINKS.md
             notice in the same folder that names the file.
Every other broken link fails (exit 1). Live candidate documents must have none.
  python check_links_vertical.py          summary + failures (JSON)
  python check_links_vertical.py --list   also every allowed broken link
"""
from pathlib import Path
from urllib.parse import unquote
import argparse, json, re, subprocess, sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
UPSTREAM = 'd38468e58eb2b02d56743e2e0cfdd8f780818a65'
CV = 'cad/gs8-d2-v1/candidate-vertical/'
FROZEN = (CV + 'history/', CV + 'routing-snapshots/', CV + 'vent-study/angled-channel-trial/')
BANNER = 'frozen copy: relative links point to the original location'
NOTICE = 'FROZEN-LINKS.md'


def git(*args):
    return subprocess.run(['git', '-C', str(REPO)] + list(args), capture_output=True, check=True).stdout.decode('utf-8')


def markdown_files():
    names = git('ls-files', '-z', '--cached', '--others', '--exclude-standard', '--', '*.md').split('\0')
    return sorted({n for n in names if n and (REPO / n).is_file()})


def links(text):
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    text = re.sub(r'`[^`\n]*`', '', text)
    for m in re.finditer(r'\[[^\]\n]*\]\(([^\n)]+)\)', text):
        t = m.group(1).strip()
        t = t[1:t.index('>')] if t.startswith('<') and '>' in t else t.split(' "')[0].split(" '")[0]
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', t) or t.startswith('#'):
            continue
        t = unquote(t.split('#', 1)[0].split('?', 1)[0])
        if t:
            yield t


def known_paths():
    """Repo-relative POSIX paths git knows (tracked, or untracked and not ignored), plus every folder that holds one."""
    files = {n for n in git('ls-files', '-z', '--cached', '--others', '--exclude-standard').split('\0') if n}
    folders = {''}
    for n in files:
        parts = n.split('/')
        for i in range(1, len(parts)):
            folders.add('/'.join(parts[:i]))
    return files, folders


def target_known(target, files, folders, repo=None):
    """True when `target` exists and git knows it; ignored or outside-repo targets are not accepted."""
    repo = Path(repo or REPO).resolve()
    if not Path(target).exists():
        return False
    try:
        rel = Path(target).resolve().relative_to(repo).as_posix()
    except ValueError:
        return False
    rel = '' if rel == '.' else rel
    return rel in files or rel in folders


def upstream_blobs():
    out = {}
    for line in git('ls-tree', '-r', UPSTREAM).splitlines():
        meta, path = line.split('\t', 1)
        out[path] = meta.split()[2]
    return out


def blob(path):
    return git('hash-object', '--', path).strip()


def bannered(rel):
    p = REPO / rel
    if BANNER in p.read_text(encoding='utf-8', errors='replace'):
        return True
    notice = p.parent / NOTICE
    return notice.is_file() and BANNER in notice.read_text(encoding='utf-8') and ('`%s`' % p.name) in notice.read_text(encoding='utf-8')


def run():
    up = upstream_blobs()
    checked, broken = 0, []
    files, folders = known_paths()
    for rel in markdown_files():
        text = (REPO / rel).read_text(encoding='utf-8', errors='replace')
        for t in links(text):
            checked += 1
            target = (REPO / rel).parent / t
            if not target_known(target, files, folders):
                broken.append((rel, t))
    files = sorted({r for r, _ in broken})
    cls = {}
    for rel in files:
        if up.get(rel) and up[rel] == blob(rel):
            cls[rel] = 'inherited'
        elif rel.startswith(FROZEN):
            cls[rel] = 'frozen' if bannered(rel) else 'frozen_without_banner'
        else:
            cls[rel] = 'live'
    allowed = [(r, t, cls[r]) for r, t in broken if cls[r] in ('inherited', 'frozen')]
    failures = [(r, t, cls[r]) for r, t in broken if cls[r] not in ('inherited', 'frozen')]
    by = {}
    for r, t, c in allowed + failures:
        by[c] = by.get(c, 0) + 1
    return dict(markdown_files=len(markdown_files()), links_checked=checked, broken=len(broken), broken_by_class=by,
                failures=failures, allowed=allowed)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args(argv)
    r = run()
    if not a.list:
        r = {k: v for k, v in r.items() if k != 'allowed'}
    print(json.dumps(r, indent=1))
    return 1 if r['failures'] else 0


if __name__ == '__main__':
    sys.exit(main())
