using GitHub.Copilot;
using HelloCopilotSDK.Helpers;

Console.WriteLine("=== Copilot accessibility guidance ===\n");

await using var client = new CopilotClient();
await client.StartAsync();

var ping = await client.PingAsync("workshop");
Console.WriteLine($"Connected to the Copilot runtime: {ping.Message}\n");

await using var session = await client.CreateSessionAsync(new SessionConfig
{
    Streaming = true,
    Tools = [AccessibilityRuleCatalog.CreateLookupTool()],
    AvailableTools = ["accessibility_rule_lookup"]
});

Console.Write("Accessibility question: ");
var question = Console.ReadLine();
if (string.IsNullOrWhiteSpace(question))
{
    Console.Error.WriteLine("Enter a question to continue.");
    return;
}

Console.WriteLine("\nCopilot:");
await ResponseStreamer.SendAndPrintAsync(
    session,
    $"Use accessibility_rule_lookup to answer this question: {question}");
