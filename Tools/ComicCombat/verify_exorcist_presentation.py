"""PIE checks for idle expressions, attack response, sprint release and outline."""
import unreal,json,math
from pathlib import Path
w=unreal.EditorLevelLibrary.get_game_world();p=unreal.GameplayStatics.get_player_character(w,0);pc=unreal.GameplayStatics.get_player_controller(w,0)
cam=p.get_component_by_class(unreal.CameraComponent);arm=p.get_component_by_class(unreal.SpringArmComponent)
out=Path(r'C:/Users/jooan/Documents/Codex/2026-10-25/x20/outputs')
s={'age':0,'checks':[],'morph_samples':[],'idle_pose_samples':[],'shots':set()}
p.set_automation_input_isolation(True);p.character_movement.stop_movement_immediately()
p.set_actor_location(unreal.Vector(-600,-600,98.15),False,True);p.set_actor_rotation(unreal.Rotator(),False)
pc.set_control_rotation(unreal.Rotator(pitch=-8,yaw=180))
oldarm=arm.target_arm_length;oldoffset=arm.socket_offset;arm.target_arm_length=200;arm.socket_offset=unreal.Vector(0,0,74)
def check(name,value,**kw):s['checks'].append(dict(test=name,passed=bool(value),**kw))
def shot(name):unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename='+str(out/name).replace('\\','/'))
def finish():
 unreal.unregister_slate_post_tick_callback(unreal._presentation_verify)
 p.inject_control_key('LeftShift',False);p.inject_control_key('LeftMouseButton',False)
 arm.target_arm_length=oldarm;arm.socket_offset=oldoffset;p.set_automation_input_isolation(False)
 names=['EA_relaxed_eye','EA_lookLeft','EA_happy_mouth','EA_blink','EA_angry_brow','EA_aa']
 for name in names:
  high=max(x[name] for x in s['morph_samples']);check(name+'_animated',high>.1,peak=high)
 poses=s['idle_pose_samples']
 yaw_span=max(x['head_yaw'] for x in poses)-min(x['head_yaw'] for x in poses)
 hand_span=max(x['hand_height'] for x in poses)-min(x['hand_height'] for x in poses)
 check('original_idle_has_body_motion',hand_span>.05,cm=hand_span)
 soles=s.get('sole_samples',[])
 check('rendered_shoe_soles_grounded',bool(soles) and max(abs(z) for row in soles for z in row)<.35,samples_cm=soles)
 check('sprint_released',not p.running and p.character_movement.max_walk_speed==480)
 check('free_camera_inherits_input',cam.use_pawn_control_rotation==False and arm.use_pawn_control_rotation)
 s['shots']=list(s['shots']);(out/'exorcist-presentation-verification.json').write_text(json.dumps(s,indent=2))
 print('EX_PRESENTATION_VERIFIED',s['checks'])
def tick(dt):
 try:
  s['age']+=dt;t=s['age']
  if not s.get('initial'):
   s['initial']=True
   check('outline_bound',any(e.weight==1 and e.object.get_base_material().get_name()=='M_EX_Outline' for e in cam.post_process_settings.weighted_blendables.array))
   check('player_stencil',p.mesh.render_custom_depth and p.mesh.custom_depth_stencil_value==11)
   check('five_secondary_motion_groups',len(unreal.KawaiiPhysicsLibrary.collect_kawaii_physics_nodes_from_component(p.mesh,unreal.GameplayTagContainer(),False) or [])==5)
   bp=unreal.load_asset('/Game/ExorcistV10/Animations/manny/ABP_CC_Unarmed')
   idle_assets=[n.get_editor_property('node').get_editor_property('sequence').get_name() for g in bp.get_animation_graphs() for n in g.get_graph_nodes_of_class(unreal.load_class(None,'/Script/AnimGraph.AnimGraphNode_SequencePlayer')) if '.Idle.' in n.get_path_name()]
   check('actual_idle_state_uses_grounded_original',idle_assets==['A_EX_GroundedIdle'],assets=idle_assets)
   root='/Game/ExorcistV10/Animations/manny/'
   source=unreal.load_asset(root+'MM_Idle');grounded=unreal.load_asset(root+'A_EX_GroundedIdle')
   bones=['hips','spine','chest','head1','upper_arm_L','upper_arm_R','hand_L','hand_R']
   error=0
   for age in [0,.5,1,1.5,2,2.5]:
    a=unreal.AnimationLibrary.get_bone_poses_for_time(source,bones,age,False);b=unreal.AnimationLibrary.get_bone_poses_for_time(grounded,bones,age,False)
    for x,y in zip(a,b):
     error=max(error,(x.translation-y.translation).length(),1-abs(x.rotation.x*y.rotation.x+x.rotation.y*y.rotation.y+x.rotation.z*y.rotation.z+x.rotation.w*y.rotation.w))
   check('original_upper_body_animation_preserved',error<.001,max_error=error)
  names=['EA_relaxed_eye','EA_lookLeft','EA_happy_mouth','EA_blink','EA_angry_brow','EA_aa']
  s['morph_samples'].append(dict(age=t,**{n:p.mesh.get_morph_target(n) for n in names}))
  if 1<t<19.9:s['idle_pose_samples'].append(dict(age=t,head_yaw=p.mesh.get_socket_rotation('head1').yaw,hand_height=p.mesh.get_socket_location('hand_R').z,sole_l=p.mesh.get_socket_location('foot_L').z-13.08,sole_r=p.mesh.get_socket_location('foot_R').z-13.08))
  if 2<t<4.5 and t>s.get('next_sole',0):
   s['next_sole']=t+.4
   s.setdefault('sole_samples',[]).append([v.z for region in [0,1,2] for v in unreal.CombatAuthoringLibrary.measure_shoe_soles(p.mesh,1,region)])
  for age,label in [(2,'neutral'),(8.3,'relaxed'),(13.3,'curious'),(18.3,'smile')]:
   if t>age and label not in s['shots']:shot('face-'+label+'.png');s['shots'].add(label)
  if t>20 and not s.get('attack'):p.inject_control_key('LeftMouseButton',True);s['attack']=True
  if t>20.12 and not s.get('release'):p.inject_control_key('LeftMouseButton',False);s['release']=True
  if t>21 and not s.get('run'):
   p.inject_control_key('LeftShift',True);s['run']=True;arm.target_arm_length=540;arm.socket_offset=oldoffset;pc.set_control_rotation(unreal.Rotator(pitch=-10,yaw=45))
  if 21<t<23:p.add_movement_input(unreal.Vector(1,0,0),1,True)
  if t>22.5 and not s.get('runcheck'):
   s['runcheck']=True;check('sprint_800',abs(p.get_velocity().length()-800)<5,actual=p.get_velocity().length())
   check('sprint_fov_ramp',80<cam.field_of_view<=81.01,fov=cam.field_of_view)
   shot('running-final.png')
  if t>23 and not s.get('stop'):p.inject_control_key('LeftShift',False);s['stop']=True
  if t>24:
   check('fov_restored',abs(cam.field_of_view-78)<.1,fov=cam.field_of_view);finish()
 except Exception as e:
  check('exception',False,error=repr(e));finish()
unreal._presentation_verify=unreal.register_slate_post_tick_callback(tick)
