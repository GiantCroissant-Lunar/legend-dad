using System.Collections.Generic;
using System.IO;
using LegendDad.Articy;

namespace LegendDad.MdkPlugin
{
	/// <summary>
	/// Writes articy IDs back to import-manifest.json after entity creation.
	/// This allows subsequent runs of vault_to_manifest.py (with --previous)
	/// to carry forward the articy IDs and compute correct diff status.
	/// </summary>
	public static class ManifestWriteback
	{
		public static void WriteIds(string manifestPath, List<IdMapping> mappings)
		{
			var json = File.ReadAllText(manifestPath);
			var manifest = ImportManifest.FromJson(json);

			var idLookup = new Dictionary<string, string>();
			foreach (var mapping in mappings)
			{
				idLookup[mapping.VaultPath] = mapping.ArticyId;
			}

			foreach (var entity in manifest.Entities)
			{
				if (idLookup.TryGetValue(entity.VaultPath, out var articyId))
				{
					entity.ArticyId = articyId;
				}
			}

			var updatedJson = Serialize.ToJson(manifest);
			File.WriteAllText(manifestPath, updatedJson);
		}
	}
}
