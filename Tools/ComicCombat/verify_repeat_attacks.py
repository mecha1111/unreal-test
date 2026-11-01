"""Repeated same-button inputs; check actual pose continuity at montage handoffs."""
import unreal,json
from pathlib import Path
w=unreal.EditorLevelLibrary.get_game_world();p=unreal.GameplayStatics.get_player_character(w,0)
pc=unreal.GameplayStatics.get_player_controller(w,0)
p.set_automation_input_isolation(True)
p.set_actor_location(unreal.Vector(-1800,-1300,98.15),False,True)
p.set_actor_rotation(unreal.Rotator(),False);pc.set_control_rotation(unreal.Rotator(pitch=-12,yaw=0))
s={'t':0,'stage':0,'start':p.attack_count,'last_count':p.attack_count,'next':.2,'release':-1,'variants':set(),'handoffs':[],'checks':[],'prev':None}
bones=['hips','hand_L','hand_R','foot_L','foot_R']
def finish():
    p.inject_control_key('LeftMouseButton',False);p.inject_control_key('RightMouseButton',False)
    p.set_automation_input_isolation(False);unreal.unregister_slate_post_tick_callback(unreal._repeat_verify)
    s['variants']=list(s['variants']);s['prev']=None
    Path(r'C:/Users/jooan/Documents/Codex/2026-10-25/x20/outputs/repeat-attacks.json').write_text(json.dumps(s,indent=2))
    print('REPEAT_ATTACKS_DONE',s['checks'])
def tick(dt):
    try:
        s['t']+=dt;t=s['t'];key='LeftMouseButton' if s['stage']==0 else 'RightMouseButton'
        if s['release']>0 and t>=s['release']:p.inject_control_key(key,False);s['release']=-1
        if t>=s['next'] and t<3.8:
            p.inject_control_key(key,True);s['release']=t+.035;s['next']=t+.12
        pos={b:p.mesh.get_socket_location(b) for b in bones}
        if p.attack_count>s['last_count']:
            if s['prev'] is not None:
                distance=max((pos[b]-s['prev'][b]).length() for b in bones)
                s['handoffs'].append(dict(stage=s['stage'],time=t,dt=dt,max_joint_delta_cm=distance))
            s['last_count']=p.attack_count
        s['prev']=pos
        if p.attacking:s['variants'].add(p.get_attack_variant())
        if t>4.9:
            count=p.attack_count-s['start'];changes=[r for r in s['handoffs'] if r['stage']==s['stage'] and r['dt']<.06]
            worst=max((r['max_joint_delta_cm'] for r in changes),default=999)
            s['checks'].append(dict(test=key+'_repeat_count',passed=count>=(7 if s['stage']==0 else 4),count=count))
            s['checks'].append(dict(test=key+'_pose_handoffs',passed=bool(changes) and worst<25,max_joint_delta_cm=worst))
            s['checks'].append(dict(test=key+'_returns_to_locomotion',passed=not p.attacking and p.mesh.get_anim_instance().get_current_active_montage() is None))
            if s['stage']==0:
                s['checks'].append(dict(test='light_attack_variation',passed={0,1,2}.issubset(s['variants'])))
                s.update(t=0,stage=1,start=p.attack_count,next=.2,release=-1,prev=None)
            else:finish()
    except Exception as e:
        s['checks'].append(dict(test='exception',passed=False,error=repr(e)));finish()
unreal._repeat_verify=unreal.register_slate_post_tick_callback(tick)
