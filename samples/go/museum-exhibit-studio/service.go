package main

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"time"

	copilot "github.com/github/copilot-sdk/go"
	"github.com/github/copilot-sdk/go/rpc"
)

const generationTimeout = 120 * time.Second

type curatorSession interface {
	SendAndWait(context.Context, string) (string, error)
	Disconnect() error
}

type curatorClient interface {
	Start(context.Context) error
	CreateSession(context.Context, *copilot.SessionConfig) (curatorSession, error)
	Stop() error
}

type generatedExhibit struct {
	Content    string
	Validation ExhibitValidation
}

type museumExhibitService struct {
	client curatorClient
}

func createSessionConfiguration(model string) *copilot.SessionConfig {
	return &copilot.SessionConfig{
		ClientName:     "museum-exhibit-studio",
		Model:          strings.TrimSpace(model),
		AvailableTools: []string{},
		Streaming:      copilot.Bool(false),
		SystemMessage: &copilot.SystemMessageConfig{
			Mode:    "replace",
			Content: curatorSystemMessage,
		},
	}
}

func createResearchSessionConfiguration(model string) *copilot.SessionConfig {
	return &copilot.SessionConfig{
		ClientName: "museum-exhibit-studio-research",
		Model:      strings.TrimSpace(model),
		Streaming:  copilot.Bool(false),
		SystemMessage: &copilot.SystemMessageConfig{
			Mode:    "replace",
			Content: researchSystemMessage,
		},
		AvailableTools:      []string{"wikipedia-search", "wikipedia-readArticle"},
		OnPermissionRequest: newWikipediaPermissionHandler(),
		MCPServers: map[string]copilot.MCPServerConfig{
			"wikipedia": copilot.MCPStdioServerConfig{
				Command:          "npx",
				Args:             []string{"-y", "wikipedia-mcp@1.0.3"},
				WorkingDirectory: ".",
				Tools:            []string{"search", "readArticle"},
			},
		},
	}
}

func newWikipediaPermissionHandler() copilot.PermissionHandlerFunc {
	var searchCalls int
	var articleCalls int
	return func(
		request copilot.PermissionRequest,
		_ copilot.PermissionInvocation,
	) (rpc.PermissionDecision, error) {
		var mcpRequest copilot.PermissionRequestMCP
		switch value := request.(type) {
		case copilot.PermissionRequestMCP:
			mcpRequest = value
		case *copilot.PermissionRequestMCP:
			mcpRequest = *value
		default:
			return rejectWikipediaPermission(), nil
		}
		if mcpRequest.ServerName != "wikipedia" ||
			(mcpRequest.ManagedApprovalRequired != nil && *mcpRequest.ManagedApprovalRequired) {
			return rejectWikipediaPermission(), nil
		}

		switch mcpRequest.ToolName {
		case "search", "wikipedia-search":
			if searchCalls >= 1 {
				return rejectWikipediaPermission(), nil
			}
			searchCalls++
		case "readArticle", "wikipedia-readArticle":
			if searchCalls == 0 || articleCalls >= 1 {
				return rejectWikipediaPermission(), nil
			}
			articleCalls++
		default:
			return rejectWikipediaPermission(), nil
		}
		return &rpc.PermissionDecisionApproveOnce{}, nil
	}
}

func rejectWikipediaPermission() rpc.PermissionDecision {
	feedback := "This workshop permits only read-only Wikipedia search and article retrieval."
	return &rpc.PermissionDecisionReject{Feedback: &feedback}
}

func (service museumExhibitService) Generate(ctx context.Context, approvedFacts []string, model string) (result generatedExhibit, err error) {
	prompt, err := buildExhibitPrompt(approvedFacts)
	if err != nil {
		return result, err
	}

	defer func() { err = errors.Join(err, service.client.Stop()) }()
	if err = service.client.Start(ctx); err != nil {
		return result, err
	}

	session, err := service.client.CreateSession(ctx, createSessionConfiguration(model))
	if err != nil {
		return result, err
	}
	defer func() { err = errors.Join(err, session.Disconnect()) }()

	generationContext, cancel := context.WithTimeout(ctx, generationTimeout)
	defer cancel()
	content, err := session.SendAndWait(generationContext, prompt)
	if err != nil {
		return result, err
	}
	if strings.TrimSpace(content) == "" {
		return result, fmt.Errorf("the curator returned no exhibit content")
	}
	return generatedExhibit{Content: content, Validation: validateExhibit(content)}, nil
}

type copilotCuratorClient struct {
	client *copilot.Client
}

func newCopilotCuratorClient() *copilotCuratorClient {
	return &copilotCuratorClient{client: copilot.NewClient(&copilot.ClientOptions{LogLevel: "error"})}
}

func (client *copilotCuratorClient) Start(ctx context.Context) error {
	return client.client.Start(ctx)
}

func (client *copilotCuratorClient) CreateSession(ctx context.Context, config *copilot.SessionConfig) (curatorSession, error) {
	session, err := client.client.CreateSession(ctx, config)
	if err != nil {
		return nil, err
	}
	return copilotCuratorSession{session: session}, nil
}

func (client *copilotCuratorClient) Stop() error {
	return client.client.Stop()
}

type copilotCuratorSession struct {
	session *copilot.Session
}

func (session copilotCuratorSession) SendAndWait(ctx context.Context, prompt string) (string, error) {
	response, err := session.session.SendAndWait(ctx, copilot.MessageOptions{Prompt: prompt})
	if err != nil || response == nil {
		return "", err
	}
	message, ok := response.Data.(*copilot.AssistantMessageData)
	if !ok {
		return "", nil
	}
	return message.Content, nil
}

func (session copilotCuratorSession) Disconnect() error {
	return session.session.Disconnect()
}
