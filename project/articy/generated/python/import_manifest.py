from dataclasses import dataclass
from typing import Any, Optional, List, Dict, TypeVar, Type, Callable, cast
from enum import Enum
from datetime import datetime
import dateutil.parser


T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def to_float(x: Any) -> float:
    assert isinstance(x, (int, float))
    return x


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_dict(f: Callable[[Any], T], x: Any) -> Dict[str, T]:
    assert isinstance(x, dict)
    return { k: f(v) for (k, v) in x.items() }


def from_datetime(x: Any) -> datetime:
    return dateutil.parser.parse(x)


@dataclass
class ConnectionElement:
    relation: str
    """Relationship type (e.g. member_of, mentor, located_in)"""

    target_vault_path: str
    """Vault path of the target entity"""

    @staticmethod
    def from_dict(obj: Any) -> 'ConnectionElement':
        assert isinstance(obj, dict)
        relation = from_str(obj.get("relation"))
        target_vault_path = from_str(obj.get("target_vault_path"))
        return ConnectionElement(relation, target_vault_path)

    def to_dict(self) -> dict:
        result: dict = {}
        result["relation"] = from_str(self.relation)
        result["target_vault_path"] = from_str(self.target_vault_path)
        return result


class Status(Enum):
    """Diff status vs previous manifest"""

    NEW = "new"
    UNCHANGED = "unchanged"
    UPDATED = "updated"


class Kind(Enum):
    ATTACK = "attack"
    SPELL = "spell"
    STATUS_INFLICT = "status_inflict"


class TargetKind(Enum):
    ALL_ENEMIES = "all_enemies"
    ENEMY = "enemy"
    SELF = "self"


@dataclass
class ActionElement:
    frequency: float
    id: str
    kind: Kind
    power_max: Optional[int] = None
    power_min: Optional[int] = None
    spell_id: Optional[str] = None
    status_effect: Optional[str] = None
    target_kind: Optional[TargetKind] = None

    @staticmethod
    def from_dict(obj: Any) -> 'ActionElement':
        assert isinstance(obj, dict)
        frequency = from_float(obj.get("frequency"))
        id = from_str(obj.get("id"))
        kind = Kind(obj.get("kind"))
        power_max = from_union([from_int, from_none], obj.get("power_max"))
        power_min = from_union([from_int, from_none], obj.get("power_min"))
        spell_id = from_union([from_str, from_none], obj.get("spell_id"))
        status_effect = from_union([from_str, from_none], obj.get("status_effect"))
        target_kind = from_union([TargetKind, from_none], obj.get("target_kind"))
        return ActionElement(frequency, id, kind, power_max, power_min, spell_id, status_effect, target_kind)

    def to_dict(self) -> dict:
        result: dict = {}
        result["frequency"] = to_float(self.frequency)
        result["id"] = from_str(self.id)
        result["kind"] = to_enum(Kind, self.kind)
        if self.power_max is not None:
            result["power_max"] = from_union([from_int, from_none], self.power_max)
        if self.power_min is not None:
            result["power_min"] = from_union([from_int, from_none], self.power_min)
        if self.spell_id is not None:
            result["spell_id"] = from_union([from_str, from_none], self.spell_id)
        if self.status_effect is not None:
            result["status_effect"] = from_union([from_str, from_none], self.status_effect)
        if self.target_kind is not None:
            result["target_kind"] = from_union([lambda x: to_enum(TargetKind, x), from_none], self.target_kind)
        return result


@dataclass
class BattleStats:
    atk: int
    battle_stats_def: int
    gold_reward: int
    max_hp: int
    spd: int
    xp_reward: int
    level: Optional[int] = None
    max_mp: Optional[int] = None

    @staticmethod
    def from_dict(obj: Any) -> 'BattleStats':
        assert isinstance(obj, dict)
        atk = from_int(obj.get("atk"))
        battle_stats_def = from_int(obj.get("def"))
        gold_reward = from_int(obj.get("gold_reward"))
        max_hp = from_int(obj.get("max_hp"))
        spd = from_int(obj.get("spd"))
        xp_reward = from_int(obj.get("xp_reward"))
        level = from_union([from_int, from_none], obj.get("level"))
        max_mp = from_union([from_int, from_none], obj.get("max_mp"))
        return BattleStats(atk, battle_stats_def, gold_reward, max_hp, spd, xp_reward, level, max_mp)

    def to_dict(self) -> dict:
        result: dict = {}
        result["atk"] = from_int(self.atk)
        result["def"] = from_int(self.battle_stats_def)
        result["gold_reward"] = from_int(self.gold_reward)
        result["max_hp"] = from_int(self.max_hp)
        result["spd"] = from_int(self.spd)
        result["xp_reward"] = from_int(self.xp_reward)
        if self.level is not None:
            result["level"] = from_union([from_int, from_none], self.level)
        if self.max_mp is not None:
            result["max_mp"] = from_union([from_int, from_none], self.max_mp)
        return result


class CurveKind(Enum):
    MONSTER_SCALING = "monster_scaling"
    STAT_GROWTH = "stat_growth"
    XP_TO_LEVEL = "xp_to_level"


@dataclass
class DataPointElement:
    level: int
    atk: Optional[int] = None
    import_manifest_schema_def: Optional[int] = None
    level_offset: Optional[int] = None
    max_hp: Optional[int] = None
    max_mp: Optional[int] = None
    spd: Optional[int] = None
    xp_required: Optional[int] = None

    @staticmethod
    def from_dict(obj: Any) -> 'DataPointElement':
        assert isinstance(obj, dict)
        level = from_int(obj.get("level"))
        atk = from_union([from_int, from_none], obj.get("atk"))
        import_manifest_schema_def = from_union([from_int, from_none], obj.get("def"))
        level_offset = from_union([from_int, from_none], obj.get("level_offset"))
        max_hp = from_union([from_int, from_none], obj.get("max_hp"))
        max_mp = from_union([from_int, from_none], obj.get("max_mp"))
        spd = from_union([from_int, from_none], obj.get("spd"))
        xp_required = from_union([from_int, from_none], obj.get("xp_required"))
        return DataPointElement(level, atk, import_manifest_schema_def, level_offset, max_hp, max_mp, spd, xp_required)

    def to_dict(self) -> dict:
        result: dict = {}
        result["level"] = from_int(self.level)
        if self.atk is not None:
            result["atk"] = from_union([from_int, from_none], self.atk)
        if self.import_manifest_schema_def is not None:
            result["def"] = from_union([from_int, from_none], self.import_manifest_schema_def)
        if self.level_offset is not None:
            result["level_offset"] = from_union([from_int, from_none], self.level_offset)
        if self.max_hp is not None:
            result["max_hp"] = from_union([from_int, from_none], self.max_hp)
        if self.max_mp is not None:
            result["max_mp"] = from_union([from_int, from_none], self.max_mp)
        if self.spd is not None:
            result["spd"] = from_union([from_int, from_none], self.spd)
        if self.xp_required is not None:
            result["xp_required"] = from_union([from_int, from_none], self.xp_required)
        return result


class Era(Enum):
    BOTH = "both"
    FATHER = "father"
    SON = "son"


@dataclass
class EncounterTableElement:
    bestiary: str
    """Vault wikilink to the bestiary entry"""

    era: Era
    weight: int

    @staticmethod
    def from_dict(obj: Any) -> 'EncounterTableElement':
        assert isinstance(obj, dict)
        bestiary = from_str(obj.get("bestiary"))
        era = Era(obj.get("era"))
        weight = from_int(obj.get("weight"))
        return EncounterTableElement(bestiary, era, weight)

    def to_dict(self) -> dict:
        result: dict = {}
        result["bestiary"] = from_str(self.bestiary)
        result["era"] = to_enum(Era, self.era)
        result["weight"] = from_int(self.weight)
        return result


@dataclass
class TemplateProperties:
    """Key-value map matching articy template fields. Narrative fields are strings; mechanical
    fields (battle_stats, actions, encounter_table, etc.) use structured types.
    """
    actions: Optional[List[ActionElement]] = None
    applies_to: Optional[str] = None
    battle_stats: Optional[BattleStats] = None
    curve_kind: Optional[CurveKind] = None
    data_points: Optional[List[DataPointElement]] = None
    difficulty_tier: Optional[int] = None
    encounter_rate: Optional[float] = None
    encounter_table: Optional[List[EncounterTableElement]] = None
    group_size_max: Optional[int] = None
    group_size_min: Optional[int] = None
    recommended_level_max: Optional[int] = None
    recommended_level_min: Optional[int] = None
    zone_affinity: Optional[List[str]] = None

    @staticmethod
    def from_dict(obj: Any) -> 'TemplateProperties':
        assert isinstance(obj, dict)
        actions = from_union([lambda x: from_list(ActionElement.from_dict, x), from_none], obj.get("actions"))
        applies_to = from_union([from_str, from_none], obj.get("applies_to"))
        battle_stats = from_union([BattleStats.from_dict, from_none], obj.get("battle_stats"))
        curve_kind = from_union([CurveKind, from_none], obj.get("curve_kind"))
        data_points = from_union([lambda x: from_list(DataPointElement.from_dict, x), from_none], obj.get("data_points"))
        difficulty_tier = from_union([from_int, from_none], obj.get("difficulty_tier"))
        encounter_rate = from_union([from_float, from_none], obj.get("encounter_rate"))
        encounter_table = from_union([lambda x: from_list(EncounterTableElement.from_dict, x), from_none], obj.get("encounter_table"))
        group_size_max = from_union([from_int, from_none], obj.get("group_size_max"))
        group_size_min = from_union([from_int, from_none], obj.get("group_size_min"))
        recommended_level_max = from_union([from_int, from_none], obj.get("recommended_level_max"))
        recommended_level_min = from_union([from_int, from_none], obj.get("recommended_level_min"))
        zone_affinity = from_union([lambda x: from_list(from_str, x), from_none], obj.get("zone_affinity"))
        return TemplateProperties(actions, applies_to, battle_stats, curve_kind, data_points, difficulty_tier, encounter_rate, encounter_table, group_size_max, group_size_min, recommended_level_max, recommended_level_min, zone_affinity)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.actions is not None:
            result["actions"] = from_union([lambda x: from_list(lambda x: to_class(ActionElement, x), x), from_none], self.actions)
        if self.applies_to is not None:
            result["applies_to"] = from_union([from_str, from_none], self.applies_to)
        if self.battle_stats is not None:
            result["battle_stats"] = from_union([lambda x: to_class(BattleStats, x), from_none], self.battle_stats)
        if self.curve_kind is not None:
            result["curve_kind"] = from_union([lambda x: to_enum(CurveKind, x), from_none], self.curve_kind)
        if self.data_points is not None:
            result["data_points"] = from_union([lambda x: from_list(lambda x: to_class(DataPointElement, x), x), from_none], self.data_points)
        if self.difficulty_tier is not None:
            result["difficulty_tier"] = from_union([from_int, from_none], self.difficulty_tier)
        if self.encounter_rate is not None:
            result["encounter_rate"] = from_union([to_float, from_none], self.encounter_rate)
        if self.encounter_table is not None:
            result["encounter_table"] = from_union([lambda x: from_list(lambda x: to_class(EncounterTableElement, x), x), from_none], self.encounter_table)
        if self.group_size_max is not None:
            result["group_size_max"] = from_union([from_int, from_none], self.group_size_max)
        if self.group_size_min is not None:
            result["group_size_min"] = from_union([from_int, from_none], self.group_size_min)
        if self.recommended_level_max is not None:
            result["recommended_level_max"] = from_union([from_int, from_none], self.recommended_level_max)
        if self.recommended_level_min is not None:
            result["recommended_level_min"] = from_union([from_int, from_none], self.recommended_level_min)
        if self.zone_affinity is not None:
            result["zone_affinity"] = from_union([lambda x: from_list(from_str, x), from_none], self.zone_affinity)
        return result


class TypeEnum(Enum):
    """Entity type, maps to articy template"""

    BESTIARY = "bestiary"
    CHARACTER = "character"
    CURVE = "curve"
    EVENT = "event"
    FACTION = "faction"
    ITEM = "item"
    LOCATION = "location"
    LORE = "lore"
    QUEST = "quest"
    ZONE = "zone"


@dataclass
class EntityElement:
    articy_id: str
    """Articy entity ID. Empty on first run, filled by MDK plugin."""

    connections: List[ConnectionElement]
    """Relationships to other entities"""

    creative_prompts: Dict[str, str]
    """Asset generation prompts keyed by type (portrait, voice, etc.)"""

    display_name: str
    """Entity display name in articy"""

    status: Status
    """Diff status vs previous manifest"""

    template_properties: TemplateProperties
    """Key-value map matching articy template fields. Narrative fields are strings; mechanical
    fields (battle_stats, actions, encounter_table, etc.) use structured types.
    """
    type: TypeEnum
    """Entity type, maps to articy template"""

    vault_path: str
    """Relative path to the source vault page"""

    dialogue_hooks: Optional[List[str]] = None
    """Hints for dialogue authoring in articy"""

    flow_notes: Optional[str] = None
    """Hints for quest/flow design in articy"""

    @staticmethod
    def from_dict(obj: Any) -> 'EntityElement':
        assert isinstance(obj, dict)
        articy_id = from_str(obj.get("articy_id"))
        connections = from_list(ConnectionElement.from_dict, obj.get("connections"))
        creative_prompts = from_dict(from_str, obj.get("creative_prompts"))
        display_name = from_str(obj.get("display_name"))
        status = Status(obj.get("status"))
        template_properties = TemplateProperties.from_dict(obj.get("template_properties"))
        type = TypeEnum(obj.get("type"))
        vault_path = from_str(obj.get("vault_path"))
        dialogue_hooks = from_union([lambda x: from_list(from_str, x), from_none], obj.get("dialogue_hooks"))
        flow_notes = from_union([from_str, from_none], obj.get("flow_notes"))
        return EntityElement(articy_id, connections, creative_prompts, display_name, status, template_properties, type, vault_path, dialogue_hooks, flow_notes)

    def to_dict(self) -> dict:
        result: dict = {}
        result["articy_id"] = from_str(self.articy_id)
        result["connections"] = from_list(lambda x: to_class(ConnectionElement, x), self.connections)
        result["creative_prompts"] = from_dict(from_str, self.creative_prompts)
        result["display_name"] = from_str(self.display_name)
        result["status"] = to_enum(Status, self.status)
        result["template_properties"] = to_class(TemplateProperties, self.template_properties)
        result["type"] = to_enum(TypeEnum, self.type)
        result["vault_path"] = from_str(self.vault_path)
        if self.dialogue_hooks is not None:
            result["dialogue_hooks"] = from_union([lambda x: from_list(from_str, x), from_none], self.dialogue_hooks)
        if self.flow_notes is not None:
            result["flow_notes"] = from_union([from_str, from_none], self.flow_notes)
        return result


@dataclass
class ImportManifest:
    """Contract between vault parser and MDK plugin. Generated by vault_to_manifest.py."""

    entities: List[EntityElement]
    generated: datetime
    """ISO 8601 timestamp of generation"""

    generated_by: str
    """Tool that generated this manifest"""

    version: str
    """Schema version (semver)"""

    @staticmethod
    def from_dict(obj: Any) -> 'ImportManifest':
        assert isinstance(obj, dict)
        entities = from_list(EntityElement.from_dict, obj.get("entities"))
        generated = from_datetime(obj.get("generated"))
        generated_by = from_str(obj.get("generated_by"))
        version = from_str(obj.get("version"))
        return ImportManifest(entities, generated, generated_by, version)

    def to_dict(self) -> dict:
        result: dict = {}
        result["entities"] = from_list(lambda x: to_class(EntityElement, x), self.entities)
        result["generated"] = self.generated.isoformat()
        result["generated_by"] = from_str(self.generated_by)
        result["version"] = from_str(self.version)
        return result


def import_manifest_from_dict(s: Any) -> ImportManifest:
    return ImportManifest.from_dict(s)


def import_manifest_to_dict(x: ImportManifest) -> Any:
    return to_class(ImportManifest, x)
