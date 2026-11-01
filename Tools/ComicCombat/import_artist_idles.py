"""Retarget the existing licensed KayKit full-body idle animations, without pose generation."""
import unreal
from pathlib import Path
def run(dt):
    unreal.unregister_slate_post_tick_callback(unreal._artist_idle_import)
    folder='/Game/ExorcistV10/External/KayKitIdle'
    task=unreal.AssetImportTask()
    task.filename=str(Path(unreal.Paths.project_dir())/'SourceArt/ExternalCombat/KayKit_Idles.glb')
    task.destination_path=folder;task.automated=True;task.save=True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    assets=registry.get_assets_by_path(folder,True)
    mesh=next(unreal.load_asset(a.package_name) for a in assets if str(a.asset_class_path.asset_name)=='SkeletalMesh')
    i=unreal.IKRetargetBatchOperationInputs()
    i.assets_to_retarget=[a for a in assets if str(a.asset_class_path.asset_name)=='AnimSequence']
    i.source_mesh=mesh
    i.target_mesh=unreal.load_asset('/Game/ExorcistV10/Character/SK_EX_Game')
    i.ik_retarget_asset=unreal.load_asset('/Game/ExorcistV10/Rig/RTG_External_KayKit')
    i.target_path='/Game/ExorcistV10/Animations/External/KayKitIdle'
    i.include_referenced_assets=False;i.overwrite_existing_files=True
    result=unreal.IKRetargetBatchOperation.run_batch_retarget(i)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
    print('ARTIST_IDLES_IMPORTED',result)
unreal._artist_idle_import=unreal.register_slate_post_tick_callback(run)
