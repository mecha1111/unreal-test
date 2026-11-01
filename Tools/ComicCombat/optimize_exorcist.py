"""Import the material-consolidated mesh with its original skeleton, then author morph-aware LODs."""
import unreal,json
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir()).resolve();D='/Game/ExorcistV10'
def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._ex_opt)
 unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 try:
  t=unreal.AssetImportTask();t.filename=str(ROOT/'SourceArt/ExorcistV10/SK_EX_Optimized.fbx');t.destination_path=D+'/Character';t.destination_name='SK_EX_Optimized';t.automated=True;t.save=True;t.replace_existing=True
  o=unreal.FbxImportUI();o.import_mesh=True;o.import_as_skeletal=True;o.import_animations=False;o.import_materials=False;o.import_textures=False;o.create_physics_asset=False
  o.skeleton=unreal.load_asset(D+'/Character/SK_EX_Game').skeleton;o.set_editor_property('automated_import_should_detect_type',False);o.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH
  o.skeletal_mesh_import_data.set_editor_property('import_morph_targets',True);o.skeletal_mesh_import_data.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
  o.skeletal_mesh_import_data.set_editor_property('import_meshes_in_bone_hierarchy',True);o.skeletal_mesh_import_data.convert_scene=True;o.skeletal_mesh_import_data.convert_scene_unit=True;t.options=o
  unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
 finally:unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 1')
 m=unreal.load_asset(D+'/Character/SK_EX_Optimized');slots=list(m.materials)
 for s in slots:
  s.material_interface=unreal.load_asset(D+'/Materials/MI_'+str(s.material_slot_name));assert s.material_interface
 m.set_editor_property('materials',slots)
 at=unreal.AssetToolsHelpers.get_asset_tools();settings=unreal.load_asset(D+'/Character/LOD_EX')
 if not settings:settings=at.create_asset('LOD_EX',D+'/Character',unreal.SkeletalMeshLODSettings,unreal.DataAssetFactory())
 groups=[]
 for ratio,screen in [(1.,1.),(.65,.65),(.35,.3),(.18,.14)]:
  group=unreal.SkeletalMeshLODGroupSettings();group.set_editor_property('screen_size',unreal.PerPlatformFloat(screen));group.set_editor_property('lod_hysteresis',.025)
  reduction=unreal.SkeletalMeshOptimizationSettings();reduction.set_editor_property('num_of_triangles_percentage',ratio);reduction.set_editor_property('num_of_vert_percentage',ratio)
  reduction.set_editor_property('max_bones_per_vertex',4);reduction.set_editor_property('remap_morph_targets',True);reduction.set_editor_property('recalc_normals',False);reduction.set_editor_property('merge_coincident_vert_bones',True)
  group.set_editor_property('reduction_settings',reduction);group.set_editor_property('bones_to_prioritize',['head1','hand_L','hand_R']);group.set_editor_property('weight_of_prioritization',2500)
  groups.append(group)
 settings.set_editor_property('lod_groups',groups);unreal.EditorAssetLibrary.save_loaded_asset(settings,False);m.set_editor_property('lod_settings',settings)
 sub=unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem);assert sub.regenerate_lod(m,4,False,False)
 unreal.EditorAssetLibrary.save_loaded_asset(m,False)
 result={'material_slots':len(slots),'lods':sub.get_lod_count(m),'sections':[sub.get_num_sections(m,i) for i in range(sub.get_lod_count(m))]}
 (ROOT/'Tools/ComicCombat/exorcist-optimization.json').write_text(json.dumps(result,indent=2))
 print('EX_OPTIMIZED',result)
unreal._ex_opt=unreal.register_slate_post_tick_callback(run)
