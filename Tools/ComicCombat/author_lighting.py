"""원본 맵을 보존하고 영상의 어두운 보라 플랫폼과 발광 수평선을 재현한다."""
import unreal
src='/Game/Playground/Maps/WhiteArena'
dest='/Game/ComicCombat/Maps/ComicArena'
if not unreal.EditorAssetLibrary.does_asset_exist(dest):
    unreal.EditorAssetLibrary.duplicate_asset(src,dest)
le=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert le.load_level(dest)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors=eas.get_all_level_actors()
floor=unreal.load_asset('/Game/ComicCombat/Materials/M_CC_ArenaFloor')
for actor in actors:
    label=actor.get_actor_label()
    if isinstance(actor,unreal.DirectionalLight):
        if label=='Comic Rim - Cyan':
            actor.set_actor_rotation(unreal.Rotator(pitch=-20,yaw=140,roll=0),False)
            actor.light_component.set_intensity(3.2)
            actor.light_component.set_light_color(unreal.LinearColor(.32,.08,1,1),False)
        else:
            actor.set_actor_rotation(unreal.Rotator(pitch=-45,yaw=-30,roll=0),False)
            actor.light_component.set_intensity(2.5)
            actor.light_component.set_light_color(unreal.LinearColor(.75,.81,1,1),False)
            actor.set_actor_label('Comic Key - Warm')
    elif isinstance(actor,unreal.SkyLight):
        actor.light_component.set_intensity(.12)
        actor.light_component.set_light_color(unreal.LinearColor(.22,.07,.5,1))
    elif isinstance(actor,unreal.StaticMeshActor) and (label.startswith('White Floor') or label=='Comic Stage - Blue Grey'):
        actor.static_mesh_component.set_material(0,floor)
        actor.set_actor_scale3d(unreal.Vector(160,160,.2))
        actor.set_actor_label('Comic Stage - Blue Grey')
    elif isinstance(actor,unreal.SkyAtmosphere) or isinstance(actor,unreal.ExponentialHeightFog):
        actor.set_actor_hidden_in_game(True)
        actor.set_is_temporarily_hidden_in_editor(True)
    elif isinstance(actor,unreal.StaticMeshActor) and ('Sky' in label or 'Boundary' in label):
        actor.set_actor_hidden_in_game(True)
        actor.set_is_temporarily_hidden_in_editor(True)
if not any(a.get_actor_label()=='Comic Rim - Cyan' for a in actors):
    rim=eas.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,400),unreal.Rotator(pitch=-22,yaw=145,roll=0))
    rim.set_actor_label('Comic Rim - Cyan')
    rim.light_component.set_intensity(3.2)
    rim.light_component.set_light_color(unreal.LinearColor(.32,.08,1,1),False)
    rim.light_component.set_cast_shadows(False)
sky=next((a for a in actors if a.get_actor_label()=='Comic Night Dome'),None)
if sky is None:
    sky=eas.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0))
    sky.set_actor_label('Comic Night Dome')
sky.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Sphere'))
sky.static_mesh_component.set_material(0,unreal.load_asset('/Game/ComicCombat/Materials/M_CC_NightSky'))
sky.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
sky.static_mesh_component.set_collision_profile_name('NoCollision')
sky.set_actor_enable_collision(False)
sky.static_mesh_component.set_cast_shadow(False)
sky.static_mesh_component.set_editor_property('visible_in_ray_tracing',False)
sky.set_actor_scale3d(unreal.Vector(400,400,400))
assert le.save_current_level()
print('COMIC_LIGHTING_COMPLETE',dest)
