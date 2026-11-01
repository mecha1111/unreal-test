"""Commandlet/editor import of original image_gen animation sheets."""
import unreal
from pathlib import Path
src=Path(unreal.Paths.project_dir())/'Tools/ComicCombat/GeneratedSheets'
for name in ['jab_burst','cross_burst','rising_burst','lightning_fork','ground_fracture']:
    task=unreal.AssetImportTask()
    task.filename=str(src/('T_Generated_'+name+'.png'))
    task.destination_path='/Game/ComicCombat/Hifi/CleanTextures'
    task.destination_name='T_Generated_'+name
    task.automated=True;task.replace_existing=True;task.save=True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex=unreal.load_asset(task.destination_path+'/'+task.destination_name)
    assert tex,name
    tex.set_editor_property('address_x',unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property('address_y',unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property('lod_group',unreal.TextureGroup.TEXTUREGROUP_EFFECTS)
    tex.set_editor_property('mip_gen_settings',unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property('max_texture_size',1024)
    tex.set_editor_property('never_stream',True)
    tex.set_editor_property('power_of_two_mode',unreal.TexturePowerOfTwoSetting.RESIZE_TO_SPECIFIC_RESOLUTION)
    tex.set_editor_property('resize_during_build_x',1024)
    tex.set_editor_property('resize_during_build_y',1024)
    unreal.EditorAssetLibrary.save_loaded_asset(tex,False)
print('VFX_VARIATIONS_IMPORTED',5)
