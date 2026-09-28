"""Build VSFS test images: one clean image and one image per kind of corruption.

The layout follows the CSE321 VSFS spec (64 blocks of 4096 bytes: superblock,
inode bitmap, data bitmap, 5 inode-table blocks, 56 data blocks). Block
pointers inside inodes are indices into the data region (0-55), which is how
src/vsfsck.c interprets them.

Each case lists the lines vsfsck must print, so run_tests.py can check that
every corruption is detected and that the clean image reports no errors.
"""
import pathlib
import struct

BLOCK = 4096
TOTAL_BLOCKS = 64
INODE_SIZE = 256
INODE_TABLE_START = 3
MAX_INODES = (BLOCK // INODE_SIZE) * 5
MAX_DATA_BLOCKS = TOTAL_BLOCKS - 8


def superblock(magic=0xD34D, block_size=BLOCK, total=TOTAL_BLOCKS, ibitmap=1,
               dbitmap=2, itable=INODE_TABLE_START, dstart=8, isize=INODE_SIZE,
               icount=MAX_INODES):
    raw = struct.pack("<HIIIIIIII", magic, block_size, total, ibitmap, dbitmap,
                      itable, dstart, isize, icount)
    return raw.ljust(BLOCK, b"\0")


def inode(links=1, dtime=0, direct=0, indirect=0, double=0, triple=0):
    # mode, uid, gid, size, atime, ctime, mtime, dtime, links, blocks,
    # direct, indirect, doubleIndirect, tripleIndirect, then 156 reserved bytes
    raw = struct.pack("<14I", 0o100644, 1000, 1000, 100, 0, 0, 0, dtime, links,
                      1, direct, indirect, double, triple)
    return raw.ljust(INODE_SIZE, b"\0")


def bitmap(bits):
    raw = bytearray(BLOCK)
    for i in bits:
        raw[i // 8] |= 1 << (i % 8)
    return bytes(raw)


def image(sb=None, inodes=None, ibits=None, dbits=None):
    """Clean default: inodes 0-2 use data blocks 0-2, bitmaps match."""
    inodes = inodes if inodes is not None else {0: inode(direct=0), 1: inode(direct=1), 2: inode(direct=2)}
    ibits = ibits if ibits is not None else set(inodes)
    dbits = dbits if dbits is not None else {0, 1, 2}
    table = bytearray(BLOCK * 5)
    for n, raw in inodes.items():
        table[n * INODE_SIZE:(n + 1) * INODE_SIZE] = raw
    data = bytes(BLOCK * MAX_DATA_BLOCKS)
    return (sb or superblock()) + bitmap(ibits) + bitmap(dbits) + bytes(table) + data


CASES = {
    "clean": (image(), []),
    "bad_magic": (image(sb=superblock(magic=0xBEEF)), ["ERROR: Invalid magic number in superblock."]),
    "bad_block_size": (image(sb=superblock(block_size=1024)), ["ERROR: Invalid block size in superblock."]),
    "bad_total_blocks": (image(sb=superblock(total=128)), ["ERROR: Invalid total block count in superblock."]),
    "bad_pointers": (image(sb=superblock(dstart=9)), ["ERROR: One or more superblock pointers are incorrect."]),
    "bad_inode_size": (image(sb=superblock(isize=128)), ["ERROR: Invalid inode size in superblock."]),
    "too_many_inodes": (image(sb=superblock(icount=MAX_INODES + 1)),
                        ["ERROR: Inode count in superblock exceeds maximum allowed."]),
    "inode_not_in_bitmap": (image(ibits={0, 1}), ["ERROR: Inode 2 is valid but not marked used in bitmap."]),
    "bitmap_marks_free_inode": (image(ibits={0, 1, 2, 5}), ["ERROR: Inode 5 marked used in bitmap but is invalid."]),
    "deleted_inode_in_bitmap": (
        image(inodes={0: inode(direct=0), 1: inode(direct=1), 2: inode(direct=2, dtime=1700000000)},
              ibits={0, 1, 2}, dbits={0, 1}),
        ["ERROR: Inode 2 marked used in bitmap but is invalid."]),
    "block_not_in_data_bitmap": (image(dbits={0, 1}), ["ERROR: Data block 2 is used but not marked in bitmap."]),
    "unreferenced_block_marked": (image(dbits={0, 1, 2, 9}),
                                  ["ERROR: Data block 9 marked used in bitmap but not referenced."]),
    "duplicate_block": (
        image(inodes={0: inode(direct=0), 1: inode(direct=1), 2: inode(direct=1)}, dbits={0, 1}),
        ["ERROR: Data block 1 is referenced by multiple inodes."]),
    "bad_direct_pointer": (
        image(inodes={0: inode(direct=0), 1: inode(direct=1), 2: inode(direct=99)}, dbits={0, 1}),
        ["ERROR: Inode 2 has invalid direct block 99."]),
    "bad_indirect_pointer": (
        image(inodes={0: inode(direct=0), 1: inode(direct=1), 2: inode(direct=2, indirect=200)}),
        ["ERROR: Inode 2 has invalid single indirect block 200."]),
}


def main():
    out = pathlib.Path(__file__).resolve().parent / "images"
    out.mkdir(exist_ok=True)
    for name, (img, _) in CASES.items():
        assert len(img) == BLOCK * TOTAL_BLOCKS, name
        (out / f"{name}.img").write_bytes(img)
    print(f"wrote {len(CASES)} images to {out}")


if __name__ == "__main__":
    main()
