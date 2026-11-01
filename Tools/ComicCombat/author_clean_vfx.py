import unreal
from pathlib import Path
def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._clean_vfx)
 # Source artwork is produced by image_gen; keep original generated RGBA intact.
 src=Path(unreal.Paths.project_dir())/'Tools/ComicCombat/GeneratedSheets'
 for name in ['impact','shock','smoke','electric','ground']:
  task=unreal.AssetImportTask();task.filename=str(src/('T_Generated_'+name+'.png'))
  task.destination_path='/Game/ComicCombat/Hifi/CleanTextures';task.destination_name='T_Clean_'+name
  task.automated=True;task.replace_existing=True;task.save=True
  unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
  tex=unreal.load_asset(task.destination_path+'/'+task.destination_name)
  tex.set_editor_property('address_x',unreal.TextureAddress.TA_CLAMP);tex.set_editor_property('address_y',unreal.TextureAddress.TA_CLAMP)
  tex.set_editor_property('lod_group',unreal.TextureGroup.TEXTUREGROUP_EFFECTS)
  tex.set_editor_property('mip_gen_settings',unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
  tex.set_editor_property('max_texture_size',1024);tex.set_editor_property('never_stream',True)
  rows={'impact':4,'shock':3,'smoke':3,'electric':2,'ground':2}[name]
  tex.set_editor_property('power_of_two_mode',unreal.TexturePowerOfTwoSetting.RESIZE_TO_SPECIFIC_RESOLUTION)
  tex.set_editor_property('resize_during_build_x',1024)
  tex.set_editor_property('resize_during_build_y',256*rows)
  unreal.EditorAssetLibrary.save_loaded_asset(tex,False)
 print('GENERATED_VFX_IMPORTED')
unreal._clean_vfx=unreal.register_slate_post_tick_callback(run)
