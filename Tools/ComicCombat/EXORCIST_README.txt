EXORCIST V10 integration — 2026-11-01

Active project: test 5.8 (Unreal Engine 5.8.4)
Original file: Downloads/exorcist_tripo_hair_v10.blend — not modified.
Active character: /Game/ExorcistV10/Character/SK_EX_Optimized
Active skeleton: SK_EX_Game_Skeleton. Native height: about 175 cm.
Training enemies remain the original SKM_Manny_Simple.

Rendering
- 13 material sections, reduced from 30 by merging equal runtime material families.
- 4 LODs: 75,232 / 50,840 / 28,881 / 16,693 vertices.
- 28 original facial morphs retained; lower LOD morph remapping enabled.
- Texture color spaces: base color sRGB, numerical masks linear. Head 4K; other maps at most 2K.
- Hair uses the v10 four-stop color ramp and imported normals. Face uses original head texture.
- Master material explicitly saves SkeletalMesh and MorphTargets usage; verified after editor restart.
- This is an explicit Unlit toon response. It is not a complete SDF face-shadow implementation.
- Blender Solidify outlines and cached cloth are not automatically transferred. Runtime Chaos cloth and full hair collision simulation are not implemented here.
- Persistent camera filter removed; transient ultimate/combo highlight only. White platform and blue daytime sky.
- TSR history 100%, output resolution unchanged. Lumen and virtual shadow quality unchanged.
- Unused character Custom Depth passes disabled.

Animation and input
- Active motions now come from Quaternius UAL 1/2 and KayKit (CC0), not the former hand-authored poses.
- Quaternius: idle, locomotion, jab, cross, hook and jump. KayKit: kick, also used for aerial kick.
- Existing asset names such as A_CC_Uppercut now contain a retimed external hook; names are retained for gameplay references.
- E overlaps external jab/cross takes; Q uses the KayKit full-body punch with charge/rush/contact/recovery retiming.
- Original imported external clips remain untouched. Replaced runtime assets are backed up under Animations/BeforeExternal.
- Existing game notify times preserved, including five-hit E and seven-hit ultimate charge.
- No deliberate pose frame stepping. Locomotion is now also Quaternius.
- The old FBX conversion had inconsistent root scale (reference 100, animated 1) and remains unused.
- Active external sources are direct publisher GLBs under SourceArt/ExternalCombat, with license files.
- Action-based facial morph blending and blinking; not speech lip synchronization.
- Free orbit camera in combat. No attack zoom/reframing/additive camera rotation.
- Controller handles raw MouseX/Y independently of combat actions; verify_free_camera.py tests actual input events.
- Orbit FOV 70, distance 365 cm; wheel adjusts 270–560 cm. Training targets ignore camera collision.
- Combat no longer applies global time dilation; local mesh hit-stop remains.
- Mesh origin lowered 2 cm to compensate CharacterMovement's floor clearance.
- refine_day_environment.py adds a brighter blue gradient/cloud sky and softer daylight. It does not edit character materials.
- Existing short hit-stop remains separate from smooth animation playback.
- Hand VFX follow the palm; EX lower_arm names mapped for ribbon roots; shoes use adjusted foot-plant height.

Reproduction order (editor scripts register a one-shot Slate callback)
1. Background Blender: export_exorcist.py, then export_exorcist_optimized.py. Never save the original blend.
2. import_exorcist_v10.py; author_exorcist_materials.py.
3. retarget_exorcist.py; connect_exorcist.py; author_exorcist_combat.py.
   Retargeting again overwrites authored combat: always run author_exorcist_combat.py last.
4. optimize_exorcist.py; author_day_arena.py; refine_day_environment.py.
5. Close editor, build testEditor Win64 Development; reopen project.
6. Allow startup shader/asset loading to finish, then PIE verify_exorcist.py. For automation/profiling temporarily disable editor background throttling; restore afterward.
7. For the CURRENT external-motion revision run import_external_combat.py, retarget_external_combat.py,
   then apply_external_combat.py LAST. author_exorcist_combat.py is legacy and overwrites external motion.
8. Run verify_free_camera.py in a fresh PIE session. It sends actual controller MouseX/Y events during LMB/RMB/E/Q.

Current combat alignment / ultimate revision
- E retains five original notify times (.20/.40/.62/.85/1.10s). Jab/cross recovery
  overlaps the following preparation; no kick clips and no full guard reset between hits.
- Q uses KayKit Melee_Unarmed_Attack_Punch_A, not the normal Quaternius cross.
  Wind-up .00-.55s, rush .55-.88s, impact .88s, recovery to 1.60s.
  Imported forward root travel is reduced to 25%, because the capsule already rushes.
- Both new clips retain original asset paths/notifies. Set EXTERNAL_ASSETS_ONLY to
  {'A_CC_DashStrike','A_CC_InkBreaker'} when rebaking only these two.
- Damage notifies queue strikes until the presentation tick after skeletal bone update.
  Contact comes from target PhysicsAsset before damage changes the reaction pose.
  Jab uses left palm; other punches use right palm; kicks use right foot/toes.
- Charge/ribbon/recovery/light use the same limb helper. Impact core stays within
  2cm of the surface, with small separated companions and outward world-space spread.
- author_highlight_only.py creates M_CC_HighlightOnly for ultimate/rising/combo hits.
  It has no persistent shading, speed filter or camera transform control. Blend weight
  is zero outside the short highlight; world/controller time dilation remains 1.
- Editor asset scripts must run SEQUENTIALLY. Wait for their saved/completed log
  marker before another mutation or editor quit; nested Slate saves can deadlock.
- verify_combat_alignment.py verifies real LMB/RMB/E/Q inputs, current limb anchors,
  physics bone contacts, VFX origins, transient highlight and free camera in PIE.
- Validation: Development Editor build passed; alignment 38/38 at a 60fps limit,
  38/38 at a 30fps limit; mouse/free-camera 20/20; six-combo/rising highlights 5/5.
  Actual E = five hits; seven hits fill Q; Q uses the right palm at the current pose.
  Packaging and performance benchmarking were not run for this revision.

Sources
Quaternius CC0: https://quaternius.com/packs/universalanimationlibrary.html
Quaternius UAL2: https://quaternius.itch.io/universal-animation-library-2
KayKit CC0: https://kaylousberg.itch.io/kaykit-character-animations
Tripo rig/animation workflow reviewed: https://www.tripo3d.ai/product-doc/module-post-processing/rigging-animation
Cascadeur export constraints reviewed: https://cascadeur.com/plans
Environment reference (Kuro Games interview): https://www.unrealengine.com/developer-interviews/exploring-the-post-apocalyptic-charm-of-asg-open-worlds-in-wuthering-waves
AMD profiling, deterministic comparisons, TSR: https://gpuopen.com/learn/unreal-engine-performance-guide/
Epic skeletal LOD and morph remapping: https://dev.epicgames.com/documentation/unreal-engine/skeletal-mesh-lods-in-unreal-engine
Epic TSR: https://dev.epicgames.com/documentation/unreal-engine/temporal-super-resolution-in-unreal-engine
Epic Niagara profiling: https://dev.epicgames.com/documentation/unreal-engine/measuring-performance-in-niagara
Epic Niagara scalability/pooling: https://dev.epicgames.com/documentation/en-us/unreal-engine/scalability-and-best-practices-for-niagara
Garland/Heckbert QEM research and texture-aware extension: https://www.cs.cmu.edu/~garland/quadrics/
Community investigation, near-clip particle culling (considered, not applied blindly): https://www.reddit.com/r/unrealengine/comments/14kkcm9/

Research is a selected review of relevant methods, not an exhaustive survey of every optimization paper.
PIE timings include editor/Slate overhead and are not packaged-build performance guarantees.

2026-11-02 secondary motion / presentation revision
See EXORCIST_SECONDARY_MOTION.txt for the current material, camera and movement settings.
The earlier speed/camera notes above are historical and superseded by that document.
Character material: M_EX_SurfaceDetail. Five post-process cloth/hair groups.
Character silhouette outline and lighting bands; original 2.5-second idle restored with
ankle-only grounding, varied idle/attack expressions. Garment collision jitter reduced.
Thirteen image_gen-created 8–16-frame RGBA effect sheets are retained, including three new
Arcane-inspired 16-frame punch/discharge/corona sheets; runtime selects a subset per attack.
Sources and prompts are retained in Tools/ComicCombat/GeneratedSheets.
Outline now runs before TSR (Before DOF) and draws inside the visible character silhouette.
Basic-hit layer count: 9 -> 4; heavy: 17 -> 7; ultimate: 21 -> 10 (excluding Niagara).
Basic hits no longer activate Niagara, ground paint, smoke, or electrical overlays.
Pooled components, 30-Hz face updates, 4 mesh LODs and secondary-motion LOD cutoff retained.
Fullscreen highlight, blue lightning overlay and colour inversion are disabled.
World-space impact/ultimate effects and their contact lighting are retained.
Resting garment physics blends out to authored animation; movement/attacks restore it.
Hair physics remains independent. See verify_resting_garments.py for transition checks.
