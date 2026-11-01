"""Preserve MM_Idle's full-body motion/stance; correct only planted ankle contact."""
import unreal,json,math
from pathlib import Path
WORK=Path(unreal.Paths.project_dir())/'Tools/ComicCombat'
DATA=json.loads((WORK/'exorcist_skeleton.json').read_text())
text=(WORK/'author_animations.py').read_text(encoding='utf-8')
exec(text[text.index('def add('):text.index('def pose(')])
ROOT='/Game/ExorcistV10/Animations/manny/'

def run(dt):
    unreal.unregister_slate_post_tick_callback(unreal._ground_idle)
    source=unreal.load_asset(ROOT+'MM_Idle')
    mesh=unreal.load_asset('/Game/ExorcistV10/Character/SK_EX_Optimized')
    name='A_EX_GroundedIdle';seq=unreal.load_asset(ROOT+name)
    if not seq:
        factory=unreal.AnimSequenceFactory();factory.target_skeleton=mesh.skeleton;factory.preview_skeletal_mesh=mesh
        seq=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,ROOT.rstrip('/'),unreal.AnimSequence,factory)
    frames=round(source.get_play_length()*60);poses=[]
    for i in range(frames+1):
        values=unreal.AnimationLibrary.get_bone_poses_for_time(source,list(DATA),i/60,False)
        poses.append({n:([p.translation.x,p.translation.y,p.translation.z],[p.rotation.x,p.rotation.y,p.rotation.z,p.rotation.w]) for n,p in zip(DATA,values)})
    first=globals_of(poses[0]);targets={};rotations={}
    settings=json.loads((WORK/'idle-sole-calibration.json').read_text()) if (WORK/'idle-sole-calibration.json').exists() else {'L':{'angle':3.3,'height_offset':0},'R':{'angle':3.7,'height_offset':0}}
    for side in ['L','R']:
        foot='foot_'+side;toe='toes_'+side
        targets[side]=first[foot][0][:];targets[side][2]+=settings[side]['height_offset']
        direction=sub(first[toe][0],first[foot][0]);direction[2]=0
        rotations[side]=qmul(axis(unit(cross(direction,[0,0,1])),settings[side]['angle']),first[foot][1])
    for local in poses:
        for side in ['L','R']:
            g=globals_of(local)
            solve_limb(local,'upper_leg_'+side,'lower_leg_'+side,'foot_'+side,targets[side],g['lower_leg_'+side][0],rotations[side])
    c=seq.controller;c.open_bracket('Ground original animated idle footwear',False)
    c.set_frame_rate(unreal.FrameRate(60,1),False);c.set_number_of_frames(unreal.FrameNumber(frames),False);c.remove_all_bone_tracks(False)
    for n in DATA:
        c.add_bone_track(n,False)
        c.set_bone_track_keys(n,[unreal.Vector(*p[n][0]) for p in poses],[unreal.Quat(*p[n][1]) for p in poses],[unreal.Vector(1,1,1)]*len(poses),False)
    c.close_bracket(False);unreal.EditorAssetLibrary.save_loaded_asset(seq,False)
    bp=unreal.load_asset(ROOT+'ABP_CC_Unarmed')
    for g in bp.get_animation_graphs():
        for n in g.get_graph_nodes_of_class(unreal.load_class(None,'/Script/AnimGraph.AnimGraphNode_SequencePlayer')):
            if '.Idle.' in n.get_path_name():
                node=n.get_editor_property('node');node.set_editor_property('sequence',seq);n.set_editor_property('node',node)
    bs=unreal.load_asset(ROOT+'BS_Idle_Walk_Run');samples=list(bs.get_editor_property('sample_data'))
    for s in samples:
        if s.get_editor_property('sample_value').y==0:s.set_editor_property('animation',seq)
    bs.set_editor_property('sample_data',samples);unreal.CombatAuthoringLibrary.rebuild_blend_space(bs)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp,False);unreal.EditorAssetLibrary.save_loaded_asset(bs,False)
    print('ORIGINAL_IDLE_GROUNDED',settings)
unreal._ground_idle=unreal.register_slate_post_tick_callback(run)
