# SPDX-License-Identifier: MIT
"""Terminal-entry rule of the static power-wire check (fixup-1 of FP-12 / VN-30). Pure Python, no CAD.

A wire capsule may touch its declared terminal part only in one run of pieces contiguous from that wire end, and
- the run is no longer than the declared maximum entry length of that terminal (from the power snapshot; where the
  real entry is unmeasured the snapshot figure is the upper end of a range and the gate is named);
- when both ends of one wire share the same terminal part, the two runs must not meet: a wire lying inside the part
  from end to end is a buried route, not two terminal entries.
"""
import math

# wire id -> (start entry kind, end entry kind); kinds name the snapshot data that bound the entry length
ENTRY_KIND = {'positive_board_to_fuse': ('root', 'fuse'), 'positive_fuse_to_housing': ('fuse', 'housing'),
              'negative_complete': ('root', 'housing')}
GATES = {'root': 'actual X1203 pads and wire exit/strain relief (snapshot root_warning; power gates)',
         'fuse': 'actual fuse-holder lead / sleeve entry (unmeasured; power gates)',
         'housing': 'actual XT30 solder-cup entry depth (unmeasured; power gates)'}


def entry_limits(snapshot, core):
    """{kind: (max entry length mm, source, gate)} from the power snapshot (no typed figures)."""
    f = snapshot['fuse']
    hb = snapshot['junction_housing_original_box']
    return {
        'root': (float(core['unmodeled_root_joint_allowance_mm']),
                 'snapshot cores[%s].unmodeled_root_joint_allowance_mm' % core['core_id'], GATES['root']),
        'fuse': (math.dist(f['start'], f['end']), 'snapshot fuse start->end (sleeve length)', GATES['fuse']),
        'housing': (max(hb[k][1] - hb[k][0] for k in ('x', 'y', 'z')),
                    'snapshot junction_housing_original_box longest edge', GATES['housing']),
    }


def polyline_length(points, s0, s1):
    seg = points[int(s0):int(math.ceil(s1)) + 1]
    return float(sum(math.dist(p, q) for p, q in zip(seg, seg[1:])))


def terminal_runs(per, points, wire_id, terminals, limits):
    """per: [(station, {part: overlap mm3}, bbox)] in station order. terminals: (start part, end part).
    Returns (excluded {(piece index, part)}, runs [dict], problems [str])."""
    kinds = ENTRY_KIND[wire_id]
    excl, runs, probs, idx = set(), [], [], {}
    for end, part in ((0, terminals[0]), (1, terminals[1])):
        order = range(len(per)) if end == 0 else range(len(per) - 1, -1, -1)
        run = []
        for k in order:
            if part in per[k][1]:
                run.append(k)
            else:
                break
        idx[end] = run
        excl |= {(k, part) for k in run}
        if not run:
            continue
        s0, s1 = sorted((per[run[0]][0], per[run[-1]][0]))
        length = polyline_length(points, s0, s1)
        lim, src, gate = limits[kinds[end]]
        row = dict(wire=wire_id, end='start' if end == 0 else 'end', part=part, entry=kinds[end], pieces=len(run),
                   stations=[s0, s1], run_length_mm=length, max_entry_mm=lim, max_entry_source=src, gate=gate,
                   max_overlap_mm3=max(per[k][1][part] for k in run))
        if length > lim + 1e-9:
            row['status'] = 'fail'
            probs.append('%s %s run in %s is %.2f mm, longer than its declared max entry %.2f mm (%s)'
                         % (wire_id, row['end'], part, length, lim, src))
        else:
            row['status'] = 'pass'
        runs.append(row)
    if terminals[0] == terminals[1] and idx[0] and idx[1] and max(idx[0]) + 1 >= min(idx[1]):
        probs.append('%s: the runs from both ends meet inside %s (the wire lies inside it end to end: a buried route, '
                     'not two terminal entries)' % (wire_id, terminals[0]))
    return excl, runs, probs
