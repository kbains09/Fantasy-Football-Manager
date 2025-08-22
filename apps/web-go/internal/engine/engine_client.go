package engine

import (
	"context"
	"net/http"
	"os"

	engineapi "github.com/kbains09/fantasymanager/packages/clients/go" 
)

func client() *engineapi.ClientWithResponses {
	base := os.Getenv("ENGINE_BASE_URL")
	if base == "" {
		base = "http://app:8000" 
	}
	c, _ := engineapi.NewClientWithResponses(base, engineapi.WithHTTPClient(&http.Client{}))
	return c
}

func FreeAgents(ctx context.Context, teamID string, limit int) ([]engineapi.FaSuggestion, error) {
	resp, err := client().GetRecommendFreeAgentsWithResponse(ctx, &engineapi.GetRecommendFreeAgentsParams{
		TeamId: teamID,
		Limit:  engineapi.NewOptInt(limit),
	})
	if err != nil {
		return nil, err
	}
	if resp.JSON200 == nil {
		return nil, err
	}
	return *resp.JSON200, nil
}
