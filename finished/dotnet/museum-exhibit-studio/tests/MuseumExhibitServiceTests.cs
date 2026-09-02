using GitHub.Copilot;
using MuseumExhibitStudio;

namespace MuseumExhibitStudio.Tests;

public sealed class MuseumExhibitServiceTests
{
    [Fact]
    public void CreateSessionConfigurationOwnsPromptAndHasNoTools()
    {
        var configuration = MuseumExhibitService.CreateSessionConfiguration("test-model");

        Assert.Equal("museum-exhibit-studio", configuration.ClientName);
        Assert.Equal("test-model", configuration.Model);
        Assert.Empty(configuration.AvailableTools!);
        Assert.Equal(SystemMessageMode.Replace, configuration.SystemMessage!.Mode);
        Assert.Equal(CuratorPrompts.SystemMessage, configuration.SystemMessage.Content);
    }

    [Fact]
    public async Task GenerateReturnsContentAndCleansUp()
    {
        var session = new FakeSession { Content = CreateValidExhibit() };
        await using var client = new FakeClient(session);
        var service = new MuseumExhibitService(client);

        var result = await service.GenerateAsync(CuratorPrompts.Apollo11Facts);

        Assert.True(result.Validation.Valid);
        Assert.True(result.Validation.Narrative.Valid);
        Assert.True(client.Started);
        Assert.True(client.Stopped);
        Assert.True(session.Disposed);
        Assert.NotNull(client.Configuration);
        Assert.All(CuratorPrompts.Apollo11Facts, fact => Assert.Contains(fact, session.Prompt));
        Assert.Equal(MuseumExhibitService.GenerationTimeout, session.Timeout);
    }

    [Fact]
    public async Task GenerateRejectsInvalidFactsBeforeStartingClient()
    {
        var session = new FakeSession();
        await using var client = new FakeClient(session);
        var service = new MuseumExhibitService(client);

        await Assert.ThrowsAsync<ArgumentException>(
            () => service.GenerateAsync([]));

        Assert.False(client.Started);
        Assert.False(client.Stopped);
        Assert.Null(client.Configuration);
        Assert.False(session.Disposed);
    }

    [Fact]
    public async Task GenerateRejectsEmptyResponseAndCleansUp()
    {
        var session = new FakeSession { Content = " " };
        await using var client = new FakeClient(session);
        var service = new MuseumExhibitService(client);

        await Assert.ThrowsAsync<InvalidOperationException>(
            () => service.GenerateAsync(CuratorPrompts.Apollo11Facts));

        Assert.True(client.Stopped);
        Assert.True(session.Disposed);
    }

    [Fact]
    public async Task GenerateCleansUpAfterSessionFailure()
    {
        var session = new FakeSession { Failure = new TimeoutException("Timed out.") };
        await using var client = new FakeClient(session);
        var service = new MuseumExhibitService(client);

        await Assert.ThrowsAsync<TimeoutException>(
            () => service.GenerateAsync(CuratorPrompts.Apollo11Facts));

        Assert.True(client.Stopped);
        Assert.True(session.Disposed);
    }

    private static string CreateValidExhibit()
    {
        var narrative = string.Join(' ', Enumerable.Range(1, 110).Select(index => $"word{index}"));
        return $"""
            # A Journey
            ## Narrative
            {narrative}
            ## Visitor questions
            1. What do you notice?
            2. What would you ask?
            3. What will you remember?
            """;
    }

    private sealed class FakeClient(FakeSession session) : ICuratorClient
    {
        public bool Started { get; private set; }
        public bool Stopped { get; private set; }
        public SessionConfig? Configuration { get; private set; }

        public Task StartAsync(CancellationToken cancellationToken = default)
        {
            Started = true;
            return Task.CompletedTask;
        }

        public Task<ICuratorSession> CreateSessionAsync(
            SessionConfig configuration,
            CancellationToken cancellationToken = default)
        {
            Configuration = configuration;
            return Task.FromResult<ICuratorSession>(session);
        }

        public Task StopAsync()
        {
            Stopped = true;
            return Task.CompletedTask;
        }

        public ValueTask DisposeAsync() => ValueTask.CompletedTask;
    }

    private sealed class FakeSession : ICuratorSession
    {
        public string? Content { get; init; }
        public Exception? Failure { get; init; }
        public string Prompt { get; private set; } = string.Empty;
        public TimeSpan Timeout { get; private set; }
        public bool Disposed { get; private set; }

        public Task<string?> SendAndWaitAsync(
            string prompt,
            TimeSpan timeout,
            CancellationToken cancellationToken = default)
        {
            Prompt = prompt;
            Timeout = timeout;
            return Failure is null
                ? Task.FromResult(Content)
                : Task.FromException<string?>(Failure);
        }

        public ValueTask DisposeAsync()
        {
            Disposed = true;
            return ValueTask.CompletedTask;
        }
    }
}
