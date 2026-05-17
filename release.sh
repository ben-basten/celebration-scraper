GOOS=darwin GOARCH=arm64 go build -o dist/cinema-darwin-arm64 cinema.go
GOOS=windows GOARCH=amd64 go build -o dist/cinema.exe cinema.go
