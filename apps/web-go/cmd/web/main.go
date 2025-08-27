package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"

	"github.com/kbains09/FantasyManager/apps/web-go/internal/engine"
)

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprint(w, `{"ok": true}`)
	})

	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain; charset=utf-8")
		io.WriteString(w, "FantasyManager web is up. Try /ui/free-agents?team_id=alpha\n")
	})

	mux.HandleFunc("/ui/free-agents", func(w http.ResponseWriter, r *http.Request) {
		teamID := r.URL.Query().Get("team_id")
		if teamID == "" {
			teamID = "alpha"
		}
		items, err := engine.FreeAgents(r.Context(), teamID, 5)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadGateway)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(items)
	})

	// Example: read ENGINE_BASE_URL env for later calls to FastAPI
	engineBase := os.Getenv("ENGINE_BASE_URL")
	if engineBase == "" {
		engineBase = "http://app:8000"
	}
	log.Println("ENGINE_BASE_URL:", engineBase)

	port := "8080"
	log.Println("web listening on :" + port)
	log.Fatal(http.ListenAndServe(":"+port, mux))
}
