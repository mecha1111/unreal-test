"""켜져 있지 않은 화면 연출의 픽셀 계산만 생략한다. 기존 그래프 연결은 보존한다."""
import unreal
mat=unreal.load_asset('/Game/ComicCombat/Materials/M_CC_ComicPost')
for node in unreal.MaterialEditingLibrary.get_material_expressions(mat):
 if not isinstance(node,unreal.MaterialExpressionCustom):continue
 code=node.get_editor_property('code')
 if '// V10_UNIFORM_BRANCHES' in code:continue
 start=code.index('float2 speedP=')
 end=code.index('// 궁극기 전용:',start)
 speed=code[start:end]
 code=code[:start]+'// V10_UNIFORM_BRANCHES\n[branch] if (SpeedAmount > 0.f) {\n'+speed+'}\n'+code[end:]
 start=code.index('float2 flashP=')
 end=code.index('// 모으는 동안',start)
 flash=code[start:end].replace('float inkFlash=','inkFlash=')
 code=code[:start]+'float inkFlash=0.f;\n[branch] if (ImpactFlash > 0.f) {\n'+flash+'}\n'+code[end:]
 start=code.index('float paper=')
 end=code.index('return lerp(color,inkFlash',start)
 code=code[:start]+'[branch] if (NegativeAmount > 0.f) {\n'+code[start:end]+'}\n'+code[end:]
 node.set_editor_property('code',code)
unreal.MaterialEditingLibrary.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat,False)
print('V10_POST_BRANCHES_SAVED')
