"""Repair the actual idle state and keep locomotion evaluating under montage slots."""
import unreal

def run(dt):
    unreal.unregister_slate_post_tick_callback(unreal._repair_anim)
    path='/Game/ExorcistV10/Animations/manny/ABP_CC_Unarmed'
    bp=unreal.load_asset(path)
    backup='/Game/ExorcistV10/BeforeDynamics/ABP_BeforeContinuityFix'
    if not unreal.EditorAssetLibrary.does_asset_exist(backup):
        unreal.EditorAssetLibrary.duplicate_asset(path,backup)
    idle=unreal.load_asset('/Game/ExorcistV10/Animations/manny/A_EX_CombatIdle')
    count=0
    for graph in bp.get_animation_graphs():
        for n in graph.get_graph_nodes_of_class(unreal.load_class(None,'/Script/AnimGraph.AnimGraphNode_Slot')):
            node=n.get_editor_property('node')
            node.set_editor_property('always_update_source_pose',True)
            n.set_editor_property('node',node)
            count+=1
        for n in graph.get_graph_nodes_of_class(unreal.load_class(None,'/Script/AnimGraph.AnimGraphNode_SequencePlayer')):
            if '.Idle.' in n.get_path_name():
                node=n.get_editor_property('node')
                node.set_editor_property('sequence',idle)
                n.set_editor_property('node',node)
                count+=1
    assert count==2, count
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
    print('ANIMATION_CONNECTIONS_REPAIRED',count)

unreal._repair_anim=unreal.register_slate_post_tick_callback(run)
