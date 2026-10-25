"""각 이미지 파츠의 알파, 색 이동, 질감 소멸을 공통 머티리얼로 제어한다."""
import unreal
from pathlib import Path
ART=Path(unreal.Paths.project_dir()).resolve()/'SourceArt/ComicCombatV3'
for file in sorted(ART.glob('T_CC3_*.png')):
    path=ROOT+'/TexturesV3/'+file.stem
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        task=unreal.AssetImportTask()
        task.filename=str(file);task.destination_path=ROOT+'/TexturesV3'
        task.destination_name=file.stem;task.automated=True;task.save=True
        TOOLS.import_asset_tasks([task])
    tex=unreal.load_asset(path)
    tex.set_editor_property('address_x',unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property('address_y',unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property('lod_group',unreal.TextureGroup.TEXTUREGROUP_EFFECTS)
    tex.set_editor_property('power_of_two_mode',unreal.TexturePowerOfTwoSetting.RESIZE_TO_SPECIFIC_RESOLUTION)
    # 원본 비율은 메시의 종횡비로 복원한다. 엔진 리소스는 BC 압축 가능한 정사각 크기로 만든다.
    size=1024 if file.stem in ['T_CC3_CoreStar','T_CC3_Bloom','T_CC3_Crescent','T_CC3_GroundSplat'] else 512
    tex.set_editor_property('resize_during_build_x',size);tex.set_editor_property('resize_during_build_y',size)
    tex.set_editor_property('max_texture_size',size)
    tex.set_editor_property('never_stream',True)
    tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_DEFAULT)
    tex.set_editor_property('mip_gen_settings',unreal.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE)
    unreal.EditorAssetLibrary.save_loaded_asset(tex,False)

mat=material('M_CC_PaintedLayer')
mat.set_editor_property('opacity_mask_clip_value',.45)
mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
uv=node(mat,unreal.MaterialExpressionTextureCoordinate,-1000,-300)
tex=node(mat,unreal.MaterialExpressionTextureSampleParameter2D,-700,-300,parameter_name='ImpactTexture',texture=unreal.load_asset(ROOT+'/TexturesV3/T_CC3_CoreStar'))
MEL.connect_material_expressions(uv,'',tex,'UVs')
p=scalar(mat,'Progress',0,0)
seed=scalar(mat,'Seed',1,160)
hue=scalar(mat,'HueOffset',0,320)
travel=scalar(mat,'HueTravel',-.20,480)
energy=scalar(mat,'Energy',2.4,640)
reveal=scalar(mat,'Reveal',0,800)
palette=scalar(mat,'Palette',0,960)
ground=scalar(mat,'Ground',0,1120)
warp=scalar(mat,'Warp',.012,1280)
texture_object=node(mat,unreal.MaterialExpressionTextureObjectParameter,-1000,-550,parameter_name='ImpactTexture',texture=unreal.load_asset(ROOT+'/TexturesV3/T_CC3_CoreStar'))
code=r'''
float2 flow=UV+float2(sin(UV.y*14-Progress*9+Seed),sin(UV.x*11+Progress*7))*Warp*sin(Progress*3.14159);
float4 art=Texture2DSample(Art,ArtSampler,saturate(flow));
float3 rgb=max(art.rgb,0);
float hi=max(rgb.r,max(rgb.g,rgb.b)),lo=min(rgb.r,min(rgb.g,rgb.b));
float delta=hi-lo;
float h=0;
if(delta>.0001) {
 h=hi==rgb.r ? (rgb.g-rgb.b)/delta : hi==rgb.g ? 2+(rgb.b-rgb.r)/delta : 4+(rgb.r-rgb.g)/delta;
 h=frac(h/6);
}
h=frac(h+HueOffset+HueTravel*Progress);
float sat=delta/max(hi,.0001)*.72;
float3 shifted=hi*lerp(float3(1,1,1),saturate(abs(frac(h+float3(0,2.0/3,1.0/3))*6-3)-1),sat);
// 넓은 면의 핑크를 억제하고 중심/전격/잔광에 다른 색 역할을 준다.
float light=dot(rgb,float3(.2126,.7152,.0722));
float3 low=float3(.12,.025,.045),mid=float3(.85,.20,.025),high=float3(1,.78,.42);
if(Palette>.5 && Palette<1.5){low=float3(.015,.06,.13);mid=float3(.04,.42,.49);high=float3(.64,.95,1);}
if(Palette>1.5 && Palette<2.5){low=float3(.025,.02,.07);mid=float3(.18,.10,.30);high=float3(.55,.42,.70);}
float3 mapped=lerp(low,mid,smoothstep(.03,.32,light));
mapped=lerp(mapped,high,smoothstep(.35,.78,light));
mapped=lerp(mapped,float3(1,.94,.82),smoothstep(.55,.9,lo));
mapped*=smoothstep(.005,.065,hi);
shifted=lerp(shifted,mapped,Palette>2.5 ? .18 : .86);
float2 cell=floor(UV*95);
float grain=frac(sin(dot(cell,float2(12.9898,78.233))+Seed)*43758.5453);
float erase=saturate((Progress-.40)/.60);
float dissolve=1-smoothstep(grain*.8+.12,grain*.8+.20,erase);
float draw=lerp(1,smoothstep(UV.x-.12,UV.x+.04,saturate(Progress*7)),Reveal);
return float4(shifted,art.a*dissolve*draw);
'''
c=custom(mat,code,[('UV',uv,''),('Art',texture_object,''),('Progress',p,''),('Seed',seed,''),('HueOffset',hue,''),('HueTravel',travel,''),('Palette',palette,''),('Warp',warp,''),('Reveal',reveal,'')])
rgb=node(mat,unreal.MaterialExpressionComponentMask,300,0,r=True,g=True,b=True,a=False)
alpha=node(mat,unreal.MaterialExpressionComponentMask,300,170,r=False,g=False,b=False,a=True)
MEL.connect_material_expressions(c,'',rgb,'');MEL.connect_material_expressions(c,'',alpha,'')
MEL.connect_material_property(rgb,'',unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(alpha,'',unreal.MaterialProperty.MP_OPACITY_MASK)
# 실제 광원에 반응하는 표면 + 밝은 부분만 발광. 바닥은 발광을 낮춰 그림자가 읽히게 한다.
def custom_at(x,y,code,inputs):
    pins=[]
    for name,_,_ in inputs:
        pin=unreal.CustomInput();pin.set_editor_property('input_name',name);pins.append(pin)
    n=node(mat,unreal.MaterialExpressionCustom,x,y,code=code,output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,inputs=pins)
    for name,expr,out in inputs:MEL.connect_material_expressions(expr,out,n,name)
    return n
glow=custom_at(500,400,r'''
float hot=pow(saturate(min(Color.r,min(Color.g,Color.b))),2);
float pulse=exp(-Progress*12);
float gain=lerp(.26+hot*2.1+pulse*.28,.07,Ground)*Energy;
return Color*gain;
''',[('Color',rgb,''),('Energy',energy,''),('Progress',p,''),('Ground',ground,'')])
MEL.connect_material_property(glow,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
normal=custom_at(500,700,r'''
float2 d=float2(.003,0);
float4 a=Texture2DSample(Art,ArtSampler,UV-d.xy),b=Texture2DSample(Art,ArtSampler,UV+d.xy);
float4 c=Texture2DSample(Art,ArtSampler,UV-d.yx),e=Texture2DSample(Art,ArtSampler,UV+d.yx);
float dx=(b.a-a.a)*.55+dot(b.rgb-a.rgb,float3(.21,.71,.08))*.3;
float dy=(e.a-c.a)*.55+dot(e.rgb-c.rgb,float3(.21,.71,.08))*.3;
return normalize(float3(-dx,-dy,1));
''',[('UV',uv,''),('Art',texture_object,'')])
MEL.connect_material_property(normal,'',unreal.MaterialProperty.MP_NORMAL)
rough=scalar(mat,'SurfaceRoughness',.68,1440)
spec=scalar(mat,'SurfaceSpecular',.18,1600)
MEL.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
MEL.connect_material_property(spec,'',unreal.MaterialProperty.MP_SPECULAR)
MEL.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat,False)

# 깊은 포도색 무광 바닥. 파란 반사광과 선명한 테두리 띠를 없앤다.
stage=unreal.load_asset(ROOT+'/Materials/M_CC_ArenaFloor')
node(stage,unreal.MaterialExpressionVectorParameter,-500,0,parameter_name='Color',default_value=unreal.LinearColor(.040,.022,.063,1))
scalar(stage,'Roughness',.95,170)
spec=scalar(stage,'Specular',.08,300)
MEL.connect_material_property(spec,'',unreal.MaterialProperty.MP_SPECULAR)
em=node(stage,unreal.MaterialExpressionConstant3Vector,-500,470,constant=unreal.LinearColor(.013,.006,.025,1))
MEL.connect_material_property(em,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.recompile_material(stage);unreal.EditorAssetLibrary.save_loaded_asset(stage,False)
le=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
le.load_level('/Game/ComicCombat/Maps/ComicArena')
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    label=a.get_actor_label()
    if isinstance(a,unreal.DirectionalLight):
        rim='Rim' in label
        a.light_component.set_intensity(.65 if rim else 4.0)
        a.light_component.set_light_color(unreal.LinearColor(.65,.30,1,1) if rim else unreal.LinearColor(1,.91,.84,1),False)
    if isinstance(a,unreal.StaticMeshActor) and ('Border' in label or ' Base' in label):
        a.set_actor_hidden_in_game(True)
        a.set_is_temporarily_hidden_in_editor(True)
    if label=='Comic Night Dome':
        a.set_actor_hidden_in_game(False)
        a.set_is_temporarily_hidden_in_editor(False)
        a.static_mesh_component.set_visibility(True)
        a.static_mesh_component.set_hidden_in_game(False)
        a.static_mesh_component.set_editor_property('reverse_culling',True)
    if label=='Comic Stage - Blue Grey':
        a.set_actor_scale3d(unreal.Vector(1000,1000,.2))
le.save_current_level()
print('CC3_IMAGE_LAYERS_COMPLETE')
