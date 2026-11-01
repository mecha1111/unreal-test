"""Retimes licensed external motion; does not author new limb poses.
Quaternius UAL 1/2 + KayKit, CC0. Original imported takes stay intact.
"""
import unreal,json,math
from pathlib import Path
WORK=Path(unreal.Paths.project_dir()).resolve()/'Tools/ComicCombat'
DATA=json.loads((WORK/'exorcist_skeleton.json').read_text())
text=(WORK/'author_animations.py').read_text(encoding='utf-8');exec(text[text.index('def add('):text.index('def pose(')])
DEST='/Game/ExorcistV10/Animations/manny/'
SRC='/Game/ExorcistV10/Animations/External/'
paths={'idle':'UAL1/UAL1_SelectedIdle_Loop','jab':'UAL1/UAL1_SelectedPunch_Jab','cross':'UAL1/UAL1_SelectedPunch_Cross','hook':'UAL2/UAL2_SelectedMelee_Hook','recover':'UAL2/UAL2_SelectedMelee_Hook_Rec','kick':'KayKit/KayKit_UnarmedMelee_Unarmed_Attack_Kick','walk':'UAL1/UAL1_SelectedWalk_Loop','jog':'UAL1/UAL1_SelectedJog_Fwd_Loop','run':'UAL1/UAL1_SelectedSprint_Loop','jump':'UAL1/UAL1_SelectedJump_Start','air':'UAL2/UAL2_SelectedNinjaJump_Start','land':'UAL1/UAL1_SelectedJump_Land'}
paths['ultimate']='KayKit/KayKit_UnarmedMelee_Unarmed_Attack_Punch_A'
cache={};manifest=[]
only_assets=globals().get('EXTERNAL_ASSETS_ONLY')
def blend(a,b,f):return {n:([x+(y-x)*f for x,y in zip(a[n][0],b[n][0])],slerp(a[n][1],b[n][1],f)) for n in DATA}
def sample(name,t):
 poses,duration=cache[name];x=min(max(t,0),duration)*30;i=min(int(x),len(poses)-2)
 return blend(poses[i],poses[i+1],min(1,x-i))
def warp(t,knots):
 for (a,x),(b,y) in zip(knots,knots[1:]):
  if t<=b:return x+(y-x)*max(0,min(1,(t-a)/(b-a)))
 return knots[-1][1]
def bake(name,duration,fn,provenance):
 if only_assets and name not in only_assets:return
 seq=unreal.load_asset(DEST+name)
 if not seq:return
 backup='/Game/ExorcistV10/Animations/BeforeExternal/'+name
 if not unreal.EditorAssetLibrary.does_asset_exist(backup):unreal.EditorAssetLibrary.duplicate_asset(seq.get_path_name(),backup)
 frames=round(duration*60);poses=[fn(i/60) for i in range(frames+1)]
 c=seq.controller;c.open_bracket('External authored motion retarget and contact retiming',False);c.set_frame_rate(unreal.FrameRate(60,1),False);c.set_number_of_frames(unreal.FrameNumber(frames),False);c.remove_all_bone_tracks(False)
 for n in DATA:
  c.add_bone_track(n,False);c.set_bone_track_keys(n,[unreal.Vector(*p[n][0]) for p in poses],[unreal.Quat(*p[n][1]) for p in poses],[unreal.Vector(1,1,1)]*len(poses),False)
 c.close_bracket(False);unreal.EditorAssetLibrary.save_loaded_asset(seq,False)
 manifest.append({'asset':seq.get_path_name(),'source':provenance,'duration':frames/60})

def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._external_apply)
 for label,path in paths.items():
  a=unreal.load_asset(SRC+path);duration=a.get_play_length();poses=[]
  for frame in range(round(duration*30)+1):
   values=unreal.AnimationLibrary.get_bone_poses_for_time(a,list(DATA),frame/30,False)
   local={n:([p.translation.x,p.translation.y,p.translation.z],[p.rotation.x,p.rotation.y,p.rotation.z,p.rotation.w]) for n,p in zip(DATA,values)}
   poses.append(local)
  # Keep the artist's body motion; only correct retargeted shoe clearance.
  floors=[min(globals_of(p)['foot_L'][0][2],globals_of(p)['foot_R'][0][2]) for p in poses]
  for local,floor in zip(poses,floors):
   correction=13.08-(floor if label in ['idle','jab','cross','hook','recover','kick','ultimate'] else min(floors))
   parent=DATA['hips']['parent'];q=globals_of(local)[parent][1]
   local['hips']=(add(local['hips'][0],rot(inv(q),[0,0,correction])),local['hips'][1])
  if label=='ultimate':
   initial_y=globals_of(poses[0])['hips'][0][1]
   for local in poses:
    g=globals_of(local);q=g[DATA['hips']['parent']][1]
    # Capsule movement already performs the rush. Retain a modest body drive,
    # rather than allowing the imported root translation to leave the capsule.
    delta=(g['hips'][0][1]-initial_y)*.75
    local['hips']=(add(local['hips'][0],rot(inv(q),[0,-delta,0])),local['hips'][1])
  cache[label]=(poses,duration)
 # KayKit has no finger chains: use the supplied Quaternius closed fist pose.
 fist=sample('jab',.2)
 for local in cache['kick'][0]+cache['ultimate'][0]:
  for n in DATA:
   if any(k in n for k in ['proximal','intermediate','distal']):local[n]=(local[n][0],fist[n][1])
 idle=lambda t:sample('idle',t%2.5)
 bake('A_EX_CombatIdle',2.5,idle,paths['idle']);bake('MM_Idle',2.5,idle,paths['idle'])
 clips=[('A_CC_Jab','jab',.4,[(0,0),(.1333,.20),(.4,.86666)]),('A_CC_Cross','cross',.5,[(0,0),(.1833,.30),(.5,1)]),('A_CC_Hammer','kick',.866667,[(0,0),(.35,.43333),(.866667,.93333)]),('A_HF_AerialStrike','kick',1,[(0,0),(.3167,.43333),(.55,.5),(1,.93333)])]
 for name,source,duration,knots in clips:bake(name,duration,lambda t,s=source,k=knots:sample(s,warp(t,k)),paths[source])
 def hook(t,end=.7,contact=.2667):
  if t<=contact:return sample('hook',t/contact*.266667)
  if t<contact+.12:return sample('hook',.266667+(t-contact)/.12*.2)
  return sample('recover',(t-contact-.12)/max(.01,end-contact-.12)*.6)
 bake('A_CC_Uppercut',.7,hook,paths['hook']+' + '+paths['recover'])
 bake('A_CC_RisingPunch',.8,lambda t:hook(t,.8,.25),paths['hook']+' + '+paths['recover'])
 def flurry(t):
  # Preserve notify/contact times, overlap recovery with the next preparation.
  # There is no intermediate return to the last frame of either source clip.
  beats=[(.20,'jab',.2),(.40,'cross',.3),(.62,'jab',.2),(.85,'cross',.3),(1.10,'cross',.3)]
  if t<=.20:return sample('jab',t)
  for (a,previous,peak),(b,following,next_peak) in zip(beats,beats[1:]):
   if t<=b:
    u=(t-a)/(b-a);f=max(0,min(1,(u-.08)/.84));f=f*f*(3-2*f)
    pose=blend(sample(previous,peak+u*.22),sample(following,next_peak*u),f)
    g=globals_of(pose);lift=13.08-min(g['foot_L'][0][2],g['foot_R'][0][2])
    q=g[DATA['hips']['parent']][1]
    pose['hips']=(add(pose['hips'][0],rot(inv(q),[0,0,lift])),pose['hips'][1])
    return pose
  return sample('cross',warp(t,[(1.10,.3),(1.566667,1)]))
 bake('A_CC_DashStrike',1.566667,flurry,'Alternating '+paths['jab']+' / '+paths['cross'])
 bake('A_CC_InkBreaker',1.6,lambda t:sample('ultimate',warp(t,[(0,0),(.32,.26),(.55,.30),(.73,.38),(.88,.50),(.99,.58),(1.6,1.166667)])),paths['ultimate']+' charge / rush / full-body punch; reduced root travel')
 for name,source in [('MM_Walk_Fwd','walk'),('MM_Run_Fwd','jog'),('MM_Sprint','run'),('A_CC_JumpLift','jump'),('A_CC_AirKick','air'),('A_CC_Land','land')]:
  bake(name,cache[source][1],lambda t,s=source:sample(s,t),paths[source])
 # Discover and replace all locomotion clips actually referenced by this blend space.
 bs=unreal.load_asset(DEST+'BS_Idle_Walk_Run');samples=list(bs.get_editor_property('sample_data'))
 visited=set()
 for entry in samples:
  a=entry.get_editor_property('animation');v=entry.get_editor_property('sample_value').y
  if a and v>0 and a.get_name() not in visited:
   label='walk' if v<=280 else 'run';bake(a.get_name(),cache[label][1],lambda t,s=label:sample(s,t),paths[label]);visited.add(a.get_name())
 manifest_file=WORK/'external-animation-manifest.json'
 if only_assets and manifest_file.exists():
  touched={entry['asset'] for entry in manifest}
  manifest[:0]=[entry for entry in json.loads(manifest_file.read_text(encoding='utf-8')) if entry['asset'] not in touched]
 manifest_file.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print('EXTERNAL_COMBAT_APPLIED',len(manifest))
unreal._external_apply=unreal.register_slate_post_tick_callback(run)
