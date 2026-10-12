#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Reproduce exploratory power options without changing selected CAD or parts.

Uses only the Python standard library. The optional geometry probe executes a
private in-memory copy of power_routes with two changed rear-run coordinates;
it imports no CAD and writes no source, STEP, manifest or selected report.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import types

HERE = Path(__file__).resolve().parent
CV = HERE.parents[1]
BASELINE = "bdfd44fc549bd8ea9ebf9a93ea4262ad5054b13f"
INPUTS = {
    "current_a": 8.6,
    "limit_v": 0.150,
    "rho20_ohm_mm2_per_m": 1.0 / 58.0,
    "alpha_per_k": 0.00393,
    "reference_c": 20.0,
    "copper_hot_c": 60.0,
    "lay_factor": 1.03,
    "strand_diameter_mm": 0.08,
    "prc16_strands_conservative": 250,
    "prc14_strands_conservative": 400,
    "pack18_strands_assumed": 150,
    "pack_lead_per_polarity_mm": 60.0,
    "fuse_cold_mohm": 4.46,
    "fuse_hot_factor": 1.30,
    "historical_connector_loop_mohm": 1.0,
    "connector_loop_sensitivities_mohm": [1.0, 1.2, 2.4],
    "added_splice_mohm_in_tabulated_drop": 0.0,
}
SOURCES = {
    "wire16": "https://www.progressiverc.com/products/prc-silicone-wire-16-awg",
    "wire14": "https://www.progressiverc.com/products/prc-silicone-wire-14-awg",
    "wire14_variants": "https://www.progressiverc.com/products/prc-silicone-wire-14-awg.json",
    "connector_page": "https://www.china-amass.net/xt30u-f-product/",
    "connector_spec_archive": "https://www.china-amass.net/uploads/XT30U-MF.rar",
    "connector_spec_version": "2025V0; female A.06.1; male A.01.1",
    "read_date_utc": "2026-10-12",
}


def area(n):
    return n * math.pi / 4 * INPUTS["strand_diameter_mm"] ** 2


def drop(total_mm, tail16_mm=0.0, connector_mohm=1.0, all16=False, splice_mohm=0.0):
    """Total includes both gauges, per polarity; splice_mohm is sum over the loop."""
    if not 0 <= tail16_mm <= total_mm:
        raise ValueError("The 16 AWG tail must lie within the total path allocation")
    d = INPUTS
    k = 1 + d["alpha_per_k"] * (d["copper_hot_c"] - d["reference_c"])
    resistivity = d["rho20_ohm_mm2_per_m"] * 1000 * d["lay_factor"]
    r16 = resistivity / area(d["prc16_strands_conservative"])
    r14 = resistivity / area(d["prc14_strands_conservative"])
    r18 = resistivity / area(d["pack18_strands_assumed"])
    if all16:
        tail16_mm = total_mm
    wire = 2 * k * ((total_mm - tail16_mm) / 1000 * r14 + tail16_mm / 1000 * r16
                    + d["pack_lead_per_polarity_mm"] / 1000 * r18)
    return d["current_a"] / 1000 * (
        wire + d["fuse_cold_mohm"] * d["fuse_hot_factor"] + connector_mohm + splice_mohm)


def max_path(connector_mohm=1.0, all16=False):
    v0 = drop(0, connector_mohm=connector_mohm, all16=all16)
    v1 = drop(1000, connector_mohm=connector_mohm, all16=all16)
    return 1000 * (INPUTS["limit_v"] - v0) / (v1 - v0)


def electrical():
    options = []
    for length in (270, 280, 285, 300):
        for tail in (0, 24, 40):
            cases = []
            for contact in INPUTS["connector_loop_sensitivities_mohm"]:
                v = drop(length, tail, contact)
                budget = (INPUTS["limit_v"] - v) / INPUTS["current_a"] * 1000
                cases.append({
                    "connector_loop_mohm": contact,
                    "drop_v_before_added_splices": round(v, 8),
                    "margin_mv": round(1000 * (INPUTS["limit_v"] - v), 5),
                    "total_added_splice_budget_mohm": round(budget, 6),
                    "each_of_two_equal_splices_budget_mohm": round(budget / 2, 6) if tail else None,
                })
            options.append({"total_path_per_polarity_mm": length,
                            "14awg_per_polarity_mm": length - tail,
                            "16awg_terminal_tail_per_polarity_mm": tail,
                            "additional_splices": 2 if tail else 0,
                            "contact_sensitivity": cases})
    return {
        "area14_mm2": area(400), "area16_mm2": area(250), "area18_assumed_mm2": area(150),
        "historical_270mm16_drop_hi_v": round(drop(270, all16=True), 8),
        "maximum_16awg_path_historical_contact_mm": round(max_path(all16=True), 6),
        "maximum_14awg_path_by_contact_mm": {
            str(c): round(max_path(c), 6) for c in INPUTS["connector_loop_sensitivities_mohm"]},
        "options": options,
    }


def hump_excess(sh):
    a1, a2 = math.radians(sh["rise_angle_deg"]), math.radians(sh["fall_angle_deg"])
    l1, l2, flat, high = (sh[k] for k in (
        "rise_straight_mm", "fall_straight_mm", "middle_straight_mm", "top_z"))
    bump = 16 * (a1 + a2) + l1 + l2 + flat
    width = flat + 16 * (math.sin(a1) + math.sin(a2))
    zbase, endbase = high - (16 * (1 - math.cos(a1)) + l1), high - (16 * (1 - math.cos(a2)) + l2)
    low = max(zbase, endbase)
    def side(d):
        a = math.acos(1 - max(0, d) / 16) if d <= 16 else math.pi / 2
        leg = max(0, d - 16)
        return 16 * math.sin(a), 16 * a + leg
    s1, s2 = side(low - zbase), side(low - endbase)
    return bump - (s1[1] + s2[1] + width - s1[0] - s2[0])


def geometry_probes():
    sys.path.insert(0, str(CV))
    import routes as R  # CAD-free source module
    source = (CV / "power_routes.py").read_text(encoding="utf-8")
    original = "rear=-100 if name=='positive' else -104"
    if source.count(original) != 1:
        raise ValueError("Power route source changed; re-review the isolated probe rather than guessing a replacement")
    observations = []
    for name, replacement in (("selected_baseline", original),
                              ("shortened_rear_probe", "rear=-95 if name=='positive' else -99")):
        module = types.ModuleType("_isolated_power_options")
        exec(compile(source.replace(original, replacement), "<isolated-power-options>", "exec"), module.__dict__)
        result = module.build(R, R.source_obstacles(158))
        cores = []
        for c in result["cores"]:
            minimum = c["modeled_length_mm"] - hump_excess(c["upper_curve"]["slack_hump"])
            cores.append({
                "id": c["id"], "family_minimum_mm": round(minimum, 6),
                "minimum_stock_with_10pct_allowance_mm": round(minimum / 0.9, 6),
                "margin_at_270mm_allocation_mm": round(270 - 27 - minimum, 6),
                "hump_top_z_mm": round(c["xz_loop_top_z"], 6),
                "wall_overrun_sample_points": len(c["wall_overrun_points"]),
                "source_proxy_hits": sorted(h["obstacle"] for h in c["source_proxy_hits"]),
            })
        observations.append({"name": name, "cores": cores})
    return {
        "scope": "Pure route/proxy arithmetic only. No exact CAD, cable-neighbour, retained-service or physical pass.",
        "source_sha256": {n: hashlib.sha256((CV / n).read_bytes()).hexdigest()
                          for n in ("power_routes.py", "routes.py")},
        "cases": observations,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true", help="compare without rewriting the saved assessment")
    p.add_argument("--out", type=Path, default=HERE / "assessment.json")
    a = p.parse_args()
    result = {
        "status": "EXPLORATORY ONLY; no final part selection, purchase or physical qualification",
        "baseline_commit": BASELINE,
        "inputs": INPUTS, "sources": SOURCES,
        "equation": "V = I/1000 * [2*k*((L14/1000)*r14 + (L16/1000)*r16 + (60/1000)*r18) + 4.46*1.30 + R_XT30_loop + sum(R_added_splices)]; k=1+0.00393*(60-20); r_gauge=(1000/58)*1.03/A_gauge in mOhm/m; lengths in mm, areas in mm^2, remaining resistances in mOhm",
        "electrical": electrical(), "geometry": geometry_probes(),
        "qualifications": [
            "No hardware measurements were made.",
            "All new splice resistance is zero only for tabulation; a real splice consumes the stated remaining budget.",
            "Vendor strand diameters and OD have no retrieved tolerance; strand counts are conservative interpretations, not measured lower bounds.",
            "1.2 and 2.4 mOhm are connector-scope sensitivity cases, not resolved specification interpretations.",
            "The 270mm positive allocation includes a 20mm rigid fuse/joint zone; no copper-displacement credit is taken.",
            "14 AWG direct termination in XT30U cups is unsupported by retrieved manufacturer evidence.",
        ],
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if a.check:
        if not a.out.is_file() or a.out.read_text(encoding="utf-8") != text:
            raise SystemExit("Assessment differs; inspect changed inputs/sources before rewriting")
        print("PASS: saved exploratory electrical and isolated route calculations reproduce")
    else:
        a.out.write_text(text, encoding="utf-8", newline="\n")
        print(a.out)


if __name__ == "__main__":
    main()
