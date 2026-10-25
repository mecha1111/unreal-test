"""접촉/충격파/연기/전격/바닥/HIT의 독립 플립북과 알파 머티리얼을 만든다."""
import unreal, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/'AnimatedSheets'
if not OUT.exists(): OUT=HERE.parent/'outputs'/'VFX-Animation-Sheets'
ROOT='/Game/ComicCombat/Hifi'
TOOLS=unreal.AssetToolsHelpers.get_asset_tools()
MEL=unreal.MaterialEditingLibrary
SHEETS=[('impact',4,4),('shock',4,3),('smoke',4,3),('electric',4,2),('ground',4,2),('hit',4,2)]
for name,cols,rows in SHEETS:
    asset='T_Animated_'+name
    task=unreal.AssetImportTask()
    task.filename=str(OUT/(asset+'.png'))
    task.destination_path=ROOT+'/AnimatedTextures'
    task.destination_name=asset
    task.automated=True;task.save=True;task.replace_existing=True
    TOOLS.import_asset_tasks([task])
    tex=unreal.load_asset(ROOT+'/AnimatedTextures/'+asset)
    assert tex,asset
    tex.set_editor_property('address_x',unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property('address_y',unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property('lod_group',unreal.TextureGroup.TEXTUREGROUP_EFFECTS)
    # 원본 격자 비율을 유지하며 셀 당 256px로 GPU 리사이즈한다. 원본 PNG는 보존한다.
    tex.set_editor_property('power_of_two_mode',unreal.TexturePowerOfTwoSetting.RESIZE_TO_SPECIFIC_RESOLUTION)
    tex.set_editor_property('resize_during_build_x',cols*256)
    tex.set_editor_property('resize_during_build_y',rows*256)
    tex.set_editor_property('max_texture_size',1024)
    tex.set_editor_property('mip_gen_settings',unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_DEFAULT)
    tex.set_editor_property('never_stream',True)
    unreal.EditorAssetLibrary.save_loaded_asset(tex,False)

def material(name):
    path=ROOT+'/Materials/'+name
    mat=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else TOOLS.create_asset(name,ROOT+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
    mat.set_editor_property('two_sided',True)
    mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_MASKED)
    mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    return mat
def node(mat,cls,x=0,y=0,**props):
    n=MEL.create_material_expression(mat,cls,x,y)
    for key,value in props.items():n.set_editor_property(key,value)
    return n
def scalar(mat,name,value,y):
    return node(mat,unreal.MaterialExpressionScalarParameter,-700,y,parameter_name=name,default_value=value)
def custom(mat,code,inputs):
    pins=[]
    for name,_,_ in inputs:
        pin=unreal.CustomInput();pin.set_editor_property('input_name',name);pins.append(pin)
    c=node(mat,unreal.MaterialExpressionCustom,0,0,code=code,output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT4,inputs=pins)
    for name,expression,output in inputs:assert MEL.connect_material_expressions(expression,output,c,name)
    return c
def finish(mat,c):
    rgb=node(mat,unreal.MaterialExpressionComponentMask,300,0,r=True,g=True,b=True)
    alpha=node(mat,unreal.MaterialExpressionComponentMask,300,170,r=False,g=False,b=False,a=True)
    MEL.connect_material_expressions(c,'',rgb,'');MEL.connect_material_expressions(c,'',alpha,'')
    MEL.connect_material_property(rgb,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(alpha,'',unreal.MaterialProperty.MP_OPACITY_MASK)
    MEL.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
code=r'''
float p=saturate(Progress);
float phase=lerp(p,p<.25?p*1.6:.4+(p-.25)*.8,saturate(FastStart));
float frame=min(Frames-1,floor(phase*Frames));
float2 cell=float2(fmod(frame,Columns),floor(frame/Columns));
// 셀 안쪽으로 샘플링하여 인접 프레임의 경계가 나타나지 않게 한다.
float2 uv=(cell+clamp(UV,.004,.996))/float2(Columns,Rows);
float4 sheet=Texture2DSample(Atlas,AtlasSampler,uv);
float3 color=sheet.rgb*Tint.rgb;
float angle=HueShift*6.2831853;
float3 axis=normalize(float3(1,1,1));
float3 shifted=color*cos(angle)+cross(axis,color)*sin(angle)+axis*dot(axis,color)*(1-cos(angle));
// 무채색 중심/잉크는 유지하고 유채색 부분만 공격 팔레트에 맞춰 회전한다.
color=lerp(color,max(0,shifted),PaletteMix);
// 밝은 중심은 크림색을 유지하고 끝부분의 주황만 미세하게 이동한다.
color*=lerp(float3(1,1,1),float3(1,.86,1.05),saturate(Progress)*.18);
return float4(color*Gain,sheet.a);
'''
for lit in [False,True]:
    mat=material('M_HF_AnimatedLit' if lit else 'M_HF_Animated')
    MEL.delete_all_material_expressions(mat)
    mat.set_editor_property('opacity_mask_clip_value',.28)
    uv=node(mat,unreal.MaterialExpressionTextureCoordinate,-700,-400)
    tex=node(mat,unreal.MaterialExpressionTextureObjectParameter,-700,-250,parameter_name='Atlas',texture=unreal.load_asset(ROOT+'/AnimatedTextures/T_Animated_impact'))
    p=scalar(mat,'Progress',0,-80)
    cols=scalar(mat,'Columns',4,80);rows=scalar(mat,'Rows',4,240)
    frames=scalar(mat,'Frames',16,400);gain=scalar(mat,'Gain',1.35,560)
    fast=scalar(mat,'FastStart',0,1250)
    hue=scalar(mat,'HueShift',0,1400)
    mix=scalar(mat,'PaletteMix',1,1550)
    tint=node(mat,unreal.MaterialExpressionVectorParameter,-700,730,parameter_name='Tint',default_value=unreal.LinearColor(1,1,1,1))
    c=custom(mat,code,[('UV',uv,''),('Atlas',tex,''),('Progress',p,''),('Columns',cols,''),('Rows',rows,''),('Frames',frames,''),('Gain',gain,''),('Tint',tint,''),('FastStart',fast,''),('HueShift',hue,''),('PaletteMix',mix,'')])
    finish(mat,c)
    if lit:
        mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
        rgb=next(n for n in MEL.get_material_expressions(mat) if isinstance(n,unreal.MaterialExpressionComponentMask) and n.get_editor_property('r'))
        MEL.connect_material_property(rgb,'',unreal.MaterialProperty.MP_BASE_COLOR)
        mul=node(mat,unreal.MaterialExpressionMultiply,520,0)
        emission=scalar(mat,'Emission',.08,920)
        MEL.connect_material_expressions(rgb,'',mul,'A');MEL.connect_material_expressions(emission,'',mul,'B')
        MEL.connect_material_property(mul,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        rough=scalar(mat,'Roughness',.85,1080)
        MEL.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
        MEL.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat,False)
# 기존 후처리의 둥근 방사형 마스크도 날카로운 꼭짓점으로 바꾼다.
post=unreal.load_asset('/Game/ComicCombat/Materials/M_CC_ComicPost')
if post:
    c=next(n for n in MEL.get_material_expressions(post) if isinstance(n,unreal.MaterialExpressionCustom))
    code=c.get_editor_property('code')
    code=code.replace('float boundary=.045+.19*pow(abs(cos(flashA*6+sin(flashA*3)*.6)),18)\n    +.08*pow(abs(sin(flashA*9+.5)),38);',
        'float toothA=1-abs(frac(flashA*1.114+.13)*2-1);\nfloat toothB=1-abs(frac(flashA*1.751+.39)*2-1);\nfloat boundary=.03+.19*pow(toothA,5)+.08*pow(toothB,9);')
    code=code.replace('negative=lerp(negative,float3(.95,.81,.12),burst*(1-selected)*.72);',
        'negative=lerp(negative,float3(1,.94,.58),step(.68,vivid)*(1-selected));')
    c.set_editor_property('code',code)
    MEL.recompile_material(post);unreal.EditorAssetLibrary.save_loaded_asset(post,False)
print('ANIMATED_SHEETS_V8_COMPLETE')
