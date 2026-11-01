"""Native EX skeleton combat: grounded guard, punches and kicks. Preserve gameplay notifies."""
import unreal,json,math
from pathlib import Path
WORK=Path(unreal.Paths.project_dir()).resolve()/'Tools/ComicCombat'
DATA=json.loads((WORK/'exorcist_skeleton.json').read_text())
MESH=unreal.load_asset('/Game/ExorcistV10/Character/SK_EX_Game')
SKELETON=MESH.skeleton
ROOT='/Game/ExorcistV10/Animations/manny/'
# Reuse the repository's quaternion/analytic two-bone IK math, not its Manny proportions.
source=(WORK/'author_animations.py').read_text(encoding='utf-8')
exec(source[source.index('def add('):source.index('def pose(')])
base=unreal.load_asset(ROOT+'A_CC_Jab')
FINGERS={}
for n in DATA:
 if any(x in n for x in ['proximal','intermediate','distal']):
  q=unreal.AnimationLibrary.get_bone_pose_for_time(base,n,0,False).rotation
  FINGERS[n]=[q.x,q.y,q.z,q.w]

def pose(height=100,lean=0,twist=0,shift=0,left=(19,20,122),right=(-19,17,121),lf=(16,7,13.08),rf=(-16,-9,13.08)):
 local={n:(t[:],q[:]) for n,(t,q) in REF.items()}
 for n,q in FINGERS.items():local[n]=(local[n][0],q)
 world=globals_of(local);parent=DATA['hips']['parent'];pt,pq=world[parent]
 local['hips']=(rot(inv(pq),sub([.335,2.35+shift,height],pt)),qmul(inv(pq),qmul(axis([0,0,1],twist*.4),REF_G['hips'][1])))
 for n in ['spine','chest']:
  world=globals_of(local);parent=DATA[n]['parent'];delta=qmul(axis([1,0,0],lean*.5),axis([0,0,1],twist*.3))
  local[n]=(local[n][0],qmul(inv(world[parent][1]),qmul(delta,world[n][1])))
 solve_limb(local,'upper_leg_L','lower_leg_L','foot_L',list(lf),[20,60,55],REF_G['foot_L'][1])
 solve_limb(local,'upper_leg_R','lower_leg_R','foot_R',list(rf),[-20,60,55],REF_G['foot_R'][1])
 solve_limb(local,'upper_arm_L','lower_arm_L','hand_L',list(left),[40,0,114])
 solve_limb(local,'upper_arm_R','lower_arm_R','hand_R',list(right),[-40,0,114])
 world=globals_of(local);n='head1';parent=DATA[n]['parent']
 local[n]=(local[n][0],qmul(inv(world[parent][1]),qmul(axis([0,0,1],twist*.12),REF_G[n][1])))
 return local

def bake(name,keys,duration=None):
 seq=unreal.load_asset(ROOT+name)
 if seq is None:
  f=unreal.AnimSequenceFactory();f.target_skeleton=SKELETON;f.preview_skeletal_mesh=MESH
  seq=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,ROOT.rstrip('/'),unreal.AnimSequence,f)
 frames=round((duration or seq.get_play_length())*60)
 c=seq.controller;c.open_bracket('Native EX full body poses',False);c.set_frame_rate(unreal.FrameRate(60,1),False);c.set_number_of_frames(unreal.FrameNumber(frames),False);c.remove_all_bone_tracks(False)
 poses=[]
 for frame in range(frames+1):
  t=frame/60;a,b=next(((a,b) for a,b in zip(keys,keys[1:]) if a[0]<=t<=b[0]),(keys[-2],keys[-1]))
  alpha=max(0,min(1,(t-a[0])/max(1e-6,b[0]-a[0])));alpha=alpha*alpha*(3-2*alpha)
  poses.append({n:([x+(y-x)*alpha for x,y in zip(a[1][n][0],b[1][n][0])],slerp(a[1][n][1],b[1][n][1],alpha)) for n in DATA})
 for n in DATA:
  c.add_bone_track(n,False)
  assert c.set_bone_track_keys(n,[unreal.Vector(*p[n][0]) for p in poses],[unreal.Quat(*p[n][1]) for p in poses],[unreal.Vector(1,1,1)]*len(poses),False)
 c.close_bracket(False);unreal.EditorAssetLibrary.save_loaded_asset(seq,False)
 return seq

def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._ex_combat)
 guard=pose();breath=pose(height=100.35,lean=-.45)
 idle=bake('A_EX_CombatIdle',[(0,guard),(1.4,breath),(2.8,guard)],2.8)
 bake('MM_Idle',[(0,guard),(1.4,breath),(2.8,guard)],2.8)
 jabwind=pose(height=98,twist=-16,left=(23,4,126));jabhit=pose(height=100,twist=22,lean=-6,shift=3,left=(5,57,134))
 crosswind=pose(height=98,twist=21,right=(-25,0,127));crosshit=pose(height=100,twist=-26,lean=-7,shift=4,right=(-4,59,133))
 upperwind=pose(height=94,twist=22,right=(-24,10,107));upperhit=pose(height=103,twist=-24,lean=4,right=(-4,34,163))
 kickwind=pose(height=100,lean=7,rf=(-14,20,54));kickhit=pose(height=103,lean=10,twist=8,rf=(-5,69,102),left=(21,20,129),right=(-22,14,127))
 bake('A_CC_Jab',[(0,guard),(.083,jabwind),(.133,jabhit),(.19,jabhit),(.32,guard),(.4,guard)])
 bake('A_CC_Cross',[(0,guard),(.117,crosswind),(.183,crosshit),(.24,crosshit),(.40,guard),(.5,guard)])
 bake('A_CC_Uppercut',[(0,guard),(.20,upperwind),(.267,upperhit),(.34,upperhit),(.57,guard),(.7,guard)])
 bake('A_CC_Hammer',[(0,guard),(.22,kickwind),(.35,kickhit),(.42,kickhit),(.63,kickwind),(.78,guard),(.867,guard)])
 keys=[(0,guard)]
 for wind,hit,wp,hp in [(.14,.20,jabwind,jabhit),(.33,.40,crosswind,crosshit),(.55,.62,jabwind,jabhit),(.78,.85,crosswind,crosshit),(1.02,1.10,upperwind,upperhit)]:keys.extend([(wind,wp),(hit,hp),(hit+.045,hp)])
 keys.extend([(1.42,guard),(1.567,guard)]);bake('A_CC_DashStrike',keys)
 charge=pose(height=92,lean=-8,twist=22,right=(-26,-7,116),left=(24,20,123))
 drive=pose(height=97,lean=-16,twist=-28,shift=5,right=(-3,61,130),left=(20,15,121))
 bake('A_CC_InkBreaker',[(0,guard),(.22,charge),(.55,charge),(.74,crosswind),(.88,drive),(.97,drive),(1.4,guard),(1.6,guard)])
 airwind=pose(height=103,lean=8,lf=(18,5,35),rf=(-15,15,55));airhit=pose(height=100,lean=12,lf=(18,-2,35),rf=(-8,55,30))
 bake('A_HF_AerialStrike',[(0,guard),(.217,airwind),(.317,airhit),(.45,airhit),(.85,guard),(1,guard)])
 bake('A_CC_RisingPunch',[(0,guard),(.183,upperwind),(.25,upperhit),(.40,upperhit),(.70,guard),(.8,guard)])
 b=unreal.load_asset(ROOT+'BS_Idle_Walk_Run');samples=list(b.get_editor_property('sample_data'))
 for s in samples:
  if s.get_editor_property('sample_value').y==0:s.set_editor_property('animation',idle)
 b.set_editor_property('sample_data',samples);unreal.EditorAssetLibrary.save_loaded_asset(b,False)
 print('EX_NATIVE_COMBAT_READY: grounded idle, punches, kicks, rush punch; notifies retained')
unreal._ex_combat=unreal.register_slate_post_tick_callback(run)
