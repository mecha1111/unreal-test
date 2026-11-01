"""Measure animated standing cloth relative to hips; no animation freeze."""
import unreal,json,math
from pathlib import Path
w=unreal.EditorLevelLibrary.get_game_world();p=unreal.GameplayStatics.get_player_character(w,0)
p.set_automation_input_isolation(True);p.character_movement.stop_movement_immediately()
bones=[f'skirt_{i}_2_CharakitEnd' for i in range(1,9)]+['Spring_03_draped_sleeve_chain1_2']
s={'age':0,'samples':[]}
def done():
 p.set_automation_input_isolation(False)
 unreal.unregister_slate_post_tick_callback(unreal._idle_cloth_probe)
 result={}
 for i,n in enumerate(bones):
  points=[a[i] for a in s['samples']]
  result[n]={'span_cm':max(math.dist(points[0],v) for v in points),'peak_step_cm':max(math.dist(a,b) for a,b in zip(points,points[1:]))}
 Path(unreal.Paths.project_dir()+'Saved/'+globals().get('RESULT_NAME','idle-cloth-before.json')).write_text(json.dumps(result,indent=2))
 print('IDLE_CLOTH_MEASURED',result)
def tick(dt):
 s['age']+=dt
 if s['age']>3:
  hip=p.mesh.get_socket_transform('hips',unreal.RelativeTransformSpace.RTS_WORLD)
  values=[unreal.MathLibrary.inverse_transform_location(hip,p.mesh.get_socket_location(n)) for n in bones]
  s['samples'].append([[v.x,v.y,v.z] for v in values])
 if s['age']>6:done()
unreal._idle_cloth_probe=unreal.register_slate_post_tick_callback(tick)
