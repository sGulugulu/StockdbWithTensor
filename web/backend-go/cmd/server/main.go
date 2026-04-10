package main

import (
	"log"
	"net/http"
	"os"

	"stocktensor/backendgo/internal/backend"
)

func main() {
	repoRoot, err := os.Getwd()
	if err != nil {
		log.Fatalf("failed to get working directory: %v", err)
	}
	handler, err := backend.NewHandler(backend.Config{
		RepoRoot: repoRoot,
	})
	if err != nil {
		log.Fatalf("failed to create server: %v", err)
	}
	address := ":8080"
	log.Printf("Go backend listening on %s", address)
	if err := http.ListenAndServe(address, handler); err != nil {
		log.Fatalf("server failed: %v", err)
	}
}
