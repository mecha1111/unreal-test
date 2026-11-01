import unreal
D='/Game/ExorcistV10';at=unreal.AssetToolsHelpers.get_asset_tools();S=unreal.RetargetSourceOrTarget
def make_rig(name,mesh,kind):
 asset=unreal.load_asset(D+'/Rig/'+name) or at.create_asset(name,D+'/Rig',unreal.IKRigDefinition,unreal.IKRigDefinitionFactory())
 c=unreal.IKRigController.get_controller(asset);c.set_skeletal_mesh(mesh)
 for chain in list(c.get_retarget_chains()):c.remove_retarget_chain(chain.chain_name)
 ex=kind=='ex';c.set_retarget_root('hips' if ex else 'pelvis')
 chains=[('Spine','spine','chest') if ex else ('Spine','spine_01','spine_05' if kind=='manny' else 'spine_03'),('Neck','neck','head1') if ex else ('Neck','neck_01','head' if kind=='manny' else 'Head')]
 for side in ['l','r']:
  suffix=side.upper()
  chains.extend([(f'Clavicle_{side}',f'shoulder_{suffix}',f'shoulder_{suffix}'),(f'Arm_{side}',f'upper_arm_{suffix}',f'hand_{suffix}'),(f'Leg_{side}',f'upper_leg_{suffix}',f'foot_{suffix}'),(f'Toe_{side}',f'toes_{suffix}',f'toes_{suffix}')] if ex else [(f'Clavicle_{side}',f'clavicle_{side}',f'clavicle_{side}'),(f'Arm_{side}',f'upperarm_{side}',f'hand_{side}'),(f'Leg_{side}',f'thigh_{side}',f'foot_{side}'),(f'Toe_{side}',f'ball_{side}',f'ball_{side}')])
  for finger in ['thumb','index','middle','ring','pinky']:
   f='little' if finger=='pinky' else finger
   chains.append((f'{finger}_{side}',f'{f}_proximal_{suffix}',f'{f}_distal_{suffix}') if ex else (f'{finger}_{side}',f'{finger}_01_{side}',f'{finger}_03_{side}'))
 for name,start,end in chains:c.add_retarget_chain(name,start,end,'')
 unreal.EditorAssetLibrary.save_loaded_asset(asset);return asset
def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._ex_retarget)
 target=unreal.load_asset(D+'/Character/SK_EX_Game')
 tr=make_rig('IK_EX',target,'ex')
 for kind,meshpath,folder,name in [('manny','/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple','/Game/ComicCombat/Animations','RTG_Manny_EX'),('quaternius',D+'/AnimationSource/SK_Quaternius',D+'/AnimationSource','RTG_Quaternius_EX')]:
  source=unreal.load_asset(meshpath);sr=make_rig('IK_'+kind,source,kind)
  rt=unreal.load_asset(D+'/Rig/'+name) or at.create_asset(name,D+'/Rig',unreal.IKRetargeter,unreal.IKRetargetFactory())
  rc=unreal.IKRetargeterController.get_controller(rt);rc.set_ik_rig(S.SOURCE,sr);rc.set_ik_rig(S.TARGET,tr)
  if rc.get_num_retarget_ops()==0:rc.add_default_ops()
  rc.auto_map_chains(unreal.AutoMapChainType.EXACT,True);rc.auto_align_all_bones(S.TARGET)
  unreal.EditorAssetLibrary.save_loaded_asset(rt)
  assets=[]
  for a in unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_path(folder,recursive=True):
   if str(a.asset_class_path.asset_name) in ['AnimSequence','AnimBlueprint','BlendSpace','BlendSpace1D']:assets.append(a)
  inputs=unreal.IKRetargetBatchOperationInputs();inputs.assets_to_retarget=assets;inputs.source_mesh=source;inputs.target_mesh=target;inputs.ik_retarget_asset=rt;inputs.target_path=D+'/Animations/'+kind;inputs.include_referenced_assets=True;inputs.overwrite_existing_files=True
  result=unreal.IKRetargetBatchOperation.run_batch_retarget(inputs);print('RETARGETED',kind,len(result))
 unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
unreal._ex_retarget=unreal.register_slate_post_tick_callback(run)
