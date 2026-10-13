#!/usr/bin/env python3
"""Derive compact Innomaker review records without importing or rebuilding CAD.

The immutable baseline BOM stays untouched. A complete, source-current fork
manifest is mandatory; missing or stale evidence fails before any output write.
No record produced here grants fabrication, fit, electrical or software release.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
FORK = BASE / "innomaker"
ROOT = BASE.parent
MANIFEST = FORK / "out/compact-kowa_lm6hc/manifest.json"
BASELINE = BASE / "BOM-VERTICAL.csv"
HISTORICAL = "historical/unqualified for Innomaker; "
HISTORICAL_NOTE = (
    "Historical baseline text; unqualified for the Innomaker fork. Any earlier "
    "export, test or pass statement below is not current Innomaker evidence. "
)
PRODUCT_URL = "https://www.inno-maker.com/product/cam-imx296color/"
SOURCES = [
    {
        "file": "fetch/manufacturer-README-46d6d217.md",
        "licence": "none stated (GitHub API license: null); not redistributed in this repository",
        "url": "https://raw.githubusercontent.com/INNO-MAKER/cam-imx296raw-trigger/46d6d217f0d754921503ef64a3d801aa935563d6/README.md",
        "commit": "46d6d217f0d754921503ef64a3d801aa935563d6",
        "sha256": "48c939936fc59d5865c9445b29baef24b2d91ad1796538429e7f77b34f1cfdc3",
    },
    {
        "file": "fetch/raspberrypi-imx296-f1c327d2.c",
        "licence": "GPL-2.0 (SPDX header in the file); cited by URL, commit and hash, not redistributed here",
        "url": "https://raw.githubusercontent.com/raspberrypi/linux/f1c327d2ae5c1ffdb7a17660bf87b4a22d2ae313/drivers/media/i2c/imx296.c",
        "commit": "f1c327d2ae5c1ffdb7a17660bf87b4a22d2ae313",
        "sha256": "2af91529cefa4510602ad6b28355207fde7ef89e105d3d54a786b853b17e50b8",
    },
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def csv_bytes(rows: list[dict], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def collect() -> dict[Path, bytes]:
    require(MANIFEST.is_file(), "Fresh Innomaker manifest is missing; run the locked fork export first.")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(manifest["storage"] == "compact" and manifest["lens"] == "kowa_lm6hc", "Wrong export variant.")
    provenance = manifest["innomaker"]
    require(provenance["amazon_asin"] == "B0CQ4DTQZ2", "Wrong camera identity.")
    headers = provenance["rear_headers"]
    require(headers["source_step_models_headers"] is False, "Header evidence changed; review records before regenerating.")
    require(headers["actual_xy_mm"] is None and headers["actual_projection_mm"] is None, "Measured headers require a reviewed records revision.")
    require(provenance["physical_qualified"] is False, "This generator is for an unqualified fork only.")
    require(not provenance["new_purchased_parts"] and provenance["exterior_change"] is False, "Scope changed.")
    require(manifest["sources"], "Manifest has no source bindings.")
    for relative, expected in manifest["sources"].items():
        path = (ROOT / relative).resolve()
        require(path.is_file() and sha(path) == expected, f"Stale or missing CAD source: {relative}")
    for source in SOURCES:
        # Third-party snapshots are not committed. Fail closed with a fetch instruction when one is absent.
        local = FORK / source["file"]
        require(local.is_file(), f"Fetch prerequisite missing: download {source['url']} to innomaker/{source['file']} "
                "(git-ignored folder) and rerun; its SHA-256 must be " + source["sha256"])
        require(sha(local) == source["sha256"], f"Software snapshot changed: {source['file']}")

    printed = sorted((r for r in manifest["rows"] if r["kind"] == "printed"), key=lambda r: r["id"])
    ids = [r["id"] for r in printed]
    production = manifest["production_prints"]
    require(len(ids) == len(set(ids)) == 9, "Expected nine distinct compact production prints.")
    require(production["assembly_row_count"] == production["piece_count"] == len(ids), "Inconsistent print counts.")
    files = sorted(f"stl/{name}.stl" for name in ids)
    require(files == sorted(production["files"]), "Production file list does not match printed rows.")
    require("tab_catch_insert" not in ids and "centring_gauge" not in ids, "Stub or gauge incorrectly counted as production.")
    print_rows = []
    for row in printed:
        name = row["id"]
        relative = f"stl/{name}.stl"
        require(sha(MANIFEST.parent / relative) == manifest["files"][relative], f"STL identity mismatch: {relative}")
        pose = manifest["print_poses"][name]
        require(pose["physical_release"] is False, f"Unexpected print release: {name}")
        print_rows.append({
            "part": name, "quantity": 1, "stl": f"out/compact-kowa_lm6hc/{relative}",
            "sha256": manifest["files"][relative], "face_down": pose["face_down"],
            "footprint_mm": json.dumps(pose["footprint_mm"], separators=(",", ":")),
            "slicer_state": pose["slicer_state"], "physical_release": "false",
            "status": "candidate/unqualified; source/header, slicing and physical gates remain HOLD",
        })

    with BASELINE.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        baseline = list(reader)
    original = {row["line"]: row for row in baseline}
    require(len(original) == len(baseline), "Duplicate baseline BOM line.")
    removed = {
        "I-tub-stub": "BFAR catch removed; fork tub is one production piece with integral passive guides.",
        "V-68": "This epoxy line solely served the removed +Y tab-catch stub (layout_id tab_catch_insert); all unrelated adhesive/RTV provisions remain.",
        "I-05B": "Obsolete official-camera PCB tripod-block kit detail only; baseline installed/purchase quantities were both zero. The functional D2 grip tripod mount and D2-31 nut remain.",
    }
    rows = []
    for source in baseline:
        if source["line"] in removed or source["section"] == "D. Printed production parts":
            continue
        row = dict(source)
        row["status"] = HISTORICAL + source["status"]
        row["note"] = HISTORICAL_NOTE + source["note"]
        if row["variant"] == "original only":
            row["installed_qty"] = row["purchase_qty"] = "0"
            row["note"] = "Not selected in this compact fork. " + row["note"]
        if row["line"] == "D2-05":
            row.update(
                item="Innomaker colour IMX296 CSI camera with CS holder (no C/CS converter in the manufacturer packing list)",
                variant="compact only", status="candidate/unqualified; rear headers (named in manufacturer docs) absent from STEP; source revision and clearance HOLD",
                sku_or_class="CAM-IMX296Color-GS / CAM-MIPI296Color; Amazon ASIN B0CQ4DTQZ2",
                supplier="Innomaker; user-selected Amazon listing B0CQ4DTQZ2",
                note="Replaces D2-05 one-for-one; not an additional camera purchase. Public STEP omits the two 2-pin rear headers (named in the manufacturer docs). Board outline OPEN: product page 38 x 38 mm, STEP 39 x 39 mm. Header XY/projection, cap identity, CS optical datum, actual converter/thread seating and clocking, holder-supported lens assembly, and full CSI route are unverified. Do not remove or bend pins. No trigger/strobe wiring is needed for the proposed ordinary free-running CSI use. No physical, optical or software qualification is claimed.",
                source=PRODUCT_URL,
            )
        elif row["line"] == "I-05A":
            row.update(
                item="C/CS converter for the Innomaker camera: NOT in the manufacturer packing list; OPEN",
                status="OPEN: confirm on receipt; if the kit has none, one must be bought (user decision; needs a reviewed BOM revision)",
                sku_or_class="Not listed in the product-page packing list (read 2026-10-13); verify received kit",
                supplier="Innomaker", source=PRODUCT_URL,
                note="Not listed by the manufacturer (packing list: camera, 15-15 and 15-22 FPC, M12 lens and holder, CS holder with IR filter). This generator does not add purchases, so purchase quantity stays 0 until a reviewed BOM revision. The 5 mm nominal register separation and OD 30.75 / ID 25.5 mm reservation are assumptions only. Received converter, threads, seating faces, rear-cell clearance and clocking remain HOLD. No optical datum or fit follows from the annular reserve.",
            )
        elif row["line"] == "D2-20":
            row.update(
                status="historical/unqualified for Innomaker; 200 mm Standard-Mini cable class retained provisionally",
                note="Retain the existing official Pi 5 Standard-Mini 22-to-15-pin, 200 mm cable provision; no second cable is added. The Innomaker kit's included cable has not been verified for pin count, contact orientation, length, stiffeners or equivalence, so it does not replace D2-20 in this BOM. Seat the Pi end on the supported bench before the official Active Cooler. Only the camera end is proposed for later panel-off access; full ribbon width, latch/jaws, bends, slack, clocking and flexible service remain HOLD. Old opening/tool reservations do not qualify the real cable.",
                source="https://www.raspberrypi.com/documentation/accessories/camera.html",
            )
        elif row["line"] == "D2-31":
            row["note"] += " The functional D2 grip tripod socket is retained: one installed 1/4-20 UNC nut in the existing base-grip hex pocket. This is separate from the removed, zero-quantity I-05B official-camera PCB tripod-block detail."
        elif row["line"] == "T-gauge":
            row["note"] = HISTORICAL_NOTE + "Retain the existing collar centring gauge for the selected lens. It is a separate non-production tool, excluded from the fresh manifest's nine production pieces. Gauge slicing, dimensional and physical acceptance remain HOLD."
        rows.append(row)

    for name in ids:
        require(f"P-{name}" in original, f"New print identity needs explicit BOM review: {name}")
        row = dict(original[f"P-{name}"])
        row.update(
            variant="compact only", status="candidate/unqualified; fresh manifest count only; print release HOLD",
            installed_qty="1", installed_unit="physical printed piece", purchase_qty="0", purchase_unit="physical printed piece",
            note=("One production piece in the fresh compact Innomaker manifest. Nine production prints total; centring gauge and coupons excluded. "
                  + ("Integral passive PCB-edge safety guides replace BFAR catches; no separately bonded stub, no V-68 epoxy, and no PCB torque or preload credit. " if name == "tub" else "")
                  + "Material class is inherited and unqualified. Use the bound print pose and STL hash in PRINT-INVENTORY.csv. Slicing, supports, dimensional coupons, strength and physical qualification remain HOLD."),
            source="out/compact-kowa_lm6hc/manifest.json",
        )
        rows.append(row)

    output_ids = {row["line"] for row in rows}
    require(not output_ids.intersection(removed), "Removed constituent or adhesive remains in BOM.")
    cooler = next(row for row in rows if row["line"] == "D2-02")
    require(cooler["sku_or_class"] == "SC1148" and cooler["installed_qty"] == "1", "Official Active Cooler changed.")
    tripod = next(row for row in rows if row["line"] == "D2-31")
    require(tripod["installed_qty"] == tripod["purchase_qty"] == "1" and tripod["layout_id"] == "tripod_nut", "Functional D2 tripod socket changed.")
    require(any(row["id"] == "tripod_nut" and row["kind"] == "cots" for row in manifest["rows"]) and "base_grip" in ids, "Functional tripod mount is missing from the fresh assembly.")
    for identity in ("D2-45", "D2-46", "D2-46R", "D2-48", "D2-49"):
        retained = next(row for row in rows if row["line"] == identity)
        require(all(retained[key] == original[identity][key] for key in ("item", "installed_qty", "purchase_qty")), f"Unrelated adhesive/consumable changed: {identity}")
    for row in rows:
        require(row["line"] in original, "A new purchased identity was added.")
        require(Decimal(row["purchase_qty"]) <= Decimal(original[row["line"]]["purchase_qty"]), f"Purchase quantity increased: {row['line']}")
    require(sum(Decimal(row["installed_qty"]) for row in rows if row["section"] == "D. Printed production parts") == 9, "Printed BOM count mismatch.")

    bom = csv_bytes(rows, fields)
    inventory = csv_bytes(print_rows, list(print_rows[0]))
    record = {
        "schema": "innomaker-review-records-v1", "state": "HOLD: source/header clearance; no fabrication or fit release",
        "scope": "compact Kowa LM6HC / Princeton storage; Innomaker colour camera substitution only",
        "restored_baseline_commit": "a0bfed9f7ed88dad78ad1a5fcb6fc7504712b338",
        "header_aware_source_checkpoint": "c6a040f9654faa9bdb761b1ae7b70cc14a9e3453",
        "lost_prior_fork": "5736870 and its lost exports/pass counts are not current evidence",
        "manifest": "out/compact-kowa_lm6hc/manifest.json", "manifest_sha256": sha(MANIFEST),
        "baseline_bom": "../BOM-VERTICAL.csv", "baseline_bom_sha256": sha(BASELINE),
        "generator": "../make_innomaker_records.py", "generator_sha256": sha(Path(__file__)),
        "source_binding_check": "All manifest-bound CAD source hashes and production STL hashes matched before generation.",
        "production_prints": {"piece_count": len(ids), "assembly_row_count": len(ids), "ids": ids, "gauge_and_coupons_excluded": True},
        "bom_rows": len(rows), "bom_sha256": hashlib.sha256(bom).hexdigest(),
        "print_inventory_sha256": hashlib.sha256(inventory).hexdigest(),
        "removed_baseline_rows": removed,
        "compact_selection": "Original-storage D2-09 retained as a zero-quantity historical alternative; P-stick_sleeve excluded from compact prints.",
        "changed_identities": ["D2-05", "I-05A"],
        "open_bom_items": ["I-05A C/CS converter not in the manufacturer packing list: confirm on receipt or buy (user decision)"],
        "third_party_files_committed": False,
        "retained_cable": "D2-20 provision retained; included Innomaker cable equivalence unknown; no duplicate purchase",
        "retained_cooler": "D2-02 official Raspberry Pi Active Cooler SC1148",
        "retained_tripod_mount": "D2-31: one installed and one purchase-provisioned 1/4-20 UNC nut; tripod_nut solid and base_grip socket retained. Removed I-05B had zero installed/purchase quantity and described only the old camera PCB's separate tripod block.",
        "retained_other_adhesives_and_consumables": ["D2-45", "D2-46", "D2-46R", "D2-48", "D2-49"],
        "new_additional_purchased_parts": [], "exterior_growth_authorized": False,
        "rear_headers": headers, "software_snapshots": SOURCES,
        "physical_qualified": False, "software_hardware_qualified": False,
        "inherited_status": "Every inherited status and note is prefixed historical/unqualified; earlier passes are not fork evidence.",
        "holds": provenance["holds"],
    }
    return {
        FORK / "BOM-INNOMAKER.csv": bom,
        FORK / "PRINT-INVENTORY.csv": inventory,
        FORK / "records.json": (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check existing records byte-for-byte; do not write.")
    args = parser.parse_args()
    outputs = collect()
    if args.check:
        for path, expected in outputs.items():
            require(path.is_file() and path.read_bytes() == expected, f"Missing or stale record: {path.relative_to(BASE).as_posix()}")
        print("Record identities and deterministic derivation verified; source/header and physical release remain HOLD.")
        return
    for path, content in outputs.items():
        path.write_bytes(content)
        print(path.relative_to(BASE).as_posix())
    print("Nine production prints derived from the fresh manifest. No physical or software qualification claimed.")


if __name__ == "__main__":
    main()
