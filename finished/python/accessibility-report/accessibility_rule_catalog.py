from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AccessibilityRule:
    criterion: str
    title: str
    when_it_applies: str
    recommendation: str
    keywords: tuple[str, ...]


ACCESSIBILITY_RULES: tuple[AccessibilityRule, ...] = (
    AccessibilityRule("1.1.1", "Non-text Content", "An informative image has no useful text alternative.", 'Add concise alt text that communicates the image purpose. Use alt="" only for decorative images.', ("image", "alt text", "text alternative")),
    AccessibilityRule("1.3.1", "Info and Relationships", "Page structure or relationships are only conveyed visually.", "Use semantic landmarks and a logical heading hierarchy so structure is programmatically available.", ("main landmark", "heading hierarchy", "page structure", "semantic")),
    AccessibilityRule("1.4.3", "Contrast (Minimum)", "Text does not have enough contrast against its background.", "Provide at least 4.5:1 contrast for normal text and 3:1 for large text.", ("contrast", "low contrast", "color")),
    AccessibilityRule("2.4.7", "Focus Visible", "Keyboard focus cannot be seen clearly.", "Keep a visible, high-contrast focus indicator on every interactive element.", ("focus", "keyboard", "outline")),
    AccessibilityRule("3.3.2", "Labels or Instructions", "A form does not provide a persistent visible label or necessary instructions.", "Provide visible labels and instructions that explain the expected input.", ("visible label", "instructions", "required field", "input format")),
    AccessibilityRule("4.1.2", "Name, Role, Value", "A form control has no programmatically determinable accessible name.", "Associate a visible <label> with the input by using matching for and id values.", ("accessible name", "programmatic label", "unlabeled input", "name role value")),
)
