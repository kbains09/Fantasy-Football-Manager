package main

import (
	"log"
	"net/http"
	"os"

	"github.com/kbains09/FantasyManager/apps/web-go/internal/http"
)

func main() {
	// Make sure ENGINE_BASE_URL is visible to the process (useful log)
	if os.Getenv("ENGINE_BASE_URL") == "" {
		log.Println("ENGINE_BASE_URL not set; engine_client will pick a default")
	}

	mux := httpserver.Routes() // build the mux

	port := "8080"
	log.Println("web listening on :" + port)
	log.Fatal(http.ListenAndServe(":"+port, mux))
}
