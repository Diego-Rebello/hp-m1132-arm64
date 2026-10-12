CC      = clang
CFLAGS  = -Wall -O2 -arch arm64 -Isrc
LDFLAGS = -lcups -lcupsimage

JBIG_SRC = src/jbig.c src/jbig_ar.c

all: rastertozjs zjsdecode

rastertozjs: src/rastertozjs.c $(JBIG_SRC)
	$(CC) $(CFLAGS) -DDEFAULT_MODEL=2 -o $@ $^ $(LDFLAGS)

zjsdecode: src/zjsdecode.c $(JBIG_SRC)
	$(CC) $(CFLAGS) -o $@ $^

check: all
	@for b in rastertozjs zjsdecode; do \
	  a=$$(lipo -archs $$b); echo "$$b: $$a"; \
	  [ "$$a" = "arm64" ] || { echo "ERRO: $$b nao e arm64"; exit 1; }; \
	done

clean:
	rm -f rastertozjs zjsdecode

.PHONY: all check clean
