"""Daylight environment only. Character materials are deliberately untouched."""
import unreal

def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._day_refine)
 mel=unreal.MaterialEditingLibrary
 sky=unreal.load_asset('/Game/ExorcistV10/Materials/M_DaySky')
 expression=unreal.load_object(None,sky.get_path_name()+':MaterialExpressionCustom_0')
 expression.set_editor_property('code',r'''
 struct CloudNoise {
  float hash(float2 p){return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453);}
  float noise(float2 p){float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+1),f.x),f.y);}
 } cn;
 float3 d=normalize(-V);float h=saturate(d.z);
 float3 sky=lerp(float3(.66,.98,1.45),float3(.035,.31,1.05),pow(h,.42));
 float2 uv=d.xy/max(.15,d.z+.2)*2.1+float2(3.7,8.1);
 float n=cn.noise(uv)*.65+cn.noise(uv*2.1)*.25+cn.noise(uv*4.3)*.1;
 float cloud=smoothstep(.55,.73,n)*smoothstep(.02,.18,h);
 float3 white=lerp(float3(.92,1.14,1.47),float3(2.1,2.15,2.2),smoothstep(.52,.78,n));
 return lerp(sky,white,cloud*.9);
 ''')
 mel.recompile_material(sky);unreal.EditorAssetLibrary.save_loaded_asset(sky,False)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 for a in actors:
  if isinstance(a,unreal.DirectionalLight) and a.get_actor_label()=='Day Sun':
   a.set_actor_rotation(unreal.Rotator(pitch=-55,yaw=-32,roll=0),False)
   c=a.light_component;c.set_intensity(7.0);c.set_editor_property('intensity',7.0);c.set_light_color(unreal.LinearColor(1,.98,.93,1),False)
   c.set_editor_property('light_source_angle',2.5)
  elif isinstance(a,unreal.SkyLight):
   c=a.light_component;c.set_intensity(1.35);c.set_editor_property('intensity',1.35);c.set_light_color(unreal.LinearColor(.88,.94,1,1));c.recapture_sky()
  elif isinstance(a,unreal.ExponentialHeightFog):
   # Preserve a clear, simple training platform, without volumetric fog cost.
   a.set_actor_hidden_in_game(True);a.set_is_temporarily_hidden_in_editor(True)
  elif isinstance(a,unreal.StaticMeshActor) and a.get_actor_label()=='White Day Platform':
   a.static_mesh_component.set_material(0,unreal.load_asset('/Game/ExorcistV10/Materials/M_DayPlatform'))
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 print('SAVE_DAY_MAP',unreal.EditorLoadingAndSavingUtils.save_map(world,'/Game/ComicCombat/Maps/ComicArena'))
 print('DAYLIGHT_REFINED_NO_CHARACTER_MATERIAL_EDITS')

unreal._day_refine=unreal.register_slate_post_tick_callback(run)
