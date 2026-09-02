using MuseumExhibitStudio;

namespace MuseumExhibitStudio.Tests;

public sealed class CuratorPromptsTests
{
    [Fact]
    public void BuildExhibitPromptIncludesFactsAndExactStructure()
    {
        var prompt = CuratorPrompts.BuildExhibitPrompt(CuratorPrompts.Apollo11Facts);

        Assert.All(CuratorPrompts.Apollo11Facts, fact => Assert.Contains(fact, prompt));
        Assert.Contains("# <an engaging exhibit title>", prompt);
        Assert.Contains("## Narrative", prompt);
        Assert.Contains("## Visitor questions", prompt);
        Assert.DoesNotContain(CuratorPrompts.Apollo11Facts[0], CuratorPrompts.SystemMessage);
    }

    [Fact]
    public void BuildExhibitPromptRejectsEmptyFacts()
    {
        var exception = Assert.Throws<ArgumentException>(
            () => CuratorPrompts.BuildExhibitPrompt([]));

        Assert.Contains("at least one approved fact", exception.Message);
    }

    [Fact]
    public void BuildExhibitPromptBoundsFactInput()
    {
        Assert.Throws<ArgumentException>(
            () => CuratorPrompts.BuildExhibitPrompt(
                Enumerable.Repeat("Approved fact.", CuratorPrompts.MaximumFactCount + 1)));
        Assert.Throws<ArgumentException>(
            () => CuratorPrompts.BuildExhibitPrompt(
                [new string('a', CuratorPrompts.MaximumFactLength + 1)]));
    }
}
