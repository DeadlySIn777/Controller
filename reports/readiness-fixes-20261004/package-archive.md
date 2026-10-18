# Bounded package archive — host evidence

4 October 2026. Implemented `controller_config/package_archive.py` and `tests/test_package_archive.py`. This is a software-only package service for `support`, `config` and `job` bytes. It never extracts files, executes job contents or applies configurations. Hardware/CAD/routing, FPGA, firmware and retained historical evidence were not edited. Missing optional Python `compression.zstd` support produces `ARCHIVE_UNAVAILABLE`, without creating an output.

The service writes one checksummed Zstandard frame containing regular USTAR files and a versioned SHA-256 manifest. Its limits are 128 files, 8 MiB per file, 32 MiB total payload, 64 KiB manifest, 16 KiB metadata, and an 8 MiB decoder window. The shared raw codec allows at most 64 MiB decompressed bytes and 65 MiB compressed input. Default compression level is 3, with levels 1–9 available. No trained dictionary is used. Limits are disclosed through `capabilities()`.

Reads reject dictionaries, missing checksums, skippable/concatenated/trailing/truncated/corrupt frames and excessive windows/output. Tar parsing rejects links, devices, directories, sparse/PAX/GNU extensions, duplicate/case-colliding names, parent/file collisions, absolute/traversal/reserved Windows paths, hidden trailing data and malformed blocks. Manifest reading requires the exact schema and kind, a complete matching inventory, sizes, SHA-256 digests, finite bounded metadata and no duplicate JSON keys. These checks establish package integrity; they do not authenticate its sender or make its contents safe to execute.

Publication fsyncs a sibling temporary file and creates the destination with an exclusive atomic hard link. Existing paths are never replaced, including a concurrent winner. Unsupported publication and fsync failures fail closed and remove the temporary file. This is a host filesystem operation, not power-loss durability or storage-wear qualification.

**28 tests reported: 27 passed, one skipped.** Windows denied creation of the filesystem symlink used by that one test. Actual archive-contained symlink/hardlink rejection ran and passed. Tests also cover an unknown-size decompression bomb, a declared 64 MiB window, compressed/member/total/count bounds, corrupted SHA and checksum, malformed schemas, atomic-publication races and unavailable runtime behavior. [Test log](package-archive-tests.log), [source-bound receipt](package-archive-verification.json), [reproducible runner](verify_package_archive.py). Five monitored source/historical-evidence files were unchanged across the captured run.

| Generated fixture | Payload bytes | Tar bytes | Zstd package bytes | Create / read milliseconds |
|---|---:|---:|---:|---:|
| Synthetic support report and 20,000 NDJSON rows | 2,026,946 | 2,037,760 | 22,536 | 8.51 / 15.92 |
| Twelve-motor simulation example configuration | 5,311 | 10,240 | 776 | 3.29 / 12.12 |
| Repeated inert job text | 660,000 | 665,600 | 437 | 6.76 / 12.29 |

All three temporary packages restored their input bytes exactly. Timings are single observations on this Windows host, including tar/manifest work, disk publication and verification. The fixtures are deliberately synthetic and repetitive; these ratios do not estimate real production corpora. No target CPU, real-time performance, power-loss behavior, physical storage endurance or wear reduction was measured. No job or machine command was run.

Primary API/format references checked during implementation: [Python compression.zstd](https://docs.python.org/3/library/compression.zstd.html), [Zstandard compression format](https://github.com/facebook/zstd/blob/dev/doc/zstd_compression_format.md).
