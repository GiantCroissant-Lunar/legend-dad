using System;
using System.Collections.Generic;
using System.IO;
using Articy.Api;
using LegendDad.Articy;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace LegendDad.MdkPlugin
{
	/// <summary>
	/// Reads import-manifest.json and creates/updates articy entities.
	/// Maps template_properties to NarrativeProps, creative_prompts to CreativePrompts,
	/// mechanical data to BattleStats/EncounterData/DifficultyData/CurveData features,
	/// and metadata to PipelineMeta features.
	/// </summary>
	public class EntityImporter
	{
		private readonly ApiSession _session;
		private readonly List<IdMapping> _idMappings = new List<IdMapping>();

		/// <summary>
		/// Maps manifest entity type to articy template technical name.
		/// Must match the technical_name values in template-definitions.json.
		/// </summary>
		private static readonly Dictionary<TypeEnum, string> TypeToTemplate = new Dictionary<TypeEnum, string>
		{
			{ TypeEnum.Character, "LD_Character" },
			{ TypeEnum.Location, "LD_Location" },
			{ TypeEnum.Zone, "LD_Zone" },
			{ TypeEnum.Faction, "LD_Faction" },
			{ TypeEnum.Quest, "LD_Quest" },
			{ TypeEnum.Item, "LD_Item" },
			{ TypeEnum.Event, "LD_Event" },
			{ TypeEnum.Lore, "LD_Lore" },
			{ TypeEnum.Bestiary, "LD_Creature" },
			{ TypeEnum.Curve, "LD_Curve" }
		};

		/// <summary>
		/// Mechanical property keys that map to specific features (not NarrativeProps).
		/// Key = property name in manifest, Value = feature base name in template-definitions.json.
		/// </summary>
		private static readonly Dictionary<string, string> MechanicalPropFeature = new Dictionary<string, string>
		{
			// Bestiary → BattleStats
			{ "battle_stats", "BattleStats" },
			{ "actions", "BattleStats" },
			{ "group_size_min", "BattleStats" },
			{ "group_size_max", "BattleStats" },
			{ "zone_affinity", "BattleStats" },
			// Zone → EncounterData
			{ "encounter_table", "EncounterData" },
			{ "encounter_rate", "EncounterData" },
			// Location → DifficultyData (difficulty_tier shared, resolved by entity type)
			{ "recommended_level_min", "DifficultyData" },
			{ "recommended_level_max", "DifficultyData" },
			{ "difficulty_tier", "EncounterData" }, // zones use EncounterData; locations handled below
			// Curve → CurveData
			{ "curve_kind", "CurveData" },
			{ "applies_to", "CurveData" },
			{ "data_points", "CurveData" }
		};

		public EntityImporter(ApiSession session)
		{
			_session = session;
		}

		public ImportReport ImportAll(string manifestPath)
		{
			var report = new ImportReport();
			var json = File.ReadAllText(manifestPath);
			var manifest = ImportManifest.FromJson(json);
			var entitiesFolder = _session.GetSystemFolder(SystemFolderNames.Entities);

			foreach (var entity in manifest.Entities)
			{
				switch (entity.Status)
				{
					case Status.Unchanged:
						report.Skipped++;
						if (!string.IsNullOrEmpty(entity.ArticyId))
							_idMappings.Add(new IdMapping(entity.VaultPath, entity.ArticyId, entity.DisplayName));
						continue;

					case Status.New:
						CreateEntity(entitiesFolder, entity);
						report.Created++;
						break;

					case Status.Updated:
						UpdateEntity(entity);
						report.Updated++;
						break;
				}
			}

			return report;
		}

		public List<IdMapping> GetIdMappings() => _idMappings;

		private void CreateEntity(ObjectProxy folder, EntityElement entity)
		{
			if (!TypeToTemplate.TryGetValue(entity.Type, out var templateName))
			{
				Console.Error.WriteLine($"Warning: unknown entity type {entity.Type} for {entity.VaultPath}");
				return;
			}

			var obj = _session.CreateEntity(folder, entity.DisplayName, templateName);
			var techName = MakeTechnicalName(entity.DisplayName);
			obj.SetTechnicalName(techName);

			SetEntityProperties(obj, entity, templateName);

			var articyId = obj[ObjectPropertyNames.Id]?.ToString() ?? "";
			_idMappings.Add(new IdMapping(entity.VaultPath, articyId, entity.DisplayName));
		}

		private void UpdateEntity(EntityElement entity)
		{
			if (string.IsNullOrEmpty(entity.ArticyId))
			{
				Console.Error.WriteLine($"Warning: cannot update entity without articy_id: {entity.VaultPath}");
				return;
			}

			ObjectProxy obj;
			try
			{
				// Try by technical name first (derived from display name), fall back to ID
				var techName = MakeTechnicalName(entity.DisplayName);
				obj = _session.GetObjectByTechName(techName);
			}
			catch
			{
				try
				{
					// Fall back to numeric ID lookup
					if (ulong.TryParse(entity.ArticyId.Replace("0x", ""), System.Globalization.NumberStyles.HexNumber, null, out var numId))
						obj = _session.GetObjectById(numId);
					else
					{
						Console.Error.WriteLine($"Warning: entity not found in articy: {entity.ArticyId} ({entity.VaultPath})");
						return;
					}
				}
				catch
				{
					Console.Error.WriteLine($"Warning: entity not found in articy: {entity.ArticyId} ({entity.VaultPath})");
					return;
				}
			}

			if (!TypeToTemplate.TryGetValue(entity.Type, out var templateName))
				return;

			SetEntityProperties(obj, entity, templateName);
			_idMappings.Add(new IdMapping(entity.VaultPath, entity.ArticyId, entity.DisplayName));
		}

		private void SetEntityProperties(ObjectProxy obj, EntityElement entity, string templateName)
		{
			// Feature technical names are prefixed with template name (see TemplateProvisioner)
			var narrativePrefix = $"{templateName}_NarrativeProps";
			var creativePrefix = $"{templateName}_CreativePrompts";
			var metaPrefix = $"{templateName}_PipelineMeta";

			if (entity.TemplateProperties != null)
			{
				// Narrative text fields (overview, backstory, etc.) — captured by JsonExtensionData
				if (entity.TemplateProperties.NarrativeFields != null)
				{
					foreach (var kvp in entity.TemplateProperties.NarrativeFields)
					{
						var propName = $"{narrativePrefix}.{kvp.Key}";
						TrySetProperty(obj, propName, kvp.Value?.ToString() ?? "");
					}
				}

				// Mechanical fields — route to their specific features
				SetMechanicalProperties(obj, entity, templateName);
			}

			// Set creative prompts (normalize hyphens to underscores)
			if (entity.CreativePrompts != null)
			{
				foreach (var kvp in entity.CreativePrompts)
				{
					var normalizedKey = kvp.Key.Replace("-", "_");
					var propName = $"{creativePrefix}.{normalizedKey}";
					TrySetProperty(obj, propName, kvp.Value);
				}
			}

			// Set pipeline metadata
			TrySetProperty(obj, $"{metaPrefix}.vault_path", entity.VaultPath);

			if (entity.DialogueHooks != null && entity.DialogueHooks.Length > 0)
			{
				var hooksText = string.Join("\n", entity.DialogueHooks);
				TrySetProperty(obj, $"{metaPrefix}.dialogue_hooks", hooksText);
			}

			if (!string.IsNullOrEmpty(entity.FlowNotes))
			{
				TrySetProperty(obj, $"{metaPrefix}.flow_notes", entity.FlowNotes);
			}
		}

		/// <summary>
		/// Set mechanical properties (battle_stats, actions, encounter_table, etc.)
		/// on their corresponding articy features. Structured data is serialized to
		/// JSON text since articy template properties are all Text type.
		/// </summary>
		private void SetMechanicalProperties(ObjectProxy obj, EntityElement entity, string templateName)
		{
			var props = entity.TemplateProperties;

			switch (entity.Type)
			{
				case TypeEnum.Bestiary:
				{
					var prefix = $"{templateName}_BattleStats";
					if (props.BattleStats != null)
						TrySetProperty(obj, $"{prefix}.battle_stats", JsonConvert.SerializeObject(props.BattleStats));
					if (props.Actions != null)
						TrySetProperty(obj, $"{prefix}.actions", JsonConvert.SerializeObject(props.Actions));
					if (props.GroupSizeMin.HasValue)
						TrySetProperty(obj, $"{prefix}.group_size_min", props.GroupSizeMin.Value.ToString());
					if (props.GroupSizeMax.HasValue)
						TrySetProperty(obj, $"{prefix}.group_size_max", props.GroupSizeMax.Value.ToString());
					if (props.ZoneAffinity != null)
						TrySetProperty(obj, $"{prefix}.zone_affinity", JsonConvert.SerializeObject(props.ZoneAffinity));
					break;
				}

				case TypeEnum.Zone:
				{
					var prefix = $"{templateName}_EncounterData";
					if (props.EncounterTable != null)
						TrySetProperty(obj, $"{prefix}.encounter_table", JsonConvert.SerializeObject(props.EncounterTable));
					if (props.EncounterRate.HasValue)
						TrySetProperty(obj, $"{prefix}.encounter_rate", props.EncounterRate.Value.ToString("F2"));
					if (props.DifficultyTier.HasValue)
						TrySetProperty(obj, $"{prefix}.difficulty_tier", props.DifficultyTier.Value.ToString());
					break;
				}

				case TypeEnum.Location:
				{
					var prefix = $"{templateName}_DifficultyData";
					if (props.RecommendedLevelMin.HasValue)
						TrySetProperty(obj, $"{prefix}.recommended_level_min", props.RecommendedLevelMin.Value.ToString());
					if (props.RecommendedLevelMax.HasValue)
						TrySetProperty(obj, $"{prefix}.recommended_level_max", props.RecommendedLevelMax.Value.ToString());
					if (props.DifficultyTier.HasValue)
						TrySetProperty(obj, $"{prefix}.difficulty_tier", props.DifficultyTier.Value.ToString());
					break;
				}

				case TypeEnum.Curve:
				{
					var prefix = $"{templateName}_CurveData";
					if (props.CurveKind.HasValue)
						TrySetProperty(obj, $"{prefix}.curve_kind", props.CurveKind.Value.ToString());
					if (!string.IsNullOrEmpty(props.AppliesTo))
						TrySetProperty(obj, $"{prefix}.applies_to", props.AppliesTo);
					if (props.DataPoints != null)
						TrySetProperty(obj, $"{prefix}.data_points", JsonConvert.SerializeObject(props.DataPoints));
					break;
				}
			}
		}

		private static void TrySetProperty(ObjectProxy obj, string propertyPath, string value)
		{
			try
			{
				obj[propertyPath] = value;
			}
			catch (Exception ex)
			{
				Console.Error.WriteLine($"Warning: failed to set {propertyPath}: {ex.Message}");
			}
		}

		/// <summary>
		/// Convert a display name to a valid articy technical name.
		/// </summary>
		private static string MakeTechnicalName(string displayName)
		{
			var tech = displayName.Replace(" ", "_").Replace("-", "_");
			var result = new System.Text.StringBuilder();
			foreach (var c in tech)
			{
				if (char.IsLetterOrDigit(c) || c == '_')
					result.Append(c);
			}
			return result.ToString();
		}
	}

	public class ImportReport
	{
		public int Created { get; set; }
		public int Updated { get; set; }
		public int Skipped { get; set; }
	}

	public class IdMapping
	{
		public string VaultPath { get; }
		public string ArticyId { get; }
		public string DisplayName { get; }

		public IdMapping(string vaultPath, string articyId, string displayName)
		{
			VaultPath = vaultPath;
			ArticyId = articyId;
			DisplayName = displayName;
		}
	}
}
