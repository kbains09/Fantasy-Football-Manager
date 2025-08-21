package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
)

func main() {
	mux := http.NewServeMux()

	// Simple health
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprint(w, `{"ok": true}`)
	})

	// Example: read ENGINE_BASE_URL env for later calls to FastAPI
	engineBase := os.Getenv("ENGINE_BASE_URL")
	if engineBase == "" {
		engineBase = "http://app:8000" // safe default inside devcontainer network
	}
	log.Println("ENGINE_BASE_URL:", engineBase)

	port := "8080"
	log.Println("web listening on :" + port)
	log.Fatal(http.ListenAndServe(":"+port, mux))
}
