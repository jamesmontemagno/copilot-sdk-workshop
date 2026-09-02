using System.Text.RegularExpressions;

namespace MuseumExhibitStudio;

public sealed record TitleValidation(int TitleCount)
{
    public bool Present => TitleCount == 1;
    public bool Valid => Present;
}

public sealed record NarrativeValidation(bool Present, int WordCount)
{
    public bool WithinLimit => WordCount is >= 100 and <= 140;
    public bool Valid => Present && WithinLimit;
}

public sealed record VisitorQuestionsValidation(
    bool Present,
    int QuestionCount,
    bool AllItemsAreQuestions)
{
    public bool ExactlyThree => QuestionCount == 3;
    public bool Valid => Present && ExactlyThree && AllItemsAreQuestions;
}

public sealed record VocabularyValidation(IReadOnlyList<string> ProhibitedTerms)
{
    public bool Valid => ProhibitedTerms.Count == 0;
}

public sealed record ExhibitValidation(
    TitleValidation Title,
    NarrativeValidation Narrative,
    VisitorQuestionsValidation VisitorQuestions,
    VocabularyValidation Vocabulary,
    IReadOnlyList<string> Errors)
{
    public bool Valid => Errors.Count == 0;
}

public static partial class ExhibitValidator
{
    private static readonly string[] ProhibitedVocabulary =
    [
        "software",
        "codebase",
        "repository",
        "terminal",
        "GitHub Copilot"
    ];

    public static ExhibitValidation Validate(string content)
    {
        ArgumentNullException.ThrowIfNull(content);

        var lines = content.ReplaceLineEndings("\n").Split('\n');
        var titleCount = lines.Count(line => TitlePattern().IsMatch(line));
        var narrativeIndex = FindHeading(lines, "## Narrative");
        var questionsIndex = FindHeading(lines, "## Visitor questions");

        var narrative = narrativeIndex >= 0 && questionsIndex > narrativeIndex
            ? string.Join(' ', lines[(narrativeIndex + 1)..questionsIndex])
            : string.Empty;
        var narrativeWordCount = WordPattern().Matches(narrative).Count;

        var questions = questionsIndex >= 0
            ? lines[(questionsIndex + 1)..]
                .Select(line => QuestionPattern().Match(line))
                .Where(match => match.Success)
                .Select(match => match.Groups[1].Value.Trim())
                .ToArray()
            : [];

        var title = new TitleValidation(titleCount);
        var narrativeValidation = new NarrativeValidation(
            narrativeIndex >= 0,
            narrativeWordCount);
        var visitorQuestions = new VisitorQuestionsValidation(
            questionsIndex >= 0,
            questions.Length,
            questions.Length > 0 && questions.All(question => question.EndsWith('?')));
        var vocabulary = new VocabularyValidation(Array.AsReadOnly(
            ProhibitedVocabulary
                .Where(term => content.Contains(term, StringComparison.OrdinalIgnoreCase))
                .ToArray()));

        var errors = new List<string>();
        if (!title.Valid)
        {
            errors.Add("The exhibit must contain exactly one level-one title.");
        }
        if (!narrativeValidation.Present)
        {
            errors.Add("The exhibit must contain a Narrative section.");
        }
        if (!narrativeValidation.WithinLimit)
        {
            errors.Add($"The narrative must contain 100-140 words; found {narrativeWordCount}.");
        }
        if (!visitorQuestions.Present)
        {
            errors.Add("The exhibit must contain a Visitor questions section.");
        }
        if (!visitorQuestions.ExactlyThree)
        {
            errors.Add($"The exhibit must contain exactly three numbered questions; found {questions.Length}.");
        }
        if (!visitorQuestions.AllItemsAreQuestions)
        {
            errors.Add("Every numbered visitor item must end with a question mark.");
        }
        if (!vocabulary.Valid)
        {
            errors.Add($"The exhibit contains prohibited vocabulary: {string.Join(", ", vocabulary.ProhibitedTerms)}.");
        }

        return new ExhibitValidation(
            title,
            narrativeValidation,
            visitorQuestions,
            vocabulary,
            errors.AsReadOnly());
    }

    private static int FindHeading(string[] lines, string heading) =>
        Array.FindIndex(lines, line => line.Trim().Equals(heading, StringComparison.OrdinalIgnoreCase));

    [GeneratedRegex(@"^# [^#].*$")]
    private static partial Regex TitlePattern();

    [GeneratedRegex(@"\b[\p{L}\p{N}]+(?:['’-][\p{L}\p{N}]+)*\b")]
    private static partial Regex WordPattern();

    [GeneratedRegex(@"^\s*\d+\.\s+(.+?)\s*$")]
    private static partial Regex QuestionPattern();
}
