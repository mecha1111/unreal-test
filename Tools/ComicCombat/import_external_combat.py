import unreal
from pathlib import Path
def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._external_import)
 base=Path(unreal.Paths.project_dir()).resolve()/'SourceArt/ExternalCombat'
 for name,folder in [('UAL1_Selected','UAL1'),('UAL2_Selected','UAL2_Selected'),('KayKit_Unarmed','KayKit_Unarmed')]:
  t=unreal.AssetImportTask();t.filename=str(base/(name+'.glb'));t.destination_path='/Game/ExorcistV10/External/'+folder;t.automated=True;t.save=True
  unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
  print('EXTERNAL_IMPORT',name,len(t.imported_object_paths))
unreal._external_import=unreal.register_slate_post_tick_callback(run)
