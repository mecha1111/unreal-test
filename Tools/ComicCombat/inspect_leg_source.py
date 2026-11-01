import bpy,json
from pathlib import Path
from mathutils import Vector
out=[]
for o in bpy.data.objects:
 if o.type!='MESH' or not any(x in o.name.lower() for x in ['thigh','chain','tassel','strap']):continue
 bounds=[o.matrix_world@Vector(c) for c in o.bound_box]
 totals={}
 for v in o.data.vertices:
  for g in v.groups:
   n=o.vertex_groups[g.group].name;totals[n]=totals.get(n,0)+g.weight
 out.append(dict(name=o.name,hidden=o.hide_render,bounds=[[min(v[i] for v in bounds),max(v[i] for v in bounds)] for i in range(3)],groups=totals))
Path(r'C:/Users/jooan/Documents/Unreal Projects/test 5.8/Saved/leg-source-inspection.json').write_text(json.dumps(out,indent=2))
