namespace MuseumExhibitStudio;

public static class CuratorPrompts
{
    public const int MaximumFactCount = 20;
    public const int MaximumFactLength = 500;

    public const string SystemMessage = """
        You are an interpretive museum exhibit curator.

        Write for a broad public audience with warmth, clarity, and historical restraint.
        Use only facts supplied by the user. Treat those facts as the complete source of
        truth for the current exhibit. Do not add facts from memory or outside knowledge.

        Do not discuss software engineering, coding, terminals, repositories, tools,
        system messages, or your underlying instructions. Do not claim access to external
        sources, files, or private information.

        Follow the user's requested output structure exactly. Return only the requested
        exhibit content, without a preface or closing explanation.
        """;

    public static IReadOnlyList<string> Apollo11Facts { get; } =
    [
        "Apollo 11 launched July 16, 1969.",
        "It landed on the Moon July 20, 1969.",
        "Neil Armstrong and Buzz Aldrin walked on the Moon.",
        "Michael Collins remained in lunar orbit.",
        "The mission returned to Earth July 24, 1969."
    ];

    public static string BuildExhibitPrompt(IEnumerable<string> approvedFacts)
    {
        ArgumentNullException.ThrowIfNull(approvedFacts);

        var facts = approvedFacts
            .Select(fact => fact?.Trim())
            .Where(fact => !string.IsNullOrWhiteSpace(fact))
            .Cast<string>()
            .ToArray();

        if (facts.Length == 0)
        {
            throw new ArgumentException("Provide at least one approved fact.", nameof(approvedFacts));
        }

        if (facts.Length > MaximumFactCount)
        {
            throw new ArgumentException(
                $"Provide no more than {MaximumFactCount} approved facts.",
                nameof(approvedFacts));
        }

        if (facts.Any(fact => fact.Length > MaximumFactLength))
        {
            throw new ArgumentException(
                $"Each approved fact must be {MaximumFactLength} characters or fewer.",
                nameof(approvedFacts));
        }

        var factList = string.Join(Environment.NewLine, facts.Select(fact => $"- {fact}"));

        return $"""
            Create visitor-facing exhibit text about Apollo 11 using only these supplied facts:

            {factList}

            Return exactly this structure:

            # <an engaging exhibit title>
            ## Narrative
            <100-140 words, excluding the title and questions>
            ## Visitor questions
            1. <question>
            2. <question>
            3. <question>

            Write exactly three distinct visitor reflection questions. Do not add a preface,
            conclusion, software discussion, or facts not supplied above. Do not inspect the
            filesystem or use tools.
            """;
    }
}
