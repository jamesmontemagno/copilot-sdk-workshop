using System.Diagnostics;
using System.Text.Json;
using GitHub.Copilot;
using MuseumExhibitStudio;

namespace MuseumExhibitStudio.Tests;

public sealed class WikipediaResearchTests
{
    [Fact]
    public void ResearchConfigurationAllowsOnlyWikipediaReadTools()
    {
        var configuration = MuseumExhibitService.CreateResearchSessionConfiguration(" test-model ");

        Assert.Equal("museum-exhibit-studio-research", configuration.ClientName);
        Assert.Equal("test-model", configuration.Model);
        Assert.Equal(
            ["wikipedia-search", "wikipedia-readArticle"],
            configuration.AvailableTools);
        Assert.NotNull(configuration.OnPermissionRequest);
        var server = Assert.IsType<McpStdioServerConfig>(configuration.McpServers!["wikipedia"]);
        Assert.Equal("npx", server.Command);
        Assert.Equal(["-y", "wikipedia-mcp@1.0.3"], server.Args);
        Assert.Equal(["search", "readArticle"], server.Tools);

        Assert.Empty(MuseumExhibitService.CreateSessionConfiguration().AvailableTools!);
    }

    [Fact]
    public async Task ResearchSeparatesReviewsAndProposalsAndCleansUp()
    {
        var session = new FakeSession { Content = CreateResearchJson() };
        await using var client = new FakeClient(session);
        var service = new MuseumExhibitService(client);

        var result = await service.ResearchAsync(CuratorPrompts.Apollo11Facts);

        Assert.True(result.Completed);
        Assert.Equal(CuratorPrompts.Apollo11Facts.Count, result.Reviews.Count);
        Assert.Single(result.Additions);
        Assert.False(result.Additions[0].Approved);
        Assert.Equal("Apollo 11", result.Additions[0].SourceTitle);
        Assert.Equal("https://en.wikipedia.org/wiki/Apollo_11", result.Additions[0].SourceUrl);
        Assert.All(result.Reviews, review => Assert.True(Enum.IsDefined(review.Status)));
        Assert.Equal(MuseumExhibitService.ResearchTimeout, session.Timeout);
        Assert.True(client.Started);
        Assert.True(client.Stopped);
        Assert.True(session.Disposed);
    }

    [Fact]
    public async Task MalformedResearchDoesNotInventEvidence()
    {
        var session = new FakeSession { Content = """{"completed":true,"reviews":[],"additions":[]}""" };
        await using var client = new FakeClient(session);

        var result = await new MuseumExhibitService(client)
            .ResearchAsync(CuratorPrompts.Apollo11Facts);

        Assert.False(result.Completed);
        Assert.Empty(result.Additions);
        Assert.All(result.Reviews, review =>
        {
            Assert.Equal(FactReviewStatus.NotChecked, review.Status);
            Assert.Null(review.EvidenceTitle);
            Assert.Null(review.EvidenceUrl);
        });
        Assert.True(client.Stopped);
        Assert.True(session.Disposed);
    }

    [Fact]
    public async Task SupportedReviewWithoutEvidenceFallsBack()
    {
        var malformed = CreateResearchJson().Replace(
            "\"evidenceTitle\":\"Apollo 11\",\"evidenceUrl\":\"https://en.wikipedia.org/wiki/Apollo_11\"",
            "\"evidenceTitle\":null,\"evidenceUrl\":null");
        var session = new FakeSession { Content = malformed };
        await using var client = new FakeClient(session);

        var result = await new MuseumExhibitService(client)
            .ResearchAsync(CuratorPrompts.Apollo11Facts);

        Assert.False(result.Completed);
        Assert.All(result.Reviews, review => Assert.Equal(FactReviewStatus.NotChecked, review.Status));
    }

    [Fact]
    public async Task UndefinedNumericStatusFallsBack()
    {
        var malformed = CreateResearchJson().Replace(
            "\"status\":\"supported\"",
            "\"status\":99");
        var session = new FakeSession { Content = malformed };
        await using var client = new FakeClient(session);

        var result = await new MuseumExhibitService(client)
            .ResearchAsync(CuratorPrompts.Apollo11Facts);

        Assert.False(result.Completed);
        Assert.All(result.Reviews, review => Assert.Equal(FactReviewStatus.NotChecked, review.Status));
    }

    [Fact]
    public async Task CurrentArticleIdUrlIsAccepted()
    {
        var content = CreateResearchJson().Replace(
            "https://en.wikipedia.org/wiki/Apollo_11",
            "https://en.wikipedia.org/?curid=970");
        var session = new FakeSession { Content = content };
        await using var client = new FakeClient(session);

        var result = await new MuseumExhibitService(client)
            .ResearchAsync(CuratorPrompts.Apollo11Facts);

        Assert.True(result.Completed);
    }

    [Fact]
    public async Task TooManyAdditionsFallBack()
    {
        using var document = JsonDocument.Parse(CreateResearchJson());
        var root = document.RootElement;
        var addition = root.GetProperty("additions")[0];
        var content = JsonSerializer.Serialize(new
        {
            reviews = root.GetProperty("reviews"),
            additions = Enumerable.Repeat(addition, MuseumExhibitService.MaximumProposedAdditions + 1),
            consultedSources = root.GetProperty("consultedSources"),
            completed = true,
            failureMessage = (string?)null
        });
        var session = new FakeSession { Content = content };
        await using var client = new FakeClient(session);

        var result = await new MuseumExhibitService(client)
            .ResearchAsync(CuratorPrompts.Apollo11Facts);

        Assert.False(result.Completed);
        Assert.Empty(result.Additions);
    }

    [Fact]
    public async Task OverlongAdditionFallsBack()
    {
        var content = CreateResearchJson().Replace(
            "The mission was crewed.",
            new string('a', CuratorPrompts.MaximumFactLength + 1));
        var session = new FakeSession { Content = content };
        await using var client = new FakeClient(session);

        var result = await new MuseumExhibitService(client)
            .ResearchAsync(CuratorPrompts.Apollo11Facts);

        Assert.False(result.Completed);
        Assert.Empty(result.Additions);
    }

    [Fact]
    public void ApprovalCannotExceedGenerationFactLimit()
    {
        var originalFacts = Enumerable.Repeat("fact", CuratorPrompts.MaximumFactCount);
        var addition = new ProposedAddition(
            "Approved fact.",
            "Apollo 11",
            "https://en.wikipedia.org/wiki/Apollo_11",
            true);

        Assert.Throws<ArgumentException>(
            () => ResearchApproval.BuildApprovedFacts(originalFacts, [addition]));
    }

    [Fact]
    public async Task TimeoutFallsBackAndCleansUp()
    {
        var session = new FakeSession { Failure = new TimeoutException("fixture timeout") };
        await using var client = new FakeClient(session);

        var result = await new MuseumExhibitService(client)
            .ResearchAsync(CuratorPrompts.Apollo11Facts);

        Assert.False(result.Completed);
        Assert.Contains("timeout", result.FailureMessage, StringComparison.OrdinalIgnoreCase);
        Assert.True(client.Stopped);
        Assert.True(session.Disposed);
    }

    [Fact]
    public async Task StartupFailureFallsBackWithoutCreatingSession()
    {
        var session = new FakeSession();
        await using var client = new FakeClient(session)
        {
            StartFailure = new InvalidOperationException("fixture startup failed")
        };

        var result = await new MuseumExhibitService(client)
            .ResearchAsync(CuratorPrompts.Apollo11Facts);

        Assert.False(result.Completed);
        Assert.False(client.SessionCreated);
        Assert.True(client.Stopped);
        Assert.All(result.Reviews, review => Assert.Equal(FactReviewStatus.NotChecked, review.Status));
    }

    [Fact]
    public void OnlyExplicitlyApprovedAdditionsEnterGenerationFacts()
    {
        var rejected = new ProposedAddition(
            "Rejected fact.",
            "Apollo 11",
            "https://en.wikipedia.org/wiki/Apollo_11",
            false);
        var approved = rejected with { Fact = "Approved fact.", Approved = true };

        var facts = ResearchApproval.BuildApprovedFacts(
            CuratorPrompts.Apollo11Facts,
            [rejected, approved]);

        Assert.DoesNotContain(rejected.Fact, facts);
        Assert.Contains(approved.Fact, facts);
        Assert.Equal(
            CuratorPrompts.Apollo11Facts.Count + 1,
            facts.Count);
    }

    [Fact]
    public async Task MockMcpExposesTwoToolsAndRequiresSearchFirst()
    {
        var fixture = Path.Combine(
            AppContext.BaseDirectory,
            "Fixtures",
            "mock-wikipedia-mcp.mjs");
        using var process = Process.Start(new ProcessStartInfo
        {
            FileName = "node",
            ArgumentList = { fixture },
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false
        }) ?? throw new InvalidOperationException("Could not start mock MCP fixture.");

        try
        {
            var tools = await SendAsync(process, 1, "tools/list");
            var names = tools.RootElement.GetProperty("result").GetProperty("tools")
                .EnumerateArray()
                .Select(tool => tool.GetProperty("name").GetString()!)
                .ToArray();
            Assert.Equal(["search", "readArticle"], names);

            var earlyRead = await SendAsync(
                process,
                2,
                "tools/call",
                new { name = "readArticle", arguments = new { title = "Apollo 11" } });
            Assert.Equal(
                "search must be called before readArticle",
                earlyRead.RootElement.GetProperty("error").GetProperty("message").GetString());

            var search = await SendAsync(
                process,
                3,
                "tools/call",
                new { name = "search", arguments = new { query = "Apollo 11" } });
            Assert.True(search.RootElement.TryGetProperty("result", out _));

            var article = await SendAsync(
                process,
                4,
                "tools/call",
                new { name = "readArticle", arguments = new { title = "Apollo 11" } });
            Assert.True(article.RootElement.TryGetProperty("result", out _));
        }
        finally
        {
            process.StandardInput.Close();
            await process.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(5));
        }

        Assert.True(process.HasExited);
        Assert.Equal(0, process.ExitCode);
    }

    private static async Task<JsonDocument> SendAsync(
        Process process,
        int id,
        string method,
        object? parameters = null)
    {
        await process.StandardInput.WriteLineAsync(JsonSerializer.Serialize(new
        {
            jsonrpc = "2.0",
            id,
            method,
            @params = parameters
        }));
        await process.StandardInput.FlushAsync();
        var response = await process.StandardOutput.ReadLineAsync();
        return JsonDocument.Parse(response ?? throw new InvalidOperationException(
            await process.StandardError.ReadToEndAsync()));
    }

    private static string CreateResearchJson()
    {
        var reviews = CuratorPrompts.Apollo11Facts.Select(fact => new
        {
            fact,
            status = "supported",
            evidenceTitle = "Apollo 11",
            evidenceUrl = "https://en.wikipedia.org/wiki/Apollo_11",
            explanation = "The fixture article supports this fact."
        });
        return JsonSerializer.Serialize(new
        {
            reviews,
            additions = new[]
            {
                new
                {
                    fact = "The mission was crewed.",
                    sourceTitle = "Apollo 11",
                    sourceUrl = "https://en.wikipedia.org/wiki/Apollo_11",
                    approved = false
                }
            },
            consultedSources = new[]
            {
                new
                {
                    title = "Apollo 11",
                    url = "https://en.wikipedia.org/wiki/Apollo_11"
                }
            },
            completed = true,
            failureMessage = (string?)null
        });
    }

    private sealed class FakeClient(FakeSession session) : ICuratorClient
    {
        public Exception? StartFailure { get; init; }
        public bool Started { get; private set; }
        public bool Stopped { get; private set; }
        public bool SessionCreated { get; private set; }
        public SessionConfig? Configuration { get; private set; }

        public Task StartAsync(CancellationToken cancellationToken = default)
        {
            if (StartFailure is not null)
            {
                return Task.FromException(StartFailure);
            }
            Started = true;
            return Task.CompletedTask;
        }

        public Task<ICuratorSession> CreateSessionAsync(
            SessionConfig configuration,
            CancellationToken cancellationToken = default)
        {
            SessionCreated = true;
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
        public TimeSpan Timeout { get; private set; }
        public bool Disposed { get; private set; }

        public Task<string?> SendAndWaitAsync(
            string prompt,
            TimeSpan timeout,
            CancellationToken cancellationToken = default)
        {
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
