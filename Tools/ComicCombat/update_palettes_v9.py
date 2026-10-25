"""사용 중인 기존 머티리얼 그래프를 유지하고 팔레트 입력만 확장한다."""
import unreal
MEL=unreal.MaterialEditingLibrary
for name in ['M_HF_Animated','M_HF_AnimatedLit']:
 mat=unreal.load_asset('/Game/ComicCombat/Hifi/Materials/'+name)
 nodes=MEL.get_material_expressions(mat)
 c=next(n for n in nodes if isinstance(n,unreal.MaterialExpressionCustom))
 pins=list(c.get_editor_property('inputs'))
 names=[str(p.get_editor_property('input_name')) for p in pins]
 for param,value in [('HueShift',0.0),('PaletteMix',1.0)]:
  if param not in names:
   pin=unreal.CustomInput();pin.set_editor_property('input_name',param);pins.append(pin)
 c.set_editor_property('inputs',pins)
 for param,value in [('HueShift',0.0),('PaletteMix',1.0)]:
  n=next((n for n in nodes if isinstance(n,unreal.MaterialExpressionScalarParameter) and str(n.get_editor_property('parameter_name'))==param),None)
  if n is None:
   n=MEL.create_material_expression(mat,unreal.MaterialExpressionScalarParameter,-700,1400)
   n.set_editor_property('parameter_name',param);n.set_editor_property('default_value',value)
  assert MEL.connect_material_expressions(n,'',c,param)
 code=c.get_editor_property('code')
 if 'float angle=HueShift' not in code:
  code=code.replace('float3 color=sheet.rgb*Tint.rgb;', '''float3 color=sheet.rgb*Tint.rgb;
float angle=HueShift*6.2831853;
float3 axis=normalize(float3(1,1,1));
float3 shifted=color*cos(angle)+cross(axis,color)*sin(angle)+axis*dot(axis,color)*(1-cos(angle));
color=lerp(color,max(0,shifted),PaletteMix);''')
 c.set_editor_property('code',code)
 for n in nodes:
  if isinstance(n,unreal.MaterialExpressionScalarParameter) and str(n.get_editor_property('parameter_name'))=='Emission':n.set_editor_property('default_value',.08)
 MEL.recompile_material(mat)
 unreal.EditorAssetLibrary.save_loaded_asset(mat,False)
print('V9_PALETTES_COMPLETE')
