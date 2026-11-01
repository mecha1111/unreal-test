"""Import original image_gen RGBA sheets without redrawing their artwork."""
import unreal
from pathlib import Path

def run(dt):
    unreal.unregister_slate_post_tick_callback(unreal._arcane_import)
    source=Path(unreal.Paths.project_dir())/'Tools/ComicCombat/import_vfx_variations.py'
    code=source.read_text(encoding='utf-8').replace("['jab_burst','cross_burst','rising_burst','lightning_fork','ground_fracture']", "['arcane_punch','arcane_ultimate','arcane_lightning']").replace("'VFX_VARIATIONS_IMPORTED',5", "'ARCANE_VFX_IMPORTED',3")
    exec(compile(code,str(source),'exec'),{})

unreal._arcane_import=unreal.register_slate_post_tick_callback(run)
