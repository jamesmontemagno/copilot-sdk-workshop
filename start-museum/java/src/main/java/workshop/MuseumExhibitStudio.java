package workshop;

// Museum Exhibit Studio — learner entrypoint.
//
// The pre-built curator helpers live beside this file as Curator*.java. Do not edit those files:
// they are the application-owned half of the workshop, and they must stay identical to the
// finished app's copy. Everything below is yours to write, one lesson at a time.
//
// Step 1  First curator session .......... create the CopilotClient, create a session with
//                                          .setOnPermissionRequest(PermissionHandler.APPROVE_ALL)
//                                          so requests get an answer, send a prompt, print the
//                                          reply, then close and stop.
// Step 2  Stream the curator ............. swap the blocking send for CuratorStreamer.streamExhibit
//                                          so tokens and [tool:start] / [tool:done] events print
//                                          live.
// Step 3  Curator voice .................. add `public static final String SYSTEM_MESSAGE = ...`
//                                          here and pass it through SystemMessageConfig with
//                                          SystemMessageMode.REPLACE.
// Step 4  Ground it in approved facts .... add selectFactSet() and buildExhibitPrompt(); register
//                                          the pre-built tool with
//                                          .setTools(List.of(CuratorFacts.approvedFactLookup(
//                                          facts))) and .setAvailableTools(List.of(
//                                          CuratorFacts.APPROVED_FACT_LOOKUP_NAME)); the prompt
//                                          tells the curator to call approved_fact_lookup first.
// Step 5  Set the guardrails ............. add generationConfig() and the single runSession()
//                                          lifecycle function: one-tool allowlist, the Step 1
//                                          permission handler carried forward, generation timeout,
//                                          blank-output rejection, cleanup in nested `finally`
//                                          blocks. Steps 6-8 reuse runSession and add nothing
//                                          to it.
// Step 6  Prove the structure ............ call CuratorValidation.formatValidation(
//                                              CuratorValidation.validateExhibit(exhibit)).
// Step 7  Wikipedia research ............. add researchConfig() with CuratorSafety.wikipediaServer()
//                                          plus CuratorSafety.wikipediaPermissionHandler(), run it
//                                          through runSession, and print sources after the
//                                          exhibit. Research never joins the approved facts.
// Step 8  Interactive exhibit page ....... add htmlConfig() with the "builtin:apply_patch"
//                                          allowlist and CuratorSafety.exhibitWritePermission(...).

// Your imports go here, and grow as the lessons progress.

public final class MuseumExhibitStudio {
    // Your SYSTEM_MESSAGE (Step 3) goes here.

    private MuseumExhibitStudio() {
    }

    public static void main(String[] args) {
        System.out.println("=== Museum Exhibit Studio starter ===");
        System.out.println("Pre-built curator helpers are ready in src/main/java/workshop/.");
        System.out.println("Continue with museum step 1 to write your first curator session.");
        // Your run flow (Steps 1-8) replaces the banner above. In Step 5 it gains the
        // try/catch/finally that reports a timeout, closes the terminal, and exits with status 1.
    }

    // Your prompt builders (Steps 4, 7, 8) go here.

    // Your session configuration builders (Steps 5, 7, 8) go here.

    // Your runSession() lifecycle function (Step 5) goes here.
}
