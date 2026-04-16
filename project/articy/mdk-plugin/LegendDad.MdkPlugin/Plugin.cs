using System;
using System.Collections.Generic;
using System.IO;
using System.Windows.Media;
using Articy.Api;
using Articy.Api.Plugins;

using Texts = LIds.LegendDad.MdkPlugin;

namespace LegendDad.MdkPlugin
{
	/// <summary>
	/// Legend Dad Importer — reads vault manifest and creates/updates articy entities.
	/// </summary>
	public partial class Plugin : MacroPlugin
	{
		public override string DisplayName
		{
			get { return LocalizeStringNoFormat(Texts.Plugin.DisplayName); }
		}

		public override string ContextName
		{
			get { return LocalizeStringNoFormat(Texts.Plugin.ContextName); }
		}

		public override List<MacroCommandDescriptor> GetMenuEntries(ContextArgsBase aArguments)
		{
			var result = new List<MacroCommandDescriptor>();
			switch (aArguments)
			{
				case GlobalContextArgs globalArgs:
					result.Add(new MacroCommandDescriptor
					{
						CaptionLid = "Import from Manifest",
						ModifiesData = true,
						Execute = ExecuteImport
					});
					result.Add(new MacroCommandDescriptor
					{
						CaptionLid = "Verify Templates",
						ModifiesData = false,
						Execute = ExecuteVerifyTemplates
					});
					result.Add(new MacroCommandDescriptor
					{
						CaptionLid = "Clean Up Imports",
						ModifiesData = true,
						Execute = ExecuteCleanUp
					});
					return result;

				default:
					return result;
			}
		}

		public override Brush GetIcon(string aIconName)
		{
			switch (aIconName)
			{
				case "$self":
					return Session.CreateBrushFromFile(Manifest.ManifestPath + "Resources\\Icon.png");
			}
			return null;
		}

		private void ExecuteImport(MacroCommandDescriptor aDescriptor, List<ObjectProxy> aSelectedObjects)
		{
			try
			{
				Session.ExecuteTaskWithProgressDialog(new AsyncTask(aDescriptor, aSelectedObjects)
				{
					TitleLid = "Importing from vault manifest...",
					AsyncAction = RunImport,
					ShowProgressBar = true,
					ShowMessages = true
				});
			}
			catch (Exception ex)
			{
				System.Windows.MessageBox.Show(
					$"Import failed:\n{ex.GetType().Name}: {ex.Message}\n\n{ex.StackTrace}",
					"Legend Dad Importer Error",
					System.Windows.MessageBoxButton.OK,
					System.Windows.MessageBoxImage.Error);
			}
		}

		private bool RunImport(AsyncTask aTask)
		{
			try
			{
				return RunImportInner(aTask);
			}
			catch (Exception ex)
			{
				aTask.AddMessage($"Exception: {ex.GetType().Name}: {ex.Message}", EntryType.Error);
				aTask.AddMessage(ex.StackTrace ?? "", EntryType.Error);
				return false;
			}
		}

		private bool RunImportInner(AsyncTask aTask)
		{
			var projectRoot = FindProjectRoot();
			if (projectRoot == null)
			{
				aTask.AddMessage("Error: could not find project/articy/ directory.", EntryType.Error);
				return false;
			}

			var templateDefsPath = Path.Combine(projectRoot, "schemas", "template-definitions.json");
			var manifestPath = Path.Combine(projectRoot, "import-manifest.json");

			if (!File.Exists(templateDefsPath))
			{
				aTask.AddMessage($"Error: {templateDefsPath} not found.", EntryType.Error);
				return false;
			}
			if (!File.Exists(manifestPath))
			{
				aTask.AddMessage($"Error: {manifestPath} not found.", EntryType.Error);
				return false;
			}

			aTask.SetMaxProgress(4);

			// Step 1: Ensure templates exist
			aTask.AddMessage("Provisioning templates...", EntryType.Info);
			var provisioner = new TemplateProvisioner(Session);
			var templateReport = provisioner.EnsureTemplates(templateDefsPath);
			aTask.AddMessage($"Templates: {templateReport.Created} created, {templateReport.Skipped} existing.", EntryType.Info);
			aTask.SetProgress(1);

			// Step 2: Import entities
			aTask.AddMessage("Importing entities...", EntryType.Info);
			var importer = new EntityImporter(Session);
			var importReport = importer.ImportAll(manifestPath);
			aTask.AddMessage($"Entities: {importReport.Created} created, {importReport.Updated} updated, {importReport.Skipped} unchanged.", EntryType.Info);
			aTask.SetProgress(2);

			// Step 3: Resolve connections
			aTask.AddMessage("Resolving connections...", EntryType.Info);
			var resolver = new ConnectionResolver(Session);
			var connReport = resolver.ResolveAll(manifestPath);
			aTask.AddMessage($"Connections: {connReport.Resolved} resolved, {connReport.Unresolved} unresolved.", EntryType.Info);
			aTask.SetProgress(3);

			// Step 4: Write back articy IDs
			aTask.AddMessage("Writing back articy IDs...", EntryType.Info);
			ManifestWriteback.WriteIds(manifestPath, importer.GetIdMappings());
			aTask.AddMessage("Import complete.", EntryType.Info);
			aTask.SetProgress(4);

			return true;
		}

		private void ExecuteCleanUp(MacroCommandDescriptor aDescriptor, List<ObjectProxy> aSelectedObjects)
		{
			try
			{
				Session.ExecuteTaskWithProgressDialog(new AsyncTask(aDescriptor, aSelectedObjects)
				{
					TitleLid = "Cleaning up imports...",
					AsyncAction = RunCleanUp,
					ShowProgressBar = true,
					ShowMessages = true
				});
			}
			catch (Exception ex)
			{
				System.Windows.MessageBox.Show(
					$"Clean up failed:\n{ex.Message}",
					"Legend Dad Importer Error",
					System.Windows.MessageBoxButton.OK,
					System.Windows.MessageBoxImage.Error);
			}
		}

		private bool RunCleanUp(AsyncTask aTask)
		{
			try
			{
				int deleted = 0;

				// Delete features by brute-force tech name lookup.
				// Features created by our plugin follow these patterns:
				//   Old: {Type}_{Feature}  e.g. Character_NarrativeProps
				//   New: LD_{Type}_{Feature}  e.g. LD_Character_NarrativeProps
				// articy may also append numbers for duplicates.
				var typeNames = new[] { "Character", "Location", "Zone", "Faction", "Quest", "Item", "Event", "Lore", "Creature", "Curve" };
				var featureSuffixes = new[] { "NarrativeProps", "CreativePrompts", "PipelineMeta", "BattleStats", "EncounterData", "DifficultyData", "CurveData" };

				foreach (var typeName in typeNames)
				{
					foreach (var suffix in featureSuffixes)
					{
						// Try both old and new naming patterns, plus numbered duplicates
						var basenames = new[] { $"{typeName}_{suffix}", $"LD_{typeName}_{suffix}" };
						foreach (var basename in basenames)
						{
							// Try the base name and up to 20 numbered variants
							for (int i = 0; i <= 20; i++)
							{
								var tryName = i == 0 ? basename : $"{basename}_{i:D2}";
								try
								{
									var obj = Session.GetObjectByTechName(tryName);
									aTask.AddMessage($"Deleting feature: {tryName}", EntryType.Warning);
									Session.DeleteObject(obj);
									deleted++;
								}
								catch
								{
									// Not found — skip
									if (i > 0) break; // Stop numbered search on first miss
								}
							}
						}
					}
				}

				// Delete templates (only LD_ prefixed ones, protect built-in Default* templates)
				try
				{
					var allTemplates = Session.GetObjectsByType(ObjectType.Template);
					foreach (var template in allTemplates)
					{
						var techName = template.GetTechnicalName();
						if (techName == null) continue;
						if (techName.StartsWith("Default")) continue; // protect built-in

						aTask.AddMessage($"Deleting template: {techName}", EntryType.Warning);
						Session.DeleteObject(template);
						deleted++;
					}
				}
				catch (Exception ex)
				{
					aTask.AddMessage($"Template cleanup failed: {ex.Message}", EntryType.Error);
				}

				// Delete ALL entities
				int entitiesDeleted = 0;
				try
				{
					var allEntities = Session.GetObjectsByType(ObjectType.Entity);
					foreach (var entity in allEntities)
					{
						var techName = entity.GetTechnicalName();
						aTask.AddMessage($"Deleting entity: {techName}", EntryType.Warning);
						Session.DeleteObject(entity);
						entitiesDeleted++;
					}
				}
				catch (Exception ex)
				{
					aTask.AddMessage($"Entity cleanup failed: {ex.Message}", EntryType.Error);
				}

				aTask.AddMessage($"Clean up complete: {deleted} features/templates deleted, {entitiesDeleted} entities deleted.", EntryType.Info);
				aTask.AddMessage("Now run 'Import from Manifest' to recreate everything cleanly.", EntryType.Info);
				return true;
			}
			catch (Exception ex)
			{
				aTask.AddMessage($"Exception: {ex.GetType().Name}: {ex.Message}", EntryType.Error);
				aTask.AddMessage(ex.StackTrace ?? "", EntryType.Error);
				return false;
			}
		}

		private void ExecuteVerifyTemplates(MacroCommandDescriptor aDescriptor, List<ObjectProxy> aSelectedObjects)
		{
			var projectRoot = FindProjectRoot();
			if (projectRoot == null) return;

			var templateDefsPath = Path.Combine(projectRoot, "schemas", "template-definitions.json");
			if (!File.Exists(templateDefsPath)) return;

			var provisioner = new TemplateProvisioner(Session);
			provisioner.VerifyTemplates(templateDefsPath);
		}

		/// <summary>
		/// Find project/articy/ root by checking known paths and walking up.
		/// The articy project is at project/articy/legend-dad/ and schemas/ is at project/articy/schemas/.
		/// </summary>
		private string FindProjectRoot()
		{
			var candidates = new List<string>();

			// Strategy 1: Use Session.GetProjectPath() or project root AbsoluteDirectoryProjectPath
			try
			{
				var projectRoot = Session.GetProjectRoot();
				if (projectRoot != null)
				{
					// Try various path properties that articy might expose
					foreach (var propName in new[] { "AbsoluteDirectoryProjectPath", "AbsoluteFilePath", ObjectPropertyNames.AbsoluteFilePath })
					{
						try
						{
							var path = projectRoot[propName]?.ToString();
							if (!string.IsNullOrEmpty(path))
							{
								var dir = Directory.Exists(path) ? path : Path.GetDirectoryName(path);
								for (int i = 0; i < 5 && dir != null; i++)
								{
									candidates.Add(dir);
									dir = Path.GetDirectoryName(dir);
								}
								break;
							}
						}
						catch { }
					}
				}
			}
			catch { }

			// Strategy 2: Try well-known absolute path
			candidates.Add(@"C:\lunar-horse\yokan-projects\legend-dad\project\articy");

			// Strategy 3: Walk up from plugin DLL
			try
			{
				var dllDir = Path.GetDirectoryName(GetType().Assembly.Location);
				var dir = dllDir;
				for (int i = 0; i < 10 && dir != null; i++)
				{
					candidates.Add(dir);
					dir = Path.GetDirectoryName(dir);
				}
			}
			catch { }

			// Check each candidate for the schemas/ subdirectory
			foreach (var candidate in candidates)
			{
				if (candidate != null && Directory.Exists(Path.Combine(candidate, "schemas")))
					return Path.GetFullPath(candidate);
			}

			return null;
		}
	}
}
