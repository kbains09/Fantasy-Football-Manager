package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/kbains09/FantasyManager/apps/web-go/internal/engine"
)

func FreeAgents(w http.ResponseWriter, r *http.Request) {
	teamID := r.URL.Query().Get("team_id")
	if teamID == "" {
		teamID = "alpha"
	}

	items, err := engine.FreeAgents(r.Context(), teamID, 5)
	if err != nil {
		http.Error(w, "engine error: "+err.Error(), http.StatusBadGateway)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(items)
}
