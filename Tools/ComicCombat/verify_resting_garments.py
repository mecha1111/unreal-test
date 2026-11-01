"""PIE regression: idle chatter, sprint/attack reactivation, and settling."""
import unreal,json,math
from pathlib import Path
w=unreal.EditorLevelLibrary.get_game_world();p=unreal.GameplayStatics.get_player_character(w,0)
face=p.get_component_by_class(unreal.ExorcistFaceComponent)
p.set_automation_input_isolation(True)
p.set_actor_location(unreal.Vector(-1800,-600,98.15),False,True)
s={'age':0,'samples':[],'run':False,'stop':False,'attack':False,'release':False}
bones=[f'skirt_{i}_2_CharakitEnd' for i in range(1,9)]

def finish():
 p.inject_control_key('LeftShift',False);p.inject_control_key('LeftMouseButton',False)
 p.character_movement.stop_movement_immediately();p.set_automation_input_isolation(False)
 unreal.unregister_slate_post_tick_callback(unreal._resting_garments)
 checks=[]
 def check(name,ok,**v):checks.append(dict(test=name,passed=bool(ok),**v))
 for name,a,b in [('initial_idle',1,2),('after_run',4.6,6),('after_attack',8.6,10)]:
  rows=[x for x in s['samples'] if a<x['time']<b]
  check(name+'_physics_blended_out',bool(rows) and max(x['weight'] for x in rows)==0)
  peak=max((math.dist(u,v) for x,y in zip(rows,rows[1:]) for u,v in zip(x['skirt'],y['skirt'])),default=999)
  check(name+'_no_collision_chatter',peak<.10,peak_step_cm=peak)
 check('sprint_restores_physics',any(2.5<x['time']<3.4 and x['weight']>.99 for x in s['samples']))
 check('attack_restores_physics',any(6.1<x['time']<7.3 and x['weight']>.99 for x in s['samples']))
 result={'checks':checks,'samples':s['samples']}
 Path(r'C:/Users/jooan/Documents/Codex/2026-10-25/x20/outputs/resting-garment-verification.json').write_text(json.dumps(result,indent=2))
 print('RESTING_GARMENTS_VERIFIED',checks)

def tick(dt):
 try:
  s['age']+=dt;t=s['age']
  if t>2 and not s['run']:p.inject_control_key('LeftShift',True);s['run']=True
  if 2<t<3.5:p.add_movement_input(unreal.Vector(1,0,0),1,True)
  if t>3.5 and not s['stop']:p.inject_control_key('LeftShift',False);s['stop']=True
  if t>6 and not s['attack']:p.inject_control_key('LeftMouseButton',True);s['attack']=True
  if t>6.1 and not s['release']:p.inject_control_key('LeftMouseButton',False);s['release']=True
  hip=p.mesh.get_socket_transform('hips',unreal.RelativeTransformSpace.RTS_WORLD)
  points=[unreal.MathLibrary.inverse_transform_location(hip,p.mesh.get_socket_location(n)) for n in bones]
  s['samples'].append(dict(time=t,weight=face.get_editor_property('cloth_physics_weight'),skirt=[[v.x,v.y,v.z] for v in points]))
  if t>10:finish()
 except Exception as e:
  print('RESTING_GARMENTS_ERROR',repr(e));finish()
unreal._resting_garments=unreal.register_slate_post_tick_callback(tick)
