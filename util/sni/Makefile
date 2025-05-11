ALL = $(BIN)

# creates static binaries
LD_FLAGS := -ldflags "-w -s"
CC := CGO_ENABLED=0 go build -trimpath -a -installsuffix cgo $(LD_FLAGS)

BIN := snicensor
SOURCES := sni.go

.PHONY: all
all: $(ALL)

docker: Dockerfile $(BIN)
	sudo docker build -t="user/snicensor" .
	sudo docker save "user/snicensor" > snicensor.docker.tar

$(BIN): $(SOURCES) go.mod
	$(CC) -o "$@" $(SOURCES)

.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR:
