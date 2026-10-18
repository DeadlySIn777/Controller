# Archive: gateware validation record before the final audit sync (2026-09-28)

These are the files that were current before gateware/tools/record_evidence.py gained a read-only --check mode. The manifest here was accidentally re-recorded at 2026-09-28T20:59:48Z by running the recorder with --check before that flag existed; its evidence bytes and source hashes were identical to the 19:42:45Z record. The recorder change itself altered a hashed source, so the regression was rerun and re-recorded instead of restoring the older timestamp.
