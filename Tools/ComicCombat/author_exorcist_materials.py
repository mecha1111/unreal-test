import unreal,json,re
from pathlib import Path
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
DEST='/Game/ExorcistV10'; mel=unreal.MaterialEditingLibrary
def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._ex_materials)
 manifest=json.loads((ROOT/'SourceArt/ExorcistV10/export-manifest.json').read_text(encoding='utf-8'))
 at=unreal.AssetToolsHelpers.get_asset_tools();tasks=[]
 unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.PNG 0')
 for name,file in manifest['textures'].items():
  asset=DEST+'/Textures/'+Path(file).stem
  if unreal.EditorAssetLibrary.does_asset_exist(asset):continue
  t=unreal.AssetImportTask();t.filename=str(ROOT/'SourceArt/ExorcistV10/Textures'/file);t.destination_path=DEST+'/Textures';t.destination_name=Path(file).stem;t.automated=True;t.save=True;t.factory=unreal.TextureFactory();tasks.append(t)
 at.import_asset_tasks(tasks)
 unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.PNG 1')
 for name,file in manifest['textures'].items():
  tex=unreal.load_asset(DEST+'/Textures/'+Path(file).stem)
  data=any(x in name for x in ['Mask','AO','Control','Normal'])
  tex.set_editor_property('srgb',not data);tex.set_editor_property('max_texture_size',4096 if 'head_BaseColor' in name else 2048)
  tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS if data else unreal.TextureCompressionSettings.TC_BC7)
  unreal.EditorAssetLibrary.save_loaded_asset(tex)
 master=unreal.load_asset(DEST+'/Materials/M_EX_Surface')
 if not master:
  master=at.create_asset('M_EX_Surface',DEST+'/Materials',unreal.Material,unreal.MaterialFactoryNew());master.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT);master.set_editor_property('two_sided',True)
  def node(cls,**kw):
   n=mel.create_material_expression(master,cls)
   for k,v in kw.items():n.set_editor_property(k,v)
   return n
  texture=node(unreal.MaterialExpressionTextureSampleParameter2D,parameter_name='Albedo',texture=unreal.load_asset(DEST+'/Textures/EX_V7_head_BaseColor'))
  mask=node(unreal.MaterialExpressionTextureSampleParameter2D,parameter_name='SurfaceMask',texture=unreal.load_asset(DEST+'/Textures/EX_V8_upper_SurfaceMask'),sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
  inputs={'Base':(texture,'RGB'),'Mask':(mask,'RGB'),'N':(node(unreal.MaterialExpressionPixelNormalWS),''),'V':(node(unreal.MaterialExpressionCameraVectorWS),'')}
  for name,default in [('Mode',0),('HitFlash',0),('HasMask',0)]:inputs[name]=(node(unreal.MaterialExpressionScalarParameter,parameter_name=name,default_value=default),'')
  for name,value in [('KeyDirection',(0.28,0.55,0.80,1)),('Tint',(1,1,1,1)),('FixedColor',(.8,.45,.3,1))]:inputs[name]=(node(unreal.MaterialExpressionVectorParameter,parameter_name=name,default_value=unreal.LinearColor(*value)),'')
  pins=[]
  for name in inputs:p=unreal.CustomInput();p.set_editor_property('input_name',name);pins.append(p)
  code='''float3 n=normalize(N),v=normalize(V),l=normalize(KeyDirection);float d=dot(n,l);float shade=smoothstep(-.12,.55,d);float3 c=Base;
float skin=HasMask*Mask.r;float metal=HasMask*Mask.b;float leather=HasMask*Mask.g;
float3 shadow=lerp(float3(.56,.57,.64),float3(.87,.74,.72),skin);
c*=lerp(shadow,float3(1,1,1),shade);c+=pow(saturate(dot(n,normalize(l+v))),lerp(18,50,metal))*(.025+.08*leather+.2*metal);
if(Mode>0.5 && Mode<1.5)c=Base*lerp(float3(.90,.81,.79),float3(1,1,1),smoothstep(-.35,.6,d));
if(Mode>1.5 && Mode<2.5){float3 a=float3(.34,.35,.40),b=float3(.48,.49,.55),e=float3(.67,.68,.72),f=float3(.77,.78,.81);c=d<.24?lerp(a,b,smoothstep(0,.24,d)):d<.44?lerp(b,e,smoothstep(.24,.44,d)):lerp(e,f,smoothstep(.44,.68,d));float3 hv=l-v;float3 h=hv*rsqrt(max(dot(hv,hv),1e-8));c=lerp(c,float3(.90,.90,.93),.16*pow(saturate(dot(n,h)),24));}
if(Mode>2.5 && Mode<3.5)c=lerp(float3(.18,.20,.24),float3(.58,.60,.64),shade)+pow(saturate(dot(n,normalize(l+v))),18)*.65;
if(Mode>3.5 && Mode<4.5)c=lerp(float3(.07,.001,.003),float3(.48,.004,.012),shade)+float3(.95,.43,.42)*pow(saturate(dot(n,normalize(l+v))),38)*.8;
if(Mode>4.5)c=FixedColor*lerp(float3(.86,.76,.76),float3(1,1,1),shade);
return lerp(c*Tint,float3(1,.89,.68),saturate(HitFlash));'''
  custom=node(unreal.MaterialExpressionCustom,inputs=pins,output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,code=code)
  for name,(n,out) in inputs.items():mel.connect_material_expressions(n,out,custom,name)
  mel.connect_material_property(custom,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR);mel.recompile_material(master);unreal.EditorAssetLibrary.save_loaded_asset(master)
 # Persist both permutations before PIE; automatic editor usage changes alone do not survive restart.
 mel.set_material_usage(master,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH)
 mel.set_material_usage(master,unreal.MaterialUsage.MATUSAGE_MORPH_TARGETS)
 mel.recompile_material(master);unreal.EditorAssetLibrary.save_loaded_asset(master,False)
 mesh=unreal.load_asset(DEST+'/Character/SK_EX_Game');slots=list(mesh.materials)
 lookup={re.sub(r'[^A-Za-z0-9_]','_',k):(k,v) for k,v in manifest['materials'].items()}
 for index,slot in enumerate(slots):
  key=str(slot.material_slot_name);original,data=lookup[key];name='MI_'+key
  inst=unreal.load_asset(DEST+'/Materials/'+name) or at.create_asset(name,DEST+'/Materials',unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
  mel.set_material_instance_parent(inst,master);mode=0;fixed=(.8,.45,.3,1)
  albedo=next((x['image'] for x in data['images'] if 'BaseColor' in x['image']),None)
  mask=next((x['image'] for x in data['images'] if 'SurfaceMask' in x['image']),None)
  if albedo:mel.set_material_instance_texture_parameter_value(inst,'Albedo',unreal.load_asset(DEST+'/Textures/'+Path(manifest['textures'][albedo]).stem))
  if mask:mel.set_material_instance_texture_parameter_value(inst,'SurfaceMask',unreal.load_asset(DEST+'/Textures/'+Path(manifest['textures'][mask]).stem))
  if 'Material_head' in key or 'NeckFaceMatched' in key or 'Iris' in key:mode=1
  if 'Material_hair' in key or 'Scalp_Root' in key:mode=2
  if any(x in key for x in ['Metal','Silver','Hardware']):mode=3
  if 'Gem' in key:mode=4
  if 'WaistSkin' in key:mode=5;fixed=(.95,.66,.53,1)
  if any(x in key for x in ['HighCollar','JacketHem','FlowerTails','OrnamentRibbon']):mode=5;fixed=(.012,.014,.021,1)
  if 'Teeth' in key:mode=5;fixed=(.82,.79,.7,1)
  if 'Tongue' in key:mode=5;fixed=(.34,.045,.065,1)
  if 'Mouth_Cavity' in key:mode=5;fixed=(.018,.002,.004,1)
  mel.set_material_instance_scalar_parameter_value(inst,'Mode',mode);mel.set_material_instance_scalar_parameter_value(inst,'HasMask',1 if mask else 0);mel.set_material_instance_vector_parameter_value(inst,'FixedColor',unreal.LinearColor(*fixed))
  slot.material_interface=inst;unreal.EditorAssetLibrary.save_loaded_asset(inst,False)
 mesh.set_editor_property('materials',slots);unreal.EditorAssetLibrary.save_loaded_asset(mesh,False)
 print('EXORCIST_MATERIALS_READY',len(slots))
unreal._ex_materials=unreal.register_slate_post_tick_callback(run)
