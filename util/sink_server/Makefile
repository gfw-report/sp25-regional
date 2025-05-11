ALL = $(BIN)

# creates static binaries
LD_FLAGS := -ldflags "-w -s"
CC := CGO_ENABLED=0 go build -trimpath -a -installsuffix cgo $(LD_FLAGS)

BIN := sink
SOURCES := sink.go parseIPPort.go

.PHONY: all
all: $(ALL)

$(BIN): $(SOURCES)
	$(CC) -o "$@" $(SOURCES)

.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR:
