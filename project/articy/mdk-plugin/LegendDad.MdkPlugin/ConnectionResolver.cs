using System;
using System.Collections.Generic;
using System.IO;
using Articy.Api;
using LegendDad.Articy;

namespace LegendDad.MdkPlugin
{
	/// <summary>
	/// Resolves connections between entities using vault_path and display_name lookups.
	/// For Phase 2, connections are stored as text in the entity's Text/Description field
	/// rather than as articy graph connections (which require Flow objects).
	/// </summary>
	public class ConnectionResolver
	{
		private readonly ApiSession _session;

		public ConnectionResolver(ApiSession session)
		{
			_session = session;
		}

		public ConnectionReport ResolveAll(string manifestPath)
		{
			var report = new ConnectionReport();
			var json = File.ReadAllText(manifestPath);
			var manifest = ImportManifest.FromJson(json);

			// Build lookup: vault_path and display_name -> articy_id
			var byPath = new Dictionary<string, string>();
			var byName = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

			foreach (var entity in manifest.Entities)
			{
				if (!string.IsNullOrEmpty(entity.ArticyId))
				{
					byPath[entity.VaultPath] = entity.ArticyId;
					byName[entity.DisplayName] = entity.ArticyId;
				}
			}

			foreach (var entity in manifest.Entities)
			{
				if (entity.Connections == null || entity.Connections.Length == 0)
					continue;

				if (string.IsNullOrEmpty(entity.ArticyId))
					continue;

				var resolvedLines = new List<string>();
				foreach (var conn in entity.Connections)
				{
					string targetId = null;
					var target = conn.TargetVaultPath;

					if (byPath.TryGetValue(target, out targetId) || byName.TryGetValue(target, out targetId))
					{
						resolvedLines.Add($"{conn.Relation}: {target} ({targetId})");
						report.Resolved++;
					}
					else
					{
						resolvedLines.Add($"{conn.Relation}: {target} (UNRESOLVED)");
						report.Unresolved++;
					}
				}

				if (resolvedLines.Count > 0)
				{
					try
					{
						// Look up the entity by technical name
						var techName = entity.DisplayName.Replace(" ", "_").Replace("-", "_");
						var cleanName = new System.Text.StringBuilder();
						foreach (var c in techName)
						{
							if (char.IsLetterOrDigit(c) || c == '_')
								cleanName.Append(c);
						}
						var obj = _session.GetObjectByTechName(cleanName.ToString());
						var existingDesc = obj[ObjectPropertyNames.Text]?.ToString() ?? "";
						var connectionsText = "\n\n--- Connections ---\n" + string.Join("\n", resolvedLines);

						if (!existingDesc.Contains("--- Connections ---"))
							obj[ObjectPropertyNames.Text] = existingDesc + connectionsText;
						else
							obj[ObjectPropertyNames.Text] = existingDesc
								.Split(new[] { "--- Connections ---" }, StringSplitOptions.None)[0]
								.TrimEnd() + connectionsText;
					}
					catch (Exception ex)
					{
						Console.Error.WriteLine($"Warning: failed to set connections on {entity.DisplayName}: {ex.Message}");
					}
				}
			}

			return report;
		}
	}

	public class ConnectionReport
	{
		public int Resolved { get; set; }
		public int Unresolved { get; set; }
	}
}
