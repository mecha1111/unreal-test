"""Exercise wheel input through the controller, including during an attack."""
import unreal,json
from pathlib import Path
w=unreal.EditorLevelLibrary.get_game_world();p=unreal.GameplayStatics.get_player_character(w,0)
pc=unreal.GameplayStatics.get_player_controller(w,0)
arm=p.get_component_by_class(unreal.SpringArmComponent)
p.set_automation_input_isolation(True)
initial=arm.target_arm_length
checks=[]
def wheel(key,count):
 for i in range(count):p.inject_control_key(key,True);p.inject_control_key(key,False)
wheel('MouseScrollUp',60)
checks.append(dict(test='close_limit_150',passed=abs(arm.target_arm_length-150)<.01,value=arm.target_arm_length))
wheel('MouseScrollDown',60)
checks.append(dict(test='far_limit_1100',passed=abs(arm.target_arm_length-1100)<.01,value=arm.target_arm_length))
p.inject_control_key('LeftMouseButton',True)
s={'age':0,'zoomed':False}
def tick(dt):
 s['age']+=dt
 if s['age']>.08 and not s['zoomed']:
  p.inject_control_key('LeftMouseButton',False)
  wheel('MouseScrollUp',4)
  checks.append(dict(test='wheel_during_attack',passed=p.attacking and abs(arm.target_arm_length-940)<.01,value=arm.target_arm_length))
  s['zoomed']=True
 if s['age']>1.2:
  checks.append(dict(test='combat_does_not_reset_zoom',passed=abs(arm.target_arm_length-940)<.01,value=arm.target_arm_length))
  arm.target_arm_length=initial;p.set_automation_input_isolation(False)
  unreal.unregister_slate_post_tick_callback(unreal._zoom_verify)
  Path(r'C:/Users/jooan/Documents/Codex/2026-10-25/x20/outputs/camera-zoom-verification.json').write_text(json.dumps(checks,indent=2))
  print('ZOOM_VERIFIED',checks)
unreal._zoom_verify=unreal.register_slate_post_tick_callback(tick)
