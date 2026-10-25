"""생성한 타격 그림과 매개변수형 VFX/만화 합성 머티리얼을 언리얼 자산으로 만든다."""
import unreal
from pathlib import Path

ROOT='/Game/ComicCombat'
OUT=Path(unreal.Paths.project_dir()).resolve() / 'SourceArt/ComicCombat'
TOOLS=unreal.AssetToolsHelpers.get_asset_tools()
MEL=unreal.MaterialEditingLibrary

for name in ['T_ComicImpact','T_ComicHeavy','T_ComicUltimate','T_ComicCrescent','T_ComicLimeBurst','T_ComicInkFlash',
             'T_ComicPartSpark','T_ComicPartBolt','T_ComicPartWedge','T_ComicPartHit','T_ComicPartQuestion']:
    path=ROOT+'/Textures/'+name
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        task=unreal.AssetImportTask()
        task.filename=str(OUT/(name+'.png'))
        task.destination_path=ROOT+'/Textures'
        task.destination_name=name
        task.automated=True
        task.save=True
        TOOLS.import_asset_tasks([task])
    tex=unreal.load_asset(path)
    tex.set_editor_property('address_x',unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property('address_y',unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property('lod_group',unreal.TextureGroup.TEXTUREGROUP_EFFECTS)
    tex.set_editor_property('power_of_two_mode',unreal.TexturePowerOfTwoSetting.RESIZE_TO_SPECIFIC_RESOLUTION)
    size=512 if 'Part' in name else 1024
    tex.set_editor_property('resize_during_build_x',size)
    tex.set_editor_property('resize_during_build_y',size)
    tex.set_editor_property('max_texture_size',size)
    tex.set_editor_property('never_stream','Part' in name or name=='T_ComicCrescent')
    tex.set_editor_property('mip_gen_settings',unreal.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE)
    tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_DEFAULT)
    tex.set_editor_property('do_scale_mips_for_alpha_coverage',True)
    tex.set_editor_property('alpha_coverage_thresholds',unreal.Vector4(0,0,0,.333))
    unreal.EditorAssetLibrary.save_loaded_asset(tex,False)

def material(name, post=False):
    path=ROOT+'/Materials/'+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mat=unreal.load_asset(path)
    else: mat=TOOLS.create_asset(name,ROOT+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
    mat.set_editor_property('two_sided',True)
    if post:
        mat.set_editor_property('material_domain',unreal.MaterialDomain.MD_POST_PROCESS)
        # UE5.8의 Scene Color After Tonemapping 위치는 로컬 API 열거형으로 선택한다.
        options=[x for x in dir(unreal.BlendableLocation) if 'TONEMAP' in x.upper() and 'AFTER' in x.upper()]
        if options: mat.set_editor_property('blendable_location',getattr(unreal.BlendableLocation,options[0]))
    else:
        mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_MASKED)
        mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
        mat.set_editor_property('opacity_mask_clip_value',.333)
    return mat

def node(mat,cls,x=0,y=0,**props):
    n=None
    for existing in MEL.get_material_expressions(mat):
        if isinstance(existing,cls) and existing.get_editor_property('material_expression_editor_x')==x and existing.get_editor_property('material_expression_editor_y')==y:
            n=existing
            break
    if n is None: n=MEL.create_material_expression(mat,cls,x,y)
    for key,value in props.items(): n.set_editor_property(key,value)
    return n

def scalar(mat,name,value,y):
    return node(mat,unreal.MaterialExpressionScalarParameter,-700,y,parameter_name=name,default_value=value)

def custom(mat,code,inputs,outtype=unreal.CustomMaterialOutputType.CMOT_FLOAT4):
    pins=[]
    for name,_,_ in inputs:
        pin=unreal.CustomInput()
        pin.set_editor_property('input_name',name)
        pins.append(pin)
    c=node(mat,unreal.MaterialExpressionCustom,0,0,code=code,output_type=outtype,
        inputs=pins)
    for name,expression,output in inputs:
        assert MEL.connect_material_expressions(expression,output,c,name), name
    return c

def finish(mat,c):
    rgb=node(mat,unreal.MaterialExpressionComponentMask,300,0,r=True,g=True,b=True)
    alpha=node(mat,unreal.MaterialExpressionComponentMask,300,170,r=False,g=False,b=False,a=True)
    assert MEL.connect_material_expressions(c,'',rgb,'')
    assert MEL.connect_material_expressions(c,'',alpha,'')
    assert MEL.connect_material_property(rgb,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    assert MEL.connect_material_property(alpha,'',unreal.MaterialProperty.MP_OPACITY_MASK)
    MEL.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)

shape=material('M_CC_Shape')
uv=node(shape,unreal.MaterialExpressionTextureCoordinate,-700,-250)
p=scalar(shape,'Progress',0,-100)
s=scalar(shape,'Shape',0,70)
seed=scalar(shape,'Seed',0,240)
tint=node(shape,unreal.MaterialExpressionVectorParameter,-700,400,parameter_name='Tint',default_value=unreal.LinearColor(1,.075,.006,1))
code=r'''
float2 p = UV * 2 - 1;
float radius = length(p);
float angle = atan2(p.y,p.x);
float aa = max(fwidth(radius),0.008);
float d = 10;
if (Shape < 0.5) {
    float sweep = saturate(Progress*8);
    float tail = saturate((Progress-.22)/.78);
    float width = .11 * max(.15,sin(saturate((angle+2.5)/3.8)*3.14159));
    d = abs(radius - .72 - .018*sin(angle*17+Seed)) - width;
    d = max(d, max((-2.5+tail*3.8)-angle, angle-(-2.5+sweep*3.8))*.2);
} else if (Shape < 1.5) {
    d = abs(radius-.75) - .027*(1-Progress*.6);
    d = max(d,(sin(angle*7+Seed)-.87)*.05);
} else if (Shape < 2.5) {
    d = abs(p.y) + abs(p.x)*.52 - .48;
    d = max(d,-p.x-.92);
} else {
    d = abs(p.x)+abs(p.y)-.78;
    d = min(d,max(abs(p.x)*.22,abs(p.y))-.18);
    d = min(d,max(abs(p.y)*.22,abs(p.x))-.18);
}
float coverage = 1-smoothstep(-aa,aa,d);
float rim = 1-smoothstep(-.045,-.015,d);
float3 ink = float3(.004,.006,.014);
float3 color = lerp(Tint.rgb, ink, rim*.95);
float noise = frac(sin(dot(floor(UV*37),float2(12.9898,78.233))+Seed)*43758.5453);
coverage *= step(saturate((Progress-.62)/.38),noise);
return float4(color,coverage);
'''
c=custom(shape,code,[('UV',uv,''),('Progress',p,''),('Shape',s,''),('Seed',seed,''),('Tint',tint,'')])
finish(shape,c)

impact=material('M_CC_Impact')
uv=node(impact,unreal.MaterialExpressionTextureCoordinate,-700,-300)
tex=node(impact,unreal.MaterialExpressionTextureSampleParameter2D,-700,-100,parameter_name='ImpactTexture',
    texture=unreal.load_asset(ROOT+'/Textures/T_ComicPartSpark'))
p=scalar(impact,'Progress',0,150)
seed=scalar(impact,'Seed',0,300)
code=r'''
float2 p=UV*2-1;
float r=length(p);
float angular=sin(atan2(p.y,p.x)*19+Seed)*.09;
float noise=frac(sin(dot(floor(UV*55),float2(12.9898,78.233)))*43758.5453);
float erosion=saturate((Progress-.28)/.72);
float threshold=saturate(.15+r*.62+angular+noise*.22);
float coverage=Alpha*step(erosion,threshold);
return float4(Color.rgb,coverage);
'''
c=custom(impact,code,[('UV',uv,''),('Color',tex,'RGB'),('Alpha',tex,'A'),('Progress',p,''),('Seed',seed,'')])
finish(impact,c)

post=material('M_CC_ComicPost',True)
scene=node(post,unreal.MaterialExpressionSceneTexture,-700,-300,scene_texture_id=unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
depth=node(post,unreal.MaterialExpressionSceneTexture,-700,-130,scene_texture_id=unreal.SceneTextureId.PPI_SCENE_DEPTH)
cd=node(post,unreal.MaterialExpressionSceneTexture,-700,40,scene_texture_id=unreal.SceneTextureId.PPI_CUSTOM_DEPTH)
stencil=node(post,unreal.MaterialExpressionSceneTexture,-700,210,scene_texture_id=unreal.SceneTextureId.PPI_CUSTOM_STENCIL)
flash=scalar(post,'ImpactFlash',0,380)
center=node(post,unreal.MaterialExpressionVectorParameter,-700,550,parameter_name='ImpactCenter',default_value=unreal.LinearColor(.5,.5,0,0))
speed=scalar(post,'SpeedAmount',0,720)
accent=scalar(post,'HitAccent',0,890)
time_node=node(post,unreal.MaterialExpressionTime,-700,1060)
darken=scalar(post,'ImpactDarken',0,1220)
postcode=r'''
float2 uv=GetDefaultSceneTextureUV(Parameters,14);
float2 pixel=View.BufferSizeAndInvSize.zw;
float selected=step(10.5,Stencil.r)*step(Stencil.r,12.5)*step(CustomDepth.r,Depth.r+3);
float neighbor=0;
float inner=0;
float2 offsets[4]={float2(1,0),float2(-1,0),float2(0,1),float2(0,-1)};
for(int i=0;i<4;i++) {
    float2 v=ViewportUVToSceneTextureUV(GetViewportUV(Parameters),25)+offsets[i]*pixel*1.6;
    float s=SceneTextureLookup(v,25,false).r;
    float z=SceneTextureLookup(v,13,false).r;
    float dz=SceneTextureLookup(v,1,false).r;
    float m=step(10.5,s)*step(s,12.5)*step(z,dz+3);
    neighbor=max(neighbor,m);
    inner=max(inner,m*step(max(4,CustomDepth.r*.012),abs(z-CustomDepth.r)));
}
float3 base=Scene.rgb;
float l=max(dot(base,float3(.2126,.7152,.0722)),.001);
float band=l<.09 ? .025 : l<.25 ? .13 : l<.52 ? .38 : .75;
float3 toon=lerp(base,base*(band/l),.30);
float2 screen=uv*View.BufferSizeAndInvSize.xy;
float2 cell=frac(screen/6)-.5;
float dots=1-smoothstep(.11,.21,length(cell));
float hatch=1-smoothstep(.08,.2,abs(frac((screen.x+screen.y)/7)-.5));
float fade=1-smoothstep(550,1600,Depth.r);
toon*=1-((l<.5 ? dots*.2 : 0)+(l<.27 ? hatch*.15 : 0))*fade;
// 배경은 색면만 약하게 정리하고 전투 대상에만 망점/해칭을 강조한다.
float3 environment=base;
float3 color=lerp(environment,toon,selected);
float outer=neighbor*(1-selected);
float3 outline=lerp(float3(.008,.012,.025),float3(.55,1,1),saturate(HitAccent));
color=lerp(color,outline,saturate(outer+inner*selected*.65));
// 어두운 바닥/하늘만 누르고 밝게 발광하는 VFX는 남긴다.
float vivid=max(base.r,max(base.g,base.b));
float keepLight=smoothstep(.35,.78,vivid);
color*=1-ImpactDarken*(1-selected*.6)*(1-keepLight)*.82;
float2 speedP=(GetViewportUV(Parameters)-.5)*float2(View.ViewSizeAndInvSize.x/View.ViewSizeAndInvSize.y,1);
float speedR=length(speedP);
float speedA=atan2(speedP.y,speedP.x);
float rays=pow(saturate(sin(speedA*47)),48)*smoothstep(.40,.78,speedR)
    *smoothstep(.55,.85,frac(speedR*9-Time*4));
color=lerp(color,float3(.65,.95,1),rays*SpeedAmount*.48);
// 궁극기 전용: 배경 전체를 검게 만들고 타격 레이어와 외곽선만 흰색으로 남긴다.
// 화면 좌표에 직접 날카로운 흰 충격선을 그린다. VFX마다 CustomDepth를 재렌더하지 않는다.
float2 flashP=(GetViewportUV(Parameters)-ImpactCenter.xy)*float2(View.ViewSizeAndInvSize.x/View.ViewSizeAndInvSize.y,1);
float flashR=length(flashP);
float flashA=atan2(flashP.y,flashP.x);
float boundary=.045+.19*pow(abs(cos(flashA*6+sin(flashA*3)*.6)),18)
    +.08*pow(abs(sin(flashA*9+.5)),38);
float burst=1-smoothstep(boundary-.002,boundary+.002,flashR);
float cuts=step(.93,sin(flashA*23+flashR*17))*step(.075,flashR);
float inkFlash=max(outer,burst*(1-cuts)*(1-selected));
return lerp(color,inkFlash.xxx,saturate(ImpactFlash));
'''
c=custom(post,postcode,[('Scene',scene,'Color'),('Depth',depth,'Color'),('CustomDepth',cd,'Color'),('Stencil',stencil,'Color'),('ImpactFlash',flash,''),('ImpactCenter',center,''),('SpeedAmount',speed,''),('HitAccent',accent,''),('Time',time_node,''),('ImpactDarken',darken,'')],unreal.CustomMaterialOutputType.CMOT_FLOAT3)
MEL.connect_material_property(c,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.recompile_material(post)
unreal.EditorAssetLibrary.save_loaded_asset(post)
print('COMIC_MATERIALS_CREATED')

armor_path=ROOT+'/Materials/M_CC_Armor'
armor=unreal.load_asset(armor_path) if unreal.EditorAssetLibrary.does_asset_exist(armor_path) else TOOLS.create_asset('M_CC_Armor',ROOT+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
color=node(armor,unreal.MaterialExpressionVectorParameter,-500,0,parameter_name='Color',default_value=unreal.LinearColor(.025,.32,.42,1))
rough=scalar(armor,'Roughness',.78,170)
spec=scalar(armor,'Specular',.25,300)
assert MEL.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
assert MEL.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
assert MEL.connect_material_property(spec,'',unreal.MaterialProperty.MP_SPECULAR)
MEL.set_base_material_usage(armor,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH,True)
MEL.recompile_material(armor)
unreal.EditorAssetLibrary.save_loaded_asset(armor,False)

floor_path=ROOT+'/Materials/M_CC_ArenaFloor'
floor=unreal.load_asset(floor_path) if unreal.EditorAssetLibrary.does_asset_exist(floor_path) else TOOLS.create_asset('M_CC_ArenaFloor',ROOT+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
floor_color=node(floor,unreal.MaterialExpressionVectorParameter,-500,0,parameter_name='Color',default_value=unreal.LinearColor(.065,.082,.11,1))
floor_rough=scalar(floor,'Roughness',.88,170)
MEL.connect_material_property(floor_color,'',unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(floor_rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
MEL.recompile_material(floor)
unreal.EditorAssetLibrary.save_loaded_asset(floor)
