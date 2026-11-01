import bpy,json,re
from pathlib import Path
root=Path(r'C:\Users\jooan\Documents\Unreal Projects\test 5.8\SourceArt\ExorcistV10');root.mkdir(parents=True,exist_ok=True)
rig=bpy.data.objects['EXORCIST_Rig']
rig.animation_data_clear();rig.data.pose_position='REST'
for p in rig.pose.bones:
 for c in list(p.constraints):p.constraints.remove(c)
 p.matrix_basis.identity()
meshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and not o.name.startswith('EX_')]
report={'meshes':[],'materials':{}}
used_images=set()
for o in meshes:
 o.animation_data_clear()
 if o.data.shape_keys:
  o.data.shape_keys.animation_data_clear()
  for k in o.data.shape_keys.key_blocks:k.value=0
 for m in list(o.modifiers):
  if m.type!='ARMATURE':o.modifiers.remove(m)
 report['meshes'].append({'name':o.name,'materials':[m.name if m else None for m in o.data.materials],'uv':[u.name for u in o.data.uv_layers]})
 for m in o.data.materials:
  if not m or m.name in report['materials']:continue
  data={'images':[],'colors':[]}
  if m.use_nodes:
   for n in m.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image:
     used_images.add(n.image);data['images'].append({'node':n.label or n.name,'image':n.image.name})
    if n.type=='VALTORGB':data['colors'].append({'label':n.label or n.name,'colors':[(x.position,list(x.color)) for x in n.color_ramp.elements]})
  report['materials'][m.name]=data
tex=root/'Textures';tex.mkdir(exist_ok=True)
for im in used_images:
 name=re.sub(r'[^A-Za-z0-9_-]','_',im.name)
 im.filepath_raw=str(tex/(name+'.png'));im.file_format='PNG';im.save()
report['textures']={i.name:re.sub(r'[^A-Za-z0-9_-]','_',i.name)+'.png' for i in used_images}
bpy.ops.object.select_all(action='DESELECT')
for o in [rig]+meshes:o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.context.scene.frame_set(1)
from mathutils import Matrix
world={o:o.matrix_world.copy() for o in [rig]+meshes}
for o in [rig]+meshes:o.matrix_world=Matrix.Scale(100,4)@world[o]
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.01
bpy.ops.export_scene.fbx(filepath=str(root/'SK_EX_Game.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},use_mesh_modifiers=False,add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',use_custom_props=False,path_mode='STRIP')
(root/'export-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('EXPORT_COMPLETE',root)
