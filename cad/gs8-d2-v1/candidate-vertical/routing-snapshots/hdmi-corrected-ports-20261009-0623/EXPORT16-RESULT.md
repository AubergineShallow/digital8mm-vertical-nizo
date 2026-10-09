# Export16: corrected USB head blocks the rear lower boss

The selected HDMI check is **4pass/2fail** against mechanical manifest
`8a288f3ac9cdae1731867b5ffed0660b7598047ae572d1c2eb410ae60cb5a2e0`.
Both full300mm ribbon poses and both HDMI head/print checks pass. The only
reported failing object is the corrected USB5V head reservation versus the tub.

Its installed intersection is283.8663036mm³ at:

- X[−152.779999,−145.2]
- Y[−15.126001,−5.326001]
- Z[8.250319,12.8]

This region corresponds to the rear lower panel boss centred atX−149.7/Z8.3,
radius4.5. The selected verifier also finds the same USB head hitting that boss
at20 sampled carrier offsets, Y0..38mm. No ribbon/header collision is reported
in that carried sweep. This is an assembly STOP, including before any uncertain
soft-lead service movement is considered.

The independent head check verifies every mechanical STEP hash against this
manifest and preserves source contacts. It finds the corrected USB head clear
of the source Pi5 geometry; all other installed parts except the tub are
rejected by disjoint final bounds. Every carried FPS part, its mated junction,
the central padded rest and open PicoBlade guide are also clear, with actual
solid bounds disjoint in X/Z. Their relative Y translation cannot create a
collision with the static head in this geometric model.

The complete unchanged modeled power cores clear the head with minimum
conservative gap16.901680mm, including0.04mm radial allowance. The inline fuse's
containing capsule clears by45.482536mm. This does not add missing root/joint
material or place the cuttable USB donor lead.

Primary reports:

- `export16-selected-hdmi-checks.json`, SHA256
  `774fe5d21768623fe1e0d8dcd1ac33d5a85df7b5ed5dde39173a5f335ce57f34`
- `export16-head-checks.json`, SHA256
  `ee23ceb9cb39cda408c568bb77fad6868f1d4d95c4b4fd2ec6622c0c87d06707`
- `head-fps-exact-arc-bounds.json`, all45 complete analytic wire primitives clear
- `head-power-clearance.json`, original full power axes and fuse retained

Any boss change must retain a viable screw seat, panel interface, load path and
tool access, then receive a new mechanical manifest and new checks. The failed
export16 reports remain unchanged. No reduction of the unmeasured USB head or
invented wire exit is used to clear the conflict.

The authoritative donor clarification is `usb-donor-provenance.json`. Final
installed copper cuts, both Pololu tails, diode and all rigid joints remain TBD.
Adafruit3557 socket/root registration, actual cooler and CSI latch/tool geometry,
complete200mm camera FPC with both true root frames, and all baseline56/M1
physical gates remain open. There is no blanket service or hardware release.
