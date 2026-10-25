"""비가산 전신 피격 4종. 짧은 충격 포즈 유지와 회복 동작을 키에 직접 굽는다."""
import unreal,json,math
from pathlib import Path
WORK=Path(unreal.Paths.project_dir()).resolve() / 'Tools/ComicCombat'
source=(WORK/'author_animations.py').read_text(encoding='utf-8')
exec(compile(source.split('\nguard=pose()')[0],'combat_pose_helpers','exec'))
idle=unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle')
base={}
for n in DATA:
 tr=unreal.AnimationLibrary.get_bone_pose_for_time(idle,n,0,False)
 base[n]=([tr.translation.x,tr.translation.y,tr.translation.z],[tr.rotation.x,tr.rotation.y,tr.rotation.z,tr.rotation.w])
base_world=globals_of(base)
def bend(bend_angle=0,twist=0,drop=0,back=0,arms=0):
 local={n:(t[:],q[:]) for n,(t,q) in base.items()}
 local['pelvis']=(add(local['pelvis'][0],[0,-back,-drop]),local['pelvis'][1])
 for n in ['spine_01','spine_02','spine_03','spine_04','spine_05']:
  world=globals_of(local);parent=DATA[n]['parent']
  delta=qmul(axis([1,0,0],bend_angle/5),axis([0,0,1],twist/5))
  local[n]=(local[n][0],qmul(inv(world[parent][1]),qmul(delta,world[n][1])))
 world=globals_of(local)
 n='head';parent=DATA[n]['parent']
 local[n]=(local[n][0],qmul(inv(world[parent][1]),qmul(axis([1,0,0],bend_angle*.20),world[n][1])))
 # 발은 원래 위치, 손은 충격 방향 반대로 벌어져 실루엣이 읽히도록 한다.
 for side,sign in [('l',1),('r',-1)]:
  foot='foot_'+side;hand='hand_'+side
  solve_limb(local,'thigh_'+side,'calf_'+side,foot,base_world[foot][0],[sign*25,65,45],base_world[foot][1])
  goal=add(base_world[hand][0],[sign*arms*.30,-arms*.15,arms])
  solve_limb(local,'upperarm_'+side,'lowerarm_'+side,hand,goal,[sign*65,5,105],base_world[hand][1])
 world=globals_of(local)
 for ik,bone in [('ik_hand_l','hand_l'),('ik_hand_r','hand_r'),('ik_foot_l','foot_l'),('ik_foot_r','foot_r')]:
  if ik in local:
   parent=DATA[ik]['parent'];pt,pq=world[parent]
   local[ik]=(rot(inv(pq),sub(world[bone][0],pt)),qmul(inv(pq),world[bone][1]))
 return local
clips=[]
for name,sign in [('A_CC_TargetHitLeft',1),('A_CC_TargetHitRight',-1)]:
 impact=bend(18,sign*14,3,3,25)
 clips.append((name,[(0,base),(.0333,impact),(.0833,impact),(.16,bend(11,sign*7,4,2,17)),(.28,bend(-5,-sign*4,1,0,10)),(.4333,base)]))
heavy=bend(34,-18,10,8,48)
clips.append(('A_CC_TargetHitHeavy',[(0,base),(.0333,heavy),(.10,heavy),(.22,bend(20,-8,13,5,35)),(.40,bend(-9,6,7,2,25)),(.6333,base)]))
ultimate=bend(43,13,15,12,58)
clips.append(('A_CC_TargetHitUltimate',[(0,base),(.0333,ultimate),(.1333,ultimate),(.26,bend(26,6,19,9,44)),(.48,bend(-13,-8,12,5,32)),(.80,base)]))
results=[]
for name,keys in clips:
 path=ROOT+'/Animations/'+name
 seq=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
 if seq is None:
  f=unreal.AnimSequenceFactory();f.target_skeleton=SKELETON;f.preview_skeletal_mesh=MESH
  seq=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,ROOT+'/Animations',unreal.AnimSequence,f)
 seq.set_editor_property('additive_anim_type',unreal.AdditiveAnimationType.AAT_NONE)
 controller=seq.controller;controller.open_bracket('Bake full-body target hit reaction',False)
 controller.set_frame_rate(unreal.FrameRate(60,1),False)
 frames=round(keys[-1][0]*30)*2
 controller.set_number_of_frames(unreal.FrameNumber(frames),False)
 controller.remove_all_bone_tracks(False)
 poses=[]
 for frame in range(frames+1):
  time=frame/60
  a,b=next(((a,b) for a,b in zip(keys,keys[1:]) if a[0]<=time<=b[0]),(keys[-2],keys[-1]))
  alpha=max(0,min(1,(time-a[0])/max(1e-8,b[0]-a[0])));alpha=alpha*alpha*(3-2*alpha)
  poses.append({n:([x+(y-x)*alpha for x,y in zip(a[1][n][0],b[1][n][0])],slerp(a[1][n][1],b[1][n][1],alpha)) for n in DATA})
 for n in DATA:
  controller.add_bone_track(n,False)
  assert controller.set_bone_track_keys(n,[unreal.Vector(*p[n][0]) for p in poses],[unreal.Quat(*p[n][1]) for p in poses],[unreal.Vector(1,1,1)]*len(poses),False)
 controller.close_bracket(False)
 unreal.EditorAssetLibrary.save_loaded_asset(seq,False)
 results.append({'asset':path,'frames':frames,'duration':seq.get_play_length(),'additive':str(seq.get_editor_property('additive_anim_type'))})
(WORK/'target-reaction-assets.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('TARGET_REACTION_ASSETS_COMPLETE',results)
