import unreal,json
from pathlib import Path
out=Path(r'C:\Users\jooan\Documents\Codex\2026-10-25\x20\outputs')
w=unreal.EditorLevelLibrary.get_game_world();p=unreal.GameplayStatics.get_player_character(w,0);pc=unreal.GameplayStatics.get_player_controller(w,0)
p.set_automation_input_isolation(True)
cam=p.get_component_by_class(unreal.CameraComponent);arm=p.get_component_by_class(unreal.SpringArmComponent)
initial_fov=cam.field_of_view;initial_arm=arm.target_arm_length
s={'t':unreal.GameplayStatics.get_time_seconds(w),'stage':-1,'checks':[],'released':False,'mouse':False}
keys=['LeftMouseButton','RightMouseButton','E','Q']
def check(name,value,**details):s['checks'].append(dict(test=name,passed=bool(value),**details))
def shot(name):unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename='+str(out/name).replace('\\','/'))
def next_attack():
 s['stage']+=1;s['t']=unreal.GameplayStatics.get_time_seconds(w);s['released']=False;s['mouse']=False;s['active_orbit']=0;s['previous_yaw']=0;s['mouse_events']=0
 p.character_movement.stop_movement_immediately();p.set_actor_location(unreal.Vector(-125,0,98.15),False,True)
 pc.set_control_rotation(unreal.Rotator(pitch=-12,yaw=0,roll=0));p.set_actor_rotation(unreal.Rotator(),False)
 if s['stage']==3:check('seven_hits_ready_for_ultimate',p.ultimate_charge>=99.99,charge=p.ultimate_charge)
 p.inject_control_key(keys[s['stage']],True)
 s['attacks']=p.attack_count
def finish():
 p.set_automation_input_isolation(False);unreal.unregister_slate_post_tick_callback(unreal._free_verify)
 (out/'free-camera-verification.json').write_text(json.dumps(s['checks'],indent=2))
 print('FREE_CAMERA_VERIFIED',s['checks'])
p.set_actor_location(unreal.Vector(-650,-600,98.15),False,True);pc.set_control_rotation(unreal.Rotator(pitch=-12,yaw=150,roll=0))
def tick(dt):
 try:
  age=unreal.GameplayStatics.get_time_seconds(w)-s['t'];stage=s['stage']
  if stage<0:
   if age>1 and not s.get('idle_shot'):
    sole=min(p.mesh.get_socket_location('foot_L').z,p.mesh.get_socket_location('foot_R').z)-13.08
    check('idle_reference_sole_clearance',-.5<sole<.75,cm=sole)
    check('camera_target_collision_ignored',all(a.get_component_by_class(unreal.CapsuleComponent).get_collision_response_to_channel(unreal.CollisionChannel.ECC_CAMERA)==unreal.CollisionResponseType.ECR_IGNORE for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.PlaygroundTarget)))
    shot('daylight-camera-final.png');s['idle_shot']=True
   elif age>1.4:next_attack()
   return
  if age>.15 and not s['released']:p.inject_control_key(keys[stage],False);s['released']=True
  current_yaw=pc.get_control_rotation().yaw
  if p.attacking:s['active_orbit']+=abs((current_yaw-s['previous_yaw']+180)%360-180)
  s['previous_yaw']=current_yaw
  if age<.8:pc.inject_mouse_delta(2,.15);s['mouse_events']+=1
  elif not s['mouse']:
   yaw=pc.get_control_rotation().yaw
   # The number of render frames varies during shader/asset loading. Require
   # observed rotation WHILE the attack is active, not an arbitrary final angle.
   check(keys[stage]+'_mouse_orbit',s['active_orbit']>.2 and p.attack_count>s['attacks'],yaw=yaw,active_orbit=s['active_orbit'],mouse_events=s['mouse_events'],attack_count=p.attack_count-s['attacks'])
   check(keys[stage]+'_camera_follows_input',abs(unreal.MathLibrary.normalized_delta_rotator(cam.get_world_rotation(),pc.get_control_rotation()).yaw)<1)
   check(keys[stage]+'_no_zoom_or_slow_camera',abs(cam.field_of_view-initial_fov)<.01 and abs(arm.target_arm_length-initial_arm)<.01 and unreal.GameplayStatics.get_global_time_dilation(w)==1)
   s['last_yaw']=yaw;s['mouse']=True
  if age>3:
   check(keys[stage]+'_no_recenter',abs(unreal.MathLibrary.normalized_delta_rotator(pc.get_control_rotation(),unreal.Rotator(yaw=s['last_yaw'])).yaw)<.01)
   if stage<3:next_attack()
   else:
    p.inject_control_key('MouseScrollUp',True);p.inject_control_key('MouseScrollUp',False)
    check('mouse_wheel_zoom',arm.target_arm_length==initial_arm-30)
    finish()
 except Exception as e:check('exception',False,error=repr(e));finish()
unreal._free_verify=unreal.register_slate_post_tick_callback(tick)

