package httpserver

import (
	"net/http"

	"github.com/kbains09/FantasyManager/apps/web-go/internal/http/handlers"
)

func Routes() *http.ServeMux {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", handlers.Health)
	mux.HandleFunc("/", handlers.Root)
	mux.HandleFunc("/freeagents", handlers.FreeAgents)
	return mux
}
