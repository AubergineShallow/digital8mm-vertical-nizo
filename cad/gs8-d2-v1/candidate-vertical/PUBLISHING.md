# Publication handoff

This is a local engineering review candidate. The approved separate destination is `AubergineShallow/digital8mm-vertical-nizo`; publication has not been completed. It is an independent repository retaining the original project's history, rather than a same-owner GitHub fork.

The original repository is `https://github.com/AubergineShallow/digital8mm`, baseline commit `d38468e58eb2b02d56743e2e0cfdd8f780818a65`. Its local push URL is deliberately disabled. Do not push this candidate to that original repository.

The delivered full Git bundle preserves the upstream history and the `redesign/vertical-pi-hidden-vents` branch. Restore it with:

```sh
git clone --branch redesign/vertical-pi-hidden-vents D2-vertical-nizo-history.bundle digital8mm-vertical-nizo
cd digital8mm-vertical-nizo
git bundle verify ../D2-vertical-nizo-history.bundle
```

Once the approved destination exists and an authorized GitHub session is available, add that destination as a separate remote and push the candidate branch. Verify the remote commit matches the local commit before claiming publication. No credential setup or access bypass is included in this handoff.

Keep the review designation visible in the repository description and README. The cooler/source conflict, possible 35 mm roof bridge, slicer/coupon tests, complete flexible wiring/service checks, thermal validation and all 56 inherited physical gates plus M1 remain unresolved. Publishing source does not authorize printing, energizing or fabrication release.
