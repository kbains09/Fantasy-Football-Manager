module github.com/kbains09/FantasyManager/apps/web-go

go 1.22

require github.com/kbains09/FantasyManager/packages/clients/go v0.0.0

require (
	github.com/apapsch/go-jsonmerge/v2 v2.0.0 // indirect
	github.com/google/uuid v1.5.0 // indirect
	github.com/oapi-codegen/runtime v1.1.2 // indirect
)

replace github.com/kbains09/FantasyManager/packages/clients/go => ../../packages/clients/go
