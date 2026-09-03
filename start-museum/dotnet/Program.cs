// Museum Exhibit Studio — learner entrypoint.
//
// The pre-built curator helpers live in Helpers/. Do not edit those files: they are the
// application-owned half of the workshop, and they must stay identical to the finished app's copy.
// Everything below is yours to write, one lesson at a time.
//
// Step 1  First curator session .......... create the CopilotClient, create a session with
//                                          OnPermissionRequest = PermissionHandler.ApproveAll so
//                                          requests get an answer, send a prompt, print the reply,
//                                          then dispose and stop.
// Step 2  Stream the curator ............. swap the blocking send for
//                                          CuratorStreamer.StreamExhibitAsync so tokens and
//                                          [tool:start] / [tool:done] events print live.
// Step 3  Curator voice .................. add `const string SystemMessage = ...` here and pass it
//                                          as SystemMessage with SystemMessageMode.Replace.
// Step 4  Ground it in approved facts .... add ReadFactSetSelection() and BuildExhibitPrompt();
//                                          register the pre-built tool with
//                                          Tools = [CuratorFacts.CreateApprovedFactLookup(facts)]
//                                          and AvailableTools =
//                                          [CuratorFacts.ApprovedFactLookupName]; the prompt tells
//                                          the curator to call approved_fact_lookup first.
// Step 5  Set the guardrails ............. add GenerationConfig() and the single RunSessionAsync()
//                                          lifecycle function: one-tool allowlist, the Step 1
//                                          permission handler carried forward, generation timeout,
//                                          blank-output rejection, cleanup in `finally`.
//                                          Steps 6-8 reuse RunSessionAsync and add nothing to it.
// Step 6  Prove the structure ............ call
//                                          CuratorValidation.FormatValidation(
//                                              CuratorValidation.ValidateExhibit(exhibit)).
// Step 7  Wikipedia research ............. add ResearchConfig() with CuratorSafety.WikipediaServer()
//                                          plus CuratorSafety.WikipediaPermissionHandler(), run it
//                                          through RunSessionAsync, and print sources after the
//                                          exhibit. Research never joins the approved facts.
// Step 8  Interactive exhibit page ....... add HtmlConfig() with the "builtin:apply_patch"
//                                          allowlist and CuratorSafety.ExhibitWritePermission(...).

// Your `using` directives go here, and grow as the lessons progress.

// Your system message (Step 3) goes here.

Console.WriteLine("=== Museum Exhibit Studio starter ===");
Console.WriteLine("Pre-built curator helpers are ready in Helpers/.");
Console.WriteLine("Continue with museum step 1 to write your first curator session.");

// Your top-level run flow (Steps 1-8) replaces the banner above, wrapped in try/catch/finally.

// Local functions come after the top-level statements. Your prompt builders (Steps 4, 7, 8),
// session configuration builders (Steps 5, 7, 8), and RunSessionAsync (Step 5) go here.
