using GitHub.Copilot;

namespace MuseumExhibitStudio;

public interface ICuratorSession : IAsyncDisposable
{
    Task<string?> SendAndWaitAsync(
        string prompt,
        TimeSpan timeout,
        CancellationToken cancellationToken = default);
}

public interface ICuratorClient : IAsyncDisposable
{
    Task StartAsync(CancellationToken cancellationToken = default);
    Task<ICuratorSession> CreateSessionAsync(
        SessionConfig configuration,
        CancellationToken cancellationToken = default);
    Task StopAsync();
}

public sealed class CopilotCuratorClient : ICuratorClient
{
    private readonly CopilotClient client = new();

    public Task StartAsync(CancellationToken cancellationToken = default) =>
        client.StartAsync(cancellationToken);

    public async Task<ICuratorSession> CreateSessionAsync(
        SessionConfig configuration,
        CancellationToken cancellationToken = default) =>
        new CopilotCuratorSession(
            await client.CreateSessionAsync(configuration, cancellationToken));

    public Task StopAsync() => client.StopAsync();

    public ValueTask DisposeAsync() => client.DisposeAsync();

    private sealed class CopilotCuratorSession(CopilotSession session) : ICuratorSession
    {
        public async Task<string?> SendAndWaitAsync(
            string prompt,
            TimeSpan timeout,
            CancellationToken cancellationToken = default)
        {
            var response = await session.SendAndWaitAsync(prompt, timeout, cancellationToken);
            return response?.Data.Content;
        }

        public ValueTask DisposeAsync() => session.DisposeAsync();
    }
}
