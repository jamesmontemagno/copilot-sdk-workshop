using System.ComponentModel;
using GitHub.Copilot;
using Microsoft.Extensions.AI;

namespace AccessibilityReport.Helpers;

public static class AccessibilityRuleCatalog
{
    private static readonly AccessibilityRule[] Rules =
    [
        new(
            "1.1.1",
            "Non-text Content",
            "An informative image has no useful text alternative.",
            "Add concise alt text that communicates the image's purpose. Use alt=\"\" only for decorative images.",
            ["image", "alt text", "text alternative"]),
        new(
            "1.3.1",
            "Info and Relationships",
            "Page structure or relationships are only conveyed visually.",
            "Use semantic landmarks and a logical heading hierarchy so structure is programmatically available.",
            ["main landmark", "heading hierarchy", "page structure", "semantic"]),
        new(
            "1.4.3",
            "Contrast (Minimum)",
            "Text does not have enough contrast against its background.",
            "Provide at least 4.5:1 contrast for normal text and 3:1 for large text.",
            ["contrast", "low contrast", "color"]),
        new(
            "2.4.7",
            "Focus Visible",
            "Keyboard focus cannot be seen clearly.",
            "Keep a visible, high-contrast focus indicator on every interactive element.",
            ["focus", "keyboard", "outline"]),
        new(
            "3.3.2",
            "Labels or Instructions",
            "A form does not provide a persistent visible label or necessary instructions.",
            "Provide visible labels and instructions that explain the expected input.",
            ["visible label", "instructions", "required field", "input format"]),
        new(
            "4.1.2",
            "Name, Role, Value",
            "A form control has no programmatically determinable accessible name.",
            "Associate a visible <label> with the input by using matching for and id values.",
            ["accessible name", "programmatic label", "unlabeled input", "name role value"])
    ];

    public static AIFunction CreateLookupTool() => CopilotTool.DefineTool(
        ([Description("The accessibility issue or WCAG criterion to look up.")] string query) =>
            Task.FromResult(Lookup(query)),
        toolOptions: new CopilotToolOptions { SkipPermission = true },
        factoryOptions: new AIFunctionFactoryOptions
        {
            Name = "accessibility_rule_lookup",
            Description = "Looks up read-only WCAG guidance maintained by this application."
        });

    public static AccessibilityRule Lookup(string query)
    {
        var normalizedQuery = query.Trim();
        return Rules.FirstOrDefault(rule =>
                   normalizedQuery.Contains(rule.Criterion, StringComparison.OrdinalIgnoreCase) ||
                   normalizedQuery.Contains(rule.Title, StringComparison.OrdinalIgnoreCase) ||
                   rule.Keywords.Any(keyword => normalizedQuery.Contains(keyword, StringComparison.OrdinalIgnoreCase)))
               ?? new AccessibilityRule(
                   "No exact match",
                   "Criterion not found",
                   "The issue is not represented in the workshop catalog.",
                   "Verify the evidence and consult the complete WCAG reference.",
                   []);
    }

    public sealed record AccessibilityRule(
        string Criterion,
        string Title,
        string WhenItApplies,
        string Recommendation,
        string[] Keywords);
}