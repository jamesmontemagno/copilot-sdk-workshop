namespace MuseumExhibitStudio.Helpers;

public static class CuratorTerminal
{
    public static string AskLine(string question)
    {
        ArgumentNullException.ThrowIfNull(question);

        Console.Write(question);
        return Console.ReadLine()?.Trim() ?? string.Empty;
    }

    public static bool AskYesNo(string question, bool defaultYes)
    {
        ArgumentNullException.ThrowIfNull(question);

        var answer = AskLine($"{question} {(defaultYes ? "[Y/n]" : "[y/N]")}: ");

        if (string.IsNullOrWhiteSpace(answer))
        {
            return defaultYes;
        }

        if (answer.Equals("y", StringComparison.OrdinalIgnoreCase) ||
            answer.Equals("yes", StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        if (answer.Equals("n", StringComparison.OrdinalIgnoreCase) ||
            answer.Equals("no", StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        return defaultYes;
    }

    public static string[] ReadFacts()
    {
        Console.WriteLine("Enter one approved fact per line. Submit a blank line when finished:");
        var facts = new List<string>();

        while (true)
        {
            var fact = AskLine(string.Empty);
            if (string.IsNullOrWhiteSpace(fact))
            {
                return facts.ToArray();
            }

            facts.Add(fact);
        }
    }

    public static void CloseTerminal()
    {
    }
}
