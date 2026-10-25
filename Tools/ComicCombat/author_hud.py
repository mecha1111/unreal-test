import unreal

def author_hud_assets():
    texture=unreal.load_asset('/Game/ComicCombat/UI/T_ComboBackplate')
    if not texture:
        unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.PNG 0')
        try:
            task=unreal.AssetImportTask()
            task.filename=unreal.Paths.project_dir()+'Tools/ComicCombat/UI/combo-backplate-v1.png'
            task.destination_path='/Game/ComicCombat/UI';task.destination_name='T_ComboBackplate'
            task.automated=True;task.save=True;task.factory=unreal.TextureFactory()
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            texture=unreal.load_asset(task.imported_object_paths[0])
            texture.set_editor_property('lod_group',unreal.TextureGroup.TEXTUREGROUP_UI)
            texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_EDITOR_ICON)
            texture.set_editor_property('mip_gen_settings',unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
            texture.set_editor_property('max_texture_size',512)
            unreal.EditorAssetLibrary.save_loaded_asset(texture)
        finally:
            unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.PNG 1')
    material=unreal.load_asset('/Game/ComicCombat/UI/M_ComboBackplate')
    if not material:material=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_ComboBackplate','/Game/ComicCombat/UI',unreal.Material,unreal.MaterialFactoryNew())
    material.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property('two_sided',True)
    mel=unreal.MaterialEditingLibrary
    existing=list(mel.get_material_expressions(material))
    def node(cls,x,y,**kwargs):
        n=next((e for e in existing if isinstance(e,cls)),None)
        if n is None:n=mel.create_material_expression(material,cls,x,y)
        for k,v in kwargs.items():n.set_editor_property(k,v)
        return n
    tex=node(unreal.MaterialExpressionTextureSample,-600,0,texture=texture)
    tint=node(unreal.MaterialExpressionVectorParameter,-600,220,parameter_name='ComboTint',default_value=unreal.LinearColor(.03,.87,.82,1))
    fade=node(unreal.MaterialExpressionScalarParameter,-600,400,parameter_name='Fade',default_value=1.0)
    pins=[]
    for name in ['Ink','Tint']:
        pin=unreal.CustomInput();pin.set_editor_property('input_name',name);pins.append(pin)
    shader=node(unreal.MaterialExpressionCustom,-240,0,inputs=pins,output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,
        code='float accent=saturate((max(Ink.g,Ink.b)-Ink.r)*3.5); float bright=max(Ink.r,max(Ink.g,Ink.b)); return lerp(Ink,Tint*bright,accent);')
    mel.connect_material_expressions(tex,'RGB',shader,'Ink');mel.connect_material_expressions(tint,'',shader,'Tint')
    opacity=node(unreal.MaterialExpressionMultiply,-220,220)
    mel.connect_material_expressions(tex,'A',opacity,'A');mel.connect_material_expressions(fade,'',opacity,'B')
    mel.connect_material_property(shader,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.connect_material_property(opacity,'',unreal.MaterialProperty.MP_OPACITY)
    mel.recompile_material(material);unreal.EditorAssetLibrary.save_loaded_asset(material)
    print('HUD_BACKPLATE_READY',material.get_path_name())

def run_once(dt):
    unreal.unregister_slate_post_tick_callback(unreal._hud_asset_author)
    author_hud_assets()
unreal._hud_asset_author=unreal.register_slate_post_tick_callback(run_once)
