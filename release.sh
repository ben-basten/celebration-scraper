if [ -z "$1" ]; then
  echo "Usage: ./release.sh <version>"
  exit 1
fi

VERSION=$1
GOOS=darwin GOARCH=arm64 go build -ldflags="-X 'main.Version=${VERSION}'" -o dist/cinema cinema.go
GOOS=windows GOARCH=amd64 go build -ldflags="-X 'main.Version=${VERSION}'" -o dist/cinema.exe cinema.go
