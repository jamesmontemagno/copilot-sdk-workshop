using System.Text;
using GitHub.Copilot;

namespace MuseumExhibitStudio.Helpers;

public static class CuratorStreamer
{
    public static readonly TimeSpan GenerationTimeout = TimeSpan.FromSeconds(120);
    public static readonly TimeSpan ResearchTimeout = TimeSpan.FromSeconds(90);

    public static async Task<string> StreamExhibitAsync(
        CopilotSession session,
        string prompt,
        TimeSpan? timeout = null,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(session);
        ArgumentNullException.ThrowIfNull(prompt);

        var response = new StringBuilder();
        var completed = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        var receivedDelta = false;
        var actualTimeout = timeout ?? GenerationTimeout;

        using var subscription = session.On<SessionEvent>(sessionEvent =>
        {
            switch (sessionEvent)
            {
                case AssistantMessageDeltaEvent delta when !string.IsNullOrEmpty(delta.Data.DeltaContent):
                    receivedDelta = true;
                    response.Append(delta.Data.DeltaContent);
                    Console.Write(delta.Data.DeltaContent);
                    break;
                case AssistantMessageEvent message when !receivedDelta && !string.IsNullOrEmpty(message.Data.Content):
                    response.Append(message.Data.Content);
                    Console.Write(message.Data.Content);
                    break;
                case ToolExecutionStartEvent tool:
                    Console.WriteLine($"\n[tool:start] {tool.Data.ToolName}");
                    break;
                case ToolExecutionCompleteEvent tool:
                    Console.WriteLine($"[tool:done] success={tool.Data.Success}");
                    break;
                case SessionIdleEvent:
                    Console.WriteLine();
                    completed.TrySetResult();
                    break;
                case SessionErrorEvent error:
                    completed.TrySetException(new InvalidOperationException(error.Data.Message));
                    break;
            }
        });

        await session.SendAsync(new MessageOptions { Prompt = prompt }, cancellationToken);
        var delayTask = Task.Delay(actualTimeout, cancellationToken);
        var finishedTask = await Task.WhenAny(completed.Task, delayTask);

        if (finishedTask == delayTask)
        {
            cancellationToken.ThrowIfCancellationRequested();
            throw new TimeoutException("The curator response reached the timeout.");
        }

        await completed.Task;
        return response.ToString();
    }
}
