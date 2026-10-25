import math
import unreal
from pathlib import Path

work=Path(unreal.Paths.project_dir()).resolve() / 'Tools/ComicCombat'
lines=['o ComicArc']
segments=48
for i in range(segments+1):
    t=i/segments
    a=-2.5+t*3.9
    width=13*(max(.03,math.sin(t*math.pi))**.65)
    for side in [-1,1]:
        radius=58+side*width
        lines.append(f'v {math.cos(a)*radius:.6f} {math.sin(a)*radius:.6f} {math.sin(a*1.2)*13:.6f}')
for i in range(segments+1):
    for v in [0,1]: lines.append(f'vt {i/segments:.6f} {v}')
for i in range(segments):
    a=i*2+1;b=a+1;c=a+2;d=a+3
    lines.extend([f'f {a}/{a} {c}/{c} {b}/{b}',f'f {b}/{b} {c}/{c} {d}/{d}'])
(work/'SM_ComicArc.obj').write_text('\n'.join(lines))
path='/Game/ComicCombat/Meshes/SM_ComicArc'
if not unreal.EditorAssetLibrary.does_asset_exist(path):
    task=unreal.AssetImportTask()
    task.filename=str(work/'SM_ComicArc.obj')
    task.destination_path='/Game/ComicCombat/Meshes'
    task.destination_name='SM_ComicArc'
    task.automated=True
    task.save=True
    options=unreal.FbxImportUI()
    options.import_mesh=True
    options.import_materials=False
    options.import_textures=False
    options.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
    options.static_mesh_import_data.combine_meshes=True
    task.options=options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    print('RIBBON_IMPORTED',task.imported_object_paths)

# author_materials.py와 같은 노드 작성 함수를 공유한다.
mat=material('M_CC_Ribbon')
uv=node(mat,unreal.MaterialExpressionTextureCoordinate,-700,-200)
p=scalar(mat,'Progress',0,0)
tint=node(mat,unreal.MaterialExpressionVectorParameter,-700,160,parameter_name='Tint',default_value=unreal.LinearColor(1,.02,.35,1))
code=r'''
float u=UV.x;
float v=UV.y;
float head=saturate(Progress*7);
float tail=saturate((Progress-.17)/.83);
float edge=.035+.028*sin(u*53)+.018*sin(u*97);
float coverage=step(tail,u)*step(u,head)*step(edge,v)*step(v,1-edge);
float inner=step(.16,v)*step(v,.80);
float highlight=step(.56+.04*sin(u*31),v)*step(v,.75);
float3 color=lerp(float3(.006,.008,.025),Tint.rgb,inner);
color=lerp(color,float3(1,.52,.85),highlight);
float cut=step(.94,frac(u*7))*step(v,.42);
coverage*=1-cut;
return float4(color,coverage);
'''
c=custom(mat,code,[('UV',uv,''),('Progress',p,''),('Tint',tint,'')])
finish(mat,c)
print('RIBBON_READY')
