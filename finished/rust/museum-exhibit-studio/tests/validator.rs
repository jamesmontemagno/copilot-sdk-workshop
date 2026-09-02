use museum_exhibit_studio::validate_exhibit;

fn valid() -> String {
    let words = (1..=110)
        .map(|i| format!("word{i}"))
        .collect::<Vec<_>>()
        .join(" ");
    format!(
        "# A Journey\n## Narrative\n{words}\n## Visitor questions\n\
         1. What do you notice?\n2. What would you ask?\n3. What will you remember?"
    )
}

#[test]
fn valid_and_missing_narrative() {
    assert!(validate_exhibit(&valid()).is_valid());
    let result = validate_exhibit(&valid().replacen("## Narrative\n", "", 1));
    assert!(!result.narrative.present);
    assert!(!result.is_valid());
}
