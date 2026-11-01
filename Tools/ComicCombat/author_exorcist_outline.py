"""Thin, depth-tested character silhouette. No world colour grading."""
import unreal
def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._ex_outline)
 M=unreal.MaterialEditingLibrary;at=unreal.AssetToolsHelpers.get_asset_tools()
 path='/Game/ExorcistV10/Materials';name='M_EX_Outline'
 mat=unreal.load_asset(path+'/'+name) or at.create_asset(name,path,unreal.Material,unreal.MaterialFactoryNew())
 M.delete_all_material_expressions(mat)
 mat.set_editor_property('material_domain',unreal.MaterialDomain.MD_POST_PROCESS)
 # Draw before TSR, and inside geometry so reprojection uses character velocity.
 mat.set_editor_property('blendable_location',unreal.BlendableLocation.BL_SCENE_COLOR_BEFORE_DOF)
 mat.set_editor_property('blendable_priority',0)
 inputs=[];nodes=[]
 for name,tex in [('Scene',unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0),('Stencil',unreal.SceneTextureId.PPI_CUSTOM_STENCIL),('Depth',unreal.SceneTextureId.PPI_CUSTOM_DEPTH),('WorldDepth',unreal.SceneTextureId.PPI_SCENE_DEPTH)]:
  n=M.create_material_expression(mat,unreal.MaterialExpressionSceneTexture);n.set_editor_property('scene_texture_id',tex)
  p=unreal.CustomInput();p.set_editor_property('input_name',name);inputs.append(p);nodes.append((name,n))
 code=r'''
 float2 uv=GetDefaultSceneTextureUV(Parameters,25);
 float2 px=View.BufferSizeAndInvSize.zw*.72;
 float edge=0;
 float selected=(abs(Stencil.r-11)<.1||abs(Stencil.r-12)<.1)?1:0;
 [unroll] for(int i=0;i<8;i++){
  float angle=i*.785398163;
  float2 d=float2(cos(angle),sin(angle))*px;
  float s=SceneTextureLookup(uv+d,25,false).r;
  float z=SceneTextureLookup(uv+d,13,false).r;
  float sceneZ=SceneTextureLookup(uv+d,1,false).r;
  float sameVisible=abs(s-Stencil.r)<.1&&z<=sceneZ+1;
  edge+=1-sameVisible;
 }
 float distanceFade=1-smoothstep(1400,2600,Depth.r);
 float coverage=smoothstep(.08,.55,edge/8)*selected*step(Depth.r,WorldDepth.r+1);
 // Hue follows the surface rather than a pure-black sticker. HDR/pre-exposed.
 float3 ink=Scene.rgb*.16;
 return lerp(Scene.rgb,ink,coverage*.72*distanceFade);
 '''
 c=M.create_material_expression(mat,unreal.MaterialExpressionCustom);c.set_editor_property('code',code);c.set_editor_property('inputs',inputs);c.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
 for name,n in nodes:M.connect_material_expressions(n,'Color',c,name)
 M.connect_material_property(c,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
 M.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat,False)
 print('EX_OUTLINE_DONE')
if unreal.EditorAssetLibrary.does_asset_exist('/Game/ExorcistV10/Materials/M_EX_Outline'):
 exec(compile(open(unreal.Paths.project_dir()+'Tools/ComicCombat/refine_toon_and_highlight.py',encoding='utf-8').read(),'refine_toon_and_highlight.py','exec'))
else:
 unreal._ex_outline=unreal.register_slate_post_tick_callback(run)
