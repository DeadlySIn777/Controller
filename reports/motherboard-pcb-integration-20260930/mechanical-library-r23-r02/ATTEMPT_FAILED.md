This attempt preserved lands/copper and fixed the seven graphic mismatches, but
native DRC reported twenty missing library lookups after the new project-local
Phoenix alias shadowed the global library. It is not adopted and is not a pass.

The passing replacement is mechanical-library-r23-r03. That project contains
all other Phoenix footprint families actually used on the board, copied
verbatim from the original stock library, and passes native DRC 0.
