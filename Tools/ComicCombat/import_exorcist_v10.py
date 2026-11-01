import unreal,json
from pathlib import Path
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
DEST='/Game/ExorcistV10'
def import_assets(dt):
 unreal.unregister_slate_post_tick_callback(unreal._ex_import)
 unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 try:
  task=unreal.AssetImportTask();task.filename=str(ROOT/'SourceArt/ExorcistV10/SK_EX_Game.fbx');task.destination_path=DEST+'/Character';task.destination_name='SK_EX_Game';task.automated=True;task.save=True;task.replace_existing=True
  opts=unreal.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=True;opts.import_animations=False;opts.import_materials=False;opts.import_textures=False;opts.create_physics_asset=True
  opts.set_editor_property('automated_import_should_detect_type',False);opts.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH
  opts.skeletal_mesh_import_data.set_editor_property('import_morph_targets',True)
  opts.skeletal_mesh_import_data.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
  opts.skeletal_mesh_import_data.set_editor_property('import_meshes_in_bone_hierarchy',True)
  opts.skeletal_mesh_import_data.convert_scene=True
  opts.skeletal_mesh_import_data.convert_scene_unit=True
  opts.skeletal_mesh_import_data.force_front_x_axis=False
  task.options=opts
  unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
  print('EXORCIST_IMPORTED',task.imported_object_paths)
 finally:unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 1')
unreal._ex_import=unreal.register_slate_post_tick_callback(import_assets)



