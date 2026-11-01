"""Hold a real impact pose for screenshot inspection, then restore all ticking.
This is a diagnostic capture, not a timed gameplay recording.
"""
import unreal
w=unreal.EditorLevelLibrary.get_game_world();p=unreal.GameplayStatics.get_player_character(w,0);pc=unreal.GameplayStatics.get_player_controller(w,0)
cam=p.get_component_by_class(unreal.CameraComponent)
pres=p.get_component_by_class(unreal.ComicCombatPresentationComponent)
s={'age':0,'stage':0,'held':False,'objects':[],'meshes':[]}
assert p.ultimate_charge>=99.99,'Run the combo verification first to earn a full charge.'
p.set_automation_input_isolation(True)
p.set_actor_location(unreal.Vector(-125,0,98.15),False,True);p.set_actor_rotation(unreal.Rotator(),False)
pc.set_control_rotation(unreal.Rotator(pitch=-12,yaw=50))
p.inject_control_key('Q',True)
def finish():
 for obj in s['objects']:
  if isinstance(obj,unreal.Actor):obj.set_actor_tick_enabled(True)
  else:obj.set_component_tick_enabled(True)
 for mesh,rate in s['meshes']:mesh.set_editor_property('global_anim_rate_scale',rate)
 p.inject_control_key('Q',False);p.set_automation_input_isolation(False)
 unreal.unregister_slate_post_tick_callback(unreal._highlight_capture)
 print('HIGHLIGHT_INSPECTION_DONE',s['held'])
def tick(dt):
 try:
  s['age']+=dt
  if s['age']>.1:p.inject_control_key('Q',False)
  active=next((e for e in cam.post_process_settings.weighted_blendables.array if e.weight>0 and e.object.get_base_material().get_name()=='M_CC_HighlightOnly'),None)
  if not s['held'] and active and active.object.get_scalar_parameter_value('ImpactFlash')>.5 and active.object.get_scalar_parameter_value('HighlightAge')>=.075:
   s['held']=True;s['hold_time']=s['age']
   s['objects']=[pres,p]+[a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.ComicCombatEffect) if a.is_effect_active()]
   for character in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Character):
    if character!=p:s['objects'].append(character)
    s['objects'].append(character.character_movement)
    s['meshes'].append((character.mesh,character.mesh.global_anim_rate_scale))
    character.mesh.set_editor_property('global_anim_rate_scale',0)
   for obj in s['objects']:
    if isinstance(obj,unreal.Actor):obj.set_actor_tick_enabled(False)
    else:obj.set_component_tick_enabled(False)
  if s['held'] and s['age']-s['hold_time']>.16 and not s.get('shot'):
   s['shot']=True
   unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename=C:/Users/jooan/Documents/Codex/2026-10-25/x20/outputs/highlight-held-inspection.png')
  if s['held'] and s['age']-s['hold_time']>.65:finish()
  elif s['age']>5:finish()
 except Exception as e:print('HIGHLIGHT_CAPTURE_ERROR',e);finish()
unreal._highlight_capture=unreal.register_slate_post_tick_callback(tick)
