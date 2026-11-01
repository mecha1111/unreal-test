import unreal,json
from pathlib import Path
w=unreal.EditorLevelLibrary.get_game_world();p=unreal.GameplayStatics.get_player_character(w,0);pc=unreal.GameplayStatics.get_player_controller(w,0)
pres=p.get_component_by_class(unreal.ComicCombatPresentationComponent)
p.set_automation_input_isolation(True);p.set_actor_location(unreal.Vector(-2200,-600,98.15),False,True);p.set_actor_rotation(unreal.Rotator(),False)
pc.set_control_rotation(unreal.Rotator(pitch=-10,yaw=65));p.inject_control_key('LeftShift',True)
s={'t':0,'initial_plants':pres.get_editor_property('foot_plant_count'),'samples':[]}
def tick(dt):
 s['t']+=dt;p.add_movement_input(unreal.Vector(1,0,0),1,True)
 if s['t']>1:s['samples'].append([s['t'],p.mesh.get_socket_location('foot_L').z,p.mesh.get_socket_location('foot_R').z])
 if s['t']>2.4 and not s.get('shot'):
  s['shot']=True
  unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename=C:/Users/jooan/Documents/Codex/2026-10-25/x20/outputs/running-final.png')
 if s['t']>4:
  s['foot_plants']=pres.get_editor_property('foot_plant_count')-s['initial_plants']
  s['speed']=p.get_velocity().length();s['animation_ground_speed']=p.mesh.get_anim_instance().get_editor_property('GroundSpeed')
  s['checks']=[{'test':'sprint_speed_and_animation_input','passed':abs(s['speed']-800)<5 and abs(s['animation_ground_speed']-800)<5},{'test':'sprint_footfall_cadence','passed':s['foot_plants']>=7,'count':s['foot_plants']}]
  p.inject_control_key('LeftShift',False);p.set_automation_input_isolation(False)
  unreal.unregister_slate_post_tick_callback(unreal._sprint_cycle)
  Path(r'C:/Users/jooan/Documents/Codex/2026-10-25/x20/outputs/sprint-cycle-verification.json').write_text(json.dumps(s,indent=2))
  print('SPRINT_CYCLE_VERIFIED',s['checks'])
unreal._sprint_cycle=unreal.register_slate_post_tick_callback(tick)
