import unreal
D='/Game/ExorcistV10/Animations/manny/'
def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._ex_locomotion)
 bs=unreal.load_asset(D+'BS_Idle_Walk_Run')
 backup='/Game/ExorcistV10/BeforeDynamics/BS_Idle_Walk_Run'
 if not unreal.EditorAssetLibrary.does_asset_exist(backup):unreal.EditorAssetLibrary.duplicate_asset(bs.get_path_name(),backup)
 params=list(bs.get_editor_property('blend_parameters'))
 params[1].set_editor_property('max',800);params[1].set_editor_property('grid_num',8);params[1].set_editor_property('snap_to_grid',False)
 bs.set_editor_property('blend_parameters',params)
 samples=[]
 for speed,clip,rate in [(0,'A_EX_CombatIdle',1),(180,'MM_Walk_Fwd',1),(480,'MM_Run_Fwd',1),(800,'MM_Sprint',1.05)]:
  anim=unreal.load_asset(D+clip);assert anim,clip
  for direction in range(-180,181,45):
   sample=unreal.BlendSample();sample.set_editor_property('animation',anim);sample.set_editor_property('sample_value',unreal.Vector(direction,speed,0));sample.set_editor_property('rate_scale',rate)
   samples.append(sample)
 bs.set_editor_property('sample_data',samples)
 assert unreal.CombatAuthoringLibrary.rebuild_blend_space(bs)
 unreal.EditorAssetLibrary.save_loaded_asset(bs,False)
 print('EX_LOCOMOTION_DONE',len(samples))
unreal._ex_locomotion=unreal.register_slate_post_tick_callback(run)
