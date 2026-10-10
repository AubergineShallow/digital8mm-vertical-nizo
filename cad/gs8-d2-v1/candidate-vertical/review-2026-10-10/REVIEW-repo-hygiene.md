# Repo-hygiene review: digital8mm-vertical-nizo @ 9ced753

Scope: repository and reproducibility of the clone at `C:\Users\Pre-Installed User\Claude\Projects\digital8mm-vertical-nizo`
(main = origin/main = origin/redesign/vertical-pi-hidden-vents = 9ced753, parent d38468e = r7).
Method: read-only git queries and probes. Nothing in the clone was written. `git status --ignored` after all probes shows only
the pre-existing `.cad.lock`. Probes and their raw outputs are next to this report:
`crlf_probe.py` -> `crlf_probe_out.json`, `bind_probe.py` -> `bind_probe_out.json`, `struct_diff_probe.py`,
`docs_audit_sandbox.py` (write-redirecting wrapper) -> `audit_utf8.json`, `reconcile_sandbox.py`.

Environment facts used: Git for Windows system config sets `core.autocrlf=true`
(`C:/Program Files/Git/etc/gitconfig`). The clone's worktree is LF only because it was cloned with autocrlf off;
its `.git/config` does not pin `core.autocrlf`. The remote is public: an unauthenticated `git ls-remote` with no
credential helper returns 9ced753.

## Findings table

| id | severity | kind | title | closable by |
|---|---|---|---|---|
| REP-1 | major | latent | `* -text` removed: a default Windows clone rewrites 702 text files, which breaks 413 recorded SHA-256 bindings (137 of them on r7 files), and `git status` still shows clean | repo |
| REP-2 | major | latent | The published snapshot cannot verify itself: 136 bound mesh files and 32 guide page images are gitignored | repo |
| REP-3 | major | latent | The documented snapshot checks fail on Windows (locale encoding, `str(Path)` backslashes, CRLF writers) | repo |
| REP-4 | major | latent | Raspberry Pi MIT notice is not carried with 7 derived Pi STEP copies, and the public repo has no NOTICE file | repo |
| REP-5 | minor | latent | +652 MB: 518 MB of it is STEP, 3 files exceed GitHub's 50 MiB warning, and the Pi STEP is duplicated (copies differ only by a timestamp) | user_decision |
| REP-6 | minor | latent | Stale or conflicting entry documents (PUBLISHING.md, root README, CLOUD-START-HERE.md, HANDOFF.md, "Library") | docs |
| REP-7 | minor | latent + existing | 214 broken relative links: 159 new ones in copied history docs, 55 inherited from r7 | docs |
| REP-8 | minor | latent | Undeclared toolchain: pypdf and scipy are missing from the lock; Blender is unpinned; g++/.so is Linux only; POSIX commands | repo |
| REP-9 | minor | latent | Evidence or inputs come from code and files that are not in the repo (/tmp scripts, Pi extractor, /tmp logs) | repo |
| REP-10 | info | latent | The documented "inspect" or check commands rewrite or move committed files | repo |
| REP-11 | info | latent | Contributor friction: stray tmp PNGs, 50 study scripts at top level, code-golf lines, a one-line commit message | repo |

What checked out: there are no tracked-but-ignored files (`git ls-files -i -c --exclude-standard` returns 0). No file exceeds
GitHub's 100 MiB hard limit. There are no absolute Windows or home paths, and the user's email does not appear in new files. PDF metadata is
neutral (ReportLab, "D2 design review"). The live candidate docs (README, REVIEW, ASSEMBLY, BOM, REPRODUCE, MEASUREMENTS)
have 0 broken links. In an LF clone the r7 `cad/gs8-d2-v1/out/build-receipt.json` still matches all 178 bindings. The three current
manifests match all their committed `sources`/`files` (128/128/130 ok) apart from the ignored meshes. `run_locked.py` is
cross-platform. DejaVuSans.ttf ships with `fonts/LICENSE-DejaVu.txt`.

## REP-1 (major, latent): line-ending protection removed

Evidence:
- r7 `.gitattributes` was `* -text`, with the comment "Build receipts and verification records hash the exact bytes ...
  any line-ending conversion ... would break them on a fresh clone". At 9ced753 it is replaced by `-diff -text` for
  only step/stp/stl/pdf/png/ttf/docx (`.gitattributes:1-8`). No rationale exists in the commit message or the docs.
- Probe `crlf_probe.py` uses `git -c core.autocrlf=true cat-file --filters`, which applies the same smudge as checkout.
  It found 702 LF text files (371 .py, 188 .json, 120 .md, 7 .csv, ...) whose bytes change on a default Windows clone.
  335 of them are r7 files. For 413 of the 702, the original SHA-256 is recorded in 174 committed files.
  137 of the 413 are r7 files, for example the r7 `out/build-receipt.json` (60 bindings) and the Fujinon `build-receipt.json` (58).
  The worst recorders are `guide-receipt.json` (204), the `integrated-fps-*checks.json` files (77-91 each), each variant `manifest.json` (76)
  and `review-docs-audit.json` (57).
- The failure is already visible in this review's own environment. In `digital8mm-vertical-nizo-rebuild`,
  `out/review-docs-audit.json` is `i/lf w/crlf`, with sha 0d2271bb... against the committed 2883c45c.... Stripping CR gives the committed hash.
  `git status` shows the file as clean.
- 66 CRLF and 6 mixed-ending r7 files (plus the new `official-fpc-sources/LICENSE.txt`) are now "text auto".
  `git add --renormalize` or an edit under autocrlf would rewrite them.

Failure scenario: the user clones with the Git for Windows defaults or GitHub Desktop. Every manifest, receipt or audit
that binds a .py/.json/.md hash now fails, including r7's own release audit. `git status` reports nothing, so the drift looks like
a design change or tampering.

Fix: restore `* -text` as the first rule. Keep the binary `-diff` rules after it. In the rebuild worktree, run
`git config core.autocrlf false` (or re-checkout after the attribute fix) before any fix is regenerated.

## REP-2 (major, latent): bound inputs are gitignored

Evidence:
- `.gitignore:29` ignores `candidate-vertical/out/*/meshes/`. Each variant `manifest.json` `files` binds 45/45/46
  `meshes/*.json` (bind probe: `missing_ignored_n` 45/45/46). `guide-receipt.json` binds 45 `mesh_files` and 32
  `page_images` (`page-*.png`, ignored by `.gitignore:31`). The probe found 77 of these missing.
- `review_docs_audit.py:19` binds `m['files']` and needs `meshes/manifest.json`. A sandboxed run (writes redirected) on the
  fresh clone gives `files pass False` (45/45/46 missing) and `mesh_manifest_identical False` for all 3 variants. The committed
  `out/review-docs-audit.json` says `True`/0 missing for all 3. The repo cannot reproduce its own audit.
- `reconcile_review_evidence.py:9` (`assert sha(D/rel)==h` over `m['files']`) stops with FileNotFoundError on
  `meshes\tripod_nut.json` when run on the clone, although REPRODUCE says it "does not execute CAD".
- `guide/package_concealed_guide.py:14-17` hashes every `page_images` and `mesh_files` entry and so cannot run.
  `guide/build_guide_concealed_vents.py:28,132` reads `out/compact-kowa_lm6hc/meshes`. REPRODUCE "For the supplied
  unchanged snapshot only" therefore cannot be run from the repo, and a re-export changes the manifest hash, as REPRODUCE itself says.
- Off-repo pointers: `history/reviewed-export18/manifest.json` binds 102 files that are not committed. The angled-channel
  manifest also binds 102. 5 render receipts point to ignored PNGs. The export18 README says the full package "remains separately
  preserved in Library".

Failure scenario: a reviewer runs the documented inspection on a clone and gets failures or crashes. A tired fixer might
then "fix" the checker or drop mesh bindings, which would weaken a check.

Fix: commit the mesh JSONs and guide page PNGs for the nominated manifest (they are deterministic inputs that are bound by hash).
Or make every verifier treat ignored caches as explicitly "regenerable, not verified" and document a re-export path that
does not claim the 53e668d4 identity. Do not delete bindings.

## REP-3 (major, latent): the documented checks are not platform-neutral

Evidence (all three commands under REPRODUCE "Inspect the supplied snapshot", run read-only on the clone):
- `make_bom_vertical.py --check` with the default Windows encoding prints `Stale output: BOM-VERTICAL.md`. The cause is
  `make_bom_vertical.py:399` `path.read_text()` with no encoding (cp1252) after `write_text(..., encoding='utf-8')`.
  With `-X utf8` it passes (131 rows).
- `structural-review/update_concealed_vent_structure.py --check` fails even with `-X utf8`:
  `AssertionError: Stale structural output: concealed-vent-structural.json`. The only difference is at line 38 of the generator,
  where `str(vp.relative_to(C))` gives `"out\\compact-kowa_lm6hc\\shadow-plenum-checks.json"` instead of the committed forward-slash path.
- `review_docs_audit.py` with the default encoding raises `UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d`.
- In the candidate .py files there are 122 `write_text(` calls in 108 files, and none passes `newline=`. On Windows they
  write CRLF, so a Windows regeneration changes every downstream hash. r7 writes with `newline='\n'` (for example `build_d2.py:62`).

Failure scenario: the user runs the snapshot checks on the project's own platform and gets false "stale" or crash results.
Regenerated evidence is then not byte-comparable with the Linux-produced snapshot.

Fix: use `encoding='utf-8'` on every read/write, `newline='\n'` on every text write, and `.as_posix()` for recorded paths.
Add a Windows smoke check of the three `--check` commands.

## REP-4 (major, latent): Raspberry Pi MIT notice

Evidence: the only notice is `routing-snapshots/hdmi-ck1044-clear-20261009-0524/official-fpc-sources/LICENSE.txt`
("Copyright (c) 2026 Raspberry Pi Ltd", MIT: "shall be included in all copies or substantial portions").
The candidate's own `official_pi5_csi.py:5` says "Preserve the manufacturer's LICENSE.txt with copies".
Seven committed derived copies sit in folders with no notice: `out/source-components/pi5-corrected.step`
(52,030,331 B), `out/{compact-kowa,compact-fujinon,original-kowa}/step/pi5.step` and the three `assembly.step`.
The manifest row `pi5` records that these come from the official RP-010083 STEP (sha 78164070...).
The repo has no root LICENSE, NOTICE or THIRD-PARTY file, and the repo is public.

Failure scenario: someone downloads a variant `out/` folder or a single STEP (the natural download unit) and redistributes
Raspberry Pi geometry without the required notice.

Fix: add a root `THIRD-PARTY-NOTICES.md` (Raspberry Pi MIT text, the source URL and hash, the list of derived files, and the DejaVu licence).
Copy `LICENSE.txt` into `out/source-components/` and into each variant `step/` folder. Also state a licence for the project's own content
(today only `tools/` and `software/gs8-camera-evf/` have one; this gap is inherited from r7).

## REP-5 (minor, latent): repository size and duplication

Evidence: the tree is 131,620,220 B at r7 and 783,828,394 B at HEAD, so 652.2 MB was added. 169 STEP files (517.7 MB) make up 79% of that.
The pack is 156.6 MiB. Files above 50 MB: three `assembly.step` at 66.2-66.5 MB (63.1-63.4 MiB, above GitHub's 50 MiB push
warning) and four Pi STEPs at 51.99-52.03 MB (49.6 MiB, just under it). The largest file has 37% headroom to the 100 MiB hard limit.
The three per-variant `pi5.step` files are byte-identical apart from the STEP header timestamp (`cmp -l` shows 5 bytes differ;
the content hash after the header is equal). That is 156 MB of duplicated working tree, and the Pi geometry appears in 7 committed files. Two
`input.json` routing snapshots are identical (11.06 MB each). There are 98 duplicate-blob groups (28.6 MB redundant). No LFS is used.

Failure scenario: slow clones (more than 780 MB checkout) and push warnings. One more detailed part in an assembly could cross 100 MiB and
block a push. Non-deterministic STEP headers make every re-export look changed.

Fix (needs a user decision): keep one Pi STEP and reference it by hash from the variants. Move the assembly STEPs to Release
assets, or regenerate them on demand (LFS is possible, but GitHub's free LFS bandwidth is small for 0.5 GB). Make STEP headers deterministic.

## REP-6 (minor, latent): stale or conflicting entry documents

Evidence: `candidate-vertical/PUBLISHING.md:3` says "publication has not been completed" and gives a bundle restore. The repo
is in fact public at 9ced753 on both `main` and `redesign/vertical-pi-hidden-vents`. Root `README.md:22` says the work is "intended
for a separate history-preserving repository", but it already is that repo. `README.md:20` sends readers to `CLOUD-START-HERE.md` for "Cloud setup".
That file is unchanged r7 text ("Fork: r5-cloud-polish-20261007", "Current result r6", "All 53 physical gates", outputs in
`cad/gs8-d2-v1/out/`) and describes the horizontal design, not the candidate (56 gates + M1). `cad/gs8-d2-v1/HANDOFF.md` still presents
r7 as current, with no pointer to the candidate. `history/reviewed-export18/README.md:1` cites an off-repo "Library".

Failure scenario: a new contributor follows CLOUD-START-HERE and rebuilds or prints the horizontal r7 body, or tries to "publish" a
repo that is already public.

Fix: update PUBLISHING.md to "published at 9ced753" (or remove it). Make the README say which design is current, and add a
banner to CLOUD-START-HERE.md and HANDOFF.md that points to the candidate. Remove the "Library" reference or replace it with an artifact location.

## REP-7 (minor): broken relative links

Evidence (probe over all 577 relative links in committed .md, resolved against the committed tree): 214 are broken.
159 of them are new: copied docs whose links break after the move, in `history/reviewed-export18/` (BOM 64, REVIEW 6, ASSEMBLY 3),
`vent-study/angled-channel-trial/` (BOM 64, REVIEW 7, ASSEMBLY 4) and `history/UPSTREAM-README-d38468e.md` (11; root-relative links
in a deep folder). 55 are inherited from r7: `candidate-fr1/CANDIDATE.md` (40, into the ignored `out/`), `electronics/gs8-evf-v1/EVF-SELECTION.md`
(10), `software/gs8-camera-evf/README.md` (4) and `LENS-M12-ANAMORPHIC.md` (1). `review_docs_audit.py` checks only "owned" live docs, so it reports 0.

Fix: add a banner to the frozen copies ("links are relative to the original location") or rewrite their links. Point the upstream README links to
d38468e on GitHub. Add a repo-wide link check.

## REP-8 (minor, latent): undeclared or unpinned toolchain

Evidence: `tools/bootstrap_cad.py:38` runs `uv pip sync` (an exact set) on `cad/gs8-pxl-v3/cad-requirements-lock.txt` (43 lines).
That lock has neither `pypdf` nor `scipy`, and the pinned venv here has neither (`find_spec` returns False).
`structural-review/build_shadow_structural_pdf.py:11` (`from pypdf import PdfReader`) is REPRODUCE step 4, so it fails in the pinned env.
`scipy.spatial.cKDTree` is imported by 8 `screen_fps_*.py` scripts and by `routing-snapshots/fps-access-20261009-0402/check-source.py`.
Blender (no version recorded anywhere) is called by `run_shadow_renders.py:9`, `run_vent_renders.py:6,8` and `render_views.py`,
and it reads the ignored `meshes/`. The render receipts record the renderer hash but not the Blender version.
`guide/software_lineart.py:8-9` compiles `raster.so` with `g++ -shared -fPIC` and loads it with ctypes. That is Linux only;
`package_concealed_guide.py:46` admits "Rebuild on Linux".
REPRODUCE uses `python3` and `.venv-cad/bin/python` (on Windows the path is `.venv-cad\Scripts\python.exe`).

Fix: add pypdf and scipy to the lock (or remove the imports). Record the Blender version in receipts and docs. Document that the
renders and the guide are Linux-only, or add a Windows build path. Give Windows commands in REPRODUCE.

## REP-9 (minor, latent): evidence or inputs that the repo cannot reproduce

Evidence: `routing-snapshots/power-csi-clear-20261009-0358/independent-audit.json:766-768` lists
`python /tmp/xt30_independent_audit/{audit,self_contact,finish_report}.py`; those scripts are not in the repo.
`out/final-check-run.json:5,11,17` points to `/tmp/d2-final-*.log`, which is not committed (`*.log` is ignored).
`probe_power_boolean2.py:9,12` reads `/tmp/oldvalid-base_grip.step`. No committed script writes `*-native.step` or
`connector-extraction.json`; only readers exist (`official_pi5_geometry.py:67`, `make_corrected_pi.py:14`). So the extraction from the
official STEP (sha 78164070..., `source_solid_indices`) cannot be reproduced, although the URL and hash allow an independent check.
REPRODUCE partly admits that `probe*` files "require recorded temporary inputs".

Fix: commit the extractor and the independent-audit scripts, or mark those JSONs "non-reproducible provenance". Drop the /tmp log pointers.

## REP-10 (info): the documented commands mutate the committed snapshot

Evidence: in REPRODUCE "Inspect the supplied snapshot", `review_docs_audit.py:119` rewrites `out/review-docs-audit.json` with a
new `generated_utc`, and on Windows with CRLF. `reconcile_review_evidence.py:53` rewrites `current-review-evidence.json`.
`run_shadow_checks.py` moves the committed `routing-snapshots/hdmi-export17-selected-20261009-0704/shadow-plenum-head-checks.json`
into `history/head-checks/`. REPRODUCE asks for a separate checkout only for the rebuild section.

Fix: add an `--out` or `--check` mode that writes outside the tree by default.

## REP-11 (info): contributor friction

Evidence: `structural-review/tmp/pdfs/supplement-{1,2}.png` are committed and nothing references them. 50 probe, study, screen and fps
scripts sit at the candidate top level beside the selected pipeline. There are 28 `source-*.py` snapshot copies. 264 lines are over 300
characters in 80 non-history .py files (26 lines over 1000; the longest, 1763, is in `out/fps-service-study/verify_fps_integrated_export17.py`).
Commit 9ced753 (636 files, 3.3 M insertions, author `dot <dot@assistant.invalid>`) has a one-line message.

Fix: move studies under `studies/`, delete the stray tmp PNGs, and add a short CONTRIBUTING or "selected pipeline" index.

## Suggestions beyond the findings

1. Do the REP-1 fix first. Every later regeneration and receipt rebind depends on byte-stable checkouts. In the rebuild worktree, set
   `core.autocrlf=false` before any fix runs.
2. Add a CI job (Linux and Windows) that clones fresh and runs the three snapshot checks, the docs audit and a link check, all read-only.
3. Decide in one place which design is current (r7 horizontal or the vertical candidate), and make README, CLOUD-START-HERE and HANDOFF agree.
