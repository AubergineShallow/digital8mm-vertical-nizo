"""r7 physical gates and r7 BX blocker fixes, mapped onto the vertical candidate (review VN-50, FP-15). CAD-free.

Every gate of the r7 build receipt (`cad/gs8-d2-v1/out/build-receipt.json` hardware_gates.gates) and every BX item of
`cad/gs8-d2-v1/guide/BLOCKERS-2026-10-08.md` gets exactly one disposition for the vertical candidate:
  carried    the gate applies unchanged (the part or interface exists in the candidate);
  re-scoped  the gate still applies, but its geometry, frame or procedure moved with the redesign: the r7 numbers in
             its acceptance text must be re-derived for the candidate before it is run;
  replaced   a candidate G-V-* gate (REVIEW.md, physical gates table) takes over its whole scope;
  retired    its subject part was deleted in the candidate (hood, pi_keeper, plunger, stick_sleeve) or r7 already
             withdrew it.
Rules used (review judgement, conservative): retired only when the subject part is absent from the candidate manifest
or r7 withdrew the gate; replaced only where a G-V-* gate names the same scope; otherwise carried or re-scoped. No
gate is closed by this table: carried, re-scoped and replaced gates all stay open physical gates.

  python make_gates_vertical.py            prints the counts
  python make_gates_vertical.py --write    rewrites GATES-VERTICAL.md and the gates blocks in README.md / REVIEW.md
  python make_gates_vertical.py --check    exit 1 if GATES-VERTICAL.md is stale or a gate/BX is unmapped
"""
DELETED_PARTS = ('hood', 'pi_keeper', 'plunger', 'stick_sleeve')
WORDS = ('carried', 're-scoped', 'replaced', 'retired')
G_V = ('G-V-STACK', 'G-V-STORAGE', 'G-V-POWER', 'G-V-HDMI', 'G-V-PIGTAIL', 'G-V-SERVICE', 'G-V-PRINT', 'G-V-THERMAL',
       'G-V-STRAP')

# gate id -> (disposition, candidate gate or check that now carries it, reason)
GATES = {
    'EVF-G1': ('carried', None, 'same HMX039 OLED and EVF board'),
    'EVF-G2': ('carried', None, 'same EVF timing on the Pi'),
    'EVF-G3': ('carried', None, 'same EVF electronics'),
    'EVF-G4': ('carried', None, 'same EVF board supply range'),
    'EVF-G4b': ('carried', None, 'same EVF rail limit (run as G-W6)'),
    'EVF-G5': ('carried', None, 'same HDMI pin 19 behaviour (run as G-W7)'),
    'EVF-G6': ('carried', None, 'same EVF electronics'),
    'EVF-G7': ('carried', None, 'same EVF optics'),
    'EVF-G8': ('carried', None, 'same EVF optics'),
    'EVF-G9': ('carried', None, 'same EVF electronics'),
    'G-CAM-1': ('carried', 'main/j7_float', 'same GS camera and J7-R float; j7_float must pass again after any CAM update'),
    'G-CAM-2': ('carried', 'main/roll_catch', 'same assembled sag acceptance and tab-catch roll stop'),
    'G-CAP-1': ('carried', None, 'the printed cap and its detent are retained'),
    'G-COL-1': ('carried', 'main/lens_clamp', 'same lens collar coupons (collar redesign FP-11d may change them)'),
    'G-COMB-1': ('carried', None, 'clearance comb calibration applies to every printed fit'),
    'G-ENC-1': ('carried', None, 'encoder cradle hooks retained in the panel'),
    'G-EVF-1': ('carried', None, 'same eyepiece spigot pull-out and diopter'),
    'G-EVF-2': ('re-scoped', 'check_scope/evf_restraint', 'the EVF +Y stop moved with the vertical layout; the candidate stop is the evf_restraint rows'),
    'G-EVF-3': ('re-scoped', 'harness + hdmi carried sweep', 'in-situ HDMI mating now follows the candidate step-5 order and the 3557/3556 heads (see G-V-HDMI)'),
    'G-FPC-1': ('carried', None, 'applies only if a shorter verified FPC is chosen instead'),
    'G-HDMI': ('re-scoped', 'G-V-HDMI', 'cable part replaced by G-V-HDMI (3557 Pi head, 3556 EVF head, 300 mm ribbon); the 18/24 switch bushing and tab part is carried'),
    'G-HDR-1': ('carried', 'harness/header_housings', 'same Pi header housings (WIRING-VERTICAL cites it)'),
    'G-J4-1': ('carried', None, 'the J4 grip joint is retained'),
    'G-KEEP-1': ('retired', 'G-V-STACK', 'pi_keeper deleted; stack retention is the carrier (G-V-STACK)'),
    'G-KEEP-1/whole': ('retired', 'G-V-STACK', 'whole-keeper cycles: pi_keeper deleted'),
    'G-KNOB-1': ('carried', None, 'same knob D-bore ladders'),
    'G-LENS': ('carried', 'main/lens_support', 'same lens line; before tub/panel/collar printing'),
    'G-MP-ENC': ('carried', None, 'same Adafruit 5880 encoder and panel cradle'),
    'G-MP-EVF': ('carried', None, 'same EVF jig measurement'),
    'G-MP-FPC': ('re-scoped', 'G-V-SERVICE', 'the r7 S-fold box ko_fpc_loop does not exist in the vertical layout; FPC length and route are re-derived'),
    'G-MP-PACK': ('carried', None, 'same 1S2P pack envelope'),
    'G-MP-STICK': ('replaced', 'G-V-STORAGE', 'stick sleeve and guide deleted; the upper-port storage reserve is G-V-STORAGE'),
    'G-MP-SW': ('carried', None, 'same 18/24 switch tab and nut on the panel'),
    'G-MP-X1203': ('re-scoped', 'G-V-STACK', 'X1203 and cooler limits were stated in the r7 horizontal frame (cooler top z 36.3, keeper finger offsets)'),
    'G-PANEL-1': ('re-scoped', 'G-V-STRAP', 'the panel is held by four screws with the shifted strap; the r7 PH1-only open/close cycle no longer describes it'),
    'G-PANEL-1/whole': ('re-scoped', 'G-V-STRAP', 'whole-panel cycles with the strap fitted, on the candidate panel and screws'),
    'G-PI-1': ('replaced', 'G-V-STACK', 'keeper finger zones deleted; standoff and stack fit are G-V-STACK'),
    'G-PLG-1': ('replaced', 'G-V-POWER', 'plunger deleted; the power switch on J2 is G-V-POWER'),
    'G-PT-1': ('carried', None, 'PT screws in printed bosses are retained'),
    'G-QT-1': ('re-scoped', 'harness/mate_reach qt_enc', 'the QT lead route and fan-in changed (VN-28); the propped-panel dry fit is re-derived'),
    'G-RUN-1': ('carried', None, 'same run button cap'),
    'G-SKIRT-1': ('retired', None, 'withdrawn in r7 (feature deleted)'),
    'G-SNAP-1': ('retired', None, 'withdrawn in r7 (Pi floor hooks deleted)'),
    'G-SNAP-2': ('re-scoped', None, 'hood hook and ledge coupons retired with the hood; the encoder cradle hook coupon is carried'),
    'G-SNAP-2/whole': ('retired', None, 'five whole-hood cycles: hood deleted'),
    'G-W1': ('carried', None, 'same pack receipt'),
    'G-W2': ('carried', None, 'same X1203 identity and pads'),
    'G-W3': ('carried', None, 'same Pi bench bring-up'),
    'G-W4': ('carried', None, 'same X1203 feed test'),
    'G-W5': ('re-scoped', 'G-V-PIGTAIL', 'the pigtail path is the candidate 270 mm route (harness lead_access/pigtail_drop; user decision 4)'),
    'G-W6': ('carried', None, 'same EVF rail test on the bench'),
    'G-W7': ('carried', None, 'same HDMI pin 19 isolation'),
    'G-W8': ('re-scoped', 'G-V-POWER', 'power key is the J2 switch, not the plunger on the Pi button'),
    'G-W9': ('carried', None, 'same controls test'),
    'G-W10': ('carried', 'G-V-STORAGE', 'same sustained recording test; G-V-STORAGE adds the upper-port reserve'),
    'G-W11': ('carried', 'G-V-THERMAL', 'closed-body thermal run; G-V-THERMAL adds the plenum and occlusion cases'),
    'G-W12': ('carried', None, 'closed-body test after the print set'),
    'G-W13': ('carried', None, 'option C regulator (user decision 10)'),
}

# BX id -> (disposition, where the candidate handles it, reason)
BX = {
    'BX-1': ('re-scoped', 'steps.py evf_mate; hdmi carried sweep', 'EVF HDMI mating order follows the candidate steps and heads'),
    'BX-2': ('carried', 'harness/mate_reach qt_enc (fails, VN-28)', 'QT reach with the panel propped is still open'),
    'BX-3': ('carried', 'harness/mate_reach xt30_pack; lead_access (fail, VN-47)', 'XT30 mating length and ties are still open (user decision 6)'),
    'BX-4': ('carried', 'main/roll_catch', 'tab-catch camera hold retained (tab printability FP-11b)'),
    'BX-5': ('carried', 'ASSEMBLY-VERTICAL.md knob press text', 'knob press by thumb; r7 handling rows not ported'),
    'BX-6': ('retired', None, 'plunger and hood deleted'),
    'BX-7': ('carried', 'steps.py foam pad order', 'foam pad present'),
    'BX-8': ('re-scoped', 'G-V-SERVICE', 'no ko_fpc_loop S-fold in the vertical layout'),
    'BX-9': ('re-scoped', 'usb_5v route volumes (FP-11f, VN-60)', 'no hood; the EVF feed parts move onto the usb_5v route'),
    'BX-10': ('re-scoped', 'harness/header_housings', 'header-to-wall distances changed with the vertical Pi'),
    'BX-11': ('re-scoped', 'G-V-STACK', 'stack handling is on the carrier'),
    'BX-12': ('re-scoped', 'main/driver', 'no hood; driver margins come from the candidate driver rows'),
    'BX-13': ('carried', None, 'same proud panel shafts before the knobs; the r7 fix is not yet written into ASSEMBLY-VERTICAL.md and r7 handling rows are not ported'),
    'BX-14': ('carried', None, 'same 18/24 shaft cut; the r7 guide fix is not yet written into ASSEMBLY-VERTICAL.md'),
    'BX-15': ('carried', 'steps.py collar and gauge before the camera (VN-39)', 'same centring gauge and collar screws'),
    'BX-16': ('re-scoped', 'harness/cable_routes run_pin37/39 (fail, VN-26)', 'the run lead route changed and is still open'),
    'BX-17': ('retired', None, 'hood deleted'),
}
