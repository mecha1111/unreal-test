import unreal
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Tools/ComicCombat'
for name in ['author_materials.py','author_ribbon.py','author_neon.py','author_animations.py','author_target_reactions.py','author_lighting.py','author_layers_v3.py','author_atmosphere.py','author_movement.py']:
    exec(compile((root/name).read_text(encoding='utf-8'),str(root/name),'exec'))
print('COMIC_ASSETS_COMPLETE')
