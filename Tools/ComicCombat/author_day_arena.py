import unreal
def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._ex_day)
 eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 actors=eas.get_all_level_actors()
 mel=unreal.MaterialEditingLibrary
 path='/Game/ExorcistV10/Materials/M_DayPlatform'
 mat=unreal.load_asset(path)
 if not mat:
  mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_DayPlatform','/Game/ExorcistV10/Materials',unreal.Material,unreal.MaterialFactoryNew())
  color=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector)
  color.set_editor_property('constant',unreal.LinearColor(.88,.88,.88,1))
  mel.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
  rough=mel.create_material_expression(mat,unreal.MaterialExpressionConstant);rough.set_editor_property('r',.85)
  mel.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
  mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat,False)
 for a in actors:
  name=a.get_actor_label()
  if isinstance(a,unreal.PostProcessVolume):a.set_editor_property('enabled',False)
  elif isinstance(a,unreal.DirectionalLight):
   c=a.light_component
   if 'Rim' in name:
    c.set_visibility(False);c.set_intensity(0);c.set_editor_property('atmosphere_sun_light',False)
   else:
    a.set_actor_rotation(unreal.Rotator(pitch=-48,yaw=-32,roll=0),False)
    c.set_visibility(True);c.set_intensity(4.5);c.set_light_color(unreal.LinearColor(1,1,1,1),False)
    c.set_editor_property('atmosphere_sun_light',True);c.set_editor_property('atmosphere_sun_light_index',0)
    c.set_editor_property('forward_shading_priority',1)
    a.set_actor_label('Day Sun')
  elif isinstance(a,unreal.SkyLight):
   c=a.light_component;c.set_visibility(True);c.set_intensity(.9);c.set_light_color(unreal.LinearColor(1,1,1,1))
   c.set_editor_property('real_time_capture',False)
  elif isinstance(a,unreal.SkyAtmosphere):
   a.set_actor_hidden_in_game(False);a.set_is_temporarily_hidden_in_editor(False)
  elif isinstance(a,unreal.ExponentialHeightFog):
   a.set_actor_hidden_in_game(True);a.set_is_temporarily_hidden_in_editor(True)
  elif isinstance(a,unreal.StaticMeshActor):
   if 'Stage' in name or name.startswith('White Floor'):
    a.static_mesh_component.set_material(0,mat);a.set_actor_label('White Day Platform')
   elif 'Sky' in name or 'Night Dome' in name or 'Boundary' in name:
    a.set_actor_hidden_in_game(True);a.set_is_temporarily_hidden_in_editor(True)
 # A stable daylight skydome keeps the hand-authored unlit character palette at exposure 0.
 sky=unreal.load_asset('/Game/ExorcistV10/Materials/M_DaySky')
 if not sky:
  sky=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_DaySky','/Game/ExorcistV10/Materials',unreal.Material,unreal.MaterialFactoryNew())
  sky.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT);sky.set_editor_property('two_sided',True);sky.set_editor_property('is_sky',True)
  direction=mel.create_material_expression(sky,unreal.MaterialExpressionCameraVectorWS)
  pin=unreal.CustomInput();pin.set_editor_property('input_name','V')
  color=mel.create_material_expression(sky,unreal.MaterialExpressionCustom);color.set_editor_property('inputs',[pin]);color.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
  color.set_editor_property('code','return lerp(float3(.66,.82,1.0),float3(.055,.34,.90),pow(saturate(-V.z),.45));')
  mel.connect_material_expressions(direction,'',color,'V');mel.connect_material_property(color,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR);mel.recompile_material(sky);unreal.EditorAssetLibrary.save_loaded_asset(sky,False)
 dome=next((a for a in actors if a.get_actor_label() in ['Comic Night Dome','Day Sky Dome']),None)
 if dome:
  dome.set_actor_label('Day Sky Dome');dome.static_mesh_component.set_material(0,sky);dome.set_actor_hidden_in_game(False);dome.set_is_temporarily_hidden_in_editor(False)
 for a in actors:
  if isinstance(a,unreal.SkyAtmosphere):a.set_actor_hidden_in_game(True);a.set_is_temporarily_hidden_in_editor(True)
 for a in actors:
  if isinstance(a,unreal.SkyLight):a.light_component.recapture_sky()
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
 print('DAY_ARENA_SAVED')
unreal._ex_day=unreal.register_slate_post_tick_callback(run)
