"""Visible character-only cel lighting and restrained contact highlight; edit graphs in place."""
import unreal
def run(dt):
    unreal.unregister_slate_post_tick_callback(unreal._toon_refine)
    mel=unreal.MaterialEditingLibrary
    path='/Game/ExorcistV10/Materials/M_EX_Outline'
    mat=unreal.load_asset(path)
    backup='/Game/ExorcistV10/BeforeDynamics/M_EX_BeforeCelLighting'
    if not unreal.EditorAssetLibrary.does_asset_exist(backup):unreal.EditorAssetLibrary.duplicate_asset(path,backup)
    custom=next(n for n in mel.get_material_expressions(mat) if isinstance(n,unreal.MaterialExpressionCustom))
    inputs=list(custom.get_editor_property('inputs'))
    if not any(str(p.get_editor_property('input_name'))=='BaseColor' for p in inputs):
        n=mel.create_material_expression(mat,unreal.MaterialExpressionSceneTexture,-500,1100)
        n.set_editor_property('scene_texture_id',unreal.SceneTextureId.PPI_BASE_COLOR)
        pin=unreal.CustomInput();pin.set_editor_property('input_name','BaseColor');inputs.append(pin)
        custom.set_editor_property('inputs',inputs)
        # Let the editor reconstruct the custom node's new input pin before linking.
        unreal._toon_refine=unreal.register_slate_post_tick_callback(run)
        return
    base_node=next(n for n in mel.get_material_expressions(mat) if isinstance(n,unreal.MaterialExpressionSceneTexture) and n.get_editor_property('scene_texture_id')==unreal.SceneTextureId.PPI_BASE_COLOR)
    assert mel.connect_material_expressions(base_node,'Color',custom,'BaseColor')
    custom.set_editor_property('code',r'''
float2 uv=GetDefaultSceneTextureUV(Parameters,25);
float2 px=View.BufferSizeAndInvSize.zw*1.2;
float selected=(abs(Stencil.r-11)<.1)?1:0;
float visible=selected*step(Depth.r,WorldDepth.r+1);
float edge=0;
[unroll] for(int i=0;i<8;i++){
 float angle=i*.785398163;float2 d=float2(cos(angle),sin(angle))*px;
 float s=SceneTextureLookup(uv+d,25,false).r;
 float z=SceneTextureLookup(uv+d,13,false).r;
 float sceneZ=SceneTextureLookup(uv+d,1,false).r;
 edge+=1-((abs(s-11)<.1&&z<=sceneZ+1)?1:0);
}
// Estimate illumination from the original painted albedo; keep hues and highlights.
float3 lum=float3(.2126,.7152,.0722);
float base=max(.035,dot(BaseColor.rgb,lum));
float lighting=dot(Scene.rgb,lum)/max(.001,base*View.PreExposure);
float bands=.38+.32*smoothstep(.43,.49,lighting)+.38*smoothstep(.82,.88,lighting);
float shadedRatio=clamp(bands/max(.08,lighting),.60,1.40);
float highlight=smoothstep(1.3,2.1,lighting);
float3 cel=Scene.rgb*lerp(shadedRatio,1,highlight);
float3 result=lerp(Scene.rgb,cel,visible*.88);
float coverage=smoothstep(.06,.48,edge/8)*visible*(1-smoothstep(1600,2600,Depth.r));
return lerp(result,result*.07,coverage*.92);
''')
    mat.set_editor_property('blendable_location',unreal.BlendableLocation.BL_SCENE_COLOR_BEFORE_DOF)
    mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat,False)
    path='/Game/ComicCombat/Materials/M_CC_HighlightOnly';mat=unreal.load_asset(path)
    backup='/Game/ExorcistV10/BeforeDynamics/M_CC_BeforeRestrainedHighlight'
    if not unreal.EditorAssetLibrary.does_asset_exist(backup):unreal.EditorAssetLibrary.duplicate_asset(path,backup)
    custom=next(n for n in mel.get_material_expressions(mat) if isinstance(n,unreal.MaterialExpressionCustom))
    custom.set_editor_property('code',r'''
// Fullscreen combat overlays are disabled by user request.
return Scene.rgb;
''')
    mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat,False)
    print('TOON_AND_RESTRAINED_HIGHLIGHT_SAVED')
unreal._toon_refine=unreal.register_slate_post_tick_callback(run)
