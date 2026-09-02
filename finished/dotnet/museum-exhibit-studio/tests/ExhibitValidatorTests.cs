using MuseumExhibitStudio;

namespace MuseumExhibitStudio.Tests;

public sealed class ExhibitValidatorTests
{
    [Fact]
    public void ValidateAcceptsACompleteExhibit()
    {
        var validation = ExhibitValidator.Validate(CreateExhibit(110, 3));

        Assert.True(validation.Valid);
        Assert.Equal(110, validation.Narrative.WordCount);
        Assert.Equal(3, validation.VisitorQuestions.QuestionCount);
    }

    [Fact]
    public void ValidateRejectsMissingTitle()
    {
        var validation = ExhibitValidator.Validate(
            CreateExhibit(110, 3).Replace("# A Journey\n", string.Empty));

        Assert.False(validation.Title.Present);
        Assert.False(validation.Valid);
    }

    [Fact]
    public void ValidateRejectsMissingNarrative()
    {
        var validation = ExhibitValidator.Validate(
            CreateExhibit(110, 3).Replace("## Narrative\n", string.Empty));

        Assert.False(validation.Narrative.Present);
        Assert.False(validation.Valid);
    }

    [Theory]
    [InlineData(99)]
    [InlineData(141)]
    public void ValidateRejectsNarrativeOutsideLimit(int wordCount)
    {
        var validation = ExhibitValidator.Validate(CreateExhibit(wordCount, 3));

        Assert.False(validation.Narrative.WithinLimit);
        Assert.False(validation.Valid);
    }

    [Theory]
    [InlineData(2)]
    [InlineData(4)]
    public void ValidateRejectsWrongQuestionCount(int questionCount)
    {
        var validation = ExhibitValidator.Validate(CreateExhibit(110, questionCount));

        Assert.False(validation.VisitorQuestions.ExactlyThree);
        Assert.False(validation.Valid);
    }

    [Fact]
    public void ValidateRejectsItemsThatAreNotQuestions()
    {
        var validation = ExhibitValidator.Validate(
            CreateExhibit(110, 3).Replace("3. Reflection question?", "3. Reflection prompt."));

        Assert.False(validation.VisitorQuestions.AllItemsAreQuestions);
        Assert.False(validation.Valid);
    }

    [Fact]
    public void ValidateReportsProhibitedVocabulary()
    {
        var validation = ExhibitValidator.Validate(
            CreateExhibit(110, 3).Replace("word1", "software"));

        Assert.Contains("software", validation.Vocabulary.ProhibitedTerms);
        Assert.False(validation.Valid);
    }

    private static string CreateExhibit(int narrativeWordCount, int questionCount)
    {
        var narrative = string.Join(' ', Enumerable.Range(1, narrativeWordCount).Select(index => $"word{index}"));
        var questions = string.Join(
            '\n',
            Enumerable.Range(1, questionCount).Select(index => $"{index}. Reflection question?"));

        return $"""
            # A Journey
            ## Narrative
            {narrative}
            ## Visitor questions
            {questions}
            """;
    }
}
