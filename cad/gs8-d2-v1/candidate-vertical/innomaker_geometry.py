"""Conditional Innomaker colour IMX296 geometry; no optical or physical release.
Photo-visible rear trigger/strobe headers are missing from the public STEP.
Their actual dimensions are unresolved and must not inherit pin-free clearance.
"""
from pathlib import Path
import hashlib
import cadquery as cq
V=cq.Vector
BASE=Path(__file__).resolve().parent
# The manufacturer STEP states no redistribution licence, so it is not committed. Fetch it locally:
# download SOURCE_URL, extract 'IMX296 With CS.stp' into innomaker/fetch/ (git-ignored); SHA256 is enforced.
SOURCE=BASE/'innomaker/fetch/IMX296 With CS.stp'
SHA256='3d53cc2b16f4c4bd91776e57548dcf191689a6d4f7ee4962411cfb3f1b496b51'
SOURCE_URL='https://www.inno-maker.com/wp-content/uploads/2021/06/IMX296-With-CS.zip'
PRODUCT_URL='https://www.inno-maker.com/product/cam-imx296color/'
CS_REFERENCE_NATIVE_Z=13.2
C_FLANGE_X=.6
CONVERTER_REGISTER_SEPARATION=5.0
CS_REFERENCE_X=C_FLANGE_X-CONVERTER_REGISTER_SEPARATION
AXIAL_OFFSET=CS_REFERENCE_X-CS_REFERENCE_NATIVE_Z
PCB_REAR_X=AXIAL_OFFSET+.9
PCB_FRONT_X=AXIAL_OFFSET+2.5
MASS_ESTIMATE_G=15.0
CAP_SOLID_INDEX=4
HEADER_PROJECTION_CASES_MM=(3.,6.,9.,12.,15.,18.)

def box(x0,x1,y0,y1,z0,z1):return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
def cylx(r,x0,x1,y=0,z=60):return cq.Solid.makeCylinder(r,x1-x0,V(x0,y,z),V(1,0,0))
def native():
    if not SOURCE.is_file():raise FileNotFoundError('Fetch prerequisite missing: manufacturer STEP not found at innomaker/fetch/IMX296 With CS.stp. Download '+SOURCE_URL+', extract that file into innomaker/fetch/ (git-ignored) and rerun; SHA-256 must be '+SHA256)
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest()!=SHA256:raise ValueError('Manufacturer STEP identity changed')
    return cq.importers.importStep(str(SOURCE)).val()
def place(s):
    # Native Z -> global X; native X -> global Z; native Y -> global -Y.
    # Native -Y CSI faces open +Y panel; opposite-edge headers face -Y.
    return s.rotate((0,0,0),(0,1,0),90).rotate((0,0,0),(1,0,0),180).translate(V(AXIAL_OFFSET,0,60))
def pcb_material():
    # Public PCB is unsewn shells. Explicit material reconstruction follows
    # STEP R3.5, not conflicting manual R2. Source0.08 edge rounds omitted.
    s=cq.Workplane('XY').box(39,39,1.6,centered=(True,True,False)).translate((0,0,.9)).edges('|Z').fillet(3.5).val()
    holes=[(x,y,1.) for x in (-17,17) for y in (-17,17)]+[(-10,0,1),(10,0,1),(10,-3.5,.755),(-10,3.5,.755)]
    for x,y,r in holes:s=s.cut(cq.Solid.makeCylinder(r,1.8,V(x,y,.8),V(0,0,1)))
    return s

def operating_camera():
    solids=native().Solids()
    if len(solids)!=29:raise ValueError('Unexpected source topology; inspect before cap-index mapping')
    return place(cq.Compound.makeCompound([s for i,s in enumerate(solids) if i!=CAP_SOLID_INDEX]+[pcb_material()]))
def supplied_reference():return place(native())
def service_envelope():
    # Caller must FUSE these touching/overlapping primitives before subtraction.
    # Covers public pin-free source only; it is not the complete photographed SKU.
    pcb=cq.Workplane('XY').box(39,39,1.6,centered=(True,True,False)).translate((0,0,.9)).edges('|Z').fillet(3.5).val()
    holder=cq.Solid.makeCylinder(14.301,10.7,V(0,0,2.5),V(0,0,1))
    rear=box(-10.51,11.51,-18.31,-11.,-1.61,.91)
    return place(cq.Compound.makeCompound([pcb,holder,rear]))
def header_sensitivity_envelope(projection_mm):
    # Assumption-only full PCB-area rear prism. None is an adopted pin height.
    # Covers XY only conditional on actual headers staying within board outline.
    if projection_mm not in HEADER_PROJECTION_CASES_MM:raise ValueError('Undeclared sensitivity case')
    return box(PCB_REAR_X-projection_mm,PCB_REAR_X,-19.5,19.5,40.5,79.5)
def converter_reserve():
    return cylx(15.375,CS_REFERENCE_X,C_FLANGE_X).cut(cylx(12.75,CS_REFERENCE_X-.1,C_FLANGE_X+.1))
def tub_guides():
    out=[]
    for z0,z1 in ((40.1,46.),(74.,81.)):
        out.append(box(PCB_REAR_X-1.2,PCB_FRONT_X+2.9,-25.55,-20.,z0,z1))
        out.append(box(PCB_FRONT_X+.5,PCB_FRONT_X+2.9,-25.55,-17.,z0,z1))
    return out

def panel_guides(local_y_shift=0):
    out=[]
    for z0,z1 in ((40.1,46.),(74.,81.)):
        out.extend([box(PCB_REAR_X-2.9,PCB_FRONT_X+2.9,20.,25.4,z0,z1),box(PCB_REAR_X-2.9,PCB_REAR_X-.5,17.,25.4,z0,z1),box(PCB_FRONT_X+.5,PCB_FRONT_X+2.9,17.,25.4,z0,z1)])
    return [s.translate(V(0,local_y_shift,0)) for s in out]
def csi_service_reserve():return box(AXIAL_OFFSET-5.,PCB_REAR_X,18.3,25.,47.5,73.5)
def camera_source():return 'Innomaker CAM-IMX296Color-GS / CAM-MIPI296Color. Public STEP plus reconstructed PCB; excludes assumed cap. REAR TRIGGER/STROBE HEADERS (named in the manufacturer docs; seen in a photograph supplied with the delivery, not committed) OMITTED FROM SOURCE: dimensional HOLD. Optical placement, cap identity and15g mass unverified. '+PRODUCT_URL

def converter_source():return 'C/CS converter: NOT in the manufacturer packing list (product page, 2026-10-13); confirm on receipt or buy one (open BOM item). Unmeasured OD30.75/ID25.5 and5mm nominal standard separation shown only as conditional reservation. No verified threads or seating. '+PRODUCT_URL

def provenance():
    return dict(product='Innomaker CAM-IMX296Color-GS / CAM-MIPI296Color',amazon_asin='B0CQ4DTQZ2',source_url=SOURCE_URL,source_step_sha256=SHA256,
        baseline_commit='a0bfed9f7ed88dad78ad1a5fcb6fc7504712b338',reconstruction='New source reconstruction after cloud workspace replacement; no lost5736870 output or pass count is carried as current evidence',
        cap_excluded_solid_index=4,cap_identification='UNVERIFIED: upper closed-disk part interpreted as protective plug',
        native_board_bounds_mm=[-19.5,19.5,-19.5,19.5,.9,2.5],product_page_board_size_mm=[38.,38.],board_outline_status='OPEN: product page says 38 x 38 mm, manufacturer STEP is 39 x 39 mm; geometry follows the STEP until the received board is measured',hole_diameter_mm=2.,hole_pitch_mm=34.,pcb_thickness_mm=1.6,pcb_corner_radius_mm=3.5,pcb_corner_conflict='ManualR2 versus STEPR3.5; material reconstruction follows STEP',
        holder_holes_native_xy_mm=[[-10,0],[10,0]],secondary_holes_native_xyr_mm=[[10,-3.5,.755],[-10,3.5,.755]],
        cs_reference_native_z_mm=CS_REFERENCE_NATIVE_Z,cs_reference_verified=False,c_flange_x_mm=C_FLANGE_X,converter_register_separation_mm=5.,converter_geometry_verified=False,
        placement_axial_offset_mm=AXIAL_OFFSET,pcb_rear_x_mm=PCB_REAR_X,pcb_front_x_mm=PCB_FRONT_X,sensor_active_plane_mm=None,
        clocking='Candidate: source native-Y CSI faces removable+Y panel. Actual seated thread clocking and cable contact orientation HOLD.',
        source_csi_native_bounds_mm=[-10.5,11.5,-18.3,-13.,-1.6,.9],
        rear_headers={'observed':'Two2-pin male headers opposite CSI, labeled Trigger+/GND and Strobe+/-. Four long rearward pins seen in a photograph supplied with the delivery (not committed); header names XTR/GND and TOUT1/TOUT2 are listed in the manufacturer docs.', 'manufacturer_docs':'https://docs.inno-maker.com/home/mipi-cameras/imx296-mipi-cameras','source_step_models_headers':False,'actual_xy_mm':None,'actual_projection_mm':None,'normal_csi_requires_header_wires':False,'removal_or_bending_assumed':False,'sensitivity_cases_mm':list(HEADER_PROJECTION_CASES_MM),'case_status':'Assumptions only, not nominal/bounded manufacturer dimensions. Full PCB-area prisms are worst-case XY only if real headers remain inside outline. No case qualifies actual headers.'},
        primary_load_path='Camera/holder -> CS thread -> C-CS converter (not in packing list; open) -> lens -> retained collar -> tub seats',catch_role='clearance safety/roll stops only, no torque or normal weight/preload credit',
        mass_estimate_g=15.,new_purchased_parts=[],exterior_change=False,physical_qualified=False,
        holds=['board outline 38 (product page) vs 39 (STEP) mm','C-flange to sensor plane: holder-mouth CS reference unverified (review B-01)','image orientation/clocking (review B-02)','lens-thread torque reaction before PCB contact (J7-R; review A-03/B-03)','rear-header dimensions/source revision','cap identification','CS/sensor/filter optical datum','received converter/threads','safe direct holder support for lens assembly','PCB edge/trace/strain/tolerance','full CSI ribbon/latch/bend/clocking/service','all original physical/power/thermal/harness holds','original QT−23.99mm historical failure','48/54fps RAW/DNG hardware validation'])
