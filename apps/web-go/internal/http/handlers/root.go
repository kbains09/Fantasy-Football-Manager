package handlers

import (
	"io"
	"net/http"
)

func Root(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	io.WriteString(w, "FantasyManager web is up. Try /freeagents?team_id=alpha\n")
}
