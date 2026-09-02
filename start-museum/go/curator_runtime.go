package main

import (
	"context"

	copilot "github.com/github/copilot-sdk/go"
)

type curatorSession interface {
	SendAndWait(context.Context, string) (string, error)
	Disconnect() error
}

type curatorClient interface {
	Start(context.Context) error
	CreateSession(context.Context, *copilot.SessionConfig) (curatorSession, error)
	Stop() error
}

type copilotCuratorClient struct {
	client *copilot.Client
}

func newCopilotCuratorClient() *copilotCuratorClient {
	return &copilotCuratorClient{
		client: copilot.NewClient(&copilot.ClientOptions{LogLevel: "error"}),
	}
}

func (client *copilotCuratorClient) Start(ctx context.Context) error {
	return client.client.Start(ctx)
}

func (client *copilotCuratorClient) CreateSession(
	ctx context.Context,
	config *copilot.SessionConfig,
) (curatorSession, error) {
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

func (session copilotCuratorSession) SendAndWait(
	ctx context.Context,
	prompt string,
) (string, error) {
	response, err := session.session.SendAndWait(
		ctx,
		copilot.MessageOptions{Prompt: prompt},
	)
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
