"""Six-hit combo and L/L/R rising attacks must not activate fullscreen highlights."""
import unreal,json
from pathlib import Path
w=unreal.EditorLevelLibrary.get_game_world();p=unreal.GameplayStatics.get_player_character(w,0)
p.set_automation_input_isolation(True)
cam=p.get_component_by_class(unreal.CameraComponent)
s={'t':unreal.GameplayStatics.get_time_seconds(w),'stage':0,'checks':[],'keys':{},'combo_flash':False,'rise_flash':False,'rising':False}
def press(key):
 p.inject_control_key(key,True);s['keys'][key]=unreal.GameplayStatics.get_time_seconds(w)+.06
def place():
 p.character_movement.stop_movement_immediately();p.set_actor_location(unreal.Vector(-125,0,98.15),False,True);p.set_actor_rotation(unreal.Rotator(),False)
def check(n,v,**d):s['checks'].append(dict(test=n,passed=bool(v),**d))
def tick(dt):
 try:
  now=unreal.GameplayStatics.get_time_seconds(w);age=now-s['t']
  for k,t in list(s['keys'].items()):
   if now>=t:p.inject_control_key(k,False);del s['keys'][k]
  active=any(e.weight>0 and isinstance(e.object,unreal.MaterialInterface) and e.object.get_base_material().get_name()=='M_CC_HighlightOnly' for e in cam.post_process_settings.weighted_blendables.array)
  if s['stage']==0:
   if age>.2 and not s.get('e'):place();press('E');s['e']=True
   if age>1.9 and not s.get('jab'):press('LeftMouseButton');s['jab']=True
   if active:s['combo_flash']=True
   if p.combo_hit_count>=6:s['six_hits']=True
   if age>3.5:
    check('six_hit_combo_without_fullscreen_flash',s.get('six_hits',False) and not s['combo_flash'],combo=p.combo_hit_count)
    s['stage']=1;s['t']=now;place()
  elif s['stage']==1:
   for time,key,flag in [(.3,'LeftMouseButton','l1'),(.57,'LeftMouseButton','l2'),(.89,'RightMouseButton','r')]:
    if age>time and not s.get(flag):press(key);s[flag]=True
   if p.get_attack_variant()==7 and p.attacking:s['rising']=True
   if p.get_attack_variant()==7 and active:s['rise_flash']=True
   if age>2:
    check('left_left_right_rising_attack',s['rising']);check('rising_hit_without_fullscreen_flash',not s['rise_flash'])
    check('normal_time_during_highlight',unreal.GameplayStatics.get_global_time_dilation(w)==1)
    check('highlight_expires',not active)
    p.set_automation_input_isolation(False);unreal.unregister_slate_post_tick_callback(unreal._extra_highlights)
    Path(r'C:\Users\jooan\Documents\Codex\2026-10-25\x20\outputs\combat-highlight-verification.json').write_text(json.dumps(s['checks'],indent=2))
    print('EXTRA_HIGHLIGHTS_VERIFIED',s['checks'])
 except Exception as e:
  unreal.unregister_slate_post_tick_callback(unreal._extra_highlights);p.set_automation_input_isolation(False);print('HIGHLIGHT_TEST_ERROR',repr(e))
unreal._extra_highlights=unreal.register_slate_post_tick_callback(tick)
