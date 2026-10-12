#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Source-backed termination sensitivity; no CAD imports or selected-part edits."""
from pathlib import Path
import argparse
import json
import math
import sys
import reproduce as base

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(base.CV))
from cv_io import read_text, write_text


def rotated_box(length, width, thickness):
    yaw, pitch = math.radians(21), math.radians(45)
    c, s, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
    matrix = [[c*cp,-s,c*sp],[s*cp,c,s*sp],[-sp,0,cp]]
    return [sum(abs(row[j])*[length,width,thickness][j] for j in range(3)) for row in matrix]


def assessment():
    cases = []
    for length in (250, 280, 285):
        for contact in (1., 1.2, 2.4):
            value = base.drop(length, connector_mohm=contact)
            cases.append(dict(path_per_polarity_mm=length, contact_loop_mohm=contact,
                              conditional_drop_v=value, conditional_margin_mv=(.15-value)*1000))
    wire20 = 1000/58 * 1.03/base.area(400)
    fixed = base.drop(0, connector_mohm=2.4)/8.6*1000
    mixed = []
    for tail in (24.,40.):
        for contact in (1.,1.2,2.4):
            value = base.drop(250,tail16_mm=tail,connector_mohm=contact)
            budget = (.15-value)*1000/8.6
            mixed.append(dict(total_per_polarity_mm=250,tail16_per_polarity_mm=tail,
                middle14_per_polarity_mm=250-tail,connector_loop_mohm=contact,
                drop_before_added_splices_v=value,additional_splices=2,
                total_hot_splice_budget_mohm=budget,equal_hot_budget_per_splice_mohm=budget/2,
                drop_if_each_added_splice_is_0p1_mohm=value+.2*8.6/1000))
    return {
        'status': 'EXPLORATORY ONLY; not a selected part, cut list, purchase or fabrication release',
        'as_of_utc': '2026-10-12',
        'equation': 'V=I/1000*[k*(r_camera20*(L_plus+L_minus)/1000+2*r_pack18_20*60/1000)+4.46*1.30+R_connector_loop+sum(R_added_splice)]',
        'mixed_gauge_equation': 'V=I/1000*[2*k*(r14_20*L14/1000+r16_20*L16/1000+r18_20*60/1000)+4.46*1.30+R_connector_loop+sum(R_added_splice)]; L14+L16 is the finished allocation per polarity',
        'units': {'L':'mm','r20':'mohm/m','R':'mohm','I':'A'},
        'unchanged_inputs': base.INPUTS,
        'derived_resistance_inputs': {
            'copper_temperature_factor': 1.1572,
            'r14_20_mohm_per_m_including_lay': wire20,
            'r16_20_mohm_per_m_including_lay': 1000/58*1.03/base.area(250),
            'r18_20_mohm_per_m_including_lay': 1000/58*1.03/base.area(150),
            'fuse_hot_mohm': 4.46*1.30,
            'pack_wire_loop_hot_mohm': 2*1.1572*.060*(1000/58*1.03/base.area(150)),
        },
        'conditional_camera_wire': {
            'area_mm2': base.area(400), 'r20_mohm_per_m_including_lay': wire20,
            'basis': 'PRC comparison construction only; NOT sourced conductor area or resistance for CAB0244',
        },
        'conditional_cases': cases,
        'mixed250_cases': mixed,
        'factory250_acceptance_budget': {
            'connector_loop_mohm_assumed_for_budget': 2.4,
            'camera_wire_r20_max_mohm_per_m_at_150mv': (150/8.6-fixed)/(2*.250*1.1572),
            'camera_wire_r20_max_mohm_per_m_at_145mv_design_target': (145/8.6-fixed)/(2*.250*1.1572),
            'note': 'Budget, not supplier guarantee. Measurement must include unbudgeted factory joints and all actual terminations; 145mV is an optional design-margin target, not a changed release limit.',
        },
        'cab0244': {
            'vendor': 'Pimoroni', 'sku': 'CAB0244', 'variant_id': '41199325249619',
            'url': 'https://shop.pimoroni.com/products/xt30-adapter-cables?variant=41199325249619',
            'variant_feed': 'https://shop.pimoroni.com/products/xt30-adapter-cables.json',
            'photo': 'https://cdn.shopify.com/s/files/1/0174/1800/files/xt30-1.jpg?v=1701882162',
            'published': {'nominal_length_mm':250, 'wire_gauge_awg':14, 'continuous_current_a':15,
                          'peak_current_a':30, 'insulation':'silicone', 'connector_label':'XT30 socket'},
            'photo_observation': 'Two recessed socket contacts at keyed projecting twin-lobe face. Matches declared camera-side contact role only.',
            'unknown': ['actual usable root-to-cut length and tolerance','minimum copper area and conductor material/strand tolerances',
                        'resistance of wire and factory joints','insulation OD and tolerance','minimum bend/straight-tail requirements',
                        'actual housing envelope and exit pitch','actual received custom-pack gender, polarity, protection and cross-mating'],
            'warning': 'Variant41199325282387 is CAB0245, a short XT60-to-XT30 adapter, not CAB0244.',
        },
        'xt30u_bare_cup': {
            'url': 'https://www.china-amass.net/xt30u-f-product/',
            'spec_archive': 'https://www.china-amass.net/uploads/XT30U-MF.rar',
            'conclusion': 'Retrieved 2025V0 specifications rate with16AWG and do not document14AWG cup fit. No trimming strands or guessed termination.',
            'resistance_scope': 'Historical1.0mohm loop is retained only as historical; published<=1.2mohm scope per contact vs loop unresolved.',
        },
        'transition_splice': {
            'manufacturer': 'TE Connectivity', 'part':'SOLISTRAND31819',
            'source': 'https://www.te.com/content/dam/te-com/documents/appliances/global/solistrand-terminals-and-splices-qrg.pdf',
            'product': 'https://www.te.com.cn/chn-zh/product-31819.html',
            'catalog_page':9, 'wire_range_awg':[16,14], 'area_range_mm2':[1.04,2.62],
            'bare_length_mm':14.40, 'bare_od_mm':4.06, 'barrel_id_mm':2.26,
            'quantity_additional':2,
            'unresolved': ['part drawing/process reconciliation','fine-strand/tool/die qualification','installed insulated OD and rigid length',
                          'pull test and strain relief','hot resistance per joint'],
            'conclusion': 'Explicit splice candidate only. At 250 mm total and 40 mm 16 AWG tails per polarity, the two added splices have a combined 0.372146 mOhm hot budget in the 2.4 mOhm loop case. At 270 mm and longer it fails before splice loss. The budget is not a supported joint resistance.',
        },
        'uh60': {
            'female_url':'https://www.china-amass.net/uh60-fgold-plating-product/',
            'male_url':'https://www.china-amass.net/uh60-mgold-plating-product/',
            'male_drawing':'https://www.china-amass.net/uploads/121.UH60-M-Product-Specification-Gold-Plated-2026V1E-Solder-cup-facing-positive-and-negative-terminals.pdf',
            'female_drawing':'https://www.china-amass.net/uploads/121.UH60-F-With-End-Cap-Product-Specification-Gold-Plated-2026V1E-Solder-cup-facing-positive-and-negative-terminals.pdf',
            'female_contact_photo':'https://cdn.globalso.com/china-amass/615.png',
            'male_contact_photo':'https://cdn.globalso.com/china-amass/518.png',
            'manufacturer_wire_support_awg':[14,12],
            'single_bare_lwt_mm':[17.2,16.4,9.2],
            'pair_bare_lwt_mm':[26.7,16.4,9.2], 'pair_bare_max_lwt_mm':[27.2,16.7,9.5],
            'pair_covered_lwt_mm':[35.2,16.4,9.2], 'pair_covered_max_lwt_mm':[35.7,16.7,9.5],
            'rear_cover':'98032.PG',
            'pair_bare_at_current_pose_max_xyz_mm':rotated_box(27.2,16.7,9.5),
            'pair_covered_at_current_pose_max_xyz_mm':rotated_box(35.7,16.7,9.5),
            'grip_bay_xy_mm':[43,25], 'pack_top_to_bay_top_mm':26.8,
            'inferred_nominal_mating_overlap_mm':17.2*2-26.7,
            'overlap_note':'Dimension subtraction, not a published extraction stroke or electrical break distance.',
            'contact_resistance_mohm':1.2, 'resistance_scope':'Per contact vs loop unresolved; use both1.2and2.4loop sensitivities.',
            'life_cycles':30, 'max_wire_od_mm':None,
            'conclusion':'Documented14AWG termination alternative, but covered pair fails existing pose width/headroom. New pair/pack interface, orientation, strain relief and extraction would require a separate proposal; not preferred over investigating CAB0244.',
        },
        'anderson_sbs_mini_screen': {
            'source':'https://www.andersonpower.com/content/dam/app/ecommerce/product-pdfs/SBS-Mini/ds-sbsmini.pdf',
            'assembly':'https://www.andersonpower.com/content/dam/ideal-anderson-power-dotcom/product-assets/default/instructions/1s6651-SBS-Mini-Assembly-Instructions.pdf',
            'housing':'B02265G4', 'camera14_contact':'1331', 'pack18_contact':'1332',
            'mated_length_mm':49.7, 'maximum_wire_od_mm':4.65,
            'conclusion':'Supported wire sizes but much longer than existing26mm proxy. Published contact resistance is average, not a worst-case mixed14/18 loop bound. No demonstrated enclosure/service advantage.',
        },
        'bounded_geometry_receipt': 'cad/gs8-d2-v1/candidate-vertical/corrective-2026-10-12/power-options/factory250-remedy-cad.json',
        'recommendation': 'Retain CAB0244 as the preferred conditional factory-termination study candidate. The completed bounded passage/run-wire/storage attempt fails rear-neck, microSD, tub and cable-neighbour screens. Actual dimensions, usable length, resistance and a complete passing route are still required before any final BOM decision. No qualified power assembly has been demonstrated.',
    }


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    path = HERE / 'termination-options.json'
    text = json.dumps(assessment(), indent=2, sort_keys=True) + '\n'
    if args.check:
        if read_text(path) != text:
            raise SystemExit('termination-options.json differs; regenerate deliberately')
        print('termination-options.json is reproducible')
    else:
        write_text(path, text)
        print('termination-options.json written')
