package main

import (
	"bufio"
	"strings"
	"testing"
)

func TestReadFactsKeepsFinalFactAtEOF(t *testing.T) {
	facts := readFacts(bufio.NewReader(strings.NewReader("Final approved fact")))
	if len(facts) != 1 || facts[0] != "Final approved fact" {
		t.Fatalf("readFacts() = %v", facts)
	}
}
