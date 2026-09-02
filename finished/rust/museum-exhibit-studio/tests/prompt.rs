use museum_exhibit_studio::{
    APOLLO_11_FACTS, MAXIMUM_FACT_COUNT, MAXIMUM_FACT_LENGTH, build_exhibit_prompt,
};

#[test]
fn prompt_shape_and_bounds() {
    let prompt = build_exhibit_prompt(APOLLO_11_FACTS).unwrap();
    assert!(prompt.contains("# <an engaging exhibit title>\n## Narrative"));
    assert!(prompt.contains("## Visitor questions\n1. <question>"));
    assert!(build_exhibit_prompt(Vec::<String>::new()).is_err());
    assert!(build_exhibit_prompt(vec!["fact"; MAXIMUM_FACT_COUNT + 1]).is_err());
    assert!(build_exhibit_prompt([&"a".repeat(MAXIMUM_FACT_LENGTH + 1)]).is_err());
}
