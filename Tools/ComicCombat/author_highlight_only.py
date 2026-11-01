"""궁극기/콤보 접촉 때만 사용하는 화면 반전. 기본 화면 필터는 포함하지 않는다."""
import unreal

def run(dt):
    unreal.unregister_slate_post_tick_callback(unreal._highlight_author)
    mel=unreal.MaterialEditingLibrary
    folder='/Game/ComicCombat/Materials';name='M_CC_HighlightOnly'
    mat=unreal.load_asset(folder+'/'+name)
    if not mat:mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,unreal.Material,unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property('material_domain',unreal.MaterialDomain.MD_POST_PROCESS)
    options=[x for x in dir(unreal.BlendableLocation) if 'TONEMAP' in x.upper() and 'AFTER' in x.upper()]
    if options:mat.set_editor_property('blendable_location',getattr(unreal.BlendableLocation,options[0]))
    mat.set_editor_property('blendable_priority',10)
    def node(cls,x,y,**kw):
        n=mel.create_material_expression(mat,cls,x,y)
        for k,v in kw.items():n.set_editor_property(k,v)
        return n
    scene=node(unreal.MaterialExpressionSceneTexture,-600,0,scene_texture_id=unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
    flash=node(unreal.MaterialExpressionScalarParameter,-600,180,parameter_name='ImpactFlash',default_value=0)
    negative=node(unreal.MaterialExpressionScalarParameter,-600,340,parameter_name='NegativeAmount',default_value=0)
    center=node(unreal.MaterialExpressionVectorParameter,-600,500,parameter_name='ImpactCenter',default_value=unreal.LinearColor(.5,.5,0,0))
    age=node(unreal.MaterialExpressionScalarParameter,-600,620,parameter_name='HighlightAge',default_value=10)
    stencil=node(unreal.MaterialExpressionSceneTexture,-600,740,scene_texture_id=unreal.SceneTextureId.PPI_CUSTOM_STENCIL)
    depth=node(unreal.MaterialExpressionSceneTexture,-600,860,scene_texture_id=unreal.SceneTextureId.PPI_CUSTOM_DEPTH)
    worlddepth=node(unreal.MaterialExpressionSceneTexture,-600,980,scene_texture_id=unreal.SceneTextureId.PPI_SCENE_DEPTH)
    inputs=[]
    for name in ['Scene','Flash','Negative','Center','Age','Stencil','Depth','WorldDepth']:
        pin=unreal.CustomInput();pin.set_editor_property('input_name',name);inputs.append(pin)
    code=r'''
float3 src=Scene.rgb;
float visible=step(Depth.r,WorldDepth.r+2);
float character=(abs(Stencil.r-11)<.1||abs(Stencil.r-12)<.1)?visible:0;
float effect=abs(Stencil.r-13)<.1?visible:0;
float2 p=(GetViewportUV(Parameters)-Center.xy)*float2(View.ViewSizeAndInvSize.x/View.ViewSizeAndInvSize.y,1);
float r=length(p);float a=atan2(p.y,p.x);
// Angular shapes expand from the actual contact. Character geometry supplies
// silhouettes; exposure/sky brightness cannot turn the whole screen white.
float rays=step(.987,sin(a*7+.3))*smoothstep(.30,.5,r);
// Exact ray/polygon intersection gives straight ink edges, not rounded petals.
float stepAngle=3.14159265/9;
float theta=a+3.14159265;
float segment=floor(theta/stepAngle);
float localAngle=theta-segment*stepAngle;
float rA=fmod(segment,2)<.5?.22:.82+.13*sin(segment*2.7);
float rB=fmod(segment+1,2)<.5?.22:.82+.13*sin((segment+1)*2.7);
float radius=rA*rB*sin(stepAngle)/max(.001,rB*sin(stepAngle-localAngle)+rA*sin(localAngle));
float burst=(1-smoothstep(radius-.002,radius+.002,r));
float bw=max(effect,max(burst,rays));
// Read black actor silhouettes inside white energy, with a thin white rim.
float2 uv=GetDefaultSceneTextureUV(Parameters,25);
float rim=0;
[unroll] for(int i=0;i<4;i++){
 float2 d=(i==0?float2(1,0):i==1?float2(-1,0):i==2?float2(0,1):float2(0,-1))*View.BufferSizeAndInvSize.zw*1.5;
 float s=SceneTextureLookup(uv+d,25,false).r;
 float z=SceneTextureLookup(uv+d,13,false).r;
 float sz=SceneTextureLookup(uv+d,1,false).r;
 rim=max(rim,((abs(s-11)<.1||abs(s-12)<.1)&&z<=sz+2&&z<=WorldDepth.r+3)?1:0);
}
bw=lerp(bw,0,character);bw=max(bw,rim*(1-character));
float l=dot(src,float3(.2126,.7152,.0722));
float3 stage=lerp(float3(.018,.022,.035)+src*.10,src,character);
stage=lerp(stage,src*1.15,effect);
float pulse=1-smoothstep(.14,.50,Age);
float coloredRay=rays*pulse*.55*(1-character);
stage+=coloredRay*float3(.40,.9,1.0);
float3 result=lerp(src,stage,saturate(Negative));
return lerp(result,bw.xxx,saturate(Flash));
'''
    c=node(unreal.MaterialExpressionCustom,0,0,code=code,inputs=inputs,output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    for name,n,output in [('Scene',scene,'Color'),('Flash',flash,''),('Negative',negative,''),('Center',center,''),('Age',age,''),('Stencil',stencil,'Color'),('Depth',depth,'Color'),('WorldDepth',worlddepth,'Color')]:mel.connect_material_expressions(n,output,c,name)
    mel.connect_material_property(c,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat,False)
    print('HIGHLIGHT_ONLY_SAVED')
if unreal.EditorAssetLibrary.does_asset_exist('/Game/ComicCombat/Materials/M_CC_HighlightOnly'):
    exec(compile(open(unreal.Paths.project_dir()+'Tools/ComicCombat/refine_toon_and_highlight.py',encoding='utf-8').read(),'refine_toon_and_highlight.py','exec'))
else:
    unreal._highlight_author=unreal.register_slate_post_tick_callback(run)
