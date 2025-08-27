package engine

import (
	"context"
	"errors"
	"net/http"
	"os"

	engineapi "github.com/kbains09/FantasyManager/packages/clients/go"
)

func baseURL() string {
	if v := os.Getenv("ENGINE_BASE_URL"); v != "" {
		return v
	}
	// Local dev (two processes): engine on :8000 localhost
	// Compose (web service): compose injects ENGINE_BASE_URL=http://engine:8000
	return "http://localhost:8000"
}

func client() *engineapi.ClientWithResponses {
	c, _ := engineapi.NewClientWithResponses(
		baseURL(),
		engineapi.WithHTTPClient(&http.Client{}),
	)
	return c
}

func FreeAgents(ctx context.Context, teamID string, limit int) ([]engineapi.FaSuggestion, error) {
	resp, err := client().GetRecommendFreeAgentsWithResponse(ctx, &engineapi.GetRecommendFreeAgentsParams{
		TeamId: teamID,
		Limit:  &limit,
	})
	if err != nil {
		return nil, err
	}
	if resp.JSON200 == nil {
		return nil, errors.New(resp.Status())
	}
	return *resp.JSON200, nil
}
