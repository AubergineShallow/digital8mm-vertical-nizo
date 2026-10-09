"""CAD-free documentation, BOM and export identity review. No geometry execution."""
import csv,hashlib,importlib.util,json,re,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent;CAD=P.parent
out={'generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'scope':'File/source identity, recorded statuses and BOM/document consistency only; no geometry rerun or physical qualification.','variants':[],'physical_qualified':False}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def entry(p):return {'path':str(p.relative_to(P)),'sha256':sha(p)}
def bindings(items,root):
 missing=[];changed=[]
 for name,h in items.items():
  p=root/name
  if not p.is_file():missing.append(name)
  elif sha(p)!=h:changed.append(name)
 return {'checked':len(items),'missing':missing,'changed':changed,'pass':not missing and not changed}
for variant,expected in [('compact-kowa_lm6hc',9),('compact-fujinon_hf6xa',9),('original-kowa_lm6hc',10)]:
 d=P/'out'/variant;m=json.loads((d/'manifest.json').read_text());h=sha(d/'manifest.json')
 printed=[r for r in m['rows'] if r['kind']=='printed'];pi=next(r for r in m['rows'] if r['id']=='pi5');keepout=[r for r in m['rows'] if r['kind']=='keepout']
 rec={'variant':variant,'manifest_sha256':h,'sources':bindings(m['sources'],CAD),'files':bindings(m['files'],d),'mesh_manifest_identical':(d/'meshes/manifest.json').exists() and (d/'manifest.json').read_bytes()==(d/'meshes/manifest.json').read_bytes(),'printed_count':len(printed),'expected_printed_count':expected,'printed_valid_one_solid':all(r['valid'] and r['solid_count']==1 for r in printed),'pi_representation':{k:pi.get(k) for k in ('geometry_role','solid_count','volume_semantics','occupied_material_volume_mm3')},'keepouts_non_material':all(r.get('occupied_material_volume_mm3')==0 for r in keepout),'reports':[]}
 for name in ['verification.json','print-mesh-checks.json']+(['csi-source-tool-checks.json','power-service-checks.json','hdmi-solid-checks.json','wire-solid-checks.json'] if variant=='compact-kowa_lm6hc' else []):
  p=d/name
  if not p.exists():rec['reports'].append({'path':str(p.relative_to(P)),'missing':True});continue
  r=json.loads(p.read_text());row=entry(p);mh=r.get('manifest_sha256',r.get('mechanical_manifest_sha256'));row['manifest_sha256']=mh;row['same_manifest']=mh==h;row['evidence_role']='historical only; report manifest differs from current variant' if mh!=h else ('historical only; full alternative audit not rerun' if variant!='compact-kowa_lm6hc' and name=='verification.json' else 'current manifest-bound scoped evidence')
  verifier={'verification.json':'verify_candidate.py','print-mesh-checks.json':'verify_print_meshes.py','csi-source-tool-checks.json':'verify_csi_source.py','power-service-checks.json':'verify_power_service.py','hdmi-solid-checks.json':'verify_hdmi.py','wire-solid-checks.json':'verify_wire_solids.py'}[name]
  reported=r.get('verification_source_sha256',r.get('source_sha256'));row['verifier_file']=verifier;row['verifier_hash_current']=reported==sha(P/verifier)
  if row['same_manifest'] and not row['verifier_hash_current']:row['evidence_role']='manifest-bound historical verifier; current verifier differs'
  for k in ['summary','status','pass_count','fail_count','physical_qualified','operational_status','declared_rigid_reservation_clear','poses','exact_intersections','hits']:
   if k in r:row[k]=r[k]
  if 'checks' in r:row['failed_checks']=[x for x in r['checks'] if x.get('status')=='fail']
  rec['reports'].append(row)
 out['variants'].append(rec)
spec=importlib.util.spec_from_file_location('vertical_review_bom',P/'make_bom_vertical.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
rows,_,base=b.build_rows();b.validate(rows,base);by={r['line']:r for r in rows}
expected=b.outputs(rows,base)
refs=[(r['line'],r['included_in']) for r in rows if r['included_in'] and r['included_in'] not in by]
source_missing=[(r['line'],r['source']) for r in rows if not r['source'].startswith(('http://','https://')) and not (P/r['source']).exists()]
out['bom']={'rows':len(rows),'baseline_rows_preserved':len(base.LINES),'included_decomposition_rows':sum(bool(r['included_in']) for r in rows),'generator_outputs_current':all((P/n).read_text()==s for n,s in expected.items()),'invalid_parent_references':refs,'missing_local_sources':source_missing,'cad_imported': 'cadquery' in sys.modules,'not_a_physical_total':True,'installed_categories':{'printed_compact':9,'printed_original':10,'body_pt_screws':7,'stack_screws':8,'stack_standoffs':4,'cooler_push_pins':2,'lens_screws':4,'lens_washers':4,'lens_inserts':4,'functional_harnesses':11,'hdmi_purchased_pieces':3,'planned_solder_joints':24}}
owned=['README.md','REPRODUCE.md','CHECKPOINT-STATUS.json','REVIEW.md','ASSEMBLY-VERTICAL.md','MEASUREMENTS-TO-CLOSE.md','make_bom_vertical.py','BOM-VERTICAL.md','BOM-VERTICAL.csv','structural-review/CONCEALED-VENT-STRUCTURAL.md','structural-review/concealed-vent-structural.json','structural-review/update_concealed_vent_structure.py','structural-review/reference-export18-structural-binding.json','structural-review/coupons/README.md','structural-review/coupon-reproducer-recovery.json'];out['documents']=[entry(P/n) for n in owned];out['missing_document_local_links']=[]
for name in [n for n in owned if n.endswith('.md')]:
 for target in re.findall(r'\]\(([^)]+)\)',(P/name).read_text()):
  if not target.startswith(('http://','https://')) and not ((P/name).parent/target.split('#')[0]).exists():out['missing_document_local_links'].append({'document':name,'target':target})
out['audit_source']={'path':Path(__file__).name,'sha256':sha(Path(__file__))}
primary=out['variants'][0]['manifest_sha256'];extras=[]
for name,source in [('out/compact-kowa_lm6hc/microsd-service-dependency.json','verify_microsd_service.py'),('out/compact-kowa_lm6hc/wall-probe-context.json','verify_wall_probe_context.py'),('out/fps-service-study/integrated-fps-checks.json','verify_fps_integrated.py'),('out/fps-service-study/integrated-fps-export18-checks.json','verify_fps_integrated.py')]:
 p=P/name
 if not p.exists():extras.append({'path':name,'pending':True});continue
 d=json.loads(p.read_text());r=entry(p);r['same_primary_manifest']=d.get('manifest_sha256',d.get('mechanical_manifest_sha256'))==primary;r['evidence_role']='current manifest-bound scoped evidence' if r['same_primary_manifest'] else 'historical only; report manifest differs from current primary';r['verifier_file']=source;r['verifier_hash_current']=d.get('verification_source_sha256',d.get('source_sha256'))==sha(P/source)
 for k in ['status','closed_panel_case','selected_procedure','scope','interpretation','physical_qualified']: 
  if k in d:r[k]=d[k]
 if 'static_and_carried_checks' in d:
  r['material_checks']=len(d['static_and_carried_checks']);r['material_hits']=sum(bool(x['hits']) for x in d['static_and_carried_checks']);r['nonmaterial_diagnostics']=len(d['non_material_reservation_diagnostics']);r['nonmaterial_hits']=sum(bool(x['hits']) for x in d['non_material_reservation_diagnostics']);r['helper_bindings']=bindings(d['frozen_helper_sha256'],P);r['verification_dependencies']=bindings(d['verification_dependency_sha256'],P);r['step_bindings']=bindings({('step/'+k+'.step'):v for k,v in d['step_sha256'].items()},P/'out/compact-kowa_lm6hc');r['frozen_input_matches']=d['input_sha256']==sha(P/'out/fps-service-study/mated-carry-input.json')
 if 'hits' in d:r['hit_poses']=len(d['hits']);r['maximum_reported_overlap_mm3']=max((x['overlap_mm3'] for x in d['hits']),default=0)
 if 'checks' in d:r['checks']=d['checks']
 extras.append(r)
out['selected_supplemental_reports']=extras
out['report_inputs']={}
for report,field,target in [('hdmi-solid-checks.json','snapshot_sha256','routing-snapshots/hdmi-corrected-ports-20261009-0623/input.json'),('power-service-checks.json','snapshot_sha256','routing-snapshots/power-yaw21-270-provisional/power-270-yaw21.json'),('wire-solid-checks.json','snapshot_sha256','routing-snapshots/power-csi-clear-20261009-0358/power-270-csi-clear.json'),('wire-solid-checks.json','helper_source_sha256','power_geometry.py'),('csi-source-tool-checks.json','source_helper_sha256','official_pi5_geometry.py')]:
 d=json.loads((P/'out/compact-kowa_lm6hc'/report).read_text());out['report_inputs'][report+'/'+field]={'path':target,'sha256':sha(P/target),'matches_report':d[field]==sha(P/target)}
cp=P/'out/comparison/assembled-comparison.json';comparison=json.loads(cp.read_text());out['assembly_comparison']={'file':entry(cp),'current_producer_file':entry(P/'measure_comparison.py'),'candidate_manifest_bindings':[{x['variant']:x['manifest_sha256']==sha(P/'out'/x['variant']/'manifest.json')} for x in comparison['candidates']]}
out['core_void_reports']=[]
for variant in ['compact-kowa_lm6hc','compact-fujinon_hf6xa','original-kowa_lm6hc']:
 p=P/'out/comparison'/('volume-'+variant+'.json');d=json.loads(p.read_text());r=entry(p);r['same_variant_manifest']=d['manifest_sha256']==sha(P/'out'/variant/'manifest.json');r['verifier_hash_current']=d['verification_source_sha256']==sha(P/'measure_volume.py');r['model_void_mm3']=d['model_void_mm3'];r['model_void_fraction']=d['model_void_fraction'];r['model_void_interval_cm3_outward_rounded']=d.get('model_void_interval_cm3_outward_rounded');r['interval_definition']=d.get('interval_definition');r['comparison_caveat']=d.get('comparison_caveat');out['core_void_reports'].append(r)
# Selected shadow-plenum evidence is separate from frozen export18 and rejected angled-channel reports.
out['concealed_vent_reports']=[]
for name,source in [('out/compact-kowa_lm6hc/shadow-plenum-checks.json','verify_shadow_plenum.py'),('out/compact-kowa_lm6hc/shadow-outlet-context-checks.json','verify_shadow_outlet_context.py'),('out/compact-kowa_lm6hc/ventilation-checks.json','verify_ventilation.py'),('structural-review/concealed-vent-structural.json','structural-review/update_concealed_vent_structure.py')]:
 p=P/name
 if not p.exists():out['concealed_vent_reports'].append({'path':name,'pending':True});continue
 d=json.loads(p.read_text());r=entry(p);r['same_primary_manifest']=d.get('manifest_sha256')==primary;r['verifier_file']=source;r['verifier_hash_current']=d.get('verification_source_sha256')==sha(P/source)
 r['evidence_role']='current manifest-bound scoped evidence' if r['same_primary_manifest'] and r['verifier_hash_current'] else 'historical or stale; manifest or verifier differs'
 for k in ['method','summary','geometry_scope','physical_qualified','changed_manifest_rows','assembly','coupon_load','remaining']:
  if k in d:r[k]=d[k]
 if 'vent_source_sha256' in d:
  r['vent_helper_current']=d['vent_source_sha256']==sha(P/'vent_geometry.py')
  if not r['vent_helper_current']:r['evidence_role']='historical or stale; ventilation helper differs'
 if 'checked_source_sha256' in d:
  r['checked_sources']=bindings(d['checked_source_sha256'],P)
  if not r['checked_sources']['pass']:r['evidence_role']='historical or stale; checked geometry source differs'
 if 'saved_material_sha256' in d:
  r['saved_material_bindings']=bindings({'step/'+k+'.step':v for k,v in d['saved_material_sha256'].items()},P/'out/compact-kowa_lm6hc')
  r['scope']=d.get('scope');r['limitations']=d.get('limitations')
  if not r['saved_material_bindings']['pass']:r['evidence_role']='historical or stale; saved material differs'
 if name.endswith('/ventilation-checks.json'):r['evidence_role']='historical rejected angled-channel trial only'
 if 'ventilation_report' in d:
  vr=d['ventilation_report'];vp=P/vr['path'];r['ventilation_receipt_current']=vp.exists() and vr.get('sha256')==sha(vp) and vr.get('same_manifest') is True
  r['reference_structural_binding_current']=d.get('reference_structural_binding_sha256')==sha(P/'structural-review/reference-export18-structural-binding.json')
  if not r['ventilation_receipt_current'] or not r['reference_structural_binding_current']:r['evidence_role']='historical or stale; calculation input receipt differs'
 out['concealed_vent_reports'].append(r)
frozen=list(csv.DictReader((P/'history/reviewed-export18/BOM-VERTICAL.csv').open()))
old_by={r['line']:r for r in frozen};current_by={r['line']:r for r in rows}
selection_fields=['variant','installed_qty','installed_unit','purchase_qty','purchase_unit','included_in','sku_or_class','supplier']
diffs=[]
for key in sorted(old_by.keys()|current_by.keys()):
 if key not in old_by or key not in current_by:diffs.append({'line':key,'inventory_changed':True});continue
 changes={f:[old_by[key][f],str(current_by[key][f])] for f in selection_fields if old_by[key][f]!=str(current_by[key][f])}
 if changes:diffs.append({'line':key,'changes':changes})
out['concealed_bom_preservation']={'reference':entry(P/'history/reviewed-export18/BOM-VERTICAL.csv'),'fields_compared':selection_fields,'differences':diffs,'unchanged':not diffs,'excludes_editorial_item_note_and_status_changes':True}
# USB-head fallback report binds complete saved parts instead of missing legacy extracts.
head_path=P/'routing-snapshots/hdmi-export17-selected-20261009-0704/shadow-plenum-head-checks.json'
if head_path.exists():
 d=json.loads(head_path.read_text());mech=d['mechanical'];head=entry(head_path)
 head.update(status=d['status'],same_primary_manifest=mech['manifest_sha256']==primary,verifier_file='verify_shadow_usb_head.py',verifier_hash_current=d['verification_source_sha256']==sha(P/'verify_shadow_usb_head.py'),step_bindings=bindings({'step/'+k+'.step':v for k,v in mech['all_step_sha256'].items()},P/'out/compact-kowa_lm6hc'),physical_qualified=d['physical_qualified'],support_coverage=d['support_coverage'],remaining=d['remaining'])
 head['evidence_role']='current manifest-bound limited head reservation' if head['same_primary_manifest'] and head['verifier_hash_current'] and head['step_bindings']['pass'] else 'historical or stale head reservation'
 out['selected_usb_head_report']=head
coupon_root=P/'vent-study/shadow-plenum-coupon';index_path=coupon_root/'coupon-index.json'
if index_path.exists():
 d=json.loads(index_path.read_text());rec=entry(index_path);rec.update(coupon_count=d['coupon_count'],same_primary_manifest=d['manifest_sha256']==primary,source_current=d['source_sha256']==sha(P/'make_shadow_plenum_coupon.py'),receipt_bindings=bindings(d['receipts'],coupon_root),production_part_count_change=d['production_part_count_change'],physical_qualified=d['physical_qualified'],receipts=[])
 for name in d['receipts']:
  r=json.loads((coupon_root/name).read_text());item=entry(coupon_root/name);item.update(same_primary_manifest=r['manifest_sha256']==primary,files=bindings(r['files'],coupon_root),step_reimport_valid=r.get('step_reimport_valid'),status=r['status'],limitations=r['limitations']);rec['receipts'].append(item)
 out['plenum_coupon_identity']=rec
rp=P/'structural-review/coupon-reproducer-recovery.json'
if rp.exists():
 d=json.loads(rp.read_text());out['restored_coupon_reproducer']={'receipt':entry(rp),'restored_file_bindings':bindings({x['path']:x['restored_sha256'] for x in d['restored_files']},P/'structural-review'),'retained_output_bindings':bindings({x['path']:x['sha256'] for x in d['retained_output_identity']},P/'structural-review'),'scope':d['scope']}
pdf_receipt=P/'structural-review/output/pdf/structural-supplement-pdf-receipt.json'
if pdf_receipt.exists():
 d=json.loads(pdf_receipt.read_text());pdf=pdf_receipt.parent/d['artifact'];out['structural_pdf']={'receipt':entry(pdf_receipt),'artifact':entry(pdf),'same_primary_manifest':d['manifest_sha256']==primary,'pdf_hash_matches':d['pdf_sha256']==sha(pdf),'source_bindings':bindings(d['source_sha256'],P),'pages':d['pages'],'text_checks_pass':d['text_checks_pass'],'visual_review':d['visual_review'],'physical_qualified':False}
status_path=P/'CHECKPOINT-STATUS.json';status=json.loads(status_path.read_text());ev=status['selected_evidence'];old_status=status['preserved_export18_checkpoint']
out['checkpoint_status']={'file':entry(status_path),'same_primary_manifest':status['manifest_sha256']==primary,'selected_evidence_binding':ev['sha256']==sha(P/ev['path']),'preserved_export18_binding':old_status['sha256']==sha(P/old_status['path']),'physical_qualified':status['physical_qualified'],'guide_receipt_current':status['guide']['receipt']['sha256']==sha(P/status['guide']['receipt']['path'])}
out['run_records']=[entry(P/n) for n in ['out/primary-refresh.json','out/final-check-run.json','out/alternative-refresh.json','out/compact-kowa_lm6hc/review-check-run.json'] if (P/n).exists()]
path=P/'out/review-docs-audit.json';path.write_text(json.dumps(out,indent=2)+'\n');print(path);print(json.dumps({'variant_source_and_file_binding':[{x['variant']:x['sources']['pass'] and x['files']['pass'] for x in out['variants']}],'bom':out['bom'],'missing_document_local_links':out['missing_document_local_links']},indent=2))
