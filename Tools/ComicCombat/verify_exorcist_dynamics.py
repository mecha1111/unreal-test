"""In-game motion/appearance regression. Screenshots require visual review as well.
Capsule clearance measures simulation bones, not every rendered cloth triangle.
"""
import unreal,json,math
from pathlib import Path
out=Path(r'C:\Users\jooan\Documents\Codex\2026-10-25\x20\outputs')
w=unreal.EditorLevelLibrary.get_game_world();p=unreal.GameplayStatics.get_player_character(w,0);pc=unreal.GameplayStatics.get_player_controller(w,0)
p.set_automation_input_isolation(True)
arm=p.get_component_by_class(unreal.SpringArmComponent);old_arm=arm.target_arm_length;arm.target_arm_length=285
s={'time':0,'stage':-1,'checks':[],'samples':[],'shots':[]}
stages=[('idle',1.8),('jog',1.0),('run_rear',1.0),('run_side',1.0),('turn',.8),('settle',2.3),('jump',1.4),('kick',1.5),('flurry',1.9)]
def check(name,ok,**kw):s['checks'].append(dict(test=name,passed=bool(ok),**kw))
def shot(label):
 if globals().get('CAPTURE_IMAGES',True):unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename='+str(out/('dynamics-'+label+'.png')).replace('\\','/'))
def advance():
 s['stage']+=1;s['time']=0;s['shot']=False;s['released']=False
 name=stages[s['stage']][0]
 if name=='run_rear':p.inject_control_key('LeftShift',True);pc.set_control_rotation(unreal.Rotator(pitch=-10,yaw=0))
 if name=='run_side':pc.set_control_rotation(unreal.Rotator(pitch=-7,yaw=85))
 if name=='turn':pc.set_control_rotation(unreal.Rotator(pitch=-8,yaw=135))
 if name=='settle':p.inject_control_key('LeftShift',False)
 if name in ['jump','kick','flurry']:
  p.inject_control_key({'jump':'SpaceBar','kick':'RightMouseButton','flurry':'E'}[name],True)
def finish():
 for key in ['LeftShift','W','SpaceBar','RightMouseButton','E']:p.inject_control_key(key,False)
 arm.target_arm_length=old_arm;p.set_automation_input_isolation(False)
 unreal.unregister_slate_post_tick_callback(unreal._dynamics_verify)
 values=[a['skirt_clearance'] for a in s['samples']]
 for name,expected in [('jog',480),('run_rear',800)]:
  speeds=[a['speed'] for a in s['samples'] if a['name']==name and a['age']>.6]
  if speeds:check(name+'_movement_speed',abs(max(speeds)-expected)<5,actual_cm_s=max(speeds))
 check('sprint_released',not p.running and p.character_movement.max_walk_speed==480)
 check('finite_secondary_bones',all(math.isfinite(x) for a in s['samples'] for x in a['hair']))
 if values:check('skirt_bone_proxy_clearance',min(values)>-2.5,minimum_cm=min(values))
 moving_sides=[a['skirt_side_clearance'] for a in s['samples'] if a['name'] in ['jog','run_rear','run_side','turn'] and a['age']>.4]
 if moving_sides:check('moving_panels_stay_on_original_body_side',min(moving_sides)>-.5,minimum_cm=min(moving_sides))
 moving=[a['skirt_clearance'] for a in s['samples'] if a['name'] in ['jog','run_rear','run_side','turn'] and a['age']>.4]
 if moving:check('moving_skirt_body_clearance',min(moving)>0,minimum_cm=min(moving))
 settled=[a['hair'] for a in s['samples'] if a['name']=='settle' and a['age']>1.7]
 if len(settled)>1:
  spread=max(math.dist(settled[0],x) for x in settled)
  check('hair_settles_after_stop',spread<3.5,spread_cm=spread)
 check('daylight_materials',all(p.mesh.get_material(i).get_base_material().get_name()=='M_EX_SurfaceDetail' for i in range(p.mesh.get_num_materials())))
 (out/globals().get('RESULT_FILE','exorcist-dynamics-verification.json')).write_text(json.dumps(s,indent=2))
 print('EX_DYNAMICS_VERIFIED',s['checks'])
def clearance(point,a,b,r):
 delta=b-a;t=max(0,min(1,unreal.MathLibrary.dot_vector_vector(point-a,delta)/max(delta.length_squared(),.001)))
 return (point-(a+delta*t)).length()-r
def tick(dt):
 try:
  s['time']+=dt
  if s['stage']<0:
   if s['time']>.7:
    pp=p.mesh.get_post_process_instance();check('post_process_anim_instance',pp is not None)
    nodes=unreal.KawaiiPhysicsLibrary.collect_kawaii_physics_nodes_from_component(p.mesh,unreal.GameplayTagContainer(),False)
    check('five_secondary_motion_groups',nodes is not None and len(nodes)==5,count=len(nodes) if nodes else 0)
    advance()
   return
  name,duration=stages[s['stage']];age=s['time']
  if name=='idle' and age>.6 and not s.get('thigh_chain_checked'):
   s['thigh_chain_checked']=True
   count,infos,error=unreal.KawaiiPhysicsLibrary.get_runtime_node_infos_on_component(p.mesh,unreal.GameplayTagContainer(),False)
   simulated=[str(b.bone_name) for info in infos for b in info.bones]
   check('thigh_chain_excluded_from_shared_collision',count==5 and not any('Spring_11_thigh_chain' in n for n in simulated),error=error)
  if name in ['jog','run_rear','run_side']:p.add_movement_input(unreal.Vector(1,0,0),1,True)
  if name=='turn':p.add_movement_input(unreal.Vector(0,1,0),1,True)
  if name in ['jump','kick','flurry'] and age>.1 and not s['released']:
   p.inject_control_key({'jump':'SpaceBar','kick':'RightMouseButton','flurry':'E'}[name],False);s['released']=True
  if age>duration*.5 and not s['shot']:shot(name);s['shot']=True
  head=p.mesh.get_socket_transform('head1',unreal.RelativeTransformSpace.RTS_WORLD)
  tip=p.mesh.get_socket_location('hair_3_2_CharakitEnd')
  hair=unreal.MathLibrary.inverse_transform_location(head,tip)
  clear=[]
  roots=[p.mesh.get_socket_location(f'skirt_{i}_1') for i in range(1,9)]
  center=unreal.Vector()
  for root in roots:center+=root/8
  sides=[]
  for i in range(1,9):
   for suffix in ['2','2_CharakitEnd']:
    point=p.mesh.get_socket_location(f'skirt_{i}_{suffix}')
    radial=roots[i-1]-center
    sides.append(unreal.MathLibrary.dot_vector_vector(point-roots[i-1],radial)/max(.001,radial.length()))
    for side in ['L','R']:
     a=p.mesh.get_socket_location('upper_leg_'+side);b=p.mesh.get_socket_location('lower_leg_'+side);d=b-a
     clear.append(clearance(point,a+d*.09,b-d*.09,9.2))
  s['samples'].append(dict(name=name,age=age,hair=[hair.x,hair.y,hair.z],skirt_clearance=min(clear),skirt_side_clearance=min(sides),speed=p.get_velocity().length()))
  if age>duration:
   if s['stage']==len(stages)-1:finish()
   else:advance()
 except Exception as e:check('exception',False,error=repr(e));finish()
p.set_actor_location(unreal.Vector(-1800,-600,98.15),False,True);p.set_actor_rotation(unreal.Rotator(),False)
pc.set_control_rotation(unreal.Rotator(pitch=-8,yaw=145))
unreal._dynamics_verify=unreal.register_slate_post_tick_callback(tick)
