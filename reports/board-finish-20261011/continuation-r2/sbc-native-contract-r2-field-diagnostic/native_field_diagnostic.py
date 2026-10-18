"""Extend the frozen native pose check with exact SMD masks, angles and fields."""
import importlib.util,json,math,sys
from pathlib import Path
import pcbnew

def main(argv):
    helper,mask_path=map(Path,argv[:2]); args=argv[2:]
    spec=importlib.util.spec_from_file_location('frozen_pose_helper',helper)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    original=pcbnew.LoadBoard; captured=[]
    def load(*a,**k):
        board=original(*a,**k);captured.append(board);return board
    pcbnew.LoadBoard=load
    try:
        code=module.main(list(args))
        if code or len(captured)!=1:raise ValueError('Original native pose gate failed')
        board=captured[0];mask=json.loads(mask_path.read_bytes())
        fps={str(f.GetReference()):f for f in board.GetFootprints()}
        cu=list(board.GetEnabledLayers().CuStack()); rows=[]; field_errors=[]
        mm=lambda p:[pcbnew.ToMM(p.x),pcbnew.ToMM(p.y)]
        angle_ok=lambda a,b:abs((a-b+180)%360-180)<1e-9
        shapes={'rect':pcbnew.PAD_SHAPE_RECT,'roundrect':pcbnew.PAD_SHAPE_ROUNDRECT,'custom':pcbnew.PAD_SHAPE_CUSTOM}
        for row in mask['footprints']:
            fp=fps[row['ref']];pads={str(p.m_Uuid.AsString()):p for p in fp.Pads()};observed=[]
            for exp in row['pads']:
                pad=pads[exp['physical_pad_UUID']]
                flashes=[str(board.GetLayerName(layer)) for layer in cu if pad.FlashLayer(layer)]
                layers=[str(board.GetLayerName(layer)) for layer in pad.GetLayerSet().Seq()]
                if str(pad.GetNetname())!=exp['expected_raw_net'] or str(pad.GetNumber())!=exp['pin']:raise ValueError('Exact native SMD identity differs')
                if mm(pad.GetPosition())!=exp['absolute_position_mm'] or not angle_ok(pad.GetOrientationDegrees(),exp['absolute_angle_deg']):raise ValueError('Exact native SMD pose differs:'+row['ref']+'/'+exp['pin'])
                if set(layers)!=set(exp['native_declared_layers']) or set(flashes)!=set(exp['expected_copper_layer_names']):raise ValueError('Native SMD declared/effective masks differ')
                if pad.GetShape(pcbnew.F_Cu)!=shapes[exp['shape']] or mm(pad.GetSize(pcbnew.F_Cu))!=exp['size_mm']:raise ValueError('Native SMD shape/size differs')
                if mm(pad.GetDrillSize())!=[0.0,0.0]:raise ValueError('Ordinary SMD has a drilled hole')
                if exp['roundrect_rratio'] and abs(pad.GetRoundRectRadiusRatio(pcbnew.F_Cu)-float(exp['roundrect_rratio']))>1e-12:raise ValueError('Native roundrect radius differs')
                observed.append({'uuid':exp['physical_pad_UUID'],'pin':exp['pin'],'raw_net':str(pad.GetNetname()),'absolute_mm':mm(pad.GetPosition()),'angle_deg':pad.GetOrientationDegrees(),'declared_layers':layers,'flashed_layers':flashes,'shape_enum':int(pad.GetShape(pcbnew.F_Cu)),'size_mm':mm(pad.GetSize(pcbnew.F_Cu))})
            fields={str(f.GetName()):f for f in fp.GetFields()};texts=[]
            users=[g for g in fp.GraphicalItems() if isinstance(g,pcbnew.PCB_TEXT)]
            for exp in row['texts']:
                if exp['kind']=='property':text=fields[exp['identity']]
                else:
                    candidates=[g for g in users if str(g.GetLayerName())==exp['native_layer'] and mm(g.GetPosition())==exp['absolute_position_mm']]
                    if len(candidates)!=1:raise ValueError('Native footprint user text is ambiguous')
                    text=candidates[0]
                if mm(text.GetPosition())!=exp['absolute_position_mm'] or str(text.GetLayerName())!=exp['native_layer'] or not angle_ok(text.GetTextAngleDegrees(),exp['native_angle_deg']):field_errors.append({'ref':row['ref'],'expected':exp,'actual_position_mm':mm(text.GetPosition()),'actual_layer':str(text.GetLayerName()),'actual_angle_deg':text.GetTextAngleDegrees()})
                texts.append({'kind':exp['kind'],'identity':exp['identity'],'absolute_mm':mm(text.GetPosition()),'angle_deg':text.GetTextAngleDegrees(),'layer':str(text.GetLayerName())})
            rows.append({'ref':row['ref'],'pads':observed,'texts':texts})
        via_spec=json.loads(Path(args[2]).read_bytes())
        vias={str(t.m_Uuid.AsString()):t for t in board.GetTracks() if isinstance(t,pcbnew.PCB_VIA)}
        for row in via_spec['added_vias']:
            if str(vias[row['uuid']].GetNetname())!=row['net_raw']:raise ValueError('Exact raw via identity differs:'+row['uuid'])
        output=Path(args[-1]); report=json.loads(output.read_bytes())
        report['SBC_exact_native_pad_masks_shapes_angles_and_field_poses']={'verdict':'PASS','rows':rows,'pad_coordinate_tolerance_mm':0,'angle_modulo_360':True,'custom_pad_primitives_byte_exact_in_host_owned_recipe':True,'no_refill_save_or_DRC':True}
        report['all_declared_vias_exact_raw_net_identity']={'verdict':'PASS','count':len(via_spec['added_vias'])}
        report['native_field_pose_diagnostic']={'verdict':'FAIL' if field_errors else 'PASS','errors':field_errors,'board_unchanged':True}
        if field_errors:report['SBC_exact_native_pad_masks_shapes_angles_and_field_poses']['verdict']='FAIL_FIELD_POSES'
        output.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
        return 1 if field_errors else 0
    finally:pcbnew.LoadBoard=original

if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
