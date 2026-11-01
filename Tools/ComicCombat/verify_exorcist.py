import unreal,time,json
from pathlib import Path
out=Path(r'C:\Users\jooan\Documents\Codex\2026-10-25\x20\outputs')
w=unreal.EditorLevelLibrary.get_game_world();p=unreal.GameplayStatics.get_player_character(w,0);pc=unreal.GameplayStatics.get_player_controller(w,0)
p.set_automation_input_isolation(True)
s={'t':unreal.GameplayStatics.get_time_seconds(w),'phase':0,'keys':{},'checks':[],'heights':[],'shot':False}
def check(name,ok,**kw):s['checks'].append(dict(test=name,passed=bool(ok),**kw))
def press(k,hold=.14):p.inject_control_key(k,True);s['keys'][k]=unreal.GameplayStatics.get_time_seconds(w)+hold
def shot(name):unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x720 filename='+str(out/('exorcist-'+name+'.png')).replace('\\','/'))
def place(x=-125,y=0,yaw=0):
 p.character_movement.stop_movement_immediately();p.set_actor_location(unreal.Vector(x,y,98),False,True);p.set_actor_rotation(unreal.Rotator(),False);pc.set_control_rotation(unreal.Rotator(pitch=-12,yaw=yaw,roll=0))
def advance():s['phase']+=1;s['t']=unreal.GameplayStatics.get_time_seconds(w);s['shot']=False
def finish():
 for k in list(s['keys']):p.inject_control_key(k,False)
 p.set_automation_input_isolation(False);unreal.unregister_slate_post_tick_callback(unreal._ex_verify)
 (out/'exorcist-verification.json').write_text(json.dumps(s['checks'],ensure_ascii=False,indent=2),encoding='utf-8');print('EX_VERIFICATION_COMPLETE',s['checks'])
place(-650,-600,150)
def tick(dt):
 try:
  now=unreal.GameplayStatics.get_time_seconds(w);age=now-s['t'];phase=s['phase']
  for k,t in list(s['keys'].items()):
   if now>=t:p.inject_control_key(k,False);del s['keys'][k]
  if phase==0 and age>.8 and not s['shot']:
   check('exorcist_mesh','SK_EX_' in p.mesh.get_skinned_asset().get_name());check('smooth_mesh',p.mesh.get_class().get_name()=='SkeletalMeshComponent' and p.display_pose_fps==0)
   check('materials',all(p.mesh.get_material(i) for i in range(p.mesh.get_num_materials())))
   master=unreal.load_asset('/Game/ExorcistV10/Materials/M_EX_Surface')
   check('persistent_morph_material_usage',master.get_editor_property('bUsedWithMorphTargets') and master.get_editor_property('bUsedWithSkeletalMesh'))
   check('no_persistent_camera_shader',all(x.weight==0 for x in p.get_component_by_class(unreal.CameraComponent).post_process_settings.weighted_blendables.array))
   shot('standing-final');s['shot']=True
  elif phase==0 and age>1.05:
   place(-1800,-600);press('W',1.5);press('LeftShift',1.1);advance()
  elif phase==1:
   if age>.25:s['heights'].append([p.mesh.get_socket_location('head1').z,p.mesh.get_socket_location('foot_L').z,p.mesh.get_socket_location('foot_R').z,p.get_actor_location().z,p.mesh.get_socket_location('hips').z])
   if age>.65 and not s['shot']:shot('running-final');s['shot']=True
   if age>1.8:
    # A sprint leans the head down legitimately. Check capsule/pelvis/foot clearance,
    # rather than requiring the head to stay at the previous animation's height.
    check('run_stays_above_ground',min(x[4] for x in s['heights'])>75 and min(x[3] for x in s['heights'])>90 and min(min(x[1:3]) for x in s['heights'])>8,min_head=min(x[0] for x in s['heights']),min_pelvis=min(x[4] for x in s['heights']),min_foot=min(min(x[1:3]) for x in s['heights']))
    check('run_hold_release',not p.running and p.character_movement.max_walk_speed==280)
    fx=p.get_component_by_class(unreal.ComicCombatPresentationComponent)
    check('footstep_vfx_at_ground',fx.get_editor_property('FootPlantCount')>0 and abs(fx.get_editor_property('LastFootPlant').z-2)<4,count=fx.get_editor_property('FootPlantCount'),z=fx.get_editor_property('LastFootPlant').z)
    place();s['hits']=p.hit_count;press('E');advance()
  elif phase==2:
   if age>.22 and not s['shot']:
    pc.set_control_rotation(unreal.Rotator(pitch=-8,yaw=60,roll=0));s['shot']=True
   if age>.42 and 'camera_test' not in s:
    cam=p.get_component_by_class(unreal.CameraComponent);boom=p.get_component_by_class(unreal.SpringArmComponent)
    check('camera_free_during_attack',abs(cam.get_world_rotation().yaw-pc.get_control_rotation().yaw)<2 and abs(boom.socket_offset.y-25)<.1,camera_yaw=cam.get_world_rotation().yaw,control_yaw=pc.get_control_rotation().yaw)
    face=p.get_component_by_class(unreal.ExorcistFaceComponent);check('attack_expression',face.expression_intensity>.3,value=face.expression_intensity)
    s['camera_test']=True;shot('punch-final')
   if age>3:
    check('flurry_five_hits',p.hit_count-s['hits']==5,hits=p.hit_count-s['hits']);place();s['charge_before']=p.ultimate_charge;press('V');advance()
  elif phase==3 and age>1.15:place();press('V');advance()
  elif phase==4 and age>1.15:
   check('seven_hits_fill_ultimate',p.ultimate_charge==100,charge=p.ultimate_charge);place();press('Q');advance()
  elif phase==5:
   if age>.4 and not s['shot']:check('ultimate_active',p.attacking and p.get_attack_variant()==5 and p.ultimate_charge==0);shot('ultimate-charge-final');s['shot']=True
   if age>3:place(-650,-600);press('B');advance()
  elif phase==6:
   if age>.36 and not s['shot']:shot('kick-final');s['shot']=True
   if age>1.4:press('SpaceBar');advance()
  elif phase==7 and age>.25:press('SpaceBar');advance()
  elif phase==8 and age>2.1:
   check('double_jump_lands',not p.character_movement.is_falling() and p.get_actor_location().z>90)
   check('training_targets_unchanged',all(a.get_component_by_class(unreal.SkeletalMeshComponent).get_skinned_asset().get_name()=='SKM_Manny_Simple' for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.PlaygroundTarget)))
   finish()
 except Exception as e:check('exception',False,error=repr(e));finish()
unreal._ex_verify=unreal.register_slate_post_tick_callback(tick)
