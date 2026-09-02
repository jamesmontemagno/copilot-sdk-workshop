use std::io::{self, Write};

use museum_exhibit_studio::{
    APOLLO_11_FACTS, CopilotCuratorClient, ExhibitValidation, ResearchResult, RuntimeError,
    approved_facts_with_additions, build_exhibit_prompt, generate_exhibit, is_timeout_error,
    research_wikipedia,
};

fn read_facts() -> io::Result<Vec<String>> {
    println!("Enter one approved fact per line. Submit a blank line when finished:");
    let mut facts = Vec::new();
    loop {
        let mut fact = String::new();
        io::stdin().read_line(&mut fact)?;
        let fact = fact.trim();
        if fact.is_empty() {
            return Ok(facts);
        }
        facts.push(fact.to_owned());
    }
}

fn print_validation(validation: &ExhibitValidation) {
    println!(
        "{}",
        if validation.is_valid() {
            "Structural checks passed."
        } else {
            "Structural checks found issues:"
        }
    );
    println!("- One level-one title: {}", validation.title.is_present());
    println!("- Narrative section: {}", validation.narrative.present);
    println!(
        "- Narrative length: {} words (within 100-140: {})",
        validation.narrative.word_count,
        validation.narrative.is_within_limit()
    );
    println!(
        "- Visitor questions section: {}",
        validation.visitor_questions.present
    );
    println!(
        "- Numbered questions: {} (exactly three: {})",
        validation.visitor_questions.question_count,
        validation.visitor_questions.has_exactly_three()
    );
    println!(
        "- Every item is a question: {}",
        validation.visitor_questions.all_items_are_questions
    );
    for error in &validation.errors {
        println!("  - {error}");
    }
    println!(
        "\nStructural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator."
    );
}

fn read_default_no(prompt: &str) -> io::Result<bool> {
    print!("{prompt} [y/N]: ");
    io::stdout().flush()?;
    let mut answer = String::new();
    io::stdin().read_line(&mut answer)?;
    Ok(answer.trim().eq_ignore_ascii_case("y"))
}

fn review_research(research: &mut ResearchResult, original_fact_count: usize) -> io::Result<()> {
    println!("\nWikipedia fact review:");
    for review in &research.reviews {
        println!("- {}: {}", review.status, review.fact);
        if let (Some(title), Some(url)) = (&review.evidence_title, &review.evidence_url) {
            println!("  Evidence: {title} ({url})");
        }
        println!("  {}", review.explanation);
    }

    let mut remaining_slots =
        museum_exhibit_studio::MAXIMUM_FACT_COUNT.saturating_sub(original_fact_count);
    for addition in &mut research.additions {
        println!("\nProposed addition: {}", addition.fact);
        println!(
            "Source: {} ({})",
            addition.source_title, addition.source_url
        );
        if remaining_slots == 0 {
            println!("Not eligible for approval: the 20-fact generation limit is already reached.");
            continue;
        }
        addition.approved = read_default_no("Approve this addition?")?;
        if addition.approved {
            remaining_slots -= 1;
        }
    }
    Ok(())
}

fn print_sources(research: &ResearchResult) {
    if research.consulted_sources.is_empty() {
        return;
    }
    println!("\nConsulted Wikipedia sources:");
    for source in &research.consulted_sources {
        println!("- {}: {}", source.title, source.url);
    }
}

#[tokio::main]
async fn main() {
    if let Err(error) = run().await {
        if is_timeout_error(error.as_ref()) {
            eprintln!("The curator did not respond within two minutes. Try again.");
        } else {
            eprintln!("Could not generate the exhibit: {error}");
        }
        std::process::exit(1);
    }
}

async fn run() -> Result<(), RuntimeError> {
    println!("=== Museum Exhibit Studio ===");
    println!("Approved Apollo 11 facts:");
    for (index, fact) in APOLLO_11_FACTS.iter().enumerate() {
        println!("{}. {fact}", index + 1);
    }

    print!("\nUse these facts? [Y/n]: ");
    io::stdout().flush()?;
    let mut choice = String::new();
    io::stdin().read_line(&mut choice)?;
    let facts = if choice.trim().eq_ignore_ascii_case("n") {
        read_facts()?
    } else {
        APOLLO_11_FACTS.map(str::to_owned).to_vec()
    };
    build_exhibit_prompt(&facts)?;

    let model = std::env::var("COPILOT_MODEL").ok();
    let mut research = None;
    if read_default_no("\nRun Wikipedia research?")? {
        let mut research_client = CopilotCuratorClient::new();
        let mut result = research_wikipedia(&mut research_client, &facts, model.as_deref()).await;
        if result.completed {
            review_research(&mut result, facts.len())?;
        } else {
            println!(
                "\nWikipedia research was not completed. Generating from the original approved facts only."
            );
            if let Some(message) = &result.failure_message {
                eprintln!("{message}");
            }
        }
        research = Some(result);
    }

    let approved_facts = match &research {
        Some(result) => approved_facts_with_additions(&facts, &result.additions)?,
        None => facts.clone(),
    };
    let mut generation_client = CopilotCuratorClient::new();
    let result =
        generate_exhibit(&mut generation_client, &approved_facts, model.as_deref()).await?;
    println!("\n{}\n", result.content);
    print_validation(&result.validation);
    if let Some(research) = &research {
        print_sources(research);
    }
    Ok(())
}
