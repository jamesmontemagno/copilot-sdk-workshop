using System.Text.Json;
using System.Text.Json.Serialization;

namespace MuseumExhibitStudio;

[JsonConverter(typeof(JsonStringEnumConverter<FactReviewStatus>))]
public enum FactReviewStatus
{
    [JsonStringEnumMemberName("supported")]
    Supported,
    [JsonStringEnumMemberName("contradicted")]
    Contradicted,
    [JsonStringEnumMemberName("not found")]
    NotFound,
    [JsonStringEnumMemberName("not checked")]
    NotChecked
}

public sealed record FactReview(
    string Fact,
    FactReviewStatus Status,
    string? EvidenceTitle,
    string? EvidenceUrl,
    string Explanation);

public sealed record ProposedAddition(
    string Fact,
    string SourceTitle,
    string SourceUrl,
    bool Approved);

public sealed record ResearchSource(string Title, string Url);

public sealed record ResearchResult(
    IReadOnlyList<FactReview> Reviews,
    IReadOnlyList<ProposedAddition> Additions,
    IReadOnlyList<ResearchSource> ConsultedSources,
    bool Completed,
    string? FailureMessage)
{
    public static ResearchResult Incomplete(IEnumerable<string> facts, string failureMessage) => new(
        facts.Select(fact => new FactReview(
            fact,
            FactReviewStatus.NotChecked,
            null,
            null,
            "Wikipedia research was not completed.")).ToArray(),
        [],
        [],
        false,
        failureMessage);
}

public static class ResearchApproval
{
    public static IReadOnlyList<string> BuildApprovedFacts(
        IEnumerable<string> originalFacts,
        IEnumerable<ProposedAddition> additions)
    {
        ArgumentNullException.ThrowIfNull(originalFacts);
        ArgumentNullException.ThrowIfNull(additions);

        var approvedFacts = originalFacts.Concat(
            additions.Where(addition => addition.Approved).Select(addition => addition.Fact)).ToArray();
        CuratorPrompts.BuildExhibitPrompt(approvedFacts);
        return approvedFacts;
    }
}

internal static class ResearchResultParser
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
    };

    public static ResearchResult Parse(string content, IReadOnlyList<string> suppliedFacts)
    {
        var result = JsonSerializer.Deserialize<ResearchResult>(content, JsonOptions)
            ?? throw new JsonException("The research response was empty.");

        if (!result.Completed || !string.IsNullOrWhiteSpace(result.FailureMessage))
        {
            throw new JsonException("The research response did not report successful completion.");
        }

        if (result.Reviews.Count != suppliedFacts.Count ||
            result.Reviews.Select(review => review.Fact)
                .Except(suppliedFacts, StringComparer.Ordinal).Any() ||
            suppliedFacts.Except(
                result.Reviews.Select(review => review.Fact),
                StringComparer.Ordinal).Any())
        {
            throw new JsonException("Every supplied fact must have exactly one review.");
        }

        foreach (var review in result.Reviews)
        {
            if (!Enum.IsDefined(review.Status))
            {
                throw new JsonException("Every fact review must use a documented status.");
            }

            if (string.IsNullOrWhiteSpace(review.Explanation))
            {
                throw new JsonException("Every fact review must include an explanation.");
            }

            var hasEvidence = !string.IsNullOrWhiteSpace(review.EvidenceTitle) ||
                              !string.IsNullOrWhiteSpace(review.EvidenceUrl);
            var requiresEvidence = review.Status is
                FactReviewStatus.Supported or FactReviewStatus.Contradicted;
            if ((requiresEvidence || hasEvidence) &&
                (string.IsNullOrWhiteSpace(review.EvidenceTitle) ||
                 !IsCanonicalWikipediaUrl(review.EvidenceUrl)))
            {
                throw new JsonException("Review evidence must include a title and canonical Wikipedia URL.");
            }
        }

        var availableFactSlots = CuratorPrompts.MaximumFactCount - suppliedFacts.Count;
        if (result.Additions.Count > MuseumExhibitService.MaximumProposedAdditions ||
            result.Additions.Count > availableFactSlots)
        {
            throw new JsonException(
                "The proposed additions exceed the remaining approved-fact capacity.");
        }

        foreach (var addition in result.Additions)
        {
            if (string.IsNullOrWhiteSpace(addition.Fact) ||
                addition.Fact.Length > CuratorPrompts.MaximumFactLength ||
                string.IsNullOrWhiteSpace(addition.SourceTitle) ||
                !IsCanonicalWikipediaUrl(addition.SourceUrl) ||
                addition.Approved)
            {
                throw new JsonException(
                    "Every proposed addition must be unapproved and include a source title and canonical Wikipedia URL.");
            }
        }

        foreach (var source in result.ConsultedSources)
        {
            if (string.IsNullOrWhiteSpace(source.Title) || !IsCanonicalWikipediaUrl(source.Url))
            {
                throw new JsonException("Every consulted source must include a title and canonical Wikipedia URL.");
            }
        }

        return result with
        {
            Reviews = result.Reviews.ToArray(),
            Additions = result.Additions.ToArray(),
            ConsultedSources = result.ConsultedSources.ToArray()
        };
    }

    private static bool IsCanonicalWikipediaUrl(string? value) =>
        Uri.TryCreate(value, UriKind.Absolute, out var uri) &&
        uri.Scheme.Equals(Uri.UriSchemeHttps, StringComparison.OrdinalIgnoreCase) &&
        uri.Host.EndsWith(".wikipedia.org", StringComparison.OrdinalIgnoreCase) &&
        (uri.AbsolutePath.StartsWith("/wiki/", StringComparison.Ordinal) ||
         IsCurrentArticleIdUrl(uri));

    private static bool IsCurrentArticleIdUrl(Uri uri) =>
        uri.AbsolutePath.Equals("/", StringComparison.Ordinal) &&
        uri.Query.StartsWith("?curid=", StringComparison.Ordinal) &&
        int.TryParse(uri.Query.AsSpan("?curid=".Length), out var pageId) &&
        pageId > 0;
}
