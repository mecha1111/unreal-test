"""Hybrid anime materials: preserve painted colour, use scene lighting for surfaces.
Run as one editor Slate callback, after mesh import has completed.
"""
import unreal,json
from pathlib import Path
D='/Game/ExorcistV10'; M=unreal.MaterialEditingLibrary
def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._ex_daylight)
 at=unreal.AssetToolsHelpers.get_asset_tools()
 master=unreal.load_asset(D+'/Materials/M_EX_SurfaceDetail') or at.create_asset('M_EX_SurfaceDetail',D+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
 unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(master)
 M.delete_all_material_expressions(master)
 master.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
 master.set_editor_property('two_sided',True)
 def node(cls,**kw):
  n=M.create_material_expression(master,cls)
  for k,v in kw.items():n.set_editor_property(k,v)
  return n
 def custom(code,inputs,typ=unreal.CustomMaterialOutputType.CMOT_FLOAT3):
  pins=[]
  for name in inputs:p=unreal.CustomInput();p.set_editor_property('input_name',name);pins.append(p)
  n=node(unreal.MaterialExpressionCustom,code=code,inputs=pins,output_type=typ)
  for name,(src,out) in inputs.items():M.connect_material_expressions(src,out,n,name)
  return n
 albedo=node(unreal.MaterialExpressionTextureSampleParameter2D,parameter_name='Albedo',texture=unreal.load_asset(D+'/Textures/EX_V7_head_BaseColor'))
 mask=node(unreal.MaterialExpressionTextureSampleParameter2D,parameter_name='SurfaceMask',texture=unreal.load_asset(D+'/Textures/EX_V8_upper_SurfaceMask'),sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
 inputs={'Base':(albedo,'RGB'),'Mask':(mask,'RGB'),'UV':(node(unreal.MaterialExpressionTextureCoordinate),'')}
 for name,value in [('Mode',0),('HitFlash',0),('HasMask',0),('FabricDetail',1),('SurfaceClass',0)]:inputs[name]=(node(unreal.MaterialExpressionScalarParameter,parameter_name=name,default_value=value),'')
 for name,value in [('Tint',(1,1,1,1)),('FixedColor',(.8,.45,.3,1))]:inputs[name]=(node(unreal.MaterialExpressionVectorParameter,parameter_name=name,default_value=unreal.LinearColor(*value)),'RGB')
 color=custom('''float3 c=Base;
 if(Mode>1.5&&Mode<2.5)c=float3(.46,.48,.54);
 if(Mode>2.5&&Mode<3.5)c=float3(.48,.51,.56);
 if(Mode>3.5&&Mode<4.5)c=float3(.34,.008,.018);
 if(Mode>4.5)c=FixedColor;
 // Preserve the painted face and garment palette; no global colour replacement.
 return max(c*Tint,0);''',inputs)
 inputs['Color']=(color,'')
 base=custom('return Color * ((Mode>.5&&Mode<1.5)? .62 : .86);',inputs)
 fill=custom('''float face=(Mode>.5&&Mode<1.5)?1:0;float skin=HasMask*Mask.r;
 float fill=lerp(.065,.28,max(face,skin));
 if(SurfaceClass>3.5&&SurfaceClass<4.5)fill=.28;
 if(Mode>1.5&&Mode<2.5)fill=.12;
 float3 c=Color*fill*float3(.96,.98,1.03);
 return lerp(c,float3(1,.89,.68),saturate(HitFlash));''',inputs)
 rough=custom('''float r=lerp(.82,.43,HasMask*Mask.g);r=lerp(r,.28,HasMask*Mask.b);r=lerp(r,.70,HasMask*Mask.r);
 if(Mode>.5&&Mode<1.5)r=.72;if(Mode>1.5&&Mode<2.5)r=.48;
 if(Mode>2.5&&Mode<3.5)r=.27;if(Mode>3.5&&Mode<4.5)r=.19;
 if(Mode>4.5)r=.64;
 if(SurfaceClass>1.5&&SurfaceClass<2.5)r=.36;
 if(SurfaceClass>3.5&&SurfaceClass<4.5)r=.72;
 float fade=saturate(1-max(length(ddx(UV*640)),length(ddy(UV*640))));
 float cloth=(Mode<.5)?(1-saturate(HasMask*(Mask.r+Mask.g+Mask.b))):0;
 return saturate(r+sin(UV.x*4021)*sin(UV.y*4021)*.045*fade*cloth*FabricDetail);''',inputs,unreal.CustomMaterialOutputType.CMOT_FLOAT1)
 metal=custom('return (Mode>2.5&&Mode<3.5)?.78:((Mode<.5)?HasMask*Mask.b*.7:0);',inputs,unreal.CustomMaterialOutputType.CMOT_FLOAT1)
 spec=custom('return (Mode>.5&&Mode<2.5)?.23:.4;',inputs,unreal.CustomMaterialOutputType.CMOT_FLOAT1)
 normal=custom('''float cloth=(Mode<.5)?1-saturate(HasMask*(Mask.r+Mask.g+Mask.b)):0;
 float2 uv=UV*640;float fade=saturate(1-max(length(ddx(uv)),length(ddy(uv))));
 float leather=max(HasMask*Mask.g,(SurfaceClass>1.5&&SurfaceClass<2.5)?1:0);
 float2 n=float2(sin(uv.x*6.283),sin(uv.y*6.283))*(.045*cloth+.012*leather)*fade*FabricDetail;
 return normalize(float3(n,1));''',inputs)
 for n,prop in [(base,unreal.MaterialProperty.MP_BASE_COLOR),(fill,unreal.MaterialProperty.MP_EMISSIVE_COLOR),(rough,unreal.MaterialProperty.MP_ROUGHNESS),(metal,unreal.MaterialProperty.MP_METALLIC),(spec,unreal.MaterialProperty.MP_SPECULAR),(normal,unreal.MaterialProperty.MP_NORMAL)]:M.connect_material_property(n,'',prop)
 for usage in [unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH,unreal.MaterialUsage.MATUSAGE_MORPH_TARGETS]:M.set_material_usage(master,usage)
 M.recompile_material(master);unreal.EditorAssetLibrary.save_loaded_asset(master,False)
 mesh=unreal.load_asset(D+'/Character/SK_EX_Optimized');slots=list(mesh.materials)
 for slot in slots:
  old=slot.material_interface
  name='MI_Day_'+str(slot.material_slot_name)
  inst=unreal.load_asset(D+'/Materials/Daylight/'+name)
  if not inst:inst=unreal.EditorAssetLibrary.duplicate_asset(old.get_path_name(),D+'/Materials/Daylight/'+name)
  M.set_material_instance_parent(inst,master);slot.material_interface=inst
  label=str(slot.material_slot_name)
  surface=2 if 'Leather' in label else 4 if 'WaistSkin' in label else 0
  M.set_material_instance_scalar_parameter_value(inst,'SurfaceClass',surface)
  M.update_material_instance(inst);unreal.EditorAssetLibrary.save_loaded_asset(inst,False)
 mesh.set_editor_property('materials',slots);unreal.EditorAssetLibrary.save_loaded_asset(mesh,False)
 # Warm daylight, neutral sky fill. Keep the user's flat white platform and blue sky.
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 for actor in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.DirectionalLight):
  light=actor.light_component;light.set_intensity(5.5);light.set_light_color(unreal.LinearColor(1,.94,.86,1))
  light.set_editor_property('light_source_angle',2.2)
 for actor in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.SkyLight):actor.light_component.set_intensity(1.1)
 winds=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.WindDirectionalSource)
 wind=next((a for a in winds if a.get_actor_label()=='Exorcist Soft Breeze'),None)
 if not wind:wind=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.WindDirectionalSource,unreal.Vector(0,0,200))
 wind.set_actor_label('Exorcist Soft Breeze');wind.set_actor_rotation(unreal.Rotator(yaw=35),False)
 wc=wind.get_component_by_class(unreal.WindDirectionalSourceComponent)
 wc.set_speed(8);wc.set_strength(.3)
 unreal.EditorLoadingAndSavingUtils.save_map(world,'/Game/ComicCombat/Maps/ComicArena')
 print('EX_DAYLIGHT_DONE',len(slots))
unreal._ex_daylight=unreal.register_slate_post_tick_callback(run)
