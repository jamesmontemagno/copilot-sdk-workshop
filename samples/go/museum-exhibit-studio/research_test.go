package main

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"os/exec"
	"slices"
	"strings"
	"testing"
	"time"

	copilot "github.com/github/copilot-sdk/go"
	"github.com/github/copilot-sdk/go/rpc"
)

func TestResearchConfigurationKeepsGenerationToolFree(t *testing.T) {
	generation := createSessionConfiguration("")
	if generation.AvailableTools == nil || len(generation.AvailableTools) != 0 {
		t.Fatalf("generation AvailableTools = %#v", generation.AvailableTools)
	}

	research := createResearchSessionConfiguration(" test-model ")
	if research.Model != "test-model" {
		t.Errorf("research Model = %q", research.Model)
	}
	if !slices.Equal(research.AvailableTools, []string{"wikipedia-search", "wikipedia-readArticle"}) {
		t.Errorf("research AvailableTools = %v", research.AvailableTools)
	}
	server, ok := research.MCPServers["wikipedia"].(copilot.MCPStdioServerConfig)
	if !ok {
		t.Fatalf("wikipedia server = %#v", research.MCPServers["wikipedia"])
	}
	if server.Command != "npx" ||
		!slices.Equal(server.Args, []string{"-y", "wikipedia-mcp@1.0.3"}) ||
		!slices.Equal(server.Tools, []string{"search", "readArticle"}) {
		t.Errorf("wikipedia server = %#v", server)
	}
}

func TestWikipediaPermissionHandlerIsDenyByDefaultAndBounded(t *testing.T) {
	handler := newWikipediaPermissionHandler()
	approvePermission(t, handler, copilot.PermissionRequestMCP{
		ServerName: "wikipedia", ToolName: "search",
	})
	approvePermission(t, handler, copilot.PermissionRequestMCP{
		ServerName: "wikipedia", ToolName: "readArticle",
	})

	rejectPermission(t, handler, copilot.PermissionRequestMCP{
		ServerName: "wikipedia", ToolName: "search",
	})
	rejectPermission(t, handler, copilot.PermissionRequestMCP{
		ServerName: "wikipedia", ToolName: "readArticle",
	})

	orderHandler := newWikipediaPermissionHandler()
	rejectPermission(t, orderHandler, copilot.PermissionRequestMCP{
		ServerName: "wikipedia", ToolName: "readArticle",
	})
	rejectPermission(t, newWikipediaPermissionHandler(), copilot.PermissionRequestMCP{
		ServerName: "other", ToolName: "search",
	})
	rejectPermission(t, newWikipediaPermissionHandler(), copilot.PermissionRequestMCP{
		ServerName: "wikipedia", ToolName: "write",
	})
	rejectPermission(t, newWikipediaPermissionHandler(), copilot.PermissionRequestRead{})

	managed := true
	rejectPermission(t, newWikipediaPermissionHandler(), copilot.PermissionRequestMCP{
		ServerName: "wikipedia", ToolName: "search", ManagedApprovalRequired: &managed,
	})
}

func approvePermission(
	t *testing.T,
	handler copilot.PermissionHandlerFunc,
	request copilot.PermissionRequest,
) {
	t.Helper()
	decision, err := handler(request, copilot.PermissionInvocation{})
	if err != nil {
		t.Fatal(err)
	}
	if _, ok := decision.(*rpc.PermissionDecisionApproveOnce); !ok {
		t.Fatalf("%T decision = %T", request, decision)
	}
}

func rejectPermission(
	t *testing.T,
	handler copilot.PermissionHandlerFunc,
	request copilot.PermissionRequest,
) {
	t.Helper()
	decision, err := handler(request, copilot.PermissionInvocation{})
	if err != nil {
		t.Fatal(err)
	}
	if _, ok := decision.(*rpc.PermissionDecisionReject); !ok {
		t.Fatalf("%T decision = %T", request, decision)
	}
}

func TestResearchLifecycleAndResultSeparation(t *testing.T) {
	content := validResearchJSON(apollo11Facts)
	session := &fakeSession{content: content}
	client := &fakeClient{session: session}

	result := (museumExhibitService{client: client}).Research(
		context.Background(), apollo11Facts, "test-model",
	)

	if !result.Completed || result.FailureMessage != nil {
		t.Fatalf("research result = %#v", result)
	}
	if !client.startCalled || !client.stopCalled || !session.disconnectCalled {
		t.Fatalf("lifecycle start=%t stop=%t disconnect=%t",
			client.startCalled, client.stopCalled, session.disconnectCalled)
	}
	if session.deadlineRemaining <= 0 || session.deadlineRemaining > researchTimeout {
		t.Errorf("research deadline = %v", session.deadlineRemaining)
	}
	if strings.Index(session.prompt, "Call search first, then always call readArticle") < 0 ||
		!strings.Contains(session.prompt, "at most three search results") {
		t.Errorf("research prompt lacks bounded tool order: %q", session.prompt)
	}
	if len(result.Reviews) != len(apollo11Facts) || len(result.Additions) != 1 {
		t.Fatalf("reviews=%d additions=%d", len(result.Reviews), len(result.Additions))
	}
	if result.Additions[0].Approved {
		t.Fatal("model output must not preapprove an addition")
	}
	if slices.Contains(apollo11Facts, result.Additions[0].Fact) {
		t.Fatal("proposed addition entered original facts")
	}
}

func TestResearchFailuresFallBackToNotChecked(t *testing.T) {
	tests := []struct {
		name   string
		client *fakeClient
	}{
		{name: "startup", client: &fakeClient{startErr: errors.New("startup failed")}},
		{name: "timeout", client: &fakeClient{
			session: &fakeSession{sendErr: context.DeadlineExceeded},
		}},
		{name: "malformed", client: &fakeClient{session: &fakeSession{content: `{"reviews":[]}`}}},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			result := (museumExhibitService{client: test.client}).Research(
				context.Background(), apollo11Facts, "",
			)
			if result.Completed || result.FailureMessage == nil {
				t.Fatalf("result = %#v", result)
			}
			if len(result.Reviews) != len(apollo11Facts) {
				t.Fatalf("reviews = %d", len(result.Reviews))
			}
			for index, review := range result.Reviews {
				if review.Fact != apollo11Facts[index] || review.Status != factNotChecked {
					t.Errorf("review %d = %#v", index, review)
				}
			}
			if !test.client.stopCalled {
				t.Error("client Stop was not called")
			}
		})
	}
}

func TestResearchRejectsInvalidStatusAndProvenance(t *testing.T) {
	invalidStatus := strings.Replace(validResearchJSON(apollo11Facts), `"supported"`, `"maybe"`, 1)
	if _, err := parseResearchResult(invalidStatus, apollo11Facts); err == nil {
		t.Fatal("invalid status must fail")
	}
	invalidURL := strings.Replace(
		validResearchJSON(apollo11Facts),
		"https://en.wikipedia.org/wiki/Apollo_11",
		"https://example.com/Apollo_11",
		1,
	)
	if _, err := parseResearchResult(invalidURL, apollo11Facts); err == nil {
		t.Fatal("non-Wikipedia evidence URL must fail")
	}
}

func TestResearchRejectsUnboundedOrNonJSONOutput(t *testing.T) {
	valid := validResearchJSON(apollo11Facts)
	tests := []struct {
		name    string
		content string
	}{
		{name: "oversized", content: strings.Repeat("x", maximumResearchResponse+1)},
		{name: "trailing prose", content: valid + "\nDone."},
		{name: "unknown field", content: strings.TrimSuffix(valid, "}") + `,"unexpected":true}`},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			if _, err := parseResearchResult(test.content, apollo11Facts); err == nil {
				t.Fatal("invalid research output must fail")
			}
		})
	}

	var tooMany ResearchResult
	if err := json.Unmarshal([]byte(valid), &tooMany); err != nil {
		t.Fatal(err)
	}
	tooMany.Additions = append(tooMany.Additions, tooMany.Additions...)
	tooMany.Additions = append(tooMany.Additions, tooMany.Additions[0])
	content, err := json.Marshal(tooMany)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := parseResearchResult(string(content), apollo11Facts); err == nil {
		t.Fatal("too many additions must fail")
	}
}

func TestApprovalDefaultsToNoAndPreservesProvenance(t *testing.T) {
	additions := []ProposedAddition{
		{
			Fact: "Rejected fact.", SourceTitle: "Apollo 11",
			SourceURL: "https://en.wikipedia.org/wiki/Apollo_11",
		},
		{
			Fact: "Approved fact.", SourceTitle: "Apollo 11",
			SourceURL: "https://en.wikipedia.org/wiki/Apollo_11",
		},
	}
	approveAdditions(bufio.NewReader(strings.NewReader("\ny\n")), additions)
	facts := approvedResearchFacts([]string{"Original fact."}, additions)
	if !slices.Equal(facts, []string{"Original fact.", "Approved fact."}) {
		t.Fatalf("approved facts = %v", facts)
	}
	if additions[1].SourceTitle != "Apollo 11" ||
		additions[1].SourceURL != "https://en.wikipedia.org/wiki/Apollo_11" {
		t.Fatalf("approved provenance changed: %#v", additions[1])
	}
}

func TestMockWikipediaMCPToolsAndOrder(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	command := exec.CommandContext(ctx, "node", "testdata/mock-wikipedia-mcp.mjs")
	stdin, err := command.StdinPipe()
	if err != nil {
		t.Fatal(err)
	}
	stdout, err := command.StdoutPipe()
	if err != nil {
		t.Fatal(err)
	}
	if err := command.Start(); err != nil {
		t.Fatal(err)
	}
	reader := bufio.NewReader(stdout)

	callMockMCP(t, stdin, reader, 1, "tools/list", nil, func(result map[string]any) {
		tools := result["tools"].([]any)
		names := []string{
			tools[0].(map[string]any)["name"].(string),
			tools[1].(map[string]any)["name"].(string),
		}
		if !slices.Equal(names, []string{"search", "readArticle"}) {
			t.Fatalf("tools = %v", names)
		}
	})
	callMockMCP(t, stdin, reader, 2, "tools/call", map[string]any{
		"name": "search", "arguments": map[string]any{"query": "Apollo 11"},
	}, nil)
	callMockMCP(t, stdin, reader, 3, "tools/call", map[string]any{
		"name": "readArticle", "arguments": map[string]any{"title": "Apollo 11"},
	}, nil)

	if err := stdin.Close(); err != nil {
		t.Fatal(err)
	}
	if err := command.Wait(); err != nil {
		t.Fatalf("mock MCP did not stop cleanly: %v", err)
	}
}

func callMockMCP(
	t *testing.T,
	stdin interface{ Write([]byte) (int, error) },
	reader *bufio.Reader,
	id int,
	method string,
	params map[string]any,
	check func(map[string]any),
) {
	t.Helper()
	request, err := json.Marshal(map[string]any{
		"jsonrpc": "2.0", "id": id, "method": method, "params": params,
	})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := stdin.Write(append(request, '\n')); err != nil {
		t.Fatal(err)
	}
	line, err := reader.ReadBytes('\n')
	if err != nil {
		t.Fatal(err)
	}
	var response struct {
		Result map[string]any `json:"result"`
		Error  any            `json:"error"`
	}
	if err := json.Unmarshal(line, &response); err != nil {
		t.Fatal(err)
	}
	if response.Error != nil {
		t.Fatalf("%s returned error: %v", method, response.Error)
	}
	if check != nil {
		check(response.Result)
	}
}

func validResearchJSON(facts []string) string {
	reviews := make([]FactReview, len(facts))
	title := "Apollo 11"
	sourceURL := "https://en.wikipedia.org/wiki/Apollo_11"
	for index, fact := range facts {
		reviews[index] = FactReview{
			Fact:          fact,
			Status:        factSupported,
			EvidenceTitle: &title,
			EvidenceURL:   &sourceURL,
			Explanation:   "The article supports this supplied fact.",
		}
	}
	result := ResearchResult{
		Reviews: reviews,
		Additions: []ProposedAddition{{
			Fact:        "Apollo 11 was the first crewed mission to land on the Moon.",
			SourceTitle: title,
			SourceURL:   sourceURL,
		}},
		ConsultedSources: []Source{{Title: title, URL: sourceURL}},
		Completed:        true,
	}
	content, err := json.Marshal(result)
	if err != nil {
		panic(err)
	}
	return string(content)
}
