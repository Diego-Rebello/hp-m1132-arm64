CC      = clang
CFLAGS  = -Wall -O2 -arch arm64 -Isrc
LDFLAGS = -lcups -lcupsimage

JBIG_SRC = src/jbig.c src/jbig_ar.c
PPD      = ppd/HP-LaserJet_Professional_M1132_MFP-arm64.ppd

all: rastertozjs zjsdecode $(PPD)

rastertozjs: src/rastertozjs.c $(JBIG_SRC) Makefile
	$(CC) $(CFLAGS) -o $@ $(filter %.c,$^) $(LDFLAGS)

# The PPD is generated; the list of sizes and options lives in scripts/make_ppd.py.
$(PPD): scripts/make_ppd.py
	python3 scripts/make_ppd.py > $@

ppd: $(PPD)

zjsdecode: src/zjsdecode.c $(JBIG_SRC)
	$(CC) $(CFLAGS) -o $@ $^

check: all
	@for b in rastertozjs zjsdecode; do \
	  a=$$(lipo -archs $$b); echo "$$b: $$a"; \
	  [ "$$a" = "arm64" ] || { echo "ERROR: $$b is not arm64"; exit 1; }; \
	done

clean:
	rm -f rastertozjs zjsdecode

.PHONY: all check clean ppd
