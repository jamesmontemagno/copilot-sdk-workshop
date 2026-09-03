using GitHub.Copilot;
using Microsoft.Extensions.AI;

namespace AccessibilityReport.Helpers;

public static class PlaywrightSnapshotReader
{
    private const long MaxSnapshotBytes = 1_000_000;
    private static readonly StringComparer PathComparer =
        OperatingSystem.IsWindows() ? StringComparer.OrdinalIgnoreCase : StringComparer.Ordinal;

    public static AIFunction CreateTool(string workingDirectory)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(workingDirectory);

        var outputDirectory = Path.GetFullPath(Path.Combine(workingDirectory, ".playwright-mcp"));
        var existingSnapshots = Directory.Exists(outputDirectory)
            ? Directory.EnumerateFiles(outputDirectory, "page-*.yml", SearchOption.TopDirectoryOnly)
                .Select(Path.GetFullPath)
                .ToHashSet(PathComparer)
            : new HashSet<string>(PathComparer);

        return CopilotTool.DefineTool(
            () => Task.FromResult(ReadLatestSnapshot(outputDirectory, existingSnapshots)),
            toolOptions: new CopilotToolOptions { SkipPermission = true },
            factoryOptions: new AIFunctionFactoryOptions
            {
                Name = "read_latest_accessibility_snapshot",
                Description = "Reads the newest Playwright accessibility snapshot created during this run."
            });
    }

    private static string ReadLatestSnapshot(
        string outputDirectory,
        IReadOnlySet<string> existingSnapshots)
    {
        if (!Directory.Exists(outputDirectory))
        {
            throw new FileNotFoundException(
                "No Playwright snapshot is available. Call browser_navigate first.");
        }

        var snapshot = Directory
            .EnumerateFiles(outputDirectory, "page-*.yml", SearchOption.TopDirectoryOnly)
            .Select(path => new FileInfo(Path.GetFullPath(path)))
            .Where(file =>
                !existingSnapshots.Contains(file.FullName) &&
                (file.Attributes & FileAttributes.ReparsePoint) == 0 &&
                file.Length is > 0 and <= MaxSnapshotBytes)
            .OrderByDescending(file => file.LastWriteTimeUtc)
            .FirstOrDefault()
            ?? throw new FileNotFoundException(
                "No current-run Playwright snapshot is available. Call browser_navigate first.");

        return File.ReadAllText(snapshot.FullName);
    }
}
