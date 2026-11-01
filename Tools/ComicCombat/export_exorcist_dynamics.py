"""Run on the original blend in a separate background Blender. Never saves over it.
Convert Blender-only cloth attachment weights to the existing accessory bones.
The skeleton, face morphs, UVs and material names remain compatible with gameplay.
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector

ROOT=Path(r'C:\Users\jooan\Documents\Unreal Projects\test 5.8')
rig=bpy.data.objects['EXORCIST_Rig']
rig.animation_data_clear();rig.data.pose_position='REST'
audit={}
def clamp(v): return max(0.,min(1.,v))
def assign(obj, vertex, weights):
    weights=sorted(((n,w) for n,w in weights.items() if w>0.00001),key=lambda p:-p[1])[:4]
    total=sum(w for _,w in weights)
    for name,w in weights:
        group=obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
        group.add([vertex.index],w/total,'REPLACE')

for obj in [bpy.data.objects['Spring_02_skirt_panels'],bpy.data.objects['Spring_03_draped_sleeve'],bpy.data.objects['Spring_04_sleeve_straps']]:
    pins=obj.vertex_groups.get('EX_ClothPin')
    old=[]
    for v in obj.data.vertices:
        weights={obj.vertex_groups[g.group].name:g.weight for g in v.groups}
        old.append(weights)
    obj.vertex_groups.clear()
    skirt='skirt_panels' in obj.name
    prefix='Spring_03_draped_sleeve' if 'draped_sleeve' in obj.name else 'Spring_04_sleeve_straps'
    for v in obj.data.vertices:
        p=obj.matrix_world@v.co; weights={}
        if skirt:
            # Upper waist is pinned to hips, lower fabric follows adjacent skirt columns.
            angle=(math.atan2(p.y/.13,p.x/.17)%(2*math.pi))/(math.pi/4)
            a=int(angle); mix=angle-a
            pin=clamp((p.z-1.045)/.065)
            lower=clamp((.97-p.z)/.17)
            weights['hips']=pin
            for index,amount in [(a%8+1,1-mix),((a+1)%8+1,mix)]:
                weights[f'skirt_{index}_1']=(1-pin)*amount*(1-lower)
                weights[f'skirt_{index}_2']=(1-pin)*amount*lower
            # A small rest clearance prevents the surface starting inside a thigh.
            radial=Vector((p.x,p.y,0)); radial.normalize()
            v.co += obj.matrix_world.inverted().to_3x3() @ (radial*.009*(1-pin))
        else:
            roots=[rig.data.bones[f'{prefix}_chain{i}_1'] for i in range(1,4)]
            distances=sorted(((abs(p.x-b.head_local.x),i,b) for i,b in enumerate(roots)),key=lambda a:a[0])[:2]
            factors=[1/max(.008,d)**3 for d,_,_ in distances]; total=sum(factors)
            # Pinned seam blends to its actual arm parent. Free tips have two joints.
            top=max(b.head_local.z for _,_,b in distances)
            pin=clamp((p.z-(top-.025))/.025)
            for (_,i,b),factor in zip(distances,factors):
                amount=factor/total; lower=clamp((b.head_local.z-.025-p.z)/.075)
                parent=b.parent.name
                weights[parent]=weights.get(parent,0)+pin*amount
                weights[f'{prefix}_chain{i+1}_1']=(1-pin)*amount*(1-lower)
                weights[f'{prefix}_chain{i+1}_2']=(1-pin)*amount*lower
        assign(obj,v,weights)
    audit[obj.name]={'vertices':len(obj.data.vertices),'groups':[g.name for g in obj.vertex_groups]}

# Reuse the established exporter in a separate output folder. It does not save the blend.
source=(ROOT/'Tools/ComicCombat/export_exorcist_optimized.py').read_text(encoding='utf-8-sig')
source=source.replace("root.mkdir(parents=True,exist_ok=True)","root=root/'Dynamics';root.mkdir(parents=True,exist_ok=True)")
source=source.replace('SK_EX_Optimized.fbx','SK_EX_Dynamics.fbx')
exec(compile(source,'export_exorcist_optimized.py','exec'))
(root/'dynamics-weights.json').write_text(json.dumps(audit,indent=2))
print('DYNAMICS_EXPORT_DONE')
