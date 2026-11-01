"""Import corrected cloth skinning into the existing runtime mesh, with a backup.
Keep asset references, skeleton, morph-aware LODs and combat montage compatibility.
"""
import unreal
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()
source=(root/'Tools/ComicCombat/optimize_exorcist.py').read_text(encoding='utf-8-sig')
source=source.replace("SourceArt/ExorcistV10/SK_EX_Optimized.fbx","SourceArt/ExorcistV10/Dynamics/SK_EX_Dynamics.fbx")
source=source.replace("unreal.unregister_slate_post_tick_callback(unreal._ex_opt)","""unreal.unregister_slate_post_tick_callback(unreal._ex_opt)
 if not unreal.EditorAssetLibrary.does_asset_exist(D+'/BeforeDynamics/SK_EX_Optimized'):
  assert unreal.EditorAssetLibrary.duplicate_asset(D+'/Character/SK_EX_Optimized',D+'/BeforeDynamics/SK_EX_Optimized')""")
source=source.replace("print('EX_OPTIMIZED',result)","print('EX_DYNAMICS_IMPORTED',result)")
exec(compile(source,'import_exorcist_dynamics_inner','exec'))
