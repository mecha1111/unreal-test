import unreal
def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._ex_connect)
 root='/Game/ExorcistV10/Animations/'
 b=unreal.load_asset(root+'manny/BS_Idle_Walk_Run')
 source=unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run')
 samples=list(source.get_editor_property('sample_data'))
 for sample in samples:
  v=sample.get_editor_property('sample_value')
  sample.set_editor_property('animation',unreal.load_asset(root+'manny/'+sample.get_editor_property('animation').get_name()))
 b.set_editor_property('sample_data',samples)
 unreal.EditorAssetLibrary.save_loaded_asset(b,False)
 bp=unreal.load_asset(root+'manny/ABP_CC_Unarmed')
 for graph in bp.get_animation_graphs():
  rigs=graph.get_graph_nodes_of_class(unreal.load_class(None,'/Script/ControlRigDeveloper.AnimGraphNode_ControlRig'))
  for rig in rigs:
   pins={str(p.get_pin_name()):p for p in rig.list_all_pins()}
   ins=pins['Source'].list_connected_pins();outs=pins['Pose'].list_connected_pins()
   if ins and outs:
    pins['Source'].break_pin_links();pins['Pose'].break_pin_links()
    for out in outs:assert ins[0].try_create_connection(out)
 unreal.BlueprintEditorLibrary.compile_blueprint(bp)
 unreal.EditorAssetLibrary.save_loaded_asset(bp)
 print('EX_CONNECT_OK: retargeted Epic locomotion; EX combat graph without Manny IK')
unreal._ex_connect=unreal.register_slate_post_tick_callback(run)
