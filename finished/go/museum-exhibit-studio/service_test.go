package main

import (
	"context"
	"errors"
	"strings"
	"testing"
	"time"

	copilot "github.com/github/copilot-sdk/go"
)

func TestCreateSessionConfiguration(t *testing.T) {
	config := createSessionConfiguration(" test-model ")
	if config.ClientName != "museum-exhibit-studio" {
		t.Errorf("ClientName = %q", config.ClientName)
	}
	if config.Model != "test-model" {
		t.Errorf("Model = %q", config.Model)
	}
	if config.AvailableTools == nil || len(config.AvailableTools) != 0 {
		t.Errorf("AvailableTools = %#v, want an explicit empty list", config.AvailableTools)
	}
	if config.Streaming == nil || *config.Streaming {
		t.Errorf("Streaming = %v, want false", config.Streaming)
	}
	if config.SystemMessage == nil || config.SystemMessage.Mode != "replace" ||
		config.SystemMessage.Content != curatorSystemMessage {
		t.Errorf("SystemMessage = %#v", config.SystemMessage)
	}
}

func TestGenerateLifecycle(t *testing.T) {
	sendFailure := errors.New("generation failed")
	createFailure := errors.New("create failed")
	startFailure := errors.New("start failed")
	tests := []struct {
		name        string
		content     string
		startErr    error
		createErr   error
		sendErr     error
		wantErr     string
		wantSession bool
		wantValid   bool
	}{
		{name: "success", content: makeExhibit(110, 3, true), wantSession: true, wantValid: true},
		{name: "empty output", content: " \n", wantErr: "no exhibit content", wantSession: true},
		{name: "send failure", sendErr: sendFailure, wantErr: sendFailure.Error(), wantSession: true},
		{name: "create failure", createErr: createFailure, wantErr: createFailure.Error()},
		{name: "start failure", startErr: startFailure, wantErr: startFailure.Error()},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			session := &fakeSession{content: test.content, sendErr: test.sendErr}
			client := &fakeClient{
				session: session, startErr: test.startErr, createErr: test.createErr,
			}
			result, err := (museumExhibitService{client: client}).Generate(
				context.Background(), apollo11Facts, "test-model",
			)

			if test.wantErr == "" && err != nil {
				t.Fatalf("Generate() unexpected error: %v", err)
			}
			if test.wantErr != "" && (err == nil || !strings.Contains(err.Error(), test.wantErr)) {
				t.Fatalf("Generate() error = %v, want containing %q", err, test.wantErr)
			}
			if !client.stopCalled {
				t.Error("client Stop was not called")
			}
			if session.disconnectCalled != test.wantSession {
				t.Errorf("session Disconnect called = %t, want %t", session.disconnectCalled, test.wantSession)
			}
			if test.wantSession {
				if client.config == nil {
					t.Fatal("session configuration was not captured")
				}
				for _, fact := range apollo11Facts {
					if !strings.Contains(session.prompt, fact) {
						t.Errorf("prompt does not contain %q", fact)
					}
				}
				if session.deadlineRemaining <= 0 || session.deadlineRemaining > generationTimeout {
					t.Errorf("send deadline remaining = %v, want within %v", session.deadlineRemaining, generationTimeout)
				}
			}
			if test.wantErr == "" && result.Validation.Valid() != test.wantValid {
				t.Errorf("validation.Valid = %t, want %t", result.Validation.Valid(), test.wantValid)
			}
			if test.wantErr == "" && !result.Validation.Narrative.Valid() {
				t.Error("validation.Narrative.Valid = false")
			}
		})
	}
}

func TestGenerateReturnsCleanupFailures(t *testing.T) {
	session := &fakeSession{content: makeExhibit(110, 3, true), disconnectErr: errors.New("disconnect failed")}
	client := &fakeClient{session: session, stopErr: errors.New("stop failed")}
	_, err := (museumExhibitService{client: client}).Generate(context.Background(), apollo11Facts, "")
	if err == nil || !strings.Contains(err.Error(), "disconnect failed") || !strings.Contains(err.Error(), "stop failed") {
		t.Fatalf("Generate() error = %v, want both cleanup failures", err)
	}
}

type fakeClient struct {
	session     *fakeSession
	startErr    error
	createErr   error
	stopErr     error
	startCalled bool
	stopCalled  bool
	config      *copilot.SessionConfig
}

func (client *fakeClient) Start(context.Context) error {
	client.startCalled = true
	return client.startErr
}

func (client *fakeClient) CreateSession(_ context.Context, config *copilot.SessionConfig) (curatorSession, error) {
	client.config = config
	if client.createErr != nil {
		return nil, client.createErr
	}
	return client.session, nil
}

func (client *fakeClient) Stop() error {
	client.stopCalled = true
	return client.stopErr
}

type fakeSession struct {
	content           string
	sendErr           error
	disconnectErr     error
	prompt            string
	deadlineRemaining time.Duration
	disconnectCalled  bool
}

func (session *fakeSession) SendAndWait(ctx context.Context, prompt string) (string, error) {
	session.prompt = prompt
	if deadline, ok := ctx.Deadline(); ok {
		session.deadlineRemaining = time.Until(deadline)
	}
	return session.content, session.sendErr
}

func (session *fakeSession) Disconnect() error {
	session.disconnectCalled = true
	return session.disconnectErr
}
