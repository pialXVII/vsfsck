# vsfsck: a consistency checker for a very simple file system

`vsfsck` reads a raw file-system image and reports every structural inconsistency
it finds: a broken superblock, inodes and bitmaps that disagree, data blocks
claimed by two files, and block pointers that point outside the disk. It is the
same class of tool as `fsck`, written in C for the VSFS layout below.

Built for CSE321 (Operating Systems) at BRAC University, Spring 2025.

## Build and run

```bash
make
./vsfsck vsfs.img
```

Example output on an image with two problems:

```
ERROR: Inode 2 is valid but not marked used in bitmap.
ERROR: Data block 1 is referenced by multiple inodes.
Superblock validation completed.
...
```

## File-system layout

| Block | Contents |
| --- | --- |
| 0 | Superblock (magic `0xD34D`, block size, block count, table locations, inode size and count) |
| 1 | Inode bitmap |
| 2 | Data bitmap |
| 3-7 | Inode table: 80 inodes of 256 bytes |
| 8-63 | 56 data blocks of 4096 bytes |

## What it checks

| Check | Detects |
| --- | --- |
| Superblock validator | wrong magic number, block size, block count, table pointers, inode size, or an inode count above the table's capacity |
| Inode bitmap | bitmap bits set for invalid inodes, and valid inodes (links > 0, not deleted) missing from the bitmap |
| Data bitmap | blocks marked used that no inode references, and referenced blocks not marked used |
| Duplicate blocks | a data block referenced by more than one inode |
| Bad blocks | direct, single, double or triple indirect pointers outside the data region |

Block pointers are read as indices into the data region (0-55).

## Tests

`tests/make_images.py` builds a clean image and one image per kind of corruption
(14 cases). `tests/run_tests.py` runs the checker on each and confirms the expected
error is reported, and that the clean image reports none. CI runs both on every push.

```bash
make test
```

## Limitations

- It reports problems; it does not repair them.
- Only the direct pointer is followed into the data bitmap. Indirect pointers are
  range-checked but their blocks are not walked.
