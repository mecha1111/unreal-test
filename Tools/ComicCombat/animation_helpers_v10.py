"""Manny 전신 키 작성 도우미. 지정된 기존 자산 경로에 키와 노티파이를 갱신한다."""
import json
import math
import unreal
from pathlib import Path

WORK = Path(__file__).resolve().parent
ROOT = '/Game/ComicCombat'
MESH = unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple')
SKELETON = MESH.get_editor_property('skeleton')
DATA = json.loads((WORK / 'manny_skeleton.json').read_text())
FISTS = json.loads((WORK / 'fist_pose.json').read_text())
# Simple 메시에서 실제로 사용하는 뼈만 기록한다. 공용 스켈레톤의 보정 뼈는 제외한다.
DATA = {n: d for n, d in DATA.items() if n == 'root' or d['parent'] != 'None'}

def add(a, b): return [a[i] + b[i] for i in range(3)]
def sub(a, b): return [a[i] - b[i] for i in range(3)]
def mul(a, s): return [v * s for v in a]
def dot(a, b): return sum(x*y for x, y in zip(a, b))
def cross(a,b): return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def length(a): return math.sqrt(dot(a, a))
def unit(a): return mul(a, 1/max(length(a), 1e-8))
def qmul(a,b):
    v=add(add(mul(b[:3],a[3]),mul(a[:3],b[3])),cross(a[:3],b[:3]))
    return v+[a[3]*b[3]-dot(a[:3],b[:3])]
def inv(q): return [-q[0],-q[1],-q[2],q[3]]
def rot(q,v): return qmul(qmul(q,v+[0]),inv(q))[:3]
def axis(axis, degrees):
    h=math.radians(degrees)*.5
    return mul(unit(axis),math.sin(h))+[math.cos(h)]
def between(a,b):
    a,b=unit(a),unit(b)
    c=cross(a,b); w=1+dot(a,b)
    if w<1e-5: return axis(cross(a,[0,0,1]) if abs(a[2])<.9 else [0,1,0],180)
    q=c+[w]; size=math.sqrt(sum(v*v for v in q))
    return [v/size for v in q]
def slerp(a,b,t):
    d=sum(x*y for x,y in zip(a,b))
    if d<0: b=[-v for v in b]; d=-d
    if d>.9995:
        q=[x+(y-x)*t for x,y in zip(a,b)]; size=math.sqrt(sum(v*v for v in q))
        return [v/size for v in q]
    angle=math.acos(max(-1,min(1,d))); si=math.sin(angle)
    return [(x*math.sin((1-t)*angle)+y*math.sin(t*angle))/si for x,y in zip(a,b)]

def globals_of(local):
    result={}
    for n,d in DATA.items():
        t,q=local[n]; p=d['parent']
        if p in result:
            pt,pq=result[p]; result[n]=(add(pt,rot(pq,t)),qmul(pq,q))
        else: result[n]=(t[:],q[:])
    return result

REF={n:(d['t'][:],d['q'][:]) for n,d in DATA.items()}
REF_G=globals_of(REF)

def solve_limb(local, first, second, end, goal, pole, end_rotation=None):
    """2관절 IK. 길이는 유지하고 pole 방향으로 무릎/팔꿈치를 배치한다."""
    world=globals_of(local); origin=world[first][0]
    l1=length(DATA[second]['t']); l2=length(DATA[end]['t'])
    to_goal=sub(goal,origin); dist=max(.1,min(length(to_goal),l1+l2-.15))
    direction=unit(to_goal); along=(l1*l1-l2*l2+dist*dist)/(2*dist)
    perp=unit(sub(sub(pole,origin),mul(direction,dot(sub(pole,origin),direction))))
    joint=add(add(origin,mul(direction,along)),mul(perp,math.sqrt(max(0,l1*l1-along*along))))
    goal=add(origin,mul(direction,dist))
    for bone,child,point in [(first,second,joint),(second,end,goal)]:
        world=globals_of(local)
        old_dir=sub(world[child][0],world[bone][0]); new_dir=sub(point,world[bone][0])
        world_q=qmul(between(old_dir,new_dir),world[bone][1])
        parent=DATA[bone]['parent']
        local[bone]=(local[bone][0],qmul(inv(world[parent][1]),world_q))
    if end_rotation is not None:
        world=globals_of(local)
        local[end]=(local[end][0],qmul(inv(world[DATA[end]['parent']][1]),end_rotation))

def pose(height=89, lean=0, twist=0, shift=0, left=(21,29,137), right=(-22,24,135),
         left_foot=(16,19,8.24), right_foot=(-16,-18,8.24), elbows=0):
    local={n:(t[:],q[:]) for n,(t,q) in REF.items()}
    for n,q in FISTS.items():
        if n in local: local[n]=(local[n][0],q)
    local['pelvis']=([twist*.10,shift*1.18+2.28,height],qmul(axis([0,0,1],twist*.60),REF['pelvis'][1]))
    for n in ['spine_01','spine_02','spine_03','spine_04','spine_05']:
        world=globals_of(local); parent=DATA[n]['parent']
        global_delta=qmul(axis([1,0,0],lean/5),axis([0,0,1],twist*.40/5))
        world_q=qmul(global_delta,world[n][1])
        local[n]=(local[n][0],qmul(inv(world[parent][1]),world_q))
    solve_limb(local,'thigh_l','calf_l','foot_l',list(left_foot),[18+twist*.14,65,44],qmul(axis([0,0,1],twist*.32),REF_G['foot_l'][1]))
    solve_limb(local,'thigh_r','calf_r','foot_r',list(right_foot),[-18+twist*.14,40,42],qmul(axis([0,0,1],twist*.32),REF_G['foot_r'][1]))
    solve_limb(local,'upperarm_l','lowerarm_l','hand_l',list(left),[65,8+elbows,107])
    solve_limb(local,'upperarm_r','lowerarm_r','hand_r',list(right),[-65,8+elbows,107])
    # 시선은 전방을 유지하고 상체 회전만큼 얼굴이 돌아가지 않게 한다.
    world=globals_of(local)
    head_q=qmul(axis([1,0,0],lean*.25),REF_G['head'][1])
    local['head']=(local['head'][0],qmul(inv(world[DATA['head']['parent']][1]),head_q))
    # 손/발 IK 보조 뼈도 실제 끝점을 따라간다.
    world=globals_of(local)
    for ik,bone in [('ik_hand_l','hand_l'),('ik_hand_r','hand_r'),('ik_foot_l','foot_l'),('ik_foot_r','foot_r')]:
        if ik in local:
            p=DATA[ik]['parent']; pt,pq=world[p]
            local[ik]=(rot(inv(pq),sub(world[bone][0],pt)),qmul(inv(pq),world[bone][1]))
    return local

guard=pose()
jab_wind=pose(height=87,twist=-18,left=(29,5,134),right=(-19,31,138),shift=-3)
jab_hit=pose(height=90,twist=23,lean=-6,left=(9,51,140),right=(-21,21,135),shift=5)
cross_wind=pose(height=86,twist=27,right=(-33,-3,135),left=(17,31,140),shift=-3)
cross_hit=pose(height=89,twist=-31,lean=-9,right=(-4,53,139),left=(22,19,135),shift=7)
upper_wind=pose(height=77,twist=27,lean=-12,right=(-30,10,101),left=(21,29,129),shift=-6)
upper_hit=pose(height=94,twist=-29,lean=6,right=(-4,35,174),left=(24,24,137),shift=5)
heavy_wind=pose(height=86,lean=12,twist=20,left=(17,-5,183),right=(-18,-8,182),shift=-5)
heavy_hit=pose(height=76,lean=-33,twist=-15,left=(10,49,98),right=(-7,50,96),shift=9)
dash_wind=pose(height=78,lean=-24,twist=-16,right=(-22,-15,119),left=(24,27,119),shift=-3)
dash_hit=pose(height=84,lean=-20,twist=-29,right=(-3,55,129),left=(22,16,120),shift=9)
ult_crouch=pose(height=70,lean=-18,twist=18,left=(26,10,93),right=(-26,5,92),shift=-5,
                left_foot=(23,24,8.24),right_foot=(-23,-21,8.24))
ult_rise=pose(height=91,lean=15,twist=10,left=(18,-9,184),right=(-18,-9,184),shift=-4,
              left_foot=(23,24,8.24),right_foot=(-23,-21,8.24))
ult_hit=pose(height=68,lean=-40,twist=-16,left=(8,50,78),right=(-8,50,78),shift=10,
             left_foot=(23,24,8.24),right_foot=(-23,-21,8.24))

# 키 사이 간격이 속도를 결정한다. 접촉 포즈를 여러 프레임 유지하되 게임/카메라 시간은 유지한다.
CLIPS=[
 ('A_CC_Jab',[(0,guard),(.10,jab_wind),(.15,jab_hit),(.20,jab_hit),(.32,guard),(.43,guard)],.125,.15,.27),
 ('A_CC_Cross',[(0,guard),(.13,cross_wind),(.20,cross_hit),(.25,cross_hit),(.39,guard),(.50,guard)],.16,.20,.33),
 ('A_CC_Uppercut',[(0,guard),(.20,upper_wind),(.29,upper_hit),(.36,upper_hit),(.55,guard),(.68,guard)],.24,.29,.48),
 ('A_CC_Hammer',[(0,guard),(.20,heavy_wind),(.28,heavy_wind),(.37,heavy_hit),(.46,heavy_hit),(.68,guard),(.82,guard)],.31,.37,.65),
 ('A_CC_DashStrike',[(0,guard),(.12,dash_wind),(.21,dash_hit),(.27,dash_hit),(.43,guard),(.55,guard)],.15,.21,.43),
 ('A_CC_InkBreaker',[(0,guard),(.22,ult_crouch),(.42,ult_crouch),(.56,ult_rise),(.65,ult_rise),(.76,ult_hit),(.89,ult_hit),(1.18,guard),(1.40,guard)],.66,.76,1.18)
]

def bake():
    results=[]
    for name,keys,trail,hit,recover in CLIPS:
        path=ROOT+'/Animations/'+name
        seq=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
        if not seq:
            factory=unreal.AnimSequenceFactory(); factory.target_skeleton=SKELETON; factory.preview_skeletal_mesh=MESH
            seq=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,ROOT+'/Animations',unreal.AnimSequence,factory)
        controller=seq.controller
        controller.open_bracket('Author comic attack poses',False)
        controller.set_frame_rate(unreal.FrameRate(60,1),False)
        # 기본 플랫폼 압축률 30fps와 정확히 나누어지도록 짝수 프레임으로 끝낸다.
        frames=math.ceil(keys[-1][0]*30)*2
        controller.set_number_of_frames(unreal.FrameNumber(frames),False)
        controller.remove_all_bone_tracks(False)
        poses=[]
        for f in range(frames+1):
            t=f/60
            pair=next(((a,b) for a,b in zip(keys,keys[1:]) if a[0]<=t<=b[0]),(keys[-2],keys[-1]))
            a,b=pair; alpha=max(0,min(1,(t-a[0])/max(1e-8,b[0]-a[0])))
            alpha=alpha*alpha*(3-2*alpha)
            poses.append({n:([x+(y-x)*alpha for x,y in zip(a[1][n][0],b[1][n][0])],slerp(a[1][n][1],b[1][n][1],alpha)) for n in DATA})
        for n,d in DATA.items():
            controller.add_bone_track(n,False)
            ok=controller.set_bone_track_keys(n,[unreal.Vector(*p[n][0]) for p in poses],
                [unreal.Quat(*p[n][1]) for p in poses],[unreal.Vector(1,1,1)]*len(poses),False)
            if not ok: raise RuntimeError('Bone track failed: '+n)
        controller.close_bracket(False)
        unreal.AnimationLibrary.remove_all_animation_notify_tracks(seq)
        # C++ 클래스가 빌드된 뒤 같은 스크립트를 재실행하면 실제 타격 노티파이를 연결한다.
        notify=unreal.load_class(None,'/Script/test.AnimNotify_ComicCue')
        if notify:
            unreal.AnimationLibrary.add_animation_notify_track(seq,'Combat')
            for time,cue in [(trail,0),(hit,1),(recover,2)]:
                event=unreal.AnimationLibrary.add_animation_notify_event(seq,'Combat',time,notify)
                event.set_editor_property('cue',cue)
        unreal.EditorAssetLibrary.save_loaded_asset(seq)
        results.append({'asset':path,'frames':frames,'duration':seq.get_play_length(),'trail':trail,'hit':hit,'recover':recover})
    (WORK/'animation_timing.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results))

bake()
