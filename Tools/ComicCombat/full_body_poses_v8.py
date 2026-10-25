"""발 디딤, 골반 선행 회전, 빠른 접촉, 후속 회복을 포함한 전신 타격 클립."""
import unreal,math,json
from pathlib import Path
WORK=Path(__file__).resolve().parent
src=(WORK/'animation_helpers_v8.py').read_text(encoding='utf-8')
exec(compile(src.split('\nguard=pose()')[0],'pose_helpers','exec'))
g=pose(height=88,twist=-9,left=(22,31,140),right=(-24,23,133),left_foot=(18,20,8.24),right_foot=(-20,-21,8.24))
jw=pose(height=83,twist=-40,lean=5,shift=-8,left=(38,0,135),right=(-17,30,141),left_foot=(23,9,14),right_foot=(-22,-23,8.24))
jh=pose(height=86,twist=39,lean=-13,shift=13,left=(5,68,141),right=(-28,18,137),left_foot=(20,42,8.24),right_foot=(-23,-20,13))
jf=pose(height=83,twist=44,lean=-17,shift=16,left=(7,61,130),right=(-28,23,135),left_foot=(20,42,8.24),right_foot=(-23,-14,13))
cw=pose(height=82,twist=43,lean=4,shift=-4,right=(-39,-9,136),left=(18,30,141),left_foot=(21,27,8.24),right_foot=(-23,-27,8.24))
ch=pose(height=86,twist=-52,lean=-16,shift=18,right=(10,70,143),left=(29,9,132),left_foot=(25,23,8.24),right_foot=(-15,0,17))
cf=pose(height=80,twist=-60,lean=-20,shift=15,right=(25,57,130),left=(32,10,130),left_foot=(26,30,8.24),right_foot=(-17,-7,13))
uw=pose(height=66,twist=40,lean=-17,shift=-9,right=(-31,-4,84),left=(23,30,127),left_foot=(25,28,8.24),right_foot=(-22,-26,8.24))
uh=pose(height=98,twist=-48,lean=10,shift=15,right=(3,38,187),left=(29,16,143),left_foot=(24,35,12),right_foot=(-20,-4,24))
uf=pose(height=91,twist=-58,lean=18,shift=14,right=(9,23,187),left=(32,15,133),left_foot=(24,35,8.24),right_foot=(-21,-6,15))
hw=pose(height=92,twist=28,lean=15,shift=-9,left=(21,-16,186),right=(-21,-12,185),left_foot=(25,15,27),right_foot=(-25,-22,8.24))
hh=pose(height=66,twist=-30,lean=-45,shift=22,left=(7,68,77),right=(-6,66,77),left_foot=(27,47,8.24),right_foot=(-25,-13,8.24))
hf=pose(height=64,twist=-39,lean=-37,shift=18,left=(12,53,68),right=(-11,52,68),left_foot=(27,47,8.24),right_foot=(-25,-13,8.24))
dw=pose(height=70,twist=35,lean=-27,shift=-5,right=(-38,-15,103),left=(26,30,116),left_foot=(22,29,8.24),right_foot=(-24,-31,12))
dh=pose(height=82,twist=-47,lean=-25,shift=20,right=(4,72,122),left=(30,9,121),left_foot=(25,48,8.24),right_foot=(-23,-27,18))
uc=pose(height=63,twist=25,lean=-22,shift=-8,left=(30,-5,87),right=(-30,-7,86),left_foot=(30,25,8.24),right_foot=(-30,-24,8.24))
ur=pose(height=102,twist=24,lean=15,shift=-5,left=(22,-7,199),right=(-21,-7,198),left_foot=(31,24,18),right_foot=(-31,-22,18))
us=pose(height=59,twist=-41,lean=-46,shift=24,left=(11,64,62),right=(-9,65,62),left_foot=(34,47,8.24),right_foot=(-34,-24,8.24))
ac=pose(height=81,twist=26,lean=12,left=(22,1,185),right=(-20,-5,184),left_foot=(22,30,38),right_foot=(-21,-9,40))
ah=pose(height=70,twist=-28,lean=-34,shift=10,left=(11,52,96),right=(-9,53,95),left_foot=(25,28,24),right_foot=(-24,-10,30))
CLIPS=[]
