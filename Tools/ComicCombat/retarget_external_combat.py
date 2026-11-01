import unreal
from pathlib import Path
D='/Game/ExorcistV10';at=unreal.AssetToolsHelpers.get_asset_tools();S=unreal.RetargetSourceOrTarget
source=(Path(unreal.Paths.project_dir())/'Tools/ComicCombat/retarget_exorcist.py').read_text(encoding='utf-8')
exec(source[source.index('def make_rig'):source.index('def run(')])

def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._external_retarget)
 registry=unreal.AssetRegistryHelpers.get_asset_registry()
 target=unreal.load_asset(D+'/Character/SK_EX_Game');tr=unreal.load_asset(D+'/Rig/IK_EX')
 for label,folder in [('UAL1',D+'/External/UAL1'),('UAL2',D+'/External/UAL2_Selected'),('KayKit',D+'/External/KayKit_Unarmed')]:
  assets=registry.get_assets_by_path(folder,True)
  meshes=[unreal.load_asset(a.package_name) for a in assets if str(a.asset_class_path.asset_name)=='SkeletalMesh']
  if not meshes:continue
  mesh=meshes[0]
  if label!='KayKit':sr=make_rig('IK_External_'+label,mesh,'quaternius')
  else:
   sr=unreal.load_asset(D+'/Rig/IK_External_KayKit') or at.create_asset('IK_External_KayKit',D+'/Rig',unreal.IKRigDefinition,unreal.IKRigDefinitionFactory())
   c=unreal.IKRigController.get_controller(sr);c.set_skeletal_mesh(mesh)
   for chain in list(c.get_retarget_chains()):c.remove_retarget_chain(chain.chain_name)
   c.set_retarget_root('hips');c.add_retarget_chain('Spine','spine','chest','');c.add_retarget_chain('Neck','head','head','')
   for side in ['l','r']:
    c.add_retarget_chain('Arm_'+side,'upperarm_'+side,'hand_'+side,'')
    c.add_retarget_chain('Leg_'+side,'upperleg_'+side,'foot_'+side,'')
    c.add_retarget_chain('Toe_'+side,'toes_'+side,'toes_'+side,'')
   unreal.EditorAssetLibrary.save_loaded_asset(sr,False)
  name='RTG_External_'+label
  rt=unreal.load_asset(D+'/Rig/'+name) or at.create_asset(name,D+'/Rig',unreal.IKRetargeter,unreal.IKRetargetFactory())
  rc=unreal.IKRetargeterController.get_controller(rt);rc.set_ik_rig(S.SOURCE,sr);rc.set_ik_rig(S.TARGET,tr)
  if not rc.get_num_retarget_ops():rc.add_default_ops()
  rc.auto_map_chains(unreal.AutoMapChainType.EXACT,True);rc.auto_align_all_bones(S.TARGET)
  unreal.EditorAssetLibrary.save_loaded_asset(rt,False)
  i=unreal.IKRetargetBatchOperationInputs();i.assets_to_retarget=[a for a in assets if str(a.asset_class_path.asset_name)=='AnimSequence'];i.source_mesh=mesh;i.target_mesh=target;i.ik_retarget_asset=rt;i.target_path=D+'/Animations/External/'+label;i.include_referenced_assets=False;i.overwrite_existing_files=True
  result=unreal.IKRetargetBatchOperation.run_batch_retarget(i);print('EXTERNAL_RETARGET',label,len(result))
 unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
unreal._external_retarget=unreal.register_slate_post_tick_callback(run)
