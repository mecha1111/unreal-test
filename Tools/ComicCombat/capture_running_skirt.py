"""Hold two real sprint poses for front/side inspection; restore all tick settings."""
import unreal
w=unreal.EditorLevelLibrary.get_game_world();p=unreal.GameplayStatics.get_player_character(w,0);pc=unreal.GameplayStatics.get_player_controller(w,0)
arm=p.get_component_by_class(unreal.SpringArmComponent);oldarm=arm.target_arm_length
p.set_automation_input_isolation(True);p.set_actor_location(unreal.Vector(-1800,-600,98.15),False,True)
p.set_actor_rotation(unreal.Rotator(),False);arm.target_arm_length=265
p.inject_control_key('LeftShift',True)
s={'age':0,'phase':0,'held':False,'shots':set()}
def hold(enabled):
 p.set_actor_tick_enabled(not enabled);p.character_movement.set_component_tick_enabled(not enabled);p.mesh.set_component_tick_enabled(not enabled)
def shot(label):
 unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename=C:/Users/jooan/Documents/Codex/2026-10-25/x20/outputs/skirt-'+label+'.png')
def finish():
 hold(False);p.inject_control_key('LeftShift',False);p.character_movement.stop_movement_immediately()
 arm.target_arm_length=oldarm;p.set_automation_input_isolation(False)
 unreal.unregister_slate_post_tick_callback(unreal._skirt_capture);print('RUNNING_SKIRT_CAPTURED')
def tick(dt):
 try:
  s['age']+=dt;t=s['age']
  if not s['held']:p.add_movement_input(unreal.Vector(1,0,0),1,True)
  if t>1 and not s['held']:
   hold(True);s['held']=True;pc.set_control_rotation(unreal.Rotator(pitch=-7,yaw=160));s['hold']=t
  if s['held']:
   age=t-s['hold']
   if age>.18 and 'front' not in s['shots']:shot('run-front-'+str(s['phase']));s['shots'].add('front')
   if age>.4 and 'side_camera' not in s['shots']:pc.set_control_rotation(unreal.Rotator(pitch=-7,yaw=-90));s['shots'].add('side_camera')
   if age>.6 and 'side' not in s['shots']:shot('run-side-'+str(s['phase']));s['shots'].add('side')
   if age>.9:
    if s['phase']==1:finish()
    else:hold(False);s.update(age=.76,phase=1,held=False,shots=set())
 except Exception as e:print('SKIRT_CAPTURE_ERROR',repr(e));finish()
unreal._skirt_capture=unreal.register_slate_post_tick_callback(tick)
