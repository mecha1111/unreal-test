"""Post-process secondary motion, evaluated after the existing combat animation.
Bone-based cloth/hair, not an imported Blender cloth cache. Colliders follow limbs.
"""
import unreal,json
from pathlib import Path
D='/Game/ExorcistV10';K=unreal.KawaiiPhysicsEditorLibrary
def run(dt):
 unreal.unregister_slate_post_tick_callback(unreal._ex_dynamics)
 mesh=unreal.load_asset(D+'/Character/SK_EX_Optimized');skel=mesh.skeleton
 asset=D+'/Animations/ABP_EX_SecondaryMotion'
 bp=unreal.load_asset(asset)
 if not bp:
  factory=unreal.AnimBlueprintFactory();factory.set_editor_property('target_skeleton',skel)
  bp=unreal.AssetToolsHelpers.get_asset_tools().create_asset('ABP_EX_SecondaryMotion',D+'/Animations',unreal.AnimBlueprint,factory)
 names=[str(n) for n in K.find_bones_by_pattern(skel,r'[A-Za-z0-9_]+')]
 def roots(pattern):return [str(n) for n in K.find_bones_by_pattern(skel,pattern)]
 groups=[
  ('skirt',roots(r'skirt_[1-8]_1'),.38,.22,.95,.93,2.8,120,0),
  ('sleeve',roots(r'Spring_03_draped_sleeve_chain[1-3]_1'),.60,.32,.84,.87,.8,45,0),
  ('accessories',roots(r'Spring_(?:04|05|06|07|08|09|10)_[A-Za-z0-9_]+_chain[1-3]_1'),.60,.40,.87,.90,.6,30,0),
  ('hair',roots(r'(?:hair_[1-6]_1|bang_(?:center|left|right)_1)'),.35,.42,.92,.94,1.1,22,0),
  ('locks',roots(r'tripo_lock_[0-9]+'),.38,.62,.96,.97,.6,12,7),
 ]
 records=[]
 def setp(h,name,value):
  assert K.set_graph_node_property_from_string(h,name,str(value)),(name,value)
 def vec(v):return '(X=%.6f,Y=%.6f,Z=%.6f)'%(v.x,v.y,v.z)
 def cap(h,parent,child,radius,shorten=.88):
  a=K.get_graph_node_reference_bone_transform(h,parent);b=K.get_graph_node_reference_bone_transform(h,child)
  assert a is not None and b is not None,(parent,child)
  local=unreal.MathLibrary.inverse_transform_location(a,b.translation)
  rot=unreal.MathLibrary.make_rot_from_z(local)
  return '(DrivingBone=(BoneName="%s"),OffsetLocation=%s,OffsetRotation=(Pitch=%.5f,Yaw=%.5f,Roll=%.5f),Radius=%.3f,Length=%.3f)'%(parent,vec(local*.5),rot.pitch,rot.yaw,rot.roll,radius,local.length()*shorten)
 for name,bones,damp,stiff,move,turn,radius,angle,dummy in groups:
  assert bones,(name,names)
  req=unreal.KawaiiPhysicsNodePlacementRequest();req.root_bone_name=bones[0];req.auto_connect=True
  handles=K.add_kawaii_physics_nodes(bp,[req],unreal.KawaiiPhysicsPlacementMatchKey.ROOT_BONE)
  h=handles[0]
  if dummy:
   a=K.get_graph_node_reference_bone_transform(h,'hair_1_1');b=K.get_graph_node_reference_bone_transform(h,'hair_1_2')
   direction=unreal.MathLibrary.inverse_transform_location(a,b.translation)
   components=[direction.x,direction.y,direction.z];axis=max(range(3),key=lambda i:abs(components[i]))
   setp(h,'BoneForwardAxis','XYZ'[axis]+('_Positive' if components[axis]>0 else '_Negative'))
  setp(h,'AdditionalRootBones','('+','.join('(RootBone=(BoneName="%s"))'%n for n in bones[1:])+')')
  setp(h,'PhysicsSettings',f'(Damping={damp},Stiffness={stiff},WorldDampingLocation={move},WorldDampingRotation={turn},Radius={radius},LimitAngle={angle})')
  setp(h,'Gravity','(X=0,Y=0,Z=-980)');setp(h,'bUseWorldSpaceGravity','True')
  setp(h,'TargetFramerate',60);setp(h,'TeleportDistanceThreshold',220);setp(h,'TeleportRotationThreshold',135)
  setp(h,'DummyBoneLength',dummy);setp(h,'bNeedWarmUp','True');setp(h,'WarmUpFrames',12)
  setp(h,'bUpdatePhysicsSettingsInGame','False')
  setp(h,'bEnableWind','True' if name in ['hair','locks'] else 'False');setp(h,'WindScale',.012)
  setp(h,'WindDirectionNoiseAngle',5)
  capsules=[]
  if name in ['skirt','accessories']:
   for side in ['L','R']:
    capsules.append(cap(h,'upper_leg_'+side,'lower_leg_'+side,9.4,.96))
    capsules.append(cap(h,'lower_leg_'+side,'foot_'+side,4.3,.80))
   capsules.append(cap(h,'hips','spine',7.5,.65))
  if name in ['sleeve','accessories']:
   for side in ['L','R']:
    capsules.append(cap(h,'upper_arm_'+side,'lower_arm_'+side,4.0,.8))
    capsules.append(cap(h,'lower_arm_'+side,'hand_'+side,3.1,.83))
   capsules.append(cap(h,'spine','chest',9.5,.7))
  if name in ['hair','locks']:
   head='head' if 'head' in names else 'head1'
   setp(h,'SphericalLimits',f'((DrivingBone=(BoneName="{head}"),OffsetLocation=(X=0,Y=0,Z=0),Radius=5.6))')
  setp(h,'CapsuleLimits','('+','.join(capsules)+')')
  if name=='skirt':
   setp(h,'BoneSubdivisionCount',3);setp(h,'BoneConstraintSubdivisionCount',2)
   constraints=[]
   for i in range(1,9):
    j=i%8+1
    for suffix in ['2','2_CharakitEnd']:
     constraints.append(f'(Bone1=(BoneName="skirt_{i}_{suffix}"),Bone2=(BoneName="skirt_{j}_{suffix}"))')
   setp(h,'BoneConstraints','('+','.join(constraints)+')')
   setp(h,'BoneConstraintIterationCountBeforeCollision',3);setp(h,'BoneConstraintIterationCountAfterCollision',0)
   sync=[]
   for side,indices in [('L',[1,2,8]),('R',[4,5,6])]:
    targets=','.join(f'(Bone=(BoneName="skirt_{i}_2"),bIncludeChildBones=True)' for i in indices)
    sync.append(f'(Bone=(BoneName="lower_leg_{side}"),TargetRoots=({targets}),GlobalScale=(X=.30,Y=.50,Z=.55))')
   setp(h,'SyncBones','('+','.join(sync)+')')
  elif name=='sleeve':setp(h,'BoneSubdivisionCount',2)
  records.append({'group':name,'roots':bones,'capsules':len(capsules),'damping':damp,'stiffness':stiff})
 K.set_anim_graph_input_pose(bp)
 for graph in bp.get_animation_graphs():
  for node in graph.get_graph_nodes_of_class(unreal.load_class(None,'/Script/KawaiiPhysicsEd.AnimGraphNode_KawaiiPhysics')):
   settings=node.get_editor_property('node');settings.set_editor_property('lod_threshold',2)
   root=str(settings.get_editor_property('root_bone').get_editor_property('bone_name'))
   settings.set_editor_property('final_body_collision_iterations',6 if root.startswith('skirt_') else 0)
   node.set_editor_property('node',settings)
 assert K.is_anim_graph_input_pose_connected(bp)
 errors,messages=K.compile_anim_blueprint_with_messages(bp)
 assert errors==0,messages
 unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
 mesh.set_editor_property('post_process_anim_blueprint',bp.generated_class())
 mesh.set_editor_property('positive_bounds_extension',unreal.Vector(10,10,10))
 mesh.set_editor_property('negative_bounds_extension',unreal.Vector(10,10,10))
 unreal.EditorAssetLibrary.save_loaded_asset(mesh,False)
 path=Path(unreal.Paths.project_dir())/'Tools/ComicCombat/exorcist-dynamics.json'
 path.write_text(json.dumps({'groups':records,'compile_messages':list(messages),'fixed_step':60},indent=2))
 print('EX_DYNAMICS_DONE',len(records))
unreal._ex_dynamics=unreal.register_slate_post_tick_callback(run)
