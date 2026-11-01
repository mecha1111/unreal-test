"""Read original skirt attachment geometry without changing/saving the source blend."""
import bpy,json,math
from pathlib import Path
rig=bpy.data.objects['EXORCIST_Rig']
rows=[]
for i in range(1,9):
 b=rig.data.bones[f'skirt_{i}_1'];p=rig.matrix_world@b.head_local
 rows.append(dict(index=i,head=list(p),angle=math.degrees(math.atan2(p.y/.13,p.x/.17))%360))
obj=bpy.data.objects['Spring_02_skirt_panels']
out=dict(roots=rows,vertices=len(obj.data.vertices),materials=[s.name for s in obj.data.materials])
Path(r'C:/Users/jooan/Documents/Unreal Projects/test 5.8/Saved/skirt-binding-inspection.json').write_text(json.dumps(out,indent=2))
print('SKIRT_BINDING_INSPECTED')
