FROM golang:1.22 as build
WORKDIR /src
COPY apps/web-go/go.mod apps/web-go/go.sum ./apps/web-go/
RUN cd apps/web-go && go mod download
COPY apps/web-go ./apps/web-go
RUN cd apps/web-go && go build -o /bin/web ./cmd/web

FROM gcr.io/distroless/base-debian12
COPY --from=build /bin/web /bin/web
EXPOSE 8080
USER nonroot:nonroot
ENTRYPOINT ["/bin/web"]
