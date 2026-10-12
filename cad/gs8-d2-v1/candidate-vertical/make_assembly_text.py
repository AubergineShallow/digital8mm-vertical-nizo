# SPDX-License-Identifier: MIT
"""Generated build-order and service blocks of ASSEMBLY-VERTICAL.md, written from steps.py (review 2026-10-10,
FP-06; closes the text side of VN-39/40/41/42/43/44/45/46).

    python make_assembly_text.py            rewrite the generated blocks in place
    python make_assembly_text.py --check    exit 1 if a block is missing, duplicated or stale (nothing written)

Blocks (everything outside them is hand-written; edit steps.py, never the block text):
  <!-- BEGIN:ops <label> --> .. <!-- END:ops <label> -->        one per steps.py section label (B0..B4, 1..8)
  <!-- BEGIN:service-routes --> .. <!-- END:service-routes -->  every SERVICE route: prerequisites, removal ops,
                                                                 the build op(s) that refit each removal
  <!-- BEGIN:service-matrix --> .. <!-- END:service-matrix -->  r7 baseline vs candidate dependency matrix,
                                                                 including both lens-change rows (VN-42)
The candidate columns are computed from steps.py (route closure, parts out, cables parted, refit chain); the r7
column quotes r7 ASSEMBLY.md section 7 (d38468e). Nothing here is a measurement. Pure Python: no CAD import.
"""
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import steps as ST  # noqa: E402
from cv_io import read_text, write_text  # noqa: E402

DOC = HERE / 'ASSEMBLY-VERTICAL.md'
_BLOCK = re.compile(r'<!-- BEGIN:(?P<name>[^>]*?) -->\n(?P<body>.*?)<!-- END:(?P=name) -->', re.S)
SHORT_TOOL = {ST.PH1: 'straight PH1 on the screw axis', ST.SOCKET: 'deep socket on the nut axis'}

# r7 baseline service (r7 ASSEMBLY.md section 7, d38468e) and the change, per candidate route. Hand-written facts.
MATRIX = [
    ('safety', 'Isolation (section 1)',
     'P1-P4: shutdown, cap off, pack out by its ribbon, XT30 parted by its housings.',
     'Same rule.'),
    ('panel', 'Control panel',
     'Items 3-5: eyecup off, 4 panel screws (hood-down pose), panel +Y about 60 mm, QT and 18/24 PH parted; the '
     'knobs ride with the panel.',
     'FPS knob, nut (deep socket) and washer come off first; the CK1044 switch stays with the module. Every panel '
     'removal is one cycle of the 30-cycle J2 pair (VN-42).'),
    ('storage', 'Recording drive',
     'Item 2: stick and sleeve out rearward (-X 70).',
     'Same direction.'),
    ('lens', 'Lens change, same collar (lens off and on)',
     '"Lens swap": panel on, body closed, no isolation (nothing electrical is touched); s_c4 one turn, nose-down, '
     'fingertip unscrew; refit with the turn-back, s_c4 0.2 N m.',
     'Closed body as in r7, refit by the r7 nose-down method (5.2). The candidate keeps the isolation route first '
     '(conservative).'),
    ('evf', 'EVF board/OLED',
     'Item 7: pack out, panel off; HDMI unplugged downward, OLED/pad/board +Y 45, eyepiece -X 30.',
     'Similar; the eyepiece stays. Finger/pliers corridor for the HDMI head not re-measured (VN-43).'),
    ('microsd', 'OS microSD',
     'Item 8: pack out; tweezers through the front slot, before the stack moves.',
     'Panel off first (closed-panel +X path blocked by the power switch); panel-off reach unqualified (VN-29, user '
     'decision).'),
    ('module', 'Pi/UPS/cooler module',
     'Item 10 (Pi stack): panel, lens, camera, collar, EVF, microSD and hood out first (items 3-9).',
     'Much shorter than r7: lens, camera, collar and EVF stay in. Passes through the module STOPs (FPC release, '
     'pigtail withdrawal, run-lead reach, fixed-to-carried leads).'),
    ('camera', 'Camera / adapter',
     'Items 6a-6b: pack out, panel off, lens off, camera -X 11.1 / up 2 / +Y 60; the collar may stay.',
     'REGRESSION (VN-42): the whole module must come out first; the camera meets the carrier after 3.9 mm. User '
     'decision 5 (section 5.3).'),
    ('collar', 'Lens change, different collar (collar swap, e.g. Kowa to Fujinon)',
     'Lens swap note + item 6c: panel off, lens and camera out (items 6a-6b), collar off, then step 7 with that '
     "collar's centring gauge (camera out), then step 8.",
     'REGRESSION (VN-42): full electronics teardown, because the gauge needs the empty lip and the camera needs the '
     'module out. User decision 5 (section 5.3).'),
    ('grip', 'Grip / base',
     'Item 11, after the Pi stack (items 8-10): run lead down through the floor hole, s_j out, base 10 mm rearward '
     'and off.',
     'Same dependency: module out first (VN-45 default); an inline run-lead junction is user decision 11.'),
]


def _idx():
    return {o['id']: i for i, o in enumerate(ST.STEPS)}


def _ids(xs):
    return ', '.join('`%s`' % x for x in xs)


def render_ops(label, steps=None):
    """Numbered operations of one ASSEMBLY section label, from steps.describe()."""
    sec = next((s for s in ST.describe(steps) if s['step'] == label), None)
    if sec is None:
        raise KeyError('no steps.py section %r' % label)
    out = []
    for n, o in enumerate(sec['ops'], 1):
        out.append('%d. **`%s`** %s' % (n, o['id'], o['doc']))
        extra = []
        if o['adds']:
            extra.append('*%s:* %s.' % ('Into the %s group' % ('bench' if o['where'] == 'bench' else 'staged')
                                          if o['where'] != 'body' else 'Enters', _ids(o['adds'])))
        if o['removes']:
            extra.append('*Leaves:* %s.' % _ids(o['removes']))
        by_tool = {}
        for f in o['fasteners']:
            by_tool.setdefault(SHORT_TOOL.get(f['tool'], f['tool']), []).append(f['id'])
        for tool, ids in by_tool.items():
            extra.append('*Drives:* %s (%s).' % (_ids(ids), tool))
        if o['connects']:
            extra.append('*Mates:* %s.' % _ids(o['connects']))
        if o['tools']:
            extra.append('*Tools:* %s.' % o['tools'].rstrip('.'))
        for m in o['motions']:
            if m['runner'] == 'verify_candidate':
                extra.append('*CAD motion:* `%s`, swept by verify_candidate.py.' % m['id'])
            elif m['runner'] == 'covered':
                extra.append('*CAD motion:* `%s`, covered by the swept reverse `%s`.' % (m['id'], m['covered_by']))
            else:
                extra.append('*CAD motion:* `%s`, not swept yet (open).' % m['id'])
        if o['no_motion']:
            extra.append('*No rigid sweep:* %s.' % o['no_motion'].rstrip('.'))
        if o.get('supported_groups'):
            extra.append('*Supported off the body:* %s (linked ribbon).' % ', '.join(o['supported_groups']))
        if o.get('flex_scope'):
            extra.append('**Flexible-motion HOLD:** %s' % o['flex_scope'])
        if o['closes']:
            extra.append('*Review:* %s.' % ', '.join(o['closes']))
        if extra:
            out.append('   ' + ' '.join(extra))
    if all(o['where'] != 'body' for o in sec['ops']):
        out.append('')
        out.append('Bench step: nothing enters the body.')
    else:
        out.append('')
        out.append('In the body after this step: %d ids (`steps.present_at`).' % sec['in_body_after'])
    return '\n'.join(out) + '\n'


def route_effect(route):
    """(chain, removed ids, unscrewed, loosened, nuts, cables parted incl. repeats) for a route and its prerequisites."""
    chain = ST.route_closure(route)
    seq = ST.service_sequence(route)
    removed = set(ST.final_state()) - set(seq[-1][3])
    ops = [o for _r, o, _b, _a in seq]
    cables = [c for o in ops for c in o['disconnects']]
    return (chain, removed, [f for o in ops for f in o['unscrews']], [f for o in ops for f in o['loosens']],
            [f for o in ops for f in o['nuts']], cables)


def _remate_op(cable):
    idx = _idx()
    return max((op for k, (part, op) in ((k, v) for k, v in ST.CONNECTIONS[cable].items() if k != 'doc')), key=idx.get)


def route_refit(route, closure=True):
    """Build ops (in build order) that put back what the route (and, with closure, its prerequisites) took out.
    The rule lives in steps.route_refit (fixup-1) so lint_refit replays exactly the documented refit."""
    return ST.route_refit(route, closure)


def render_service_routes():
    idx = _idx()
    out = []
    for r, d in ST.SERVICE.items():
        chain = ST.route_closure(r)
        out.append('**`%s`**: %s Do first: %s.' % (r, d['doc'], ' -> '.join('`%s`' % x for x in chain[:-1]) or
                                                    'nothing'))
        out.append('')
        for n, o in enumerate(d['ops'], 1):
            bits = []
            if o['unscrews']:
                bits.append('screws out %s' % _ids(o['unscrews']))
            if o['loosens']:
                bits.append('loosened only %s' % _ids(o['loosens']))
            if o['nuts']:
                bits.append('nut off %s (deep socket)' % _ids(o['nuts']))
            if o['disconnects']:
                bits.append('parts %s' % _ids(o['disconnects']))
            refit = sorted(set(o['reverse_of']) | {o.get('remate_at', {}).get(c, _remate_op(c)) for c in o['disconnects']}, key=idx.get)
            ref = _ids(refit) if refit else ''
            if o['refit']:
                ref = (ref + '; ' if ref else '') + o['refit']
            out.append('%d. `%s` %s%s *Refit:* %s.' % (n, o['id'], o['doc'].rstrip('.') + '.',
                                                        (' (' + '; '.join(bits) + ')') if bits else '',
                                                        ref.rstrip('.') or 'none (nothing removed)'))
        whole = route_refit(r)
        out.append('')
        out.append('Refit, whole chain (this route and every route done first), in build order: %s.' % (
            ' -> '.join('`%s`' % x for x in whole) or 'no build op; use the text refit above'))
        out.append('')
    return '\n'.join(out)


def render_service_matrix():
    by = {r: (label, r7, change) for r, label, r7, change in MATRIX}
    missing = [r for r in ST.SERVICE if r not in by] + [r for r in by if r not in ST.SERVICE]
    if missing:
        raise KeyError('service matrix rows out of step with steps.SERVICE: %s' % missing)
    out = ['| Target (route) | r7 baseline (r7 ASSEMBLY s7) | Candidate: routes first | Candidate: what comes out | '
           'Candidate refit (build ops, build order) | Change vs r7 |', '|---|---|---|---|---|---|']
    for r in ST.SERVICE:
        label, r7, change = by[r]
        chain, removed, unscrewed, loosened, nuts, cables = route_effect(r)
        first = ' -> '.join('`%s`' % x for x in chain[:-1]) or 'none'
        what = '%d ids; %d screws out%s%s; cables parted: %s; J2 cycles: %d' % (
            len(removed), len(unscrewed), ', %d loosened' % len(loosened) if loosened else '',
            ', %d nut%s' % (len(nuts), '' if len(nuts) == 1 else 's') if nuts else '',
            ', '.join(sorted(set(cables))) or 'none', cables.count('j2'))
        refit = route_refit(r)
        texts = [o['id'] for x in chain for o in ST.SERVICE[x]['ops'] if o['refit']]
        out.append('| %s: `%s` | %s | %s | %s | %d ops: %s%s | %s |' % (
            label, r, r7, first, what, len(refit), ', '.join('`%s`' % x for x in refit),
            ''.join('; plus the text refit of `%s` (section 5 routes)' % x for x in texts), change))
    return '\n'.join(out) + '\n'


def blocks():
    """{block name: generated text}."""
    out = {'ops ' + s['step']: render_ops(s['step']) for s in ST.describe()}
    out['service-routes'] = render_service_routes()
    out['service-matrix'] = render_service_matrix()
    return out


def apply(text, want=None):
    """(new text, problems). Problems: missing / duplicated / unknown blocks; the text is only rewritten in place."""
    want = blocks() if want is None else want
    names = [m.group('name') for m in _BLOCK.finditer(text)]
    probs = ['duplicated block %s' % n for n in sorted({n for n in names if names.count(n) > 1})]
    probs += ['missing block %s' % n for n in want if n not in names]
    probs += ['unknown block %s' % n for n in names if n not in want]

    def sub(m):
        return '<!-- BEGIN:%s -->\n%s<!-- END:%s -->' % (m.group('name'), want.get(m.group('name'), m.group('body')),
                                                         m.group('name'))
    return _BLOCK.sub(sub, text), probs


def stale_blocks(text, want=None):
    want = blocks() if want is None else want
    have = {m.group('name'): m.group('body') for m in _BLOCK.finditer(text)}
    return sorted(n for n in want if n in have and have[n] != want[n])


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    text = read_text(DOC)
    new, probs = apply(text)
    stale = stale_blocks(text)
    if '--check' in argv:
        for p in probs + ['stale block %s' % n for n in stale]:
            print(p)
        print('ASSEMBLY-VERTICAL.md generated blocks: %s' % ('current' if not (probs or stale) else 'NOT current'))
        return 1 if probs or stale else 0
    if probs:
        for p in probs:
            print(p)
        return 1
    if new != text:
        write_text(DOC, new)
    print('ASSEMBLY-VERTICAL.md: %d blocks, %d rewritten' % (len(blocks()), len(stale)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
