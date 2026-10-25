"""과장된 전신 키와 L-L-R 상승 펀치. 기존 직렬화 자산 경로는 보존한다."""
import unreal,math,json
from pathlib import Path
WORK=Path(__file__).resolve().parent
src=(WORK/'animation_helpers_v8.py').read_text(encoding='utf-8')
exec(compile(src.split('\nguard=pose()')[0],'pose_helpers','exec'))
g=pose(height=85,twist=-12,left=(24,33,140),right=(-26,23,132),left_foot=(22,22,8.24),right_foot=(-22,-24,8.24))
# 팔만 내미는 포즈를 피한다. 매 타격마다 지지발, 골반 높이, 흉곽 회전과 반대팔을 함께 바꾼다.
jw=pose(height=77,twist=-53,lean=8,shift=-12,left=(43,-8,133),right=(-17,35,146),left_foot=(26,8,21),right_foot=(-25,-28,8.24))
jh=pose(height=87,twist=56,lean=-19,shift=19,left=(3,79,145),right=(-35,9,127),left_foot=(23,49,8.24),right_foot=(-23,-28,18))
jf=pose(height=80,twist=65,lean=-22,shift=20,left=(14,69,125),right=(-30,15,126),left_foot=(24,49,8.24),right_foot=(-23,-20,15))
cw=pose(height=74,twist=61,lean=9,shift=-12,right=(-45,-20,132),left=(20,34,145),left_foot=(27,30,8.24),right_foot=(-28,-34,8.24))
ch=pose(height=88,twist=-68,lean=-20,shift=25,right=(10,85,143),left=(37,-4,124),left_foot=(28,44,8.24),right_foot=(-17,6,24))
cf=pose(height=77,twist=-77,lean=-25,shift=23,right=(37,61,125),left=(35,3,124),left_foot=(28,44,8.24),right_foot=(-19,-6,16))
uw=pose(height=60,twist=54,lean=-22,shift=-12,right=(-39,-12,78),left=(24,33,123),left_foot=(29,32,8.24),right_foot=(-26,-31,8.24))
uh=pose(height=100,twist=-62,lean=13,shift=18,right=(2,39,201),left=(37,5,134),left_foot=(25,41,15),right_foot=(-22,1,27))
uf=pose(height=92,twist=-72,lean=21,shift=16,right=(15,18,193),left=(35,10,129),left_foot=(25,41,8.24),right_foot=(-23,-6,18))
# 강공격은 크게 감았다가 찍는 양손 해머. 기본 잽/크로스/상승과 실루엣을 구분한다.
hw=pose(height=96,twist=45,lean=23,shift=-15,left=(24,-23,202),right=(-24,-24,201),left_foot=(29,10,36),right_foot=(-29,-29,8.24))
hh=pose(height=57,twist=-43,lean=-47,shift=25,left=(8,75,67),right=(-8,74,67),left_foot=(31,55,8.24),right_foot=(-29,-18,8.24))
hf=pose(height=61,twist=-50,lean=-38,shift=21,left=(15,60,62),right=(-10,57,63),left_foot=(31,55,8.24),right_foot=(-29,-18,8.24))
# E 후반은 같은 잽 복제 대신 왼 훅 → 낮은 오른 보디 → 상승으로 연결한다.
hookw=pose(height=76,twist=-67,lean=-6,shift=-4,left=(67,-10,133),right=(-19,34,140),left_foot=(30,38,8.24),right_foot=(-27,-22,12))
hook=pose(height=83,twist=74,lean=-15,shift=15,left=(-28,59,143),right=(-33,3,119),left_foot=(30,42,8.24),right_foot=(-25,-12,20))
bodyw=pose(height=61,twist=64,lean=-26,shift=-3,right=(-47,-15,86),left=(20,36,124),left_foot=(30,36,8.24),right_foot=(-29,-26,8.24))
body=pose(height=67,twist=-64,lean=-30,shift=21,right=(7,77,98),left=(35,0,115),left_foot=(30,44,8.24),right_foot=(-25,-9,14))
# Q: 낮게 모으기 → 지지발 밀기 → 앞발 딛기 → 골반/가슴을 반대로 틀며 긴 직선 펀치.
qc=pose(height=58,twist=68,lean=-15,shift=-18,left=(22,37,126),right=(-42,-32,87),left_foot=(31,31,8.24),right_foot=(-30,-39,8.24))
qcoil=pose(height=55,twist=76,lean=-21,shift=-21,left=(25,40,123),right=(-47,-37,88),left_foot=(32,31,8.24),right_foot=(-31,-41,8.24))
qr=pose(height=69,twist=58,lean=-34,shift=8,left=(25,39,125),right=(-44,-27,112),left_foot=(27,50,18),right_foot=(-27,-40,24))
qplant=pose(height=75,twist=46,lean=-30,shift=14,left=(30,35,124),right=(-44,-14,122),left_foot=(31,65,8.24),right_foot=(-29,-33,30))
qp=pose(height=89,twist=-78,lean=-24,shift=29,left=(39,-12,117),right=(5,95,136),left_foot=(31,63,8.24),right_foot=(-23,-28,26))
qf=pose(height=73,twist=-88,lean=-29,shift=26,left=(34,-9,113),right=(38,66,111),left_foot=(31,63,8.24),right_foot=(-25,-21,19))
qsettle=pose(height=72,twist=-40,lean=-12,shift=9,left=(28,25,129),right=(-22,36,121),left_foot=(27,37,8.24),right_foot=(-25,-24,8.24))
# 상승 펀치는 깊은 앉기와 오른 주먹/무릎의 상승을 동시에 읽게 한다. 캡슐 상승은 명중 노티파이가 맡는다.
rw=pose(height=51,twist=69,lean=-28,shift=-12,right=(-42,-13,69),left=(27,36,118),left_foot=(32,34,8.24),right_foot=(-30,-32,8.24))
rh=pose(height=101,twist=-73,lean=15,shift=17,right=(0,32,214),left=(39,4,131),left_foot=(24,39,18),right_foot=(-26,29,61))
rf=pose(height=94,twist=-91,lean=21,shift=10,right=(10,11,201),left=(36,8,125),left_foot=(23,28,27),right_foot=(-26,25,58))
ac=pose(height=79,twist=42,lean=20,left=(24,-9,201),right=(-23,-12,200),left_foot=(24,36,44),right_foot=(-24,-14,43))
ah=pose(height=64,twist=-44,lean=-40,shift=15,left=(10,61,83),right=(-10,60,83),left_foot=(28,32,25),right_foot=(-28,-16,29))
CLIPS=[
 ('A_CC_Jab',[(0,g),(.0833,jw),(.1333,jh),(.1833,jh),(.25,jf),(.40,g)],.0833,.1333,.25),
 ('A_CC_Cross',[(0,g),(.1167,cw),(.1833,ch),(.2333,ch),(.30,cf),(.50,g)],.1167,.1833,.3167),
 ('A_CC_Uppercut',[(0,g),(.1833,uw),(.2667,uh),(.3333,uh),(.4333,uf),(.70,g)],.20,.2667,.50),
 ('A_CC_Hammer',[(0,g),(.20,hw),(.2667,hw),(.35,hh),(.4167,hh),(.50,hf),(.85,g)],.2833,.35,.65),
 ('A_CC_DashStrike',[(0,g),(.12,jw),(.20,jh),(.25,cw),(.34,ch),(.39,hookw),(.48,hook),(.53,bodyw),(.62,body),(.72,uw),(.88,uh),(.96,uf),(1.08,cf),(1.30,g)],.14,.20,1.04),
 ('A_CC_InkBreaker',[(0,g),(.18,qc),(.38,qcoil),(.49,qcoil),(.55,qr),(.69,qr),(.78,qplant),(.88,qp),(.98,qp),(1.14,qf),(1.33,qsettle),(1.60,g)],.74,.88,1.15),
 ('A_HF_AerialStrike',[(0,g),(.1333,ac),(.20,ac),(.30,ah),(.75,ah),(.9667,g)],.2167,.3167,.85),
 ('A_CC_RisingPunch',[(0,g),(.16,rw),(.25,rh),(.35,rh),(.55,rf),(.80,g)],.1833,.25,.55)
]
exec(compile(src[src.index('def bake():'):],'bake_phase_clips','exec'))
notify=unreal.load_class(None,'/Script/test.AnimNotify_ComicCue')
for name,events in [
 ('A_CC_DashStrike',[(.14,20),(.20,10),(.28,21),(.34,11),(.42,22),(.48,12),(.56,23),(.62,13),(.80,24),(.88,14),(1.04,2)]),
 ('A_CC_InkBreaker',[(.55,30),(.74,0),(.88,1),(1.15,2)])]:
 seq=unreal.load_asset(ROOT+'/Animations/'+name)
 unreal.AnimationLibrary.remove_all_animation_notify_tracks(seq)
 unreal.AnimationLibrary.add_animation_notify_track(seq,'Combat')
 for at,cue in events:
  event=unreal.AnimationLibrary.add_animation_notify_event(seq,'Combat',at,notify)
  event.set_editor_property('cue',cue)
 unreal.EditorAssetLibrary.save_loaded_asset(seq,False)
print('COMBAT_V9_ANIMATIONS_COMPLETE')
