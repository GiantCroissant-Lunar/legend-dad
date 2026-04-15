# project/shared/lib/contracts/content_manager_api.gd
#
# Documentation-only interface defining the autoload API. Concrete impl lives at
# project/hosts/complete-app/scripts/content_manager.gd. content-app preview
# scenes mock this via preview/mock_kernel.gd.
#
# Signals:
#   bundle_loading(bundle_id: String)
#   bundle_loaded(bundle_id: String)
#   bundle_load_failed(bundle_id: String, reason: String)
#   bundle_unloaded(bundle_id: String)
#   bundle_will_reload(bundle_id: String)   # hot-reload only
#
# Methods:
#   load_bundle(bundle_id) -> bool
#   unload_bundle(bundle_id) -> bool
#   is_loaded(bundle_id) -> bool
#   loaded_bundles() -> Array[String]
#   describe(bundle_id) -> Dictionary
#   get_enemy_definition(id: String) -> EnemyDefinition
#   get_npc_definition(id: String) -> NpcDefinition
#   get_hud_widget(id: String) -> HudWidgetDefinition
#   get_item_definition(id: String) -> ItemDefinition
#   get_spell_definition(id: String) -> SpellDefinition
class_name ContentManagerApi
extends RefCounted
