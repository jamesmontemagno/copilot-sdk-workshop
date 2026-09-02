export type AccessibilityRule = {
  criterion: string;
  title: string;
  whenItApplies: string;
  recommendation: string;
  keywords: string[];
};

export const accessibilityRules: readonly AccessibilityRule[] = [
  {
    criterion: "1.1.1",
    title: "Non-text Content",
    whenItApplies: "An informative image has no useful text alternative.",
    recommendation: 'Add concise alt text that communicates the image purpose. Use alt="" only for decorative images.',
    keywords: ["image", "alt text", "text alternative"],
  },
  {
    criterion: "1.3.1",
    title: "Info and Relationships",
    whenItApplies: "Page structure or relationships are only conveyed visually.",
    recommendation: "Use semantic landmarks and a logical heading hierarchy so structure is programmatically available.",
    keywords: ["main landmark", "heading hierarchy", "page structure", "semantic"],
  },
  {
    criterion: "1.4.3",
    title: "Contrast (Minimum)",
    whenItApplies: "Text does not have enough contrast against its background.",
    recommendation: "Provide at least 4.5:1 contrast for normal text and 3:1 for large text.",
    keywords: ["contrast", "low contrast", "color"],
  },
  {
    criterion: "2.4.7",
    title: "Focus Visible",
    whenItApplies: "Keyboard focus cannot be seen clearly.",
    recommendation: "Keep a visible, high-contrast focus indicator on every interactive element.",
    keywords: ["focus", "keyboard", "outline"],
  },
  {
    criterion: "3.3.2",
    title: "Labels or Instructions",
    whenItApplies: "A form does not provide a persistent visible label or necessary instructions.",
    recommendation: "Provide visible labels and instructions that explain the expected input.",
    keywords: ["visible label", "instructions", "required field", "input format"],
  },
  {
    criterion: "4.1.2",
    title: "Name, Role, Value",
    whenItApplies: "A form control has no programmatically determinable accessible name.",
    recommendation: "Associate a visible <label> with the input by using matching for and id values.",
    keywords: ["accessible name", "programmatic label", "unlabeled input", "name role value"],
  },
];
