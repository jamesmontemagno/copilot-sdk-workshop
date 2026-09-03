// Museum Exhibit Studio — learner entrypoint.
//
// The pre-built curator helpers live in src/curator.ts. Do not edit that file: it is the
// application-owned half of the workshop, and it must stay identical to the finished app's copy.
// Everything below is yours to write, one lesson at a time.
//
// Step 1  First curator session .......... create the CopilotClient, create a session, send a
//                                          prompt, print the reply, then disconnect and stop.
// Step 2  Stream the curator ............. swap the blocking send for streamExhibit() so tokens
//                                          and [tool:start] / [tool:done] events print live.
// Step 3  Curator voice .................. add `const systemMessage = ...` here and pass it as
//                                          systemMessage: { mode: "replace", content: ... }.
// Step 4  Ground it in approved facts .... add chooseFactSet() and buildExhibitPrompt(); register
//                                          the pre-built tool with
//                                          tools: [createApprovedFactLookup(approvedFacts)] and
//                                          availableTools: [approvedFactLookupName]; the prompt
//                                          tells the curator to call approved_fact_lookup first.
// Step 5  Set the guardrails ............. add generationConfig() and the single runSession()
//                                          lifecycle function: one-tool allowlist, generation
//                                          timeout, blank-output rejection, cleanup in `finally`.
//                                          Steps 6-8 reuse runSession() and add nothing to it.
// Step 6  Prove the structure ............ call formatValidation(validateExhibit(exhibit)).
// Step 7  Wikipedia research ............. add researchConfig() with the scoped Wikipedia MCP
//                                          server plus wikipediaPermissionHandler(), run it
//                                          through runSession(), and print sources after the
//                                          exhibit. Research never joins the approved facts.
// Step 8  Interactive exhibit page ....... add htmlConfig() with the "builtin:apply_patch"
//                                          allowlist and exhibitWritePermission(process.cwd()).

// Your SDK and "./curator.js" imports go here, and grow as the lessons progress.

// Your system message (Step 3) goes here.

// Your prompt builders (Steps 4, 7, 8) go here.

// Your session configuration builders (Steps 5, 7, 8) go here.

// Your runSession() lifecycle function (Step 5) goes here.

console.log("=== Museum Exhibit Studio starter ===");
console.log("Pre-built curator helpers are ready in src/curator.ts.");
console.log("Continue with museum step 1 to write your first curator session.");

// Your main() (Steps 1-8) goes here, and the call that runs it.
