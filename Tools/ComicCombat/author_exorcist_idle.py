"""Restore original standing motion; prefer its sole-calibrated derivative when present."""
import unreal
from pathlib import Path
ROOT='/Game/ExorcistV10/Animations/manny/'
def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._ex_idle)
 idle=unreal.load_asset(ROOT+'A_EX_GroundedIdle') if unreal.EditorAssetLibrary.does_asset_exist(ROOT+'A_EX_GroundedIdle') else unreal.load_asset(ROOT+'MM_Idle')
 bp=unreal.load_asset(ROOT+'ABP_CC_Unarmed')
 for graph in bp.get_animation_graphs():
  for n in graph.get_graph_nodes_of_class(unreal.load_class(None,'/Script/AnimGraph.AnimGraphNode_SequencePlayer')):
   if '.Idle.' in n.get_path_name():
    node=n.get_editor_property('node');node.set_editor_property('sequence',idle);n.set_editor_property('node',node)
 bs=unreal.load_asset(ROOT+'BS_Idle_Walk_Run');samples=list(bs.get_editor_property('sample_data'))
 for sample in samples:
  if sample.get_editor_property('sample_value').y==0:sample.set_editor_property('animation',idle)
 bs.set_editor_property('sample_data',samples)
 unreal.CombatAuthoringLibrary.rebuild_blend_space(bs)
 unreal.BlueprintEditorLibrary.compile_blueprint(bp)
 unreal.EditorAssetLibrary.save_loaded_asset(bs,False);unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
 print('ORIGINAL_STANCE_ANIMATION_RESTORED',idle.get_path_name(),idle.get_play_length())
unreal._ex_idle=unreal.register_slate_post_tick_callback(run)
