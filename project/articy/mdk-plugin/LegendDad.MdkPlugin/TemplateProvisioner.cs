using System;
using System.IO;
using Articy.Api;
using Articy.Api.ObjectCustomization;
using Newtonsoft.Json.Linq;

namespace LegendDad.MdkPlugin
{
	/// <summary>
	/// Reads template-definitions.json and creates/verifies articy templates.
	/// Each template gets features with TextPropertyBlueprint properties.
	/// </summary>
	public class TemplateProvisioner
	{
		private readonly ApiSession _session;

		public TemplateProvisioner(ApiSession session)
		{
			_session = session;
		}

		public TemplateReport EnsureTemplates(string templateDefsPath)
		{
			var report = new TemplateReport();
			var defs = JObject.Parse(File.ReadAllText(templateDefsPath));
			var templates = (JObject)defs["templates"];

			foreach (var templateEntry in templates)
			{
				var templateDef = (JObject)templateEntry.Value;
				var technicalName = (string)templateDef["technical_name"];

				if (TemplateExists(technicalName))
				{
					report.Skipped++;
					continue;
				}

				CreateTemplate(templateDef);
				report.Created++;
			}

			return report;
		}

		public TemplateReport VerifyTemplates(string templateDefsPath)
		{
			var report = new TemplateReport();
			var defs = JObject.Parse(File.ReadAllText(templateDefsPath));
			var templates = (JObject)defs["templates"];

			foreach (var templateEntry in templates)
			{
				var templateDef = (JObject)templateEntry.Value;
				var technicalName = (string)templateDef["technical_name"];

				if (TemplateExists(technicalName))
					report.Skipped++;
				else
					report.Missing++;
			}

			return report;
		}

		private bool TemplateExists(string technicalName)
		{
			try
			{
				var obj = _session.GetObjectByTechName(technicalName);
				// Verify it's actually a template, not a system object or entity with the same name
				return obj.ObjectType == ObjectType.Template;
			}
			catch
			{
				return false;
			}
		}

		private void CreateTemplate(JObject templateDef)
		{
			var technicalName = (string)templateDef["technical_name"];
			var displayName = (string)templateDef["display_name"];
			var objectTypeStr = (string)templateDef["articy_object_type"];

			var objectType = objectTypeStr == "FlowFragment"
				? ObjectType.FlowFragment
				: ObjectType.Entity;

			var bp = _session.BeginNewObjectTemplate(objectType);
			bp.TechnicalName = technicalName;
			bp.DisplayName = displayName;

			var features = (JObject)templateDef["features"];
			if (features != null)
			{
				foreach (var featureEntry in features)
				{
					var featureTechName = featureEntry.Key;
					var featureDef = (JObject)featureEntry.Value;
					var featureProxy = GetOrCreateFeature(featureTechName, featureDef, technicalName, displayName);
					bp.AddFeature(featureProxy);
				}
			}

			_session.EndObjectTemplate(bp);
		}

		/// <summary>
		/// Create a feature with text properties.
		/// Feature technical names are prefixed with the template name to avoid
		/// collisions (e.g. Character_NarrativeProps, Location_NarrativeProps).
		/// </summary>
		private ObjectProxy GetOrCreateFeature(string baseTechName, JObject featureDef, string templateTechName, string templateDisplayName)
		{
			var featureTechName = $"{templateTechName}_{baseTechName}";

			// Check if feature already exists
			try
			{
				var existing = _session.GetObjectByTechName(featureTechName);
				if (existing.ObjectType == ObjectType.Feature)
					return existing;
			}
			catch { }

			var baseDisplayName = (string)featureDef["display_name"];
			var featureDisplayName = $"{templateDisplayName} - {baseDisplayName}";

			var bp = _session.BeginNewFeature();
			bp.TechnicalName = featureTechName;
			bp.DisplayName = featureDisplayName;

			var properties = (JObject)featureDef["properties"];
			if (properties != null)
			{
				foreach (var propEntry in properties)
				{
					var propTechName = propEntry.Key;
					var propDef = (JObject)propEntry.Value;
					var propDisplayName = (string)propDef["display_name"];

					var propBp = bp.AddProperty<TextPropertyBlueprint>();
					propBp.TechnicalName = propTechName;
					propBp.DisplayName = propDisplayName;
				}
			}

			return _session.EndFeature(bp);
		}
	}

	public class TemplateReport
	{
		public int Created { get; set; }
		public int Skipped { get; set; }
		public int Missing { get; set; }
	}
}
