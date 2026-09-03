# Museum Exhibit Studio — learner entrypoint.
#
# The pre-built curator helpers live in curator.py. Do not edit that file: it is the
# application-owned half of the workshop, and it must stay identical to the finished app's copy.
# Everything below is yours to write, one lesson at a time.
#
# Step 1  First curator session .......... create the CopilotClient, create a session with
#                                          on_permission_request=PermissionHandler.approve_all so
#                                          requests get an answer, send a prompt, print the reply,
#                                          then disconnect and stop.
# Step 2  Stream the curator ............. swap the blocking send for stream_exhibit() so tokens
#                                          and [tool:start] / [tool:done] events print live.
# Step 3  Curator voice .................. add `SYSTEM_MESSAGE = """..."""` here and pass it as
#                                          system_message={"mode": "replace", "content": ...}.
# Step 4  Ground it in approved facts .... add build_exhibit_prompt(); register the pre-built tool
#                                          with tools=[create_approved_fact_lookup(facts)] and
#                                          available_tools=[APPROVED_FACT_LOOKUP_NAME]; the prompt
#                                          tells the curator to call approved_fact_lookup first.
# Step 5  Set the guardrails ............. add generation_config() and the single run_session()
#                                          lifecycle function: one-tool allowlist, the Step 1
#                                          permission handler carried forward, generation timeout,
#                                          blank-output rejection, cleanup in `finally`.
#                                          Steps 6-8 reuse run_session() and add nothing to it.
# Step 6  Prove the structure ............ call format_validation(validate_exhibit(exhibit)).
# Step 7  Wikipedia research ............. add research_config() with wikipedia_server() plus
#                                          wikipedia_permission_handler(), run it through
#                                          run_session(), and print sources after the exhibit.
#                                          Research never joins the approved facts.
# Step 8  Interactive exhibit page ....... add html_config() with the "builtin:apply_patch"
#                                          allowlist and exhibit_write_permission(...).

# Your imports from `curator` go here, and grow as the lessons progress.

# Your SYSTEM_MESSAGE (Step 3) goes here.

# Your prompt builders (Steps 4, 7, 8) go here.

# Your session configuration builders (Steps 5, 7, 8) go here.

# Your run_session() lifecycle function (Step 5) goes here.


def main() -> None:
    print("=== Museum Exhibit Studio starter ===")
    print("Pre-built curator helpers are ready in curator.py.")
    print("Continue with museum step 1 to write your first curator session.")
    # Your run flow (Steps 1-8) replaces the banner above. It becomes `async def main() -> int`
    # once you create a session, and the entrypoint below becomes asyncio.run(main()).


if __name__ == "__main__":
    main()
