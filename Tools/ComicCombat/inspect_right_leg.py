import unreal
w=unreal.EditorLevelLibrary.get_game_world();p=unreal.GameplayStatics.get_player_character(w,0);pc=unreal.GameplayStatics.get_player_controller(w,0)
arm=p.get_component_by_class(unreal.SpringArmComponent);oldarm=arm.target_arm_length
p.set_automation_input_isolation(True);p.set_actor_location(unreal.Vector(-1800,-600,98.15),False,True);p.set_actor_rotation(unreal.Rotator(),False)
arm.target_arm_length=230;pc.set_control_rotation(unreal.Rotator(pitch=-8,yaw=90))
p.inject_control_key('LeftShift',True);s={'age':0}
def tick(dt):
 s['age']+=dt;t=s['age'];p.add_movement_input(unreal.Vector(1,0,0),1,True)
 for when,label in [(1.0,'attached'),(1.7,'hidden')]:
  if t>when and label not in s:
   s[label]=True
   unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename=C:/Users/jooan/Documents/Codex/2026-10-25/x20/outputs/right-leg-'+label+'.png')
 if t>1.3 and not s.get('hide'):
  s['hide']=True;p.mesh.hide_bone_by_name('Spring_11_thigh_chain_chain1_1',unreal.PhysBodyOp.PBO_NONE)
 if t>2.2:
  p.mesh.un_hide_bone_by_name('Spring_11_thigh_chain_chain1_1');p.inject_control_key('LeftShift',False)
  p.character_movement.stop_movement_immediately();p.set_automation_input_isolation(False);arm.target_arm_length=oldarm
  unreal.unregister_slate_post_tick_callback(unreal._right_leg_inspect);print('RIGHT_LEG_INSPECTED')
unreal._right_leg_inspect=unreal.register_slate_post_tick_callback(tick)
