# FPC: what the current HDMI audit establishes

The interacting camera loom remains **unresolved**. The HDMI audit does not
contain a full 200 mm FPC, and its orientation-independent overlap does not prove
an actual ribbon collision. The existing data are insufficient to place a
complete, source-grounded strip without selecting an unmeasured free-flex root
datum at each connector. A nominal illustration could assume those datums, but
would not close this gap.

## Represented material and missing stock

The retained purchased item is the official 200 mm Raspberry Pi Standard–Mini
22-to-15 camera cable, BOM D2-20. No shorter cable or reduced width is adopted.
The conservative planning width remains 16 mm across the entire 200 mm.

`source-signal_routes.py` represents only a circular-filleted centerline through:

1. Pi nominal root (−83, −0.8, 61)
2. (−83, −0.8, 82)
3. (−33.5, −0.8, 82)
4. (−33.5, 0, 43.75)
5. Camera nominal root (−28.09, 0, 43.75)

The raw polyline is 114.168365 mm; replacing three right-angle corners with
R1 arcs gives 112.880754 mm. Initial and final declared straight allowances are
5 and 4 mm. The final raw leg is 5.41 mm, leaving only 4.41 mm after its R1 trim.
Neither 4 mm nor R1 is a measured/qualified camera-cable requirement.

The attributes `full_width_mm=16` and `thickness_allowance_mm=0.3` are numbers,
not material-coordinate faces, sections, width vectors, stiffener solids or a
developable strip. None of the 112.880754 mm has a checked ribbon orientation.

The exact arithmetic remainder is **87.119246 mm**, 43.56% of the nominal stock.
It has no route, material faces, bends, or connection to the centerline. The
current `fpc_fold` reservation is X[−118.5,−101.9], Y[−23.2,−6.7],
Z[78.2,88.5]: 16.6 × 16.5 × 10.3 mm, volume 2821.17 mm³. A 20% fill calculation
offers 564.234 mm³ versus 418.172 mm³ of nominal remainder material. That is only
a volume comparison, not a continuous placement or proof of acceptable bends.
The box lies at least 18.9 mm farther in −X than the centerline, so even reaching
and leaving it consumes additional material absent from the current route.

## Connector and stiffener limits

- Pi: `p_fpc_pi` has no rigid box. Its only source solid is a coarse CAM1 socket
  box X[−88,−78], Y[−3.4,2.1], Z[56.3,61]. The nominal route starts at its upper
  face, but the real cable clamping/insertion plane, contact side, outward
  stiffener length and first bendable station are not defined. The box itself is
  only 10 mm in X; it cannot establish an actual 11.5/16 mm cable-end envelope.
- Camera: `p_fpc_cam` reserves X[−28.09,−25.09], Y[−8.5,8.5],
  Z[41.25,46.25], a 3 × 17 × 5 mm estimated stiffener/housing region. The source
  explicitly labels the approximately 3 mm protrusion an MP-CAM estimate. This
  does not specify the actual stiffener's flexible-boundary station, insertion
  depth, contact normal, latch positions or the entire rigid end region.
- Both contact-side/width-frame relationships are open in `MEASURED-PARTS.md`
  MP-FPC. Simply extruding the centerline with a 16 mm rectangle would impose an
  arbitrary roll and can turn a flatwise bend into an edgewise deformation.

**The next exact datum required is the first bendable cross-section of the
fully inserted cable at each end:** position in the installed coordinate frame,
outgoing tangent, width direction/contact-side normal, and distance from the
cable's physical tip through the engaged and stiffened material. Without these,
the free material length to be distributed is not known and a route solve can
silently count stiffened/inserted length as foldable stock. Body and stiffener
thickness and permitted static/service radius are also required to qualify it.

## Maximum defensible reservation now

Retain the full 200 mm × 16 mm planning stock, the existing 0.3 mm body-thickness
allowance, the entire estimated camera end box, and the unresolved Pi end region.
Do not shorten the stock, narrow it by revision inference, or call a root-free
87 mm storage volume a complete cable. The 16.6 × 16.5 × 10.3 mm box is the
largest **currently declared** local stock reservation; no larger cleared,
connected ribbon volume has been established in this task.

For the already represented centerline only, an orientation-independent circular
envelope for a 16 × 0.3 mm rectangular section has radius
sqrt(8² + 0.15²) = 8.001406 mm, before sampling or positional allowance. With
0.02 mm sampling allowance, use 8.021406 mm. The exploratory audit used 8.02 mm,
which was based on half-width plus sampling alone. This 0.001406 mm distinction
does not turn any reported overlap into a clearance. Neither envelope contains
the unshaped 87.119246 mm stock, the unmeasured thicker stiffeners, or a service
deployment. No full-loom clearance is claimed.

A complete model is a feasible *next design exercise* after the two root frames
are supplied: consume engaged/stiffened stock explicitly, solve the remaining
length as a full-width developable surface with finite-radius folds and connected
storage, then check that entire surface plus roots in installed and service poses
against HDMI, power and actual print solids. If only hypothetical root frames are
available, keep that result in a separate named assumption study and retain the
physical gates. R1 must not become an approved limit through this process.

## Primary-source revision check

[Raspberry Pi's camera-cable page](https://www.raspberrypi.com/products/camera-cable/)
confirms shielded 22-way-compatible camera cables in 200, 300 and 500 mm lengths.

[PCN 36](https://pip-assets.raspberrypi.com/categories/1267-pcn/documents/RP-009201-PC-1-15%20to%2022%20pin%20camera%20cables%20Rev%202.pdf),
dated 15 September 2025, moved the width transition to the 15-pin end and reduced
most of those cables from 16 to 11.5 mm. It explicitly allows old/new distribution
overlap. Received revision is unknown, so the present 16 mm conservative width
remains. The PCN supplies no dimensioned transition station, body/stiffener
thickness or qualified bend radius for the retained cable.

The separately published Standard–Mini **display** cable reference drawing is
not used as camera-cable thickness or stiffener evidence. [PCN 48](https://pip-assets.raspberrypi.com/categories/1267-pcn/documents/RP-010539-PC-1-PCN%2048_%20Zero%20Camera%20Cable%20form%20factor%20and%20manufacturing%20change.pdf)
concerns the 150/38 mm Zero camera-cable variants; it does not establish the
dimensions of this retained 200 mm item.
