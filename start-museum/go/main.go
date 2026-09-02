package main

import "fmt"

// Museum Exhibit Studio — learner entrypoint.
//
// The pre-built curator helpers live in curator.go. Do not edit that file: it is the
// application-owned half of the workshop, and it must stay identical to the finished app's copy.
// Everything below is yours to write, one lesson at a time.
//
// Step 1  First curator session .......... create the client with copilot.NewClient, create a
//                                          session, send a prompt, print the reply, then
//                                          disconnect and stop.
// Step 2  Stream the curator ............. swap the blocking send for StreamExhibit so tokens and
//                                          [tool:start] / [tool:done] events print live.
// Step 3  Curator voice .................. add `const systemMessage = ...` here and pass it as
//                                          SystemMessage with Mode "replace".
// Step 4  Ground it in approved facts .... add buildExhibitPrompt(); register the pre-built tool
//                                          with Tools: []copilot.Tool{lookup} from
//                                          ApprovedFactLookup(facts) and AvailableTools:
//                                          []string{ApprovedFactLookupName}; the prompt tells the
//                                          curator to call approved_fact_lookup first.
// Step 5  Set the guardrails ............. add generationConfig() and the single runSession()
//                                          lifecycle function: one-tool allowlist, generation
//                                          timeout, blank-output rejection, cleanup via defer.
//                                          Steps 6-8 reuse runSession and add nothing to it.
// Step 6  Prove the structure ............ call FormatValidation(ValidateExhibit(exhibit)).
// Step 7  Wikipedia research ............. add researchConfig() with WikipediaServer() plus
//                                          WikipediaPermissionHandler(), run it through
//                                          runSession, and print sources after the exhibit.
//                                          Research never joins the approved facts.
// Step 8  Interactive exhibit page ....... add htmlConfig() with the "builtin:apply_patch"
//                                          allowlist and ExhibitWritePermission(...).

// Your system message (Step 3) goes here.

// Your prompt builders (Steps 4, 7, 8) go here.

// Your session configuration builders (Steps 5, 7, 8) go here.

// Your runSession() lifecycle function (Step 5) goes here.

func main() {
	fmt.Println("=== Museum Exhibit Studio starter ===")
	fmt.Println("Pre-built curator helpers are ready in curator.go.")
	fmt.Println("Continue with museum step 1 to write your first curator session.")
	// Your run flow (Steps 1-8) replaces the banner above. In Step 5 main() becomes a thin
	// wrapper over a run() error { ... } function so failures exit with status 1.
}
