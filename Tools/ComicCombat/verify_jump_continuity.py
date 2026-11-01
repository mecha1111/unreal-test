"""Actual input: sprint -> jump -> landing; record rendered foot poses, not speed alone."""
import unreal,json
from pathlib import Path
w=unreal.EditorLevelLibrary.get_game_world()
p=unreal.GameplayStatics.get_player_character(w,0)
a=p.mesh.get_anim_instance()
p.set_automation_input_isolation(True)
p.set_actor_location(unreal.Vector(-2500,-1600,98.15),False,True)
p.inject_control_key('LeftShift',True)
s={'t':0,'rows':[],'keys':{},'events':set(),'checks':[],'landings':[],'was_falling':False}
def press(key):
    p.inject_control_key(key,True);s['keys'][key]=s['t']+.07
def tick(dt):
    try:
        s['t']+=dt;t=s['t']
        p.add_movement_input(unreal.Vector(1,0,0),1,True)
        for when in [.7,3.5,3.85]:
            if t>=when and when not in s['events']:
                press('SpaceBar');s['events'].add(when)
        for k,end in list(s['keys'].items()):
            if t>end:p.inject_control_key(k,False);del s['keys'][k]
        falling=p.character_movement.is_falling()
        if s['was_falling'] and not falling:s['landings'].append(t)
        s['was_falling']=falling
        m=a.get_current_active_montage()
        s['rows'].append(dict(t=t,fall=falling,speed=p.get_velocity().length(),
            main=str(unreal.CombatAuthoringLibrary.get_animation_state(p.mesh,'Main States')),
            locomotion=str(unreal.CombatAuthoringLibrary.get_animation_state(p.mesh,'Locomotion')),
            montage=m.get_name() if m else None,
            footL=p.mesh.get_socket_location('foot_L').z,footR=p.mesh.get_socket_location('foot_R').z))
        if t>6:
            for i,land in enumerate(s['landings']):
                rows=[r for r in s['rows'] if land+.25<r['t']<land+.8]
                s['checks'].append(dict(test='landing_'+str(i)+'_running_pose',passed=bool(rows) and all(r['montage'] is None and r['locomotion']=='Walk / Run' for r in rows)))
                span=max((r['footL'] for r in rows),default=0)-min((r['footL'] for r in rows),default=0)
                s['checks'].append(dict(test='landing_'+str(i)+'_animated_stride',passed=span>20,foot_height_span_cm=span))
            s['checks'].append(dict(test='single_and_double_jump_land',passed=len(s['landings'])==2,count=len(s['landings'])))
            p.inject_control_key('LeftShift',False);p.set_automation_input_isolation(False)
            unreal.unregister_slate_post_tick_callback(unreal._jump_continuity)
            s['events']=list(s['events'])
            Path(r'C:/Users/jooan/Documents/Codex/2026-10-25/x20/outputs/jump-continuity.json').write_text(json.dumps(s,indent=2))
            print('JUMP_CONTINUITY_DONE',s['checks'])
    except Exception as e:
        p.inject_control_key('LeftShift',False);p.set_automation_input_isolation(False)
        unreal.unregister_slate_post_tick_callback(unreal._jump_continuity);print('JUMP_CONTINUITY_ERROR',repr(e))
unreal._jump_continuity=unreal.register_slate_post_tick_callback(tick)
