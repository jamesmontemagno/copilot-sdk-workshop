namespace MuseumExhibitStudio.Helpers;

public sealed record CuratorFactSet(string Key, string Label, IReadOnlyList<string> Facts);

public static class CuratorFacts
{
    public const int MaximumFactCount = 20;
    public const int MaximumFactLength = 500;

    public static IReadOnlyList<string> Apollo11Facts { get; } =
    [
        "Apollo 11 launched July 16, 1969.",
        "It landed on the Moon July 20, 1969.",
        "Neil Armstrong and Buzz Aldrin walked on the Moon.",
        "Michael Collins remained in lunar orbit.",
        "The mission returned to Earth July 24, 1969."
    ];

    public static IReadOnlyList<string> GreatBarrierReefFacts { get; } =
    [
        "The Great Barrier Reef lies off the coast of Queensland, Australia.",
        "It stretches for about 2,300 kilometres.",
        "It is made up of more than 2,900 individual reefs.",
        "It was added to the UNESCO World Heritage List in 1981.",
        "Rising sea temperatures have caused repeated coral bleaching events."
    ];

    public static IReadOnlyList<string> TerracottaArmyFacts { get; } =
    [
        "The Terracotta Army was buried near the tomb of China's first emperor, Qin Shi Huang.",
        "Farmers digging a well discovered the site in 1974.",
        "The pits contain thousands of life-sized clay soldiers.",
        "Each figure was assembled from moulded parts and finished by hand.",
        "The site sits near the modern city of Xi'an in Shaanxi Province."
    ];

    public static IReadOnlyList<CuratorFactSet> FactSets { get; } =
    [
        new("apollo11", "Apollo 11", Apollo11Facts),
        new("reef", "Great Barrier Reef", GreatBarrierReefFacts),
        new("terracotta", "Terracotta Army", TerracottaArmyFacts)
    ];

    public static string[] BoundFacts(IEnumerable<string?> facts)
    {
        ArgumentNullException.ThrowIfNull(facts);

        var boundedFacts = facts
            .Select(fact => fact?.Trim())
            .Where(fact => !string.IsNullOrWhiteSpace(fact))
            .Cast<string>()
            .ToArray();

        if (boundedFacts.Length == 0)
        {
            throw new ArgumentException("Provide at least one approved fact.");
        }

        if (boundedFacts.Length > MaximumFactCount)
        {
            throw new ArgumentException("Provide no more than 20 approved facts.");
        }

        if (boundedFacts.Any(fact => fact.Length > MaximumFactLength))
        {
            throw new ArgumentException("Each approved fact must be 500 characters or fewer.");
        }

        return boundedFacts;
    }
}
