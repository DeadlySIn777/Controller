# Disconnected SIM2 provider and plant

`ProviderPlant` is a deterministic C++ virtual device model driven by observed
RTL STEP, DIR, individual enable, permission, watchdog-progress and rearm pins.
It contains no device, network, file or paid-provider transport. A caller must
first validate the complete reviewed manifest and explicitly construct a
nonzero simulation context. This context remains distinct from CNC3 SYNC/motion
sessions. Physical authority and production-profile completion are always false.

`SimulationIdentity` requires the full source and configuration SHA256 digests,
their nonzero 32-bit identifiers, a nonzero run-context session and explicit
disconnected opt-in. The shortened identifiers are not authentication. The
standalone ledger serializes its snapshot fields explicitly and checks CRC32C, exact
full digests, tag/ABI/session, consecutive nonwrapping sequence, capture time,
freshness, field bounds and complete valid providers. A rejection latches. New
contexts cannot rebind sources/configuration in place, reuse a session or accept
facts captured before their reset. Initial construction has no implicit facts.

The model publishes a heartbeat every 5,000 virtual 50MHz ticks (100us). A record
is unavailable at age 22,000 ticks (440us); the independent RTL boundary enforces
its own age/sequence/context checks. Continuous raw ABZ/probe pins remain distinct
from atomic DI/DO/home/limit snapshots. General 24 DI has explicit independent
stimulus; geometry does not silently assign those channels. Twelve home/low/high
limit observations and the first probe surface derive integer STEP coordinates.
Both probes can also receive deliberate external stimuli. No automatic homing
permission or physical wiring discovery is inferred.

Alarm-current polarity is an explicit plant configuration supplied by the
reviewed manifest. A normally-closed healthy circuit's modeled current differs
from an alarm assertion; independent alarm faults toggle that current before
the actual RTL filter. Low/high limit injections are separate twelve-bit masks,
ORed with geometric sensor observations without modifying general DI.

All twelve emitted STEP streams have independent observed, accepted and inhibited
edge counts. Mechanical acceptance requires the actual armed channel, enable,
model watchdog, permission and separately observed gate/OPI. Stall and direction
faults alter mechanical acceptance independently of commanded motion. Four ABZ
streams derive that actual accepted motion, one edge per motor STEP; unsupported
encoder mappings/ratios refuse. Their explicit default fixture is 3,200 edges
per motor revolution, and each index waveform uses its configured period. Actual
index one-shot/counter capture belongs the consuming RTL.

The four motor gate domains retain TX/A/B/BOE: motors0..7 require mask0x3 and
motors8..11 require0xf. Motor request starts an independent gate delay. A later
runtime OPI rearm must occur after the gate was observed high; it starts a
separate OPI delay. General outputs have their own gate/rearm/OPI domain, with no
reuse of BOE. Actual requested16DO only apply after that independent chain.
Open and stuck-high faults provide separate applied/fault feedback; a stuck-high
observation is retained even during inhibit instead of hidden as zero.

Virtual M/O watchdogs drop after11ms without observed progress and recover after
a stopped request plus100 core ticks. Their timed drop/recovery is witnessed by
the consuming RTL self-test. These are model assumptions, not a measured
electrical inhibit rating. The virtual reset button requires a deliberate50ms
press, limits a press and ready window to5s, and never reuses a consumed held
press. Configuration timing, electrical output limits and frozen96/176 frames
are unchanged.

`drive_inputs` and `observe_outputs` map the exact runtime-top ABI. Transport must
shift actual compiled RTL SPI pins; this model never manufactures response bytes.
The [standalone executed checks](../../reports/deeper-runtime-20261004/providers/README.md)
are separate from the continuous HAL/RTL pipeline and physical qualification.
