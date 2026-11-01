"""PIE: real inputs, limb anchors, physics contact, five punches and transient highlight."""
import unreal,json
from pathlib import Path
out=Path(r'C:\Users\jooan\Documents\Codex\2026-10-25\x20\outputs')
w=unreal.EditorLevelLibrary.get_game_world();p=unreal.GameplayStatics.get_player_character(w,0);pc=unreal.GameplayStatics.get_player_controller(w,0)
p.set_automation_input_isolation(True)
cam=p.get_component_by_class(unreal.CameraComponent)
initial_fov=cam.field_of_view
state={'stage':-1,'t':unreal.GameplayStatics.get_time_seconds(w),'checks':[],'contacts':[],'atlases':set(),'ultimate_vfx':False,'ultimate_light':0,'ultimate_motion':False}
keys=['LeftMouseButton','RightMouseButton','E','Q']
def check(name,passed,**details):state['checks'].append(dict(test=name,passed=bool(passed),**details))
def weights():return [e for e in cam.post_process_settings.weighted_blendables.array if isinstance(e.object,unreal.MaterialInterface) and e.object.get_base_material().get_name()=='M_CC_HighlightOnly']
def screenshot(name):
 if globals().get('CAPTURE_IMAGES',True):unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename='+str(out/name).replace('\\','/'))
def advance():
 state.update(stage=state['stage']+1,t=unreal.GameplayStatics.get_time_seconds(w),released=False,hits=p.hit_count,seen=p.hit_count,flash=False,ink=False,orbit=0,prev_yaw=55)
 p.character_movement.stop_movement_immediately();p.set_actor_location(unreal.Vector(-125,0,98.15),False,True)
 p.set_actor_rotation(unreal.Rotator(),False);pc.set_control_rotation(unreal.Rotator(pitch=-12,yaw=55,roll=0))
 if state['stage']==3:check('ultimate_ready_after_seven_hits',p.ultimate_charge>=99.99,charge=p.ultimate_charge)
 p.inject_control_key(keys[state['stage']],True)
def finish():
 check('generated_punch_retained','T_Generated_arcane_punch' in state['atlases'])
 check('ultimate_generated_sheets_restored',{'T_Generated_arcane_ultimate','T_Generated_arcane_lightning'}.issubset(state['atlases']))
 state['atlases']=sorted(state['atlases'])
 p.set_automation_input_isolation(False)
 unreal.unregister_slate_post_tick_callback(unreal._alignment_verify)
 (out/globals().get('RESULT_FILE','combat-alignment-verification.json')).write_text(json.dumps(state,indent=2),encoding='utf-8')
 print('COMBAT_ALIGNMENT_VERIFIED',sum(x['passed'] for x in state['checks']),len(state['checks']))
def tick(dt):
 try:
  stage=state['stage'];age=unreal.GameplayStatics.get_time_seconds(w)-state['t']
  if stage==3:
   state['ultimate_vfx']|=any(e.is_effect_active() for e in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.ComicCombatEffect))
   state['ultimate_light']=max(state['ultimate_light'],max((c.intensity for c in p.get_components_by_class(unreal.PointLightComponent) if c.is_visible()),default=0))
   state['ultimate_motion']|=p.attacking and p.get_attack_variant()==5
  for effect in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.ComicCombatEffect):
   if effect.is_effect_active():
    for mesh in effect.get_components_by_class(unreal.StaticMeshComponent):
     material=mesh.get_material(0)
     if mesh.is_visible() and isinstance(material,unreal.MaterialInstanceDynamic):
      atlas=material.get_texture_parameter_value('Atlas')
      if atlas:state['atlases'].add(atlas.get_name())
  if stage<0:
   if age>1:
    check('normal_view_has_no_active_filter',all(x.weight==0 for x in weights()))
    check('fullscreen_highlight_material_not_bound',not weights())
    advance()
   return
  if age>.09 and not state['released']:p.inject_control_key(keys[stage],False);state['released']=True
  if age<1.4:
   yaw=pc.get_control_rotation().yaw
   if p.attacking:state['orbit']+=abs((yaw-state['prev_yaw']+180)%360-180)
   state['prev_yaw']=yaw;pc.inject_mouse_delta(.4,0)
  if p.hit_count>state['seen']:
   state['seen']=p.hit_count
   contact=p.last_contact_point;strike=p.last_strike_point
   effects=[e for e in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.ComicCombatEffect) if e.is_effect_active()]
   nearest=min([(e.get_actor_location()-contact).length() for e in effects],default=999)
   variant=p.get_attack_variant()
   if variant==3:
    a=p.mesh.get_socket_location('foot_R');b=p.mesh.get_socket_location('toes_R');limb=a+(b-a)*.8
   else:
    side='L' if (variant==0 or (variant==4 and state['seen']-state['hits'] in [1,3])) else 'R'
    a=p.mesh.get_socket_location('hand_'+side);b=p.mesh.get_socket_location('middle_proximal_'+side);limb=a+(b-a)*.75
   error=(limb-strike).length()
   state['contacts'].append(dict(key=keys[stage],bone=str(p.last_contact_bone),point=[contact.x,contact.y,contact.z],strike=[strike.x,strike.y,strike.z],limb_error=error,vfx_origin_error=nearest))
   check(keys[stage]+'_physics_contact_'+str(p.hit_count),str(p.last_contact_bone) not in ['None',''],bone=str(p.last_contact_bone))
   check(keys[stage]+'_vfx_at_contact_'+str(p.hit_count),nearest<.5,error_cm=nearest)
   check(keys[stage]+'_current_limb_anchor_'+str(p.hit_count),error<12,error_cm=error)
   if stage==0:screenshot('contact-jab-final.png')
   if stage==1:screenshot('contact-kick-final.png')
  for entry in weights():
   if entry.weight>0:
    state['flash']=True
    if stage==3 and state['ink'] and not state.get('negative_shot') and entry.object.get_scalar_parameter_value('NegativeAmount')>.5 and entry.object.get_scalar_parameter_value('ImpactFlash')==0:
     screenshot('ultimate-negative-final.png');state['negative_shot']=True
    if entry.object.get_scalar_parameter_value('ImpactFlash')>.5:
     state['ink']=True
     if stage==3 and not state.get('ink_shot'):screenshot('ultimate-ink-final.png');state['ink_shot']=True
  if age>3:
   count=p.hit_count-state['hits']
   check(keys[stage]+'_hits',count>= (5 if stage==2 else 1),count=count)
   check(keys[stage]+'_free_camera',state['orbit']>.2 and abs(cam.field_of_view-initial_fov)<.01 and unreal.GameplayStatics.get_global_time_dilation(w)==1,orbit=state['orbit'])
   if stage==3:
    check('ultimate_fullscreen_highlight_disabled',not state['flash'] and not state['ink'])
    check('ultimate_spawned_vfx_restored',state['ultimate_vfx'])
    check('ultimate_effect_light_restored',state['ultimate_light']>0,intensity=state['ultimate_light'])
    check('ultimate_motion_preserved',state['ultimate_motion'])
    check('highlight_restores_daylight',all(x.weight==0 for x in weights()))
    finish()
   else:advance()
 except Exception as e:check('exception',False,error=repr(e));finish()
unreal._alignment_verify=unreal.register_slate_post_tick_callback(tick)
