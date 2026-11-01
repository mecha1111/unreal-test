import unreal,json,math
from pathlib import Path
WORK=Path(unreal.Paths.project_dir()).resolve()/'Tools/ComicCombat'
DATA=json.loads((WORK/'exorcist_skeleton.json').read_text())
source=(WORK/'author_animations.py').read_text(encoding='utf-8');exec(source[source.index('def add('):source.index('def pose(')])
def local_pose(a,t):
 poses=unreal.AnimationLibrary.get_bone_poses_for_time(a,list(DATA),t,False)
 return {n:([p.translation.x,p.translation.y,p.translation.z],[p.rotation.x,p.rotation.y,p.rotation.z,p.rotation.w]) for n,p in zip(DATA,poses)}
result={}
for entry in unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_path('/Game/ExorcistV10/Animations/External',True):
 if str(entry.asset_class_path.asset_name)!='AnimSequence':continue
 a=unreal.load_asset(entry.package_name);samples=[]
 for i in range(round(a.get_play_length()*30)+1):
  g=globals_of(local_pose(a,i/30));samples.append({'t':i/30,**{n:[round(x,2) for x in g[n][0]] for n in ['hips','hand_L','hand_R','foot_L','foot_R']}})
 result[a.get_name()]=samples
Path(r'C:\Users\jooan\Documents\Codex\2026-10-25\x20\outputs\external-motion-samples.json').write_text(json.dumps(result))
print('MOTION_SAMPLES_READY')
