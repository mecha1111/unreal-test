import unreal,json,time
from pathlib import Path
OUT=Path(r'C:\Users\jooan\Documents\Codex\2026-10-25\x20\outputs')
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
p=unreal.GameplayStatics.get_player_character(w,0);pc=unreal.GameplayStatics.get_player_controller(w,0)
c=p.get_component_by_class(unreal.ComicCombatPresentationComponent)
targets=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.PlaygroundTarget)
tests=[
 ('rising_combo',(-125,0,100),[(0,'LeftMouseButton'),(.10,'LeftMouseButton'),(.30,'RightMouseButton')],3.0,3),
 ('cancel_charge',(-500,0,100),[(0,'Q'),(.22,'LeftControl')],1.8,1),
 ('wide_ultimate',(-600,-260,100),[(0,'Q')],2.8,1),
 ('repeat_ultimate',(-600,-260,100),[(0,'Q')],2.8,1),
 ('behind_whiff',(1000,0,100),[(0,'Q')],2.3,1),
 ('flurry',(-125,0,100),[(0,'E')],2.2,1),
 ('flurry_cancel',(-125,0,100),[(0,'E'),(.40,'LeftControl')],2.0,1),
 ('jump_cancel',(-500,0,100),[(0,'Q'),(.2,'SpaceBar')],1.8,1),
 ('combo_milestone',(-125,0,100),[(0,'E'),(1.55,'LeftMouseButton')],3.0,2),
 ('cancel_slow',(-500,0,100),[(0,'Q')],2.2,1),
 ('run_footplants',(-900,-800,100),[(0,'W'),(0,'LeftShift')],1.5,0)
]
state={'i':0,'phase':'reset','results':[],'keys':{},'cancel_slow_sent':False}
def press(key):
 p.inject_control_key(key,True)
 if key not in ['W','LeftShift']:state['keys'][key]=time.monotonic()+.035
def cleanup():
 for key in ['W','LeftShift','LeftMouseButton','RightMouseButton','Q','E','LeftControl','SpaceBar']:p.inject_control_key(key,False)
 unreal.GameplayStatics.set_global_time_dilation(w,1.0)
def finish():
 cleanup();unreal.unregister_slate_post_tick_callback(unreal._combat_v9_test)
 (OUT/'combat-v9-verification.json').write_text(json.dumps(state['results'],indent=2),encoding='utf-8')
 print('V9_TEST_COMPLETE',state['results'])
def tick(dt):
 try:
  if state['i']>=len(tests):finish();return
  name,pos,events,duration,expected_attacks=tests[state['i']];now=time.monotonic()
  for key,until in list(state['keys'].items()):
   if now>=until:p.inject_control_key(key,False);del state['keys'][key]
  if state['phase']=='reset':
   cleanup();press('LeftControl')
   p.set_actor_location(unreal.Vector(*pos),False,False);p.character_movement.stop_movement_immediately()
   pc.set_control_rotation(unreal.Rotator(pitch=-12,yaw=0,roll=0))
   # Reset follows real cancel and combo timeout.
   state.update(phase='settle',t=now);return
  if state['phase']=='settle':
   if now-state['t']<2.3:return
   state.update(phase='play',t=now,sent=0,a=p.attack_count,h=p.hit_count,c=p.cancel_count,foot=c.get_editor_property('FootPlantCount'),variants=[],slow=False,min_time=1.0,max_z=p.get_actor_location().z,max_enemy_z=96,contacts=[],max_speed=0,feet=[],cancel_slow_sent=False,hit_events=[])
  age=now-state['t']
  while state['sent']<len(events) and age>=events[state['sent']][0]:
   press(events[state['sent']][1]);state['sent']+=1
  dilation=unreal.GameplayStatics.get_global_time_dilation(w)
  state['min_time']=min(state['min_time'],dilation)
  if dilation<.9:state['slow']=True
  if name=='cancel_slow' and dilation<.9 and not state['cancel_slow_sent']:
   press('LeftControl');state['cancel_slow_sent']=True
  if p.attacking:
   variant=p.get_attack_variant()
   if not state['variants'] or state['variants'][-1]!=variant:state['variants'].append(variant)
  state['max_z']=max(state['max_z'],p.get_actor_location().z)
  state['max_enemy_z']=max(state['max_enemy_z'],*[a.get_actor_location().z for a in targets])
  state['max_speed']=max(state['max_speed'],p.get_velocity().length())
  if p.hit_count-state['h']>len(state['hit_events']):state['hit_events'].append(age);state['contacts'].append(list(p.last_contact_point.to_tuple()))
  if name=='run_footplants':state['feet'].append([age,p.mesh.get_socket_location('foot_l').z,p.mesh.get_socket_location('foot_r').z,c.get_editor_property('FootPlantCount')])
  if age<duration:return
  hits=p.hit_count-state['h'];attacks=p.attack_count-state['a'];cancels=p.cancel_count-state['c']
  ok=attacks==expected_attacks
  if name=='rising_combo':ok &= state['variants']==[0,1,7] and hits==3 and state['max_enemy_z']>280 and state['slow']
  if name in ['wide_ultimate','repeat_ultimate']:ok &= hits>=1 and p.get_ultimate_cooldown()==0 and state['slow']
  if name in ['behind_whiff','cancel_charge','jump_cancel']:ok &= hits==0
  if name in ['cancel_charge','jump_cancel']:ok &= cancels==1
  if name=='jump_cancel':ok &= state['max_z']>180
  if name=='flurry':ok &= hits==5
  if name=='flurry_cancel':ok &= 1<=hits<=2 and cancels==1
  if name=='combo_milestone':ok &= hits==6 and state['slow']
  if name=='cancel_slow':ok &= state['cancel_slow_sent'] and cancels==1
  if name=='run_footplants':ok &= c.get_editor_property('FootPlantCount')-state['foot']>=3 and state['max_speed']>700
  ok &= abs(dilation-1)<.001
  result={'test':name,'passed':bool(ok),'hits':hits,'attacks':attacks,'cancels':cancels,'variants':state['variants'],'minimum_time_scale':state['min_time'],'final_time_scale':dilation,'max_player_z':state['max_z'],'max_target_z':state['max_enemy_z'],'max_speed':state['max_speed'],'footplants':c.get_editor_property('FootPlantCount')-state['foot'],'contacts':state['contacts'],'hit_times':state['hit_events']}
  if name=='run_footplants':result['foot_samples']=state['feet']
  state['results'].append(result)
  (OUT/'combat-v9-verification.json').write_text(json.dumps(state['results'],indent=2),encoding='utf-8')
  print('V9_RESULT',name,ok,hits,attacks)
  state.update(i=state['i']+1,phase='reset')
 except Exception as e:
  state['results'].append({'error':repr(e),'passed':False});finish()
unreal._combat_v9_test=unreal.register_slate_post_tick_callback(tick)
print('V9_TEST_STARTED')
