# SPDX-License-Identifier: MIT
"""Deterministic export helpers and the bound-cache tool (review VN-04 / VN-17, fix FP-03).

1. Deterministic export (export_candidate.py, make_corrected_pi.py, the concealed guide builder)
   - Every STEP file is written through export_step() / save_assembly(): the wall-clock time OCCT puts in
     the HEADER FILE_NAME record is replaced by the fixed STEP_STAMP. Nothing else in the file changes.
   - Manifests and receipts record UNRECORDED instead of a wall-clock time (built_utc, generated_utc).
   - Mesh JSON is a pure function of the saved, hash-bound STEP file: the STEP is read back and
     tessellated with MESH_TOLERANCE (mesh_from_step). So a mesh cache can be rebuilt from tracked files
     alone, without re-running model.build().
   - Manifest key order is sorted, so it does not depend on directory listing order.
   Byte identity holds for the same platform and the same pinned runtime (Python, CadQuery, OCP), which the
   manifest records. Across platforms OCCT float formatting differs in the last digit (review
   REPRODUCTION.md: 9 of 47 STEP files, 37 of 45 meshes), so a byte comparison there is not meaningful.

2. Bound caches
   The manifests bind out/<variant>/meshes/*.json and the guide receipt binds guide/out-concealed-vents/
   page-*.png by SHA-256, but .gitignore excludes both (about 34 MB of meshes per variant). By default they
   are not committed (user decision VN-04 / VN-16). No binding is dropped: this tool sorts each binding into
   tracked file or git-ignored cache, verifies caches when present, rebuilds mesh caches on demand from the
   bound STEP files, and says exactly what must be regenerated when it cannot do it itself.

CLI (run from anywhere; `status` imports no CAD, `regenerate` imports CadQuery, run it through run_locked.py):
    python export_cache.py status [--variant V ...] [--no-guide] [--json PATH]
    python export_cache.py regenerate [--variant V ...] [--force]
Exit codes: 0 every binding present and byte-identical; 3 only git-ignored caches are missing and this tool
can say how to rebuild them; 1 anything else (a bound file differs, a tracked bound file is missing, or a
missing cache cannot be rebuilt from tracked files, e.g. a pre-FP-03 manifest).
"""
from cv_io import read_text, write_text
from pathlib import Path, PurePosixPath
import argparse, hashlib, importlib.metadata, json, os, platform, re, sys

HERE = Path(__file__).resolve().parent
VARIANTS = ('compact-kowa_lm6hc', 'compact-fujinon_hf6xa', 'original-kowa_lm6hc')
STEP_STAMP = '1970-01-01T00:00:00'
UNRECORDED = 'unrecorded (deterministic build, FP-03)'
MESH_TOLERANCE = (0.07, 0.15)
MESH_SOURCE = 'saved STEP read back with STEPControl_Reader.OneShape, tessellate(0.07, 0.15)'
GUIDE_DIR = 'guide/out-concealed-vents'
GUIDE_RECEIPT = GUIDE_DIR + '/guide-receipt.json'
GUIDE_VARIANT = 'compact-kowa_lm6hc'   # build_guide_concealed_vents.py renders this variant's meshes
LOCK = 'cad/gs8-d2-v1/run_locked.py --'
TOOL = 'cad/gs8-d2-v1/candidate-vertical/export_cache.py'
POLICY = {
    'step_file_name_time': STEP_STAMP,
    'recorded_times': UNRECORDED,
    'mesh_source': MESH_SOURCE,
    'key_order': 'sorted',
    'byte_identity_scope': 'same platform and pinned runtime (python, cadquery, cadquery_ocp) as recorded',
    'git_ignored_caches': 'meshes/*.json (rebuild: export_cache.py regenerate)',
    'tool': 'export_cache.py',
}
_FILE_NAME = re.compile(rb"(FILE_NAME\s*\(\s*'(?:[^']|'')*'\s*,\s*')((?:[^']|'')*)(')")
_MESH_CACHE = re.compile(r'^meshes/[^/]+\.json$')      # relative to out/<variant>; .gitignore: out/*/meshes/
_PAGE_CACHE = re.compile(r'^page-[^/]+\.png$')         # relative to GUIDE_DIR; .gitignore: page-*.png


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def is_mesh_cache(rel):
    return bool(_MESH_CACHE.match(rel))


def is_page_cache(rel):
    return bool(_PAGE_CACHE.match(rel))


def runtime():
    """Runtime identity recorded in manifests; byte identity is only claimed between equal runtimes."""
    def version(dist):
        try:
            return importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError:
            return None
    return {'python': platform.python_version(), 'cadquery': version('cadquery'),
            'cadquery_ocp': version('cadquery-ocp'), 'platform': sys.platform + '-' + platform.machine().lower()}


# ---------------------------------------------------------------- deterministic STEP writing

def normalize_step_header(path, stamp=STEP_STAMP):
    """Replace the FILE_NAME time stamp in the STEP HEADER section with `stamp`; return the old value.

    Only the HEADER section is searched, so DATA strings are never touched. Idempotent."""
    path = Path(path)
    data = path.read_bytes()
    end = data.find(b'ENDSEC;')
    if not data.lstrip().startswith(b'ISO-10303-21;') or end < 0:
        raise ValueError('not a STEP file: %s' % path)
    match = _FILE_NAME.search(data, 0, end)
    if match is None:
        raise ValueError('STEP header has no FILE_NAME record: %s' % path)
    old = match.group(2).decode('latin-1')
    new = stamp.encode('ascii')
    if match.group(2) != new:
        tmp = path.with_name(path.name + '.fp03tmp')
        tmp.write_bytes(data[:match.start(2)] + new + data[match.end(2):])
        os.replace(tmp, path)
    return old


def export_step(shape, path):
    """cq.exporters.export to STEP, then fix the header time."""
    import cadquery as cq
    cq.exporters.export(shape, str(path))
    return normalize_step_header(path)


def save_assembly(assembly, path):
    """cq.Assembly.save to STEP, then fix the header time and put the colour section in canonical order."""
    assembly.save(str(path))
    old = normalize_step_header(path)
    canonicalize_step_styles(path)
    return old


# ---------------------------------------------------------------- export folder plan (fixup-1, FP-01/FP-03)
# export_candidate.py writes the Raspberry Pi licence copies itself (FP-01: a licence beside every Pi-derived
# file: assembly.step in out/<variant>/, pi5.step in step/), so an in-place re-export and a clean --out export
# both carry them, and the stale-file check runs against the planned names BEFORE anything is written.
PI_LICENCE_SOURCE = 'routing-snapshots/hdmi-ck1044-clear-20261009-0524/official-fpc-sources/LICENSE.txt'
PI_LICENCE_COPY = 'LICENSE-RaspberryPi.txt'
PI_LICENCE_COPIES = (PI_LICENCE_COPY, 'step/' + PI_LICENCE_COPY)   # relative to out/<variant>
EXPORT_FOLDERS = ('step', 'stl', 'meshes')
GAUGE_FILES = ('step/centring_gauge.step', 'stl/centring_gauge.stl')
# T2 (VN-53, FP-11b): the bonded +Y tab-catch stub is printed on its own (model.tub_print_parts); like the gauge it is
# not an assembly row (the 'tub' row is the bonded tub), so its files are planned here.
TAB_CATCH_INSERT = 'tab_catch_insert'
INSERT_FILES = ('step/%s.step' % TAB_CATCH_INSERT, 'stl/%s.stl' % TAB_CATCH_INSERT)


def licence_bytes(root=HERE):
    """The manufacturer's LICENSE.txt with LF line endings (the bytes of every LICENSE-RaspberryPi.txt copy)."""
    return (Path(root) / PI_LICENCE_SOURCE).read_bytes().replace(b'\r\n', b'\n')


def write_licence_copies(out, root=HERE):
    data = licence_bytes(root)
    for rel in PI_LICENCE_COPIES:
        p = Path(out) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return set(PI_LICENCE_COPIES)


def planned_export_files(rows):
    """Every file export_candidate.py writes for rows [(id, kind)], relative to out/<variant> (not manifest.json)."""
    files = set(GAUGE_FILES) | set(INSERT_FILES) | set(PI_LICENCE_COPIES)
    for name, kind in rows:
        files |= {'step/%s.step' % name, 'meshes/%s.json' % name}
        if kind == 'printed':
            files.add('stl/%s.stl' % name)
    return files


def leftover_files(out, planned):
    """Files in step/, stl/ or meshes/ that an export writing `planned` would not overwrite (they would be bound
    as if current). manifest.json copies are rewritten by the export and are not leftovers."""
    out = Path(out)
    return sorted(f.relative_to(out).as_posix() for folder in EXPORT_FOLDERS if (out / folder).is_dir()
                  for f in (out / folder).iterdir()
                  if f.is_file() and f.name != 'manifest.json' and f.relative_to(out).as_posix() not in planned)


# OCCT's XCAF writer emits the trailing colour section (MDGPR -> STYLED_ITEM -> ... -> COLOUR_RGB) in the
# iteration order of a shape-keyed hash map, i.e. by memory address, so its entity order and numbering change
# from run to run although geometry and colours are identical (measured: 1358 of 1,377,609 lines in the
# compact-Kowa assembly.step). These are the only entity types that section may hold.
STYLE_TYPES = frozenset({
    'MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION', 'STYLED_ITEM', 'OVER_RIDING_STYLED_ITEM',
    'PRESENTATION_STYLE_ASSIGNMENT', 'SURFACE_STYLE_USAGE', 'SURFACE_SIDE_STYLE', 'SURFACE_STYLE_FILL_AREA',
    'FILL_AREA_STYLE', 'FILL_AREA_STYLE_COLOUR', 'COLOUR_RGB', 'DRAUGHTING_PRE_DEFINED_COLOUR', 'CURVE_STYLE',
    'DRAUGHTING_PRE_DEFINED_CURVE_FONT', 'PRESENTATION_LAYER_ASSIGNMENT', 'INVISIBILITY',
    'SURFACE_STYLE_RENDERING', 'SURFACE_STYLE_RENDERING_WITH_PROPERTIES', 'SURFACE_STYLE_TRANSPARENT'})
_SET_LISTS = {'MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION', 'PRESENTATION_LAYER_ASSIGNMENT',
              'INVISIBILITY'}  # their entity lists are SETs in AP214, so their order carries no meaning
_STYLE_START = re.compile(rb'(?:^|\n)(#\d+\s*=\s*(?:%s)\s*\()' % b'|'.join(t.encode() for t in sorted(STYLE_TYPES, key=len, reverse=True)))
_RECORD = re.compile(r'#(\d+)\s*=\s*([A-Z_0-9]+)\s*\((.*)\)\Z', re.S)
_REF = re.compile(r'#(\d+)')


def _records(text):
    """Split STEP DATA text into records at ';' outside quoted strings."""
    out, start, quoted = [], 0, False
    for i, ch in enumerate(text):
        if ch == "'":
            quoted = not quoted
        elif ch == ';' and not quoted:
            out.append(text[start:i].strip())
            start = i + 1
    if text[start:].strip():
        raise ValueError('unterminated STEP record in colour section')
    return out


def _unwrap(body):
    """Remove the writer's line wrapping (newline plus indent) outside quoted strings."""
    parts = body.split("'")
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r'\s*\n\s*', '', parts[i])
    return "'".join(parts)


def canonicalize_step_styles(path):
    """Rewrite the trailing colour section of a STEP file in a canonical order; return its entity count.

    Geometry entities and their numbers are untouched. The section must be the file's last entities, hold only
    STYLE_TYPES, and nothing before it may reference it; otherwise ValueError (never a silent rewrite).
    Entities are emitted depth-first from the presentation roots, sorted by a content key in which every
    reference into the section is replaced by the key of its target; ids are reassigned from the section's
    first id. Set-valued lists are sorted. Idempotent; a file without a colour section is left as is."""
    path = Path(path)
    data = path.read_bytes()
    begin = data.find(b'\nDATA;')
    end = data.rfind(b'ENDSEC;')
    if begin < 0 or end < begin:
        raise ValueError('no DATA section: %s' % path)
    match = _STYLE_START.search(data, begin, end)
    if match is None:
        return 0
    cut = match.start(1)
    tail = data[cut:end].decode('latin-1')
    recs = {}
    for rec in _records(tail):
        m = _RECORD.match(rec)
        if m is None or m.group(2) not in STYLE_TYPES:
            raise ValueError('colour section holds a non-style record: %s' % rec[:120])
        body = _unwrap(m.group(3))
        if '#' in ''.join(body.split("'")[1::2]):
            raise ValueError('reference-like text inside a string in the colour section')
        recs[int(m.group(1))] = (m.group(2), body)
    first = min(recs)
    if sorted(recs) != list(range(first, first + len(recs))):
        raise ValueError('colour section ids are not one contiguous block')
    if any(int(x) >= first for x in re.findall(rb'#(\d+)', data[begin:cut])):
        raise ValueError('an entity before the colour section references it')
    refs = {i: [int(x) for x in _REF.findall(body) if int(x) in recs] for i, (_, body) in recs.items()}
    keys = {}

    def key(i):
        if i not in keys:
            kind, body = recs[i]
            text = _REF.sub(lambda m: '<%s>' % key(int(m.group(1))) if int(m.group(1)) in recs else m.group(0), body)
            if kind in _SET_LISTS:
                text = re.sub(r'\(([^()]*)\)', lambda m: '(' + ','.join(sorted(x.strip() for x in m.group(1).split(','))) + ')', text)
            keys[i] = hashlib.sha256((kind + '(' + text + ')').encode('latin-1')).hexdigest()
        return keys[i]

    referenced = {j for js in refs.values() for j in js}
    roots = sorted((i for i in recs if i not in referenced), key=key)
    order, seen = [], set()

    def visit(i):
        if i in seen:
            return
        seen.add(i)
        order.append(i)
        kind, body = recs[i]
        children = refs[i]
        if kind in _SET_LISTS:
            children = sorted(children, key=key)
        for j in children:
            visit(j)

    for r in roots:
        visit(r)
    if len(order) != len(recs):
        raise ValueError('colour section has a reference cycle')
    new = {old: first + n for n, old in enumerate(order)}
    lines = []
    for old in order:
        kind, body = recs[old]
        if kind in _SET_LISTS:
            body = re.sub(r'\(([^()]*)\)', lambda m: '(' + ','.join(
                sorted((x.strip() for x in m.group(1).split(',')), key=lambda x: key(int(x[1:])) if _REF.fullmatch(x) and int(x[1:]) in recs else x)) + ')', body)
        body = _REF.sub(lambda m: '#%d' % new[int(m.group(1))] if int(m.group(1)) in recs else m.group(0), body)
        lines.append('#%d = %s(%s);\n' % (new[old], kind, body))
    out = data[:cut] + ''.join(lines).encode('latin-1') + data[end:]
    if out != data:
        tmp = path.with_name(path.name + '.fp03tmp')
        tmp.write_bytes(out)
        os.replace(tmp, path)
    return len(recs)


# ---------------------------------------------------------------- mesh JSON (a function of the STEP bytes)

def base_material(name, kind):
    mat = 'silver' if name in ('tub', 'panel') else 'black'
    if kind in ('cots', 'hardware'):
        mat = {'pi5': 'pcb', 'x1203': 'pcb', 'evf_board': 'pcb', 'encoder': 'pcb', 'cooler': 'metal',
               'x1203_kit': 'brass', 'lens': 'lens', 'eyepiece': 'lens', 'hmx039': 'glass', 'pack': 'battery',
               'xt30_pair': 'connector', 'run_button': 'red', 'tripod_nut': 'metal', 'strap': 'strap',
               'foam_pad': 'rubber'}.get(name, 'metal' if kind == 'hardware' else 'black')
    if name == 'eyecup':
        mat = 'rubber'
    return mat


def face_materials(name, vertices, faces, mat):
    mats = []
    for f in faces:
        pts = [vertices[i] for i in f]
        vmat = mat
        if name == 'panel' and all(abs(q[1] - 27.6) < .008 for q in pts):
            vmat = 'paint_black'
        if name == 'knob_fps' and all(abs(q[1] - 36.6) < .008 for q in pts):
            vmat = 'paint_white'
        if name == 'encoder' and all(q[1] > 25.2 for q in pts):
            vmat = 'metal'
        mats.append(vmat)
    return mats


def read_step(path):
    """The STEP file's shape (one root, or a compound of all roots), as a cadquery Shape."""
    import cadquery as cq
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPControl import STEPControl_Reader
    reader = STEPControl_Reader()
    if reader.ReadFile(str(path)) != IFSelect_RetDone:
        raise ValueError('cannot read STEP: %s' % path)
    reader.TransferRoots()
    return cq.Shape.cast(reader.OneShape())


def mesh_bytes(name, kind, shape):
    vv, ff = shape.tessellate(*MESH_TOLERANCE)
    vs = [[v.x, v.y, v.z] for v in vv]
    fs = [list(f) for f in ff]
    mesh = {'id': name, 'kind': kind, 'vertices': vs, 'faces': fs,
            'materials': face_materials(name, vs, fs, base_material(name, kind))}
    return json.dumps(mesh, separators=(',', ':')).encode('utf-8')


def mesh_from_step(name, kind, step_path):
    return mesh_bytes(name, kind, read_step(step_path))


def write_mesh(json_path, name, kind, step_path):
    data = mesh_from_step(name, kind, step_path)
    Path(json_path).write_bytes(data)
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------- binding status

def classify(items, root, cache_rule):
    """Sort {relative path: sha256} into tracked files and git-ignored caches and check each one."""
    groups = {g: {'checked': 0, 'present_match': 0, 'missing': [], 'changed': []} for g in ('tracked', 'cache')}
    for rel, digest in sorted(items.items()):
        g = groups['cache' if cache_rule(rel) else 'tracked']
        g['checked'] += 1
        p = Path(root) / rel
        if not p.is_file():
            g['missing'].append(rel)
        elif sha(p) != digest:
            g['changed'].append(rel)
        else:
            g['present_match'] += 1
    return groups


def require_files(items, variant_dir):
    """Reconciler gate: every bound export file must be present and byte-identical.

    A changed file, or a missing tracked file, raises AssertionError('Export mismatch', rel) as before. When
    only git-ignored mesh caches are missing, the AssertionError names how many and the command that rebuilds
    them, instead of a FileNotFoundError traceback. Nothing passes without its bytes being checked."""
    d = Path(variant_dir)
    missing = []
    for rel, digest in sorted(items.items()):
        p = d / rel
        if not p.is_file():
            if not is_mesh_cache(rel):
                raise AssertionError('Export mismatch', rel, 'tracked bound file missing')
            missing.append(rel)
        elif sha(p) != digest:
            raise AssertionError('Export mismatch', rel)
    if missing:
        manifest = d / 'manifest.json'
        legacy = manifest.is_file() and json.loads(read_text(manifest)).get('determinism', {}).get('mesh_source') != MESH_SOURCE
        how = ('this manifest predates FP-03, so they cannot be rebuilt from the STEP files; re-export the variant and '
               'rebind its evidence (FP-16)' if legacy else
               'rebuild with: python %s %s regenerate --variant %s (then rerun)' % (LOCK, TOOL, d.name))
        raise AssertionError('Bound cache missing', len(missing), 'git-ignored mesh JSON, first %s; %s' % (missing[0], how))


def _state(groups, regenerable):
    t, c = groups['tracked'], groups['cache']
    if t['missing'] or t['changed'] or c['changed']:
        return 'mismatch'
    if c['missing']:
        return 'cache_missing' if regenerable else 'cache_missing_unregenerable'
    return 'complete'


def variant_report(variant_dir, root=HERE):
    d = Path(variant_dir)
    variant = d.name
    m = json.loads(read_text(d / 'manifest.json'))
    regenerable = m.get('determinism', {}).get('mesh_source') == MESH_SOURCE
    groups = classify(m['files'], d, is_mesh_cache)
    copy = d / 'meshes' / 'manifest.json'
    rep = {'variant': variant, 'manifest_sha256': sha(d / 'manifest.json'), 'tracked': groups['tracked'],
           'cache': groups['cache'], 'mesh_manifest_copy': 'missing' if not copy.is_file() else
           ('match' if copy.read_bytes() == (d / 'manifest.json').read_bytes() else 'differs'),
           'regenerable_from_bound_step': regenerable, 'recorded_runtime': m.get('runtime'), 'host_runtime': runtime()}
    rep['state'] = _state(groups, regenerable)
    rep['action'] = variant_action(rep)
    return rep


def variant_action(rep):
    v, c = rep['variant'], rep['cache']
    same_runtime = rep['recorded_runtime'] == rep['host_runtime']
    if rep['state'] == 'complete':
        return 'none: every bound file is present and byte-identical'
    if rep['state'] == 'cache_missing':
        return ('%d git-ignored mesh JSON file(s) missing; rebuild them from the bound STEP files: python %s %s '
                'regenerate --variant %s' % (len(c['missing']), LOCK, TOOL, v))
    if rep['state'] == 'cache_missing_unregenerable':
        return ('%d git-ignored mesh JSON file(s) missing and NOT rebuildable from tracked files: this manifest '
                'predates FP-03 (meshes were tessellated in memory, not from the saved STEP). Re-export the variant '
                'with export_candidate.py and rebind the dependent evidence (FP-16).' % len(c['missing']))
    note = '' if same_runtime else (' This host runtime %s differs from the recorded %s, so cache bytes are not '
                                    'expected to match.' % (rep['host_runtime'], rep['recorded_runtime']))
    return ('bound file(s) differ or a tracked bound file is missing: tracked missing %d, tracked changed %d, cache '
            'changed %d.%s' % (len(rep['tracked']['missing']), len(rep['tracked']['changed']), len(c['changed']), note))


def summarize_bindings(binding, manifest, variant):
    """CAD-free summary of an already computed {'missing', 'changed'} binding result (docs audit)."""
    regenerable = manifest.get('determinism', {}).get('mesh_source') == MESH_SOURCE
    cache_missing = [r for r in binding['missing'] if is_mesh_cache(r)]
    rep = {'variant': variant, 'recorded_runtime': manifest.get('runtime'), 'host_runtime': runtime(),
           'regenerable_from_bound_step': regenerable,
           'tracked': {'missing': [r for r in binding['missing'] if not is_mesh_cache(r)],
                       'changed': [r for r in binding['changed'] if not is_mesh_cache(r)]},
           'cache': {'bound': sum(map(is_mesh_cache, manifest['files'])), 'missing': cache_missing,
                     'changed': [r for r in binding['changed'] if is_mesh_cache(r)]},
           'cache_rule': 'meshes/*.json are git-ignored regenerable caches (FP-03); their bindings are kept'}
    rep['state'] = _state(rep, regenerable)
    rep['action'] = variant_action(rep)
    return rep


def source_bindings(items, root):
    """{checked, missing, changed, pass} for {path relative to root: sha256} (fixup-1: the guide receipt's `sources`,
    relative to cad/gs8-d2-v1, so an edited guide input or document makes the guide stale in the docs audit)."""
    missing = [n for n in sorted(items) if not (Path(root) / n).is_file()]
    changed = [n for n in sorted(items) if n not in missing and sha(Path(root) / n) != items[n]]
    return {'checked': len(items), 'missing': missing, 'changed': changed, 'pass': not missing and not changed}


def guide_report(root=HERE):
    """Status of the concealed guide receipt's bindings: tracked PDF, mesh caches and page-image caches."""
    root = Path(root)
    rec = json.loads(read_text(root / GUIDE_RECEIPT))
    vdir = root / 'out' / GUIDE_VARIANT
    meshes = classify(rec.get('mesh_files', {}), vdir, is_mesh_cache)
    pages = classify(rec.get('page_images', {}), root / GUIDE_DIR, is_page_cache)
    pdf = root / GUIDE_DIR / rec['guide_pdf_filename']
    deterministic = rec.get('generated_utc') == UNRECORDED
    nominated = rec.get('nominated_manifest_sha256')
    rep = {'receipt': GUIDE_RECEIPT, 'nominated_manifest_sha256': nominated,
           'nominated_manifest_current': (vdir / 'manifest.json').is_file() and nominated == sha(vdir / 'manifest.json'),
           'pdf_match': pdf.is_file() and sha(pdf) == rec.get('guide_pdf_sha256'),
           'mesh_files': meshes['cache'], 'page_images': pages['cache'],
           'unexpected_tracked': meshes['tracked']['checked'] + pages['tracked']['checked'],
           'deterministic_build': deterministic, 'sources': source_bindings(rec.get('sources', {}), root.parent)}
    missing_pages = len(pages['cache']['missing'])
    if meshes['cache']['changed'] or pages['cache']['changed'] or not rep['pdf_match'] or rep['unexpected_tracked']:
        rep['state'] = 'mismatch'
    elif missing_pages or meshes['cache']['missing']:
        rep['state'] = 'cache_missing' if deterministic else 'cache_missing_unregenerable'
    else:
        rep['state'] = 'complete'
    rebuild = ('python %s cad/gs8-d2-v1/candidate-vertical/guide/build_guide_concealed_vents.py --manifest-sha256 %s '
               '(first rebuild the mesh caches; the build rewrites the tracked receipt and PDF, so `git diff` must then '
               'show no change; it needs the compiled rasterizer guide/raster.cpp, which only builds on Linux today, '
               'VN-12)' % (LOCK, nominated))
    rep['action'] = {'complete': 'none: every bound guide file is present and byte-identical',
                     'cache_missing': '%d page image(s) and %d mesh file(s) missing; rebuild: %s' % (
                         missing_pages, len(meshes['cache']['missing']), rebuild),
                     'cache_missing_unregenerable': '%d page image(s) and %d mesh file(s) missing and NOT reproducible '
                     'byte-for-byte: this receipt predates FP-03 (page 20 printed the wall-clock build time). Rebuild '
                     'and re-review the guide after the next export (FP-16): %s' % (
                         missing_pages, len(meshes['cache']['missing']), rebuild),
                     'mismatch': 'a bound guide file differs (PDF, page image or mesh cache); inspect before use'}[rep['state']]
    return rep


# ---------------------------------------------------------------- regeneration

def regenerate_variant(variant_dir, force=False, log=print):
    """Rebuild the variant's git-ignored mesh JSON from its bound STEP files and verify each against the
    manifest. A matching file is written in place; a non-matching one only to meshes/_mismatch/ (never over
    a bound path). Returns {relative path: outcome}."""
    d = Path(variant_dir)
    raw = (d / 'manifest.json').read_bytes()
    m = json.loads(raw.decode('utf-8'))
    if m.get('determinism', {}).get('mesh_source') != MESH_SOURCE:
        raise ValueError('%s: manifest predates FP-03; its meshes cannot be rebuilt from the STEP files. '
                         'Re-export the variant instead.' % d.name)
    rows = {'meshes/' + r['mesh']: r for r in m['rows']}
    (d / 'meshes').mkdir(exist_ok=True)
    outcome = {}
    for rel, digest in sorted(m['files'].items()):
        if not is_mesh_cache(rel):
            continue
        target = d / rel
        if not force and target.is_file() and sha(target) == digest:
            outcome[rel] = 'present'
            continue
        row = rows.get(rel)
        step_rel = 'step/%s.step' % (row['id'] if row else PurePosixPath(rel).stem)
        step = d / step_rel
        if row is None or m['files'].get(step_rel) is None or not step.is_file() or sha(step) != m['files'][step_rel]:
            outcome[rel] = 'step_missing_or_unbound'
            log(rel, outcome[rel], flush=True)
            continue
        data = mesh_from_step(row['id'], row['kind'], step)
        if hashlib.sha256(data).hexdigest() == digest:
            target.write_bytes(data)
            outcome[rel] = 'regenerated'
        else:
            bad = d / 'meshes' / '_mismatch' / target.name
            bad.parent.mkdir(exist_ok=True)
            bad.write_bytes(data)
            outcome[rel] = 'mismatch'
        log(rel, outcome[rel], flush=True)
    copy = d / 'meshes' / 'manifest.json'
    if not copy.is_file() or copy.read_bytes() != raw:
        copy.write_bytes(raw)
    return outcome


def _variant_dirs(names, root=HERE):
    return [Path(n).resolve() if Path(n).name != n else root / 'out' / n for n in names]  # a bare name is a variant


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    st = sub.add_parser('status', help='verify bound files; CAD-free')
    st.add_argument('--variant', action='append', help='variant name or folder (default: all three)')
    st.add_argument('--no-guide', action='store_true', help='skip the guide receipt')
    st.add_argument('--json', type=Path, help='also write the full report here')
    rg = sub.add_parser('regenerate', help='rebuild missing mesh JSON from the bound STEP files (imports CadQuery)')
    rg.add_argument('--variant', action='append', help='variant name or folder (default: all three)')
    rg.add_argument('--force', action='store_true', help='rebuild present files too (written only if they match)')
    a = ap.parse_args(argv)
    dirs = _variant_dirs(a.variant or VARIANTS)
    if a.cmd == 'regenerate':
        bad = 0
        for d in dirs:
            try:
                res = regenerate_variant(d, force=a.force)
            except ValueError as e:
                print('FAIL', e, flush=True)
                bad += 1
                continue
            counts = {k: list(res.values()).count(k) for k in sorted(set(res.values()))}
            print(d.name, counts, flush=True)
            bad += sum(v not in ('present', 'regenerated') for v in res.values())
        if bad:
            print('Not all bound mesh caches could be rebuilt byte-identically (see above).', flush=True)
            return 1
    report = {'variants': [variant_report(d) for d in dirs], 'policy': POLICY}
    if a.cmd == 'status' and not a.no_guide:
        report['guide'] = guide_report()
    if a.cmd == 'status' and a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        write_text(a.json, json.dumps(report, indent=2) + '\n')
    items = report['variants'] + ([report['guide']] if 'guide' in report else [])
    for r in items:
        print('%-22s %-28s %s' % (r.get('variant', 'guide'), r['state'], r['action']), flush=True)
    states = {r['state'] for r in items}
    if states <= {'complete'}:
        return 0
    if states <= {'complete', 'cache_missing'}:
        return 3
    return 1


if __name__ == '__main__':
    sys.exit(main())
