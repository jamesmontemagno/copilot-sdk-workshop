import { createInterface } from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import { apollo11Facts } from "./prompts.js";
import {
  selectApprovedFacts,
  type ProposedAddition,
  type ResearchResult,
} from "./research.js";
import { createCopilotCuratorClient, MuseumExhibitService } from "./service.js";
import type { ExhibitValidation } from "./validator.js";

const terminal = createInterface({ input, output });

try {
  console.log("=== Museum Exhibit Studio ===");
  console.log("Approved Apollo 11 facts:");
  apollo11Facts.forEach((fact, index) => console.log(`${index + 1}. ${fact}`));

  const answer = (await terminal.question("\nUse these facts? [Y/n]: ")).trim();
  const facts = answer.toLocaleLowerCase() === "n" ? await readFacts() : apollo11Facts;
  const researchAnswer = (await terminal.question("\nRun Wikipedia research? [y/N]: ")).trim();
  let research: ResearchResult | undefined;
  let approvedFacts = [...facts];
  if (researchAnswer.toLocaleLowerCase() === "y") {
    research = await new MuseumExhibitService(createCopilotCuratorClient())
      .research(facts, process.env.COPILOT_MODEL);
    printResearch(research);
    if (research.completed) {
      for (const addition of research.additions) {
        const approval = (await terminal.question(
          `Approve addition "${addition.fact}"? [y/N]: `,
        )).trim();
        addition.approved = approval.toLocaleLowerCase() === "y";
      }
      approvedFacts = selectApprovedFacts([...facts], research.additions);
    } else {
      console.log(
        "Wikipedia research was not completed. Generating from the original approved facts only.",
      );
      if (research.failureMessage) console.log(`Research error: ${research.failureMessage}`);
    }
  }

  const result = await new MuseumExhibitService(createCopilotCuratorClient())
    .generate(approvedFacts, process.env.COPILOT_MODEL);

  console.log(`\n${result.content}\n`);
  printValidation(result.validation);
  if (research?.completed && research.consultedSources.length > 0) {
    console.log("\nConsulted Wikipedia sources:");
    research.consultedSources.forEach((source) =>
      console.log(`- ${source.title}: ${source.url}`));
  }
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message.toLocaleLowerCase().includes("timeout")
    ? "The curator did not respond within two minutes. Try again."
    : `Could not generate the exhibit: ${message}`);
  process.exitCode = 1;
} finally {
  terminal.close();
}

function printResearch(research: ResearchResult): void {
  console.log("\nWikipedia fact review:");
  research.reviews.forEach((review) => {
    console.log(`- [${review.status}] ${review.fact}`);
    console.log(`  ${review.explanation}`);
    if (review.evidenceTitle && review.evidenceUrl) {
      console.log(`  Source: ${review.evidenceTitle}: ${review.evidenceUrl}`);
    }
  });
  if (research.additions.length > 0) {
    console.log("\nProposed additions:");
    research.additions.forEach(printAddition);
  }
}

function printAddition(addition: ProposedAddition): void {
  console.log(`- ${addition.fact}`);
  console.log(`  Source: ${addition.sourceTitle}: ${addition.sourceUrl}`);
}

async function readFacts(): Promise<string[]> {
  console.log("Enter one approved fact per line. Submit a blank line when finished:");
  const facts: string[] = [];
  while (true) {
    const fact = (await terminal.question("")).trim();
    if (!fact) return facts;
    facts.push(fact);
  }
}

function printValidation(validation: ExhibitValidation): void {
  console.log(validation.valid ? "Structural checks passed." : "Structural checks found issues:");
  console.log(`- One level-one title: ${validation.title.present}`);
  console.log(`- Narrative section: ${validation.narrative.present}`);
  console.log(`- Narrative length: ${validation.narrative.wordCount} words (within 100-140: ${validation.narrative.withinLimit})`);
  console.log(`- Visitor questions section: ${validation.visitorQuestions.present}`);
  console.log(`- Numbered questions: ${validation.visitorQuestions.questionCount} (exactly three: ${validation.visitorQuestions.exactlyThree})`);
  console.log(`- Every item is a question: ${validation.visitorQuestions.allItemsAreQuestions}`);
  validation.errors.forEach((error) => console.log(`  - ${error}`));
  console.log("\nStructural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator.");
}
