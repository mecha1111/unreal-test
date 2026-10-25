"""공격 준비/스윙/명중/회복 노티파이와 E 5연타, Q 차지 돌진 펀치를 작성한다."""
import unreal,math,json
from pathlib import Path
WORK=Path(__file__).resolve().parent
src=(WORK/'animation_helpers_v8.py').read_text(encoding='utf-8')
old=(WORK/'full_body_poses_v8.py').read_text(encoding='utf-8')
exec(compile(old[:old.index('CLIPS=[')],'full_body_poses','exec'))

# 중심을 낮춰 오른 주먹을 뒤로 당기고, 골반과 지지발부터 앞으로 회전한다.
qc=pose(height=66,twist=48,lean=-19,shift=-13,left=(21,31,124),right=(-40,-23,104),left_foot=(26,34,8.24),right_foot=(-28,-34,8.24))
qr=pose(height=73,twist=45,lean=-30,shift=4,left=(23,35,126),right=(-37,-20,118),left_foot=(23,32,12),right_foot=(-27,-37,16))
qp=pose(height=84,twist=-62,lean=-24,shift=26,left=(32,0,123),right=(7,80,133),left_foot=(26,51,8.24),right_foot=(-23,-23,23))
qf=pose(height=76,twist=-74,lean=-29,shift=24,left=(33,0,120),right=(27,60,112),left_foot=(28,51,8.24),right_foot=(-23,-19,17))
CLIPS=[
 ('A_CC_Jab',[(0,g),(.0833,jw),(.1333,jh),(.1667,jh),(.2167,jf),(.40,g)],.0833,.1333,.25),
 ('A_CC_Cross',[(0,g),(.1167,cw),(.1833,ch),(.2167,ch),(.2833,cf),(.50,g)],.1167,.1833,.3167),
 ('A_CC_Uppercut',[(0,g),(.1833,uw),(.2667,uh),(.3167,uh),(.40,uf),(.70,g)],.20,.2667,.50),
 ('A_CC_Hammer',[(0,g),(.20,hw),(.2667,hw),(.35,hh),(.40,hh),(.50,hf),(.85,g)],.2833,.35,.65),
 ('A_CC_DashStrike',[(0,g),(.12,jw),(.20,jh),(.25,cw),(.34,ch),(.39,jw),(.48,jh),(.53,cw),(.62,ch),(.72,uw),(.88,uh),(.94,uf),(1.08,cf),(1.30,g)],.14,.20,1.04),
 ('A_CC_InkBreaker',[(0,g),(.20,qc),(.49,qc),(.55,qr),(.74,qr),(.88,qp),(.96,qp),(1.15,qf),(1.55,g)],.74,.88,1.15),
 ('A_HF_AerialStrike',[(0,g),(.1333,ac),(.20,ac),(.30,ah),(.75,ah),(.9667,g)],.2167,.3167,.85)
]
exec(compile(src[src.index('def bake():'):],'bake_phase_clips','exec'))
notify=unreal.load_class(None,'/Script/test.AnimNotify_ComicCue')
for name,events in [
 ('A_CC_DashStrike',[(.14,20),(.20,10),(.28,21),(.34,11),(.42,22),(.48,12),(.56,23),(.62,13),(.80,24),(.88,14),(1.04,2)]),
 ('A_CC_InkBreaker',[(.55,30),(.74,0),(.88,1),(1.15,2)])]:
    seq=unreal.load_asset(ROOT+'/Animations/'+name)
    unreal.AnimationLibrary.remove_all_animation_notify_tracks(seq)
    unreal.AnimationLibrary.add_animation_notify_track(seq,'Combat')
    for at,cue in events:
        event=unreal.AnimationLibrary.add_animation_notify_event(seq,'Combat',at,notify)
        event.set_editor_property('cue',cue)
    unreal.EditorAssetLibrary.save_loaded_asset(seq,False)

print('COMBAT_V8_ANIMATIONS_COMPLETE')
