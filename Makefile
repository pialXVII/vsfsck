CC ?= gcc
CFLAGS ?= -std=c11 -Wall -Wextra -O2

vsfsck: src/vsfsck.c
	$(CC) $(CFLAGS) -o $@ $<

test: vsfsck
	python3 tests/run_tests.py

clean:
	rm -f vsfsck vsfsck.exe tests/images/*.img

.PHONY: test clean
