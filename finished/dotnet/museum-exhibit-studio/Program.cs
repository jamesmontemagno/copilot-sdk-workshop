using MuseumExhibitStudio;

Console.WriteLine("=== Museum Exhibit Studio ===");
Console.WriteLine("Approved Apollo 11 facts:");

for (var index = 0; index < CuratorPrompts.Apollo11Facts.Count; index++)
{
    Console.WriteLine($"{index + 1}. {CuratorPrompts.Apollo11Facts[index]}");
}

Console.Write("\nUse these facts? [Y/n]: ");
var useDefaults = Console.ReadLine()?.Trim();
var facts = useDefaults?.Equals("n", StringComparison.OrdinalIgnoreCase) == true
    ? ReadFacts()
    : CuratorPrompts.Apollo11Facts;

await using var client = new CopilotCuratorClient();
var studio = new MuseumExhibitService(client);
ResearchResult? research = null;

Console.Write("Run Wikipedia research? [y/N]: ");
if (Console.ReadLine()?.Trim().Equals("y", StringComparison.OrdinalIgnoreCase) == true)
{
    research = await studio.ResearchAsync(facts, Environment.GetEnvironmentVariable("COPILOT_MODEL"));
    PrintResearch(research);

    if (research.Completed)
    {
        var additions = research.Additions.ToArray();
        for (var index = 0; index < additions.Length; index++)
        {
            var addition = additions[index];
            Console.Write($"Approve addition {index + 1}? [y/N]: ");
            if (Console.ReadLine()?.Trim().Equals("y", StringComparison.OrdinalIgnoreCase) == true)
            {
                additions[index] = addition with { Approved = true };
            }
        }
        research = research with { Additions = additions };
    }
    else
    {
        Console.WriteLine(
            "Wikipedia research was not completed. " +
            "Generating from the original approved facts only.");
    }
}

try
{
    var approvedFacts = ResearchApproval.BuildApprovedFacts(
        facts,
        research?.Additions ?? []);
    var result = await studio.GenerateAsync(
        approvedFacts,
        Environment.GetEnvironmentVariable("COPILOT_MODEL"));
    Console.WriteLine($"\n{result.Content}\n");
    PrintValidation(result.Validation);
    PrintSources(research);
    return 0;
}
catch (TimeoutException)
{
    Console.Error.WriteLine("The curator did not respond within two minutes. Try again.");
    return 1;
}
catch (Exception exception)
{
    Console.Error.WriteLine($"Could not generate the exhibit: {exception.Message}");
    return 1;
}

static IReadOnlyList<string> ReadFacts()
{
    Console.WriteLine("Enter one approved fact per line. Submit a blank line when finished:");
    var facts = new List<string>();

    while (true)
    {
        var fact = Console.ReadLine();
        if (string.IsNullOrWhiteSpace(fact))
        {
            return facts;
        }

        facts.Add(fact.Trim());
    }
}

static void PrintResearch(ResearchResult research)
{
    Console.WriteLine("\nWikipedia fact review:");
    foreach (var review in research.Reviews)
    {
        Console.WriteLine($"- [{FormatStatus(review.Status)}] {review.Fact}");
        Console.WriteLine($"  {review.Explanation}");
        if (review.EvidenceTitle is not null && review.EvidenceUrl is not null)
        {
            Console.WriteLine($"  Evidence: {review.EvidenceTitle} - {review.EvidenceUrl}");
        }
    }

    if (research.Additions.Count > 0)
    {
        Console.WriteLine("\nProposed additions:");
        for (var index = 0; index < research.Additions.Count; index++)
        {
            var addition = research.Additions[index];
            Console.WriteLine($"{index + 1}. {addition.Fact}");
            Console.WriteLine($"   Source: {addition.SourceTitle} - {addition.SourceUrl}");
        }
    }

    if (!research.Completed && !string.IsNullOrWhiteSpace(research.FailureMessage))
    {
        Console.WriteLine($"Research detail: {research.FailureMessage}");
    }
}

static string FormatStatus(FactReviewStatus status) => status switch
{
    FactReviewStatus.Supported => "supported",
    FactReviewStatus.Contradicted => "contradicted",
    FactReviewStatus.NotFound => "not found",
    FactReviewStatus.NotChecked => "not checked",
    _ => throw new ArgumentOutOfRangeException(nameof(status))
};

static void PrintSources(ResearchResult? research)
{
    if (research is not { Completed: true, ConsultedSources.Count: > 0 })
    {
        return;
    }

    Console.WriteLine("\nConsulted Wikipedia sources:");
    foreach (var source in research.ConsultedSources)
    {
        Console.WriteLine($"- {source.Title}: {source.Url}");
    }
}

static void PrintValidation(ExhibitValidation validation)
{
    Console.WriteLine(validation.Valid
        ? "Structural checks passed."
        : "Structural checks found issues:");

    Console.WriteLine($"- One level-one title: {validation.Title.Present}");
    Console.WriteLine($"- Narrative section: {validation.Narrative.Present}");
    Console.WriteLine(
        $"- Narrative length: {validation.Narrative.WordCount} words " +
        $"(within 100-140: {validation.Narrative.WithinLimit})");
    Console.WriteLine($"- Visitor questions section: {validation.VisitorQuestions.Present}");
    Console.WriteLine(
        $"- Numbered questions: {validation.VisitorQuestions.QuestionCount} " +
        $"(exactly three: {validation.VisitorQuestions.ExactlyThree})");
    Console.WriteLine($"- Every item is a question: {validation.VisitorQuestions.AllItemsAreQuestions}");

    foreach (var error in validation.Errors)
    {
        Console.WriteLine($"  - {error}");
    }

    Console.WriteLine(
        "\nStructural checks do not prove factual grounding. " +
        "Unsupported claims require human review or a separate evaluator.");
}
