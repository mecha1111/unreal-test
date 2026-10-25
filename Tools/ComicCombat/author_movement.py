"""발밑 곡선/먼지 머티리얼, 가는 주변 속도선, 도약/공중 차기/착지 포즈를 만든다."""
import unreal,math,json
from pathlib import Path
WORK=Path(unreal.Paths.project_dir()).resolve() / 'Tools/ComicCombat'
source=(WORK/'author_materials.py').read_text(encoding='utf-8')
# 공용 노드 도우미만 사용하며 기존 바닥/전투 머티리얼을 다시 만들지 않는다.
ROOT='/Game/ComicCombat'
TOOLS=unreal.AssetToolsHelpers.get_asset_tools()
MEL=unreal.MaterialEditingLibrary
exec(compile(source[source.index('def material('):source.index("shape=material(")],'material_helpers','exec'))
mat=material('M_CC_Movement')
mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
uv=node(mat,unreal.MaterialExpressionTextureCoordinate,-700,-250)
p=scalar(mat,'Progress',0,-100)
shape=scalar(mat,'Shape',0,70)
seed=scalar(mat,'Seed',0,240)
tint=node(mat,unreal.MaterialExpressionVectorParameter,-700,400,parameter_name='Tint',default_value=unreal.LinearColor(.68,.67,.62,1))
code=r'''
float2 q=UV*2-1;
float r=length(q);
float a=atan2(q.y,q.x);
float d=10;
if(Shape<.5){
    // 반원 두 개가 갈라져 흩어지는 붓 먼지. 구름 덩어리나 큰 흰 카드로 채우지 않는다.
    float2 c=q-float2(-.14,.02);
    float ca=atan2(c.y,c.x);
    float rr=.53+.018*sin(ca*3+Seed);
    float width=.095*pow(saturate(.5+.5*sin(ca*1.4+Seed)),.7);
    d=abs(length(c)-rr)-width;
    d=max(d,(sin(ca*1.4+Seed+Progress)-.60)*.10);
    float2 e=(q-float2(.30,-.19))*float2(1.1,1.5);
    float ea=atan2(e.y,e.x);
    float d2=abs(length(e)-.39)-.060*pow(saturate(.5+.5*sin(ea+Seed)),.7);
    d2=max(d2,(sin(ea*1.3+Seed)-.35)*.14);
    d=min(d,d2);
}else if(Shape<1.5){
    float taper=saturate(1-abs(q.x));
    d=abs(q.y-.05*sin(q.x*3+Seed))-.055*taper*taper;
    d=max(d,abs(q.x)-.94);
}else{
    d=abs(r-(.73+.018*sin(a*9+Seed)))-.030*(1-Progress*.65);
    d=max(d,(sin(a*4+Seed)-.3)*.12);
}
float aa=max(fwidth(d),.005);
float mask=1-smoothstep(-aa,aa,d);
float grain=frac(sin(dot(floor(UV*80),float2(12.9898,78.233))+Seed)*43758.5453);
mask*=step(saturate((Progress-.48)/.52),grain);
float shade=.65+.35*saturate(UV.y+.14*sin(UV.x*19+Seed));
return float4(Tint.rgb*shade,mask);
'''
c=custom(mat,code,[('UV',uv,''),('Progress',p,''),('Shape',shape,''),('Seed',seed,''),('Tint',tint,'')])
rgb=node(mat,unreal.MaterialExpressionComponentMask,300,0,r=True,g=True,b=True,a=False)
alpha=node(mat,unreal.MaterialExpressionComponentMask,300,170,r=False,g=False,b=False,a=True)
MEL.connect_material_expressions(c,'',rgb,'');MEL.connect_material_expressions(c,'',alpha,'')
MEL.connect_material_property(rgb,'',unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(alpha,'',unreal.MaterialProperty.MP_OPACITY_MASK)
gain=node(mat,unreal.MaterialExpressionMultiply,500,400)
gain.set_editor_property('const_b',.18)
MEL.connect_material_expressions(rgb,'',gain,'A')
MEL.connect_material_property(gain,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.connect_material_property(scalar(mat,'Roughness',.9,600),'',unreal.MaterialProperty.MP_ROUGHNESS)
MEL.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat,False)

post=unreal.load_asset(ROOT+'/Materials/M_CC_ComicPost')
for n in MEL.get_material_expressions(post):
 if isinstance(n,unreal.MaterialExpressionCustom):
  code=n.get_editor_property('code')
  start=code.index('float rays=')
  end=code.index('// 궁극기 전용:',start)
  code=code[:start]+r'''
// 소수의 1px 내외 스트로크가 화면 바깥으로 이동한다. 중앙 70%는 깨끗하게 남긴다.
float rays=0;
for(int j=0;j<10;j++){
    float phase=frac(Time*1.7+j*.618);
    float cycle=floor(Time*1.7+j*.618);
    float angle=j*2.39996+sin(cycle*1.71+j)*.15;
    float da=atan2(sin(speedA-angle),cos(speedA-angle));
    float radial=.50+phase*.65;
    float strokeCoverage=1-smoothstep(.0005,.0023,abs(da));
    float segment=smoothstep(radial-.14,radial-.10,speedR)*(1-smoothstep(radial,radial+.03,speedR));
    rays=max(rays,strokeCoverage*segment*sin(phase*3.14159));
}
color=lerp(color,float3(.76,.79,.80),rays*SpeedAmount*.58);
'''+code[end:]
  n.set_editor_property('code',code)
MEL.recompile_material(post);unreal.EditorAssetLibrary.save_loaded_asset(post,False)

source=(WORK/'author_animations.py').read_text(encoding='utf-8')
exec(compile(source.split('\nguard=pose()')[0],'pose_helpers','exec'))
neutral=pose(height=89,left=(29,9,112),right=(-29,8,112),left_foot=(14,8,8.24),right_foot=(-14,-8,8.24))
lift=pose(height=93,lean=-12,twist=-8,left=(33,32,155),right=(-29,-14,128),left_foot=(15,22,31),right_foot=(-16,-28,14))
tuck=pose(height=86,lean=-18,twist=6,left=(34,24,148),right=(-29,14,140),left_foot=(20,33,48),right_foot=(-20,-22,32))
airkick=pose(height=93,lean=14,twist=-16,left=(43,4,150),right=(-35,30,142),left_foot=(16,65,65),right_foot=(-20,-25,34))
land=pose(height=67,lean=-23,left=(35,23,104),right=(-35,22,105),left_foot=(23,19,8.24),right_foot=(-23,-16,8.24))
recover=pose(height=92,lean=-7,left=(28,13,126),right=(-29,12,125))
clips=[('A_CC_JumpLift',[(0,neutral),(.06,lift),(.16,lift),(.30,tuck),(.40,tuck)]),
       ('A_CC_AirKick',[(0,tuck),(.07,airkick),(.15,airkick),(.32,tuck),(.40,tuck)]),
       ('A_CC_Land',[(0,neutral),(.05,land),(.10,land),(.22,recover),(.34,neutral)])]
results=[]
for name,keys in clips:
 path=ROOT+'/Animations/'+name
 seq=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
 if seq is None:
  factory=unreal.AnimSequenceFactory();factory.target_skeleton=SKELETON;factory.preview_skeletal_mesh=MESH
  seq=TOOLS.create_asset(name,ROOT+'/Animations',unreal.AnimSequence,factory)
 seq.set_editor_property('additive_anim_type',unreal.AdditiveAnimationType.AAT_NONE)
 controller=seq.controller;controller.open_bracket('Author movement response',False)
 controller.set_frame_rate(unreal.FrameRate(60,1),False)
 frames=math.ceil(keys[-1][0]*30)*2
 controller.set_number_of_frames(unreal.FrameNumber(frames),False);controller.remove_all_bone_tracks(False)
 poses=[]
 for frame in range(frames+1):
  time=frame/60
  a,b=next(((a,b) for a,b in zip(keys,keys[1:]) if a[0]<=time<=b[0]),(keys[-2],keys[-1]))
  alpha=max(0,min(1,(time-a[0])/max(1e-8,b[0]-a[0])));alpha=alpha*alpha*(3-2*alpha)
  poses.append({n:([x+(y-x)*alpha for x,y in zip(a[1][n][0],b[1][n][0])],slerp(a[1][n][1],b[1][n][1],alpha)) for n in DATA})
 for n in DATA:
  controller.add_bone_track(n,False)
  assert controller.set_bone_track_keys(n,[unreal.Vector(*p[n][0]) for p in poses],[unreal.Quat(*p[n][1]) for p in poses],[unreal.Vector(1,1,1)]*len(poses),False)
 controller.close_bracket(False)
 unreal.EditorAssetLibrary.save_loaded_asset(seq,False)
 results.append({'asset':path,'duration':seq.get_play_length()})
(WORK/'movement-assets.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('MOVEMENT_V4_ASSETS_COMPLETE',results)

# 발 IK가 작성한 전신 점프/공격 포즈를 다시 보정하지 않도록 전투 전용 복제본에서 순서를 바꾼다.
bp_path=ROOT+'/Animations/ABP_CC_Unarmed'
bp=unreal.load_asset(bp_path) if unreal.EditorAssetLibrary.does_asset_exist(bp_path) else unreal.EditorAssetLibrary.duplicate_asset('/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed',bp_path)
graph=bp.get_animation_graphs()[0]
def find_node(cls):
 module='ControlRigDeveloper' if cls=='AnimGraphNode_ControlRig' else 'AnimGraph'
 return graph.get_graph_nodes_of_class(unreal.load_class(None,'/Script/'+module+'.'+cls))[0]
slot=find_node('AnimGraphNode_Slot');rig=find_node('AnimGraphNode_ControlRig');output=find_node('AnimGraphNode_Root')
def pin(node,name):return next(p for p in node.list_all_pins() if str(p.get_pin_name())==name)
slot_source=pin(slot,'Source');slot_pose=pin(slot,'Pose');rig_source=pin(rig,'Source');rig_pose=pin(rig,'Pose');result=pin(output,'Result')
if slot_source.list_connected_pins()[0].get_owning_node()!=rig:
 locomotion=slot_source.list_connected_pins()[0]
 slot_source.break_pin_links();slot_pose.break_pin_links();rig_pose.break_pin_links()
 assert locomotion.try_create_connection(rig_source)
 assert rig_pose.try_create_connection(slot_source)
 assert slot_pose.try_create_connection(result)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
print('COMBAT_MONTAGE_AFTER_FOOT_IK',bp_path)
