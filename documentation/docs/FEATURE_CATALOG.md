# Feature catalogue — 200 supplied proposals

Imported 28 September 2026. All entries are **proposals**, not an installed feature list. The wording comes from the supplied notes; incidental claims about other products are not independently established by this import. Original citation placeholders are preserved only in the source archive, not treated as evidence.

[Priorities and acceptance gates](PLATFORM_ROADMAP.md) · [Machine-readable catalogue](../WORKSPACE_REFERENCES.md#artifact-e86fa22afb61cac4) · [Actual engineering evidence](../reports/ENGINEERING_STATUS.md)

H = source explicitly marks additional hardware; R = substantial development. An absent mark does not mean a feature has no hardware or engineering dependency. The first demonstrations exercise a bounded subset of a feature; they do not qualify its full scope.

## 1–10: Wiring and commissioning

**F001. Component-aware wiring generator** — first core demonstration

Select the actual drives, switches, spindle, and controller modules; generate terminal-to-terminal diagrams and flag incompatible electrical interfaces before wiring.

**F002. Press-to-identify inputs** — first core demonstration

Enter commissioning mode, activate a switch, and assign the detected input visually. Identify inverted logic, stuck inputs, and multiple switches changing together.

**F003. Motor-driver setup translator** — first core demonstration

Convert screw lead, gearing, microstepping, and driver timing requirements into controller settings, with a physical measurement step to verify the result.

**F004. Controlled first-motion wizard** — first core demonstration

Commission one joint at a time using bounded moves, direction confirmation, scale checks, and verified limits instead of immediately enabling full-speed jogging.

**F005. VFD commissioning assistant** — H

Provide model-specific connection and parameter instructions, then verify commanded versus actual spindle behavior using supported feedback.

**F006. Independent gantry squaring** — H, first core demonstration

Home dual-drive gantries independently, measure repeatability, and warn when the two sides require an unusually large correction.

**F007. Visual kinematics configuration**

Configure supported Cartesian, CoreXY, dual-gantry, and rotary arrangements through diagrams, while explicitly rejecting unsupported combinations rather than silently accepting them.

**F008. Graphical machine-sequence builder**

Build operational sequences such as “clamp, confirm pressure, start spindle” with timeouts, simulated inputs, and an explanation of why a sequence cannot advance.

**F009. Built-in signal oscilloscope**

Display timestamped step commands, encoder feedback, probe transitions, drive alarms, and machine-state changes on one synchronized timeline.

**F010. Existing-configuration importer**

Import supported settings from Grbl, Klipper, or LinuxCNC configurations, explain the mapping, and flag anything that cannot be translated reliably.


## 11–20: Registration and probing

**F011. Guided stock probing** — H, first core demonstration

Find edges, corners, bore centers, and bosses using illustrated routines that preview the intended probe movements before execution.

**F012. Crooked-stock registration** — H

Measure reference features and calculate the stock’s translation and rotation, allowing an awkward blank to remain where it is clamped.

**F013. Surface-following machining** — H

Probe a warped board, PCB, or sheet and compensate engraving depth against its measured surface instead of assuming everything is perfectly flat.

**F014. Tool measurement with confidence checks** — H

Measure tool length, repeat the measurement when inconsistent, and flag contamination or an implausible change rather than blindly accepting it.

**F015. Two-sided machining registration** — H

Guide the flip operation using pins or probed references, calculate the second-side transform, and show whether the two setups agree.

**F016. Rotary-axis calibration wizard** — H

Measure the rotary centerline, angular zero, and alignment relative to the linear axes instead of requiring manual coordinate calculations.

**F017. Leadscrew-error mapping** — H

Import or measure positioning errors along an axis and generate a calibrated compensation map with a visible valid range.

**F018. Backlash characterization** — H

Measure reversal error at several positions, distinguish repeatable backlash from inconsistent motion, and explain when mechanical repair is needed instead of compensation.

**F019. Thermal-drift compensation** — H, R

Use temperature and reference measurements to apply bounded corrections from a validated machine model, with compensation disabled outside the calibrated conditions.

**F020. Inspect-and-correct finishing** — H, R

Measure a feature after a machining pass and propose a bounded wear-offset adjustment or finishing pass, with operator approval before recutting.


## 21–30: Preflight and simulation

**F021. Whole-job preflight** — first core demonstration

Check units, work offsets, required tools, travel, spindle limits, and machine configuration against the actual program before allowing execution.

**F022. Execution-matched simulation** — R

Preview supported programs through the same interpreter semantics used for machining, including offsets, canned cycles, and declared macro behavior—not just straight-line backplotting.

**F023. Fixture-aware collision checking** — R

Include clamps, toolholders, spindle bodies, fixtures, and machine limits in the check, and clearly mark unmodeled or unverified regions.

**F024. Remaining-stock tracking** — R

Estimate what material remains after each operation so subsequent previews can distinguish cutting stock from moving through already-cleared space.

**F025. “Why is it moving there?” coordinate explanation**

Click any destination and see how machine coordinates, work offsets, tool length, rotation, and active modes produced it.

**F026. Conversational machining with previews**

Generate pockets, bolt circles, facing, slots, and turning operations from dimensions, while showing the resulting toolpath and required tools.

**F027. CAD-feature-to-operation assistant** — R

Recognize supported holes, pockets, and faces; suggest machining operations and setups for review instead of treating imported CAD as merely a picture.

**F028. Remnant-aware nesting**

Arrange parts inside a saved scrap outline, avoiding marked holes, clamps, damaged regions, and unusable edges rather than assuming a rectangular sheet.

**F029. Automatic setup invalidation** — first core demonstration

Moving a clamp, changing a toolholder, replacing stock, or editing offsets invalidates the affected collision and setup checks automatically.

**F030. Machine-specific completion estimates**

Estimate time using actual acceleration limits, spindle ramp-up, probing, tool changes, and programmed waits, then refine estimates from recorded jobs.


## 31–40: Recovery and diagnostics

**F031. Truly local job execution** — first core demonstration

Validate and store the complete job on the controller before running, so an interface disconnect does not become a missing-G-code problem.

**F032. Reconnection without duplicate commands** — first core demonstration

Restore the live controller state after a network interruption, reject stale requests, and prevent two interfaces from simultaneously owning motion control.

**F033. Guided restart from a selected operation**

Reconstruct modal state, verify the tool and work registration, and preview a suitable entry path before resuming—not merely jump to a line number.

**F034. Power-loss recovery assessment** — H

Preserve checkpoints and determine what must be rehomed, remeasured, or inspected before restarting. Never equate a saved position with verified physical position.

**F035. Broken-tool recovery workflow** — H

Guide replacement, tool measurement, inspection, and re-entry into the unfinished operation without requiring the operator to manually edit the entire program.

**F036. Process-aware park and return**

Pause, move to an approved access position, and return through a checked route, while refusing generic retract behavior during incompatible operations.

**F037. Machine “black box” recorder** — first core demonstration

Preserve the commands, feedback, alarms, and state transitions immediately before and after a fault, including events too brief to notice on-screen.

**F038. Plain-language fault diagnosis**

Explain “clamp pressure dropped before spindle enable disappeared,” distinguish evidence from inference, and identify the next measurement instead of displaying only an alarm number.

**F039. Transactional updates and rollback**

Update firmware, gateware, and configuration as a compatible set; retain a known-good version and prohibit updates while the machine is armed.

**F040. ESP32 rescue interface**

Keep a separate diagnostic path available when the main Linux system fails, with fault history and controlled recovery—not unverified mid-cut motion takeover.


## 41–50: Advanced CNC

**F041. Load-aware adaptive feed** — H, R

Adjust feed within approved limits using spindle-load or cutting-force feedback, while distinguishing normal engagement changes from overload conditions.

**F042. Chatter detection and bounded response** — H, R

Analyze vibration and propose or apply validated spindle-speed/feed adjustments, rather than simply slowing every noisy cut.

**F043. Commanded-versus-actual position dashboard** — H

Compare commanded position, motor-encoder position, and linear-scale position where available, helping expose lost motion downstream of the motor.

**F044. Actual feed per spindle revolution** — H

Maintain the selected feed per revolution using measured spindle motion instead of assuming the spindle always reaches its commanded speed.

**F045. Encoder-synchronized threading** — H

Coordinate the cutting axis to spindle angle through speed variation, with setup tests for encoder direction, index, scaling, and synchronization.

**F046. Rigid tapping with verified reversal** — H

Coordinate spindle reversal and axial withdrawal, with explicit checks for the drive’s capabilities and synchronization errors.

**F047. Constant-surface-speed turning** — H

Adjust spindle speed as cutting diameter changes, with clear maximum-RPM limits and a preview of the expected speed range.

**F048. Existing-thread pickup** — H, R

Help locate the phase and pitch of an existing thread so it can be chased or extended without manually guessing alignment.

**F049. Spindle-to-C-axis transitions** — H, R

Switch a supported spindle between rotation and position control through a verified sequence that prevents conflicting commands or incorrect clamp states.

**F050. Five-axis tool-center-point control** — H, R

Maintain the programmed tool-tip position while rotary axes move, using calibrated geometry, tool length, and validated machine kinematics.


## 51–60: Tool changing and automation

**F051. ATC teaching wizard** — H

Teach rack or carousel locations visually, then test each movement and sensor transition individually before allowing a complete automatic tool change.

**F052. Tool-seated verification** — H

Confirm the expected drawbar, tool-present, and changer states; identify the exact failed condition instead of reporting a generic tool-change alarm.

**F053. Automatic tool-break checks** — H

Compare tool measurements before and after critical operations, or use a suitable break detector, to stop subsequent operations from machining with a missing cutter.

**F054. Sister-tool substitution** — H

Replace an expired or failed tool with an approved equivalent, revalidate its offsets, and identify which operations can resume with it.

**F055. Workholding verification** — H

Monitor vacuum, pneumatic, or hydraulic holding conditions against process-specific limits and inhibit the next operation when holding conditions are inadequate.

**F056. Fixture identity and setup recall** — H

Identify a fixture, load its tools and setup recipe, then verify its physical registration before accepting the saved work offsets.

**F057. Interchangeable-head recognition** — H

Identify a spindle, laser, extruder, or dispenser and load its offsets and permitted outputs, with process changes allowed only while disarmed.

**F058. Position-synchronized auxiliary outputs** — H

Trigger dispensing, marking, cameras, or valves at defined path positions rather than depending on a user-interface timer.

**F059. Discoverable expansion devices** — H, first plasma module demonstration

Recognize supported modules, show their capabilities and firmware compatibility, and bind their signals without hand-editing low-level configuration.

**F060. Registered print–probe–mill workflows** — H, R

Print a part, measure it, and machine selected surfaces within a coordinated setup, with process-specific clearances and tool changes.


## 61–70: Printer calibration and protection

**F061. Guided pressure-advance calibration**

Generate a test, help evaluate the result, and save the setting against the actual nozzle, material, temperature, and extrusion configuration.

**F062. Automatic resonance characterization** — H

Measure vibration, propose input-shaping settings, and show the associated acceleration and smoothing tradeoffs for each toolhead configuration.

**F063. Temperature-aware adaptive bed mapping** — H

Measure only the required print area while tracking whether bed temperature or machine changes make the previous mesh unreliable.

**F064. Actual-nozzle Z referencing** — H

Establish nozzle height through a suitable contact system, incorporating nozzle cleaning and repeatability checks instead of trusting a fixed probe offset forever.

**F065. Measured filament delivery** — H

Compare requested extrusion with actual filament movement, report persistent discrepancies, and pause when the delivery system is no longer following commands.

**F066. Jam-source diagnosis** — H, R

Combine filament motion, spool tension, and available drive data to distinguish likely tangles, slipping, and nozzle restrictions, while reporting diagnostic uncertainty.

**F067. Calibrated volumetric-flow limits**

Characterize a material/hotend combination and flag or constrain toolpaths that demand more melt flow than the validated setup can provide.

**F068. Verified heater fault handling** — H

Detect implausible temperatures, inadequate heating, and heating while commanded off; use an independent cutoff path where required to interrupt failed power switching.

**F069. First-layer inspection** — H, R

Check deposited lines for missing regions, gross gaps, or excessive buildup and pause for review; allow correction only within a validated adjustment envelope.

**F070. Selective failed-object cancellation**

Cancel one object in a multi-part print while preserving the others, then reevaluate travel paths around the failed material.


## 71–80: Advanced printing

**F071. Automatic multi-tool offset calibration** — H

Measure the relative nozzle positions and verify alignment with a test pattern, rather than relying on repeated manual tuning prints.

**F072. Measured purge completion** — H, R

Reduce unnecessary color-change purging by monitoring the extrudate against a validated transition criterion, with conservative fallback behavior.

**F073. Independent-carriage collision management** — H, R

Coordinate multiple moving printheads using their actual envelopes, parked positions, and remaining printed geometry.

**F074. Verified spool-change continuation** — H

Switch to an approved replacement material, confirm filament delivery, restore extrusion conditions, and resume from a controlled checkpoint.

**F075. Chamber thermal-stability management** — H

Start temperature-sensitive operations only after the chamber meets defined stability criteria, then coordinate cooling rather than abruptly ending heat control.

**F076. Zoned-bed temperature control** — H

Heat only needed regions while monitoring boundary temperatures and avoiding uneven thermal conditions across the part.

**F077. Force-aware resin peeling** — H, R

Measure separation loads and adapt supported lift profiles within validated limits, while recognizing abnormal sticking or release behavior.

**F078. Resin exposure-uniformity calibration** — H, R

Use suitable optical measurements to generate supported exposure corrections, while synchronizing the exposure engine and motion system.

**F079. Nonplanar printing support** — R

Execute supported curved-layer paths with nozzle-body collision checks and suitable extrusion control, rather than treating every layer as a horizontal plane.

**F080. Verified batch changeover** — H, R

Permit the next print only after the supported removal mechanism completes and bed clearance is confirmed; otherwise stop for operator intervention.


## 81–90: Laser setup and execution

**F081. Height-corrected camera placement** — H

Calibrate camera distortion and material height so artwork placement remains meaningful when switching between thin sheet and thicker objects.

**F082. Fiducial-based print-and-cut registration** — H

Locate reference marks, report registration error, and apply only the approved translation, rotation, or scaling needed for that job.

**F083. Surface-following focus** — H, R

Measure a supported surface and adjust focus through the job within the optical system’s validated range.

**F084. Calibrated energy-per-distance control** — R

Account for actual motion speed and a measured power-response curve when commanding the laser, rather than assuming every power percentage is proportional.

**F085. Bidirectional engraving calibration**

Generate and evaluate alignment patterns to compensate direction-dependent scan offsets at different engraving speeds.

**F086. Dedicated raster execution** — R

Coordinate pixel timing, motion, and overscan so engraving is not reduced to a huge stream of poorly timed individual G-code movements.

**F087. Measured kerf and fit calibration**

Generate test coupons, record measured results, and apply material/process-specific fit compensation for press-fit and slip-fit parts.

**F088. Tapered-object rotary engraving** — H, R

Map artwork onto a supported tapered shape while accounting for changing circumference and focus, instead of treating every object as a cylinder.

**F089. Cut-through verification** — H, R

Use a suitable sensing method to assess whether a supported material was fully cut and identify where another pass is justified.

**F090. Verified laser operating conditions** — H

Require the relevant enclosure, cooling, and extraction conditions before beam enable, with independent hardware inhibition where needed—not just on-screen warnings.


## 91–100: Plasma and platform services

**F091. Ohmic/float sensing diagnostics** — H, first plasma module demonstration

Test material sensing, detect stuck or inconsistent signals, and explain when the machine is using the verified fallback method.

**F092. Context-aware torch-height control** — H, first plasma module demonstration

Combine arc feedback with actual speed and path conditions so corner slowdowns and existing gaps do not provoke inappropriate height corrections.

**F093. Guided failed-pierce recovery** — H

Identify the failed pierce, inspect the conditions, and prepare a bounded retry or alternate lead-in rather than restarting the entire sheet blindly.

**F094. Breakaway-torch recovery** — H

Stop on a breakaway event, guide mechanical reseating, reverify torch registration, and prepare a checked return to the interrupted cut.

**F095. Small-hole process control**

Apply validated hole-specific speed, height-control, and supported power-source settings, with the resulting changes visible in the job preview.

**F096. Heat-aware cutting sequence** — R

Distribute cuts to reduce concentrated heating and avoid prematurely releasing unstable pieces, while respecting tabs, clamps, and required operation order.

**F097. Consumable-condition tracking** — H, R

Combine pierce history, operating data, and observed cut quality to recommend inspection or replacement rather than relying only on an hour counter.

**F098. Built-in real-time qualification**

Test controller timing under representative graphics and I/O loads, record the margin, and flag configuration changes that invalidate the previous qualification.

**F099. Evidence-based local diagnostic assistant** — R

Answer questions using the installed machine configuration, manuals, and logs; propose reviewed actions rather than directly issuing unverified machine commands.

**F100. Complete portable machine backup** — first core demonstration

Export a reproducible package containing configuration, compatible software versions, wiring, tools, calibration, fixtures, and job data, with a guided restore-verification process.


## 101–110: Motion development

**F101. Jerk-limited S-curve motion** — R

Control how quickly acceleration changes, with separate profiles for cutting, rapid travel, and delicate positioning.

**F102. Handwheel-controlled program execution** — H

Turn the handwheel to advance through a programmed toolpath; stop turning to request a controlled hold. LinuxCNC’s external adaptive-feed interface provides a foundation for this integration.

**F103. Electronic cam profiles** — H, R

Make an axis follow a programmable displacement-versus-spindle-angle curve for cam grinding, eccentric features, or synchronized repetitive mechanisms.

**F104. Electronic gearing** — H, R

Maintain a commanded angular ratio between separate rotating axes, with phase-error monitoring for applications such as gear hobbing.

**F105. Automatic rotary unwinding** — R

Plan when and where a rotary axis can unwind without wrapping cables, striking fixtures, or changing the intended tool orientation.

**F106. True dual-loop position control** — H, R

Use motor feedback for the inner drive loop and a linear scale for an outer correction loop, with stability limits—not merely display both positions.

**F107. Guided servo-loop tuning** — H, R

Perform bounded identification moves, evaluate following error and oscillation, and propose gains and filters with a reversible comparison test.

**F108. Constant-force machining** — H, R

Maintain controlled contact force during sanding, polishing, deburring, or surface finishing instead of relying entirely on fixed Z positions.

**F109. Tolerance-bounded toolpath smoothing** — R

Replace suitable chains of tiny segments with smoother trajectories while showing the maximum permitted contour deviation. Look-ahead and smoothing are established methods for managing this tradeoff.

**F110. Payload-aware acceleration limits**

Select a tested motion envelope based on the installed toolhead, fixture, or moving-bed load instead of using one acceleration setting for every configuration.


## 111–120: Lathe, mill and grinder

**F111. Main-spindle/subspindle part transfer** — H, R

Coordinate spindle speed, phase, approach, and verified clamping before transferring a part between chucks.

**F112. Live-tool polar interpolation** — H, R

Convert supported XY-style contours into coordinated linear and C-axis motion for machining features on a lathe’s part face.

**F113. Coordinated tailstock and steady-rest control** — H

Schedule support engagement around the toolpath, verify position and pressure, and prevent tool approaches through occupied support regions.

**F114. Intelligent bar-feeder cycles** — H

Track remaining bar length, account for cutoff losses, verify feed movement, and refuse a new part when insufficient usable stock remains.

**F115. Spindle-locked broaching cycles** — H

Generate incremental keyway or slot-broaching strokes with verified spindle orientation and a suitable locking mechanism. LinuxCNC already provides spindle-orientation interfaces to build around.

**F116. Oscillatory chip-breaking motion** — R

Superimpose a validated feed-axis oscillation during supported turning operations to interrupt chip formation without manually programming every oscillation.

**F117. Automatic grinding-wheel dressing** — H

Execute dressing routines, update the wheel’s effective geometry, and account for the resulting changes in machining position and permitted operating speed.

**F118. Coolant-aware deep-hole drilling** — H

Coordinate peck depth, full withdrawals, flushing intervals, and verified coolant delivery instead of relying on one fixed canned cycle.

**F119. Cutting-tool deflection compensation** — R

Use a calibrated tool/stickout/load model to propose bounded finishing-path corrections for tool bending, with the assumptions visible to the operator.

**F120. Condition-based spindle warmup** — H

Run an approved warmup sequence and evaluate temperature, vibration, and idle history before declaring the spindle ready for precision work.


## 121–130: Machine measurement

**F121. Interactive spindle-tramming assistant** — H

Take indicator or probe measurements and show which mounting adjustment to make, in which direction, and by approximately how much.

**F122. Circular-interpolation diagnostic tests** — H

Run controlled circles with a ballbar or other suitable measurement system and separate measured contour error from the commanded path.

**F123. Direction-dependent probe calibration** — H

Characterize probe triggering from different approach directions and apply calibrated corrections rather than assuming identical behavior in every direction.

**F124. Tool-runout measurement** — H

Measure the rotating tool or holder, record runout against that assembly, and flag an unacceptable setup before a precision operation.

**F125. Three-plane squareness calibration**

Measure XY, XZ, and YZ skew separately and generate bounded geometry corrections. Klipper’s documented skew correction provides an existing example of this capability.

**F126. Best-fit setup for castings and rough blanks** — H, R

Measure an irregular blank and find a proposed part placement that leaves sufficient machining allowance on all critical surfaces.

**F127. Clamp-distortion measurement** — H

Compare selected reference points before and after tightening the workholding to identify where the fixture is bending the part.

**F128. Measurement-confidence reporting**

Attach repeatability and calibration uncertainty to inspection results, so a screen displaying four decimal places does not imply that accuracy.

**F129. Spindle-bearing health trending** — H, R

Compare controlled no-cut vibration measurements over time and flag developing changes separately from cutting chatter.

**F130. Verified lubrication delivery** — H

Confirm lubricant reaches monitored circuits, track consumption against axis travel, and identify failed delivery rather than merely counting pump commands.


## 131–140: Industrial interfaces

**F131. Voltage readings at field terminals** — H

Show the measured voltage at supported input and supply terminals, helping distinguish “the switch is off” from “the sensor has no power.”

**F132. Individually protected output branches** — H

Measure load current, detect overloads, isolate the affected branch, and identify the connected device while initiating the configured machine fault response.

**F133. Broken-wire and short-circuit detection** — H

Use supported supervised input circuits to distinguish a legitimate switch state from an open cable or shorted pair.

**F134. Configurable PNP/NPN sensor inputs** — H

Support documented sourcing and sinking sensor configurations through rated interface hardware, with changes restricted to a disarmed setup state.

**F135. Plug-in wiring-harness tester** — H

Test disconnected harnesses for swapped pins, shorts, continuity, and intermittent connections before attaching expensive drives or sensors.

**F136. EtherCAT servo integration module** — H, R

Add a supported digital-drive backend with explicit drive profiles, feedback mapping, timing qualification, and fault handling—not an unexplained Ethernet socket.

**F137. Absolute-encoder interface modules** — H

Support defined protocols such as SSI or BiSS-C, including encoder status checks and a verified procedure for establishing machine position.

**F138. Replaceable field-I/O protection cartridges** — H

Put vulnerable interface and protection components on serviceable modules so one damaged field connection does not require replacing the entire controller.

**F139. Electrical-noise correlation tests** — H, R

During controlled testing, correlate unexpected input transitions or communication errors with VFD starts, contactor switching, and other electrical events.

**F140. Vertical-axis brake verification** — H

Test the holding and release sequence under controlled conditions and detect disagreement between brake commands and available feedback. Keep required safety functions in appropriate hardware.


## 141–150: Operator tools

**F141. Teach-and-repeat programming**

Jog through a sequence, capture meaningful points and actions, then edit and preview the generated program before allowing automatic execution.

**F142. Virtual stops for manual machining**

Set temporary approach limits and endpoints for manual facing, drilling, or positioning without rewriting the machine’s permanent travel limits.

**F143. Augmented camera setup view** — H, R

Overlay work-coordinate axes, fixture outlines, and selected toolpath features on a calibrated live camera image, with registration uncertainty visible.

**F144. Dedicated manual-DRO mode** — H

Use installed scales as a digital readout while motion outputs remain positively disabled, allowing the same system to support manual machine operation.

**F145. Visual program-revision comparison**

Highlight changed toolpaths, depths, feeds, tools, and offsets between an approved program and a replacement file before loading it.

**F146. G-code macro debugger**

Step through macros in simulation, inspect variables and branches, set breakpoints, and identify the exact condition causing an unexpected move.

**F147. Transactional work-offset editing**

Preview and approve a group of offset changes together, preserve the previous set, and allow reversal while halted without confusing that with reversing physical motion.

**F148. Common-tool batching across fixtures** — R

Group proven-independent operations by tool across multiple workpieces while preserving each part’s required operation order.

**F149. Oversized-tool magazine management** — H

Reserve adjacent pockets around large cutters and check the permitted tool arrangements before a carousel or rack movement.

**F150. Resource-controlled local graphics**

Limit memory and CPU consumption by CAD import, previews, and optional applications; defer heavy work rather than letting it consume unrestricted controller resources.


## 151–160: Specialized printing

**F151. Actual nozzle-pressure feedback** — H, R

Regulate extrusion using measured melt pressure rather than relying exclusively on a predictive pressure-advance model.

**F152. Continuous material-ratio blending** — H, R

Coordinate multiple material feeds to produce calibrated composition or color gradients within a toolpath, including transport-delay compensation.

**F153. Pellet-extruder control** — H, R

Coordinate auger speed, melt-zone temperatures, pressure, and measured delivery for supported pellet-fed printheads.

**F154. Continuous-fiber placement** — H, R

Synchronize fiber feeding, cutting, and consolidation with the print path, including allowable bend radii and termination locations.

**F155. Embedded-insert workflow** — H

Pause at planned cavities, guide insertion of nuts, magnets, or electronics, verify placement, and check nozzle clearance before continuing.

**F156. Directional material-shrinkage compensation** — R

Apply a calibrated material/process model to the prepared geometry, distinguishing directional shrinkage from machine squareness or positioning errors.

**F157. Layer-by-layer dimensional inspection** — H, R

Scan the growing part and compare its geometry with the expected layer, then flag accumulated height or shape errors before completion.

**F158. Active anti-ooze nozzle control** — H

Coordinate a supported shutoff valve or needle mechanism with extrusion and travel, including verified opening delays and pressure release.

**F159. Toolpath-aware part cooling**

Adjust cooling and minimum revisit time based on the local feature and deposition schedule rather than using one fan percentage for an entire layer.

**F160. Filament-diameter and ovality compensation** — H

Measure filament cross-section upstream and correct the corresponding extrusion volume after accounting for travel delay to the nozzle.


## 161–170: Advanced laser processing

**F161. Transactional variable-data marking**

Generate names, dates, serial numbers, or CSV-driven text, then record each item as pending, completed, or uncertain. Variable-data generation is established; reliable completion accounting would be your addition.

**F162. Read-back verification of markings** — H, R

Scan the finished barcode, QR code, or supported text and compare its contents against what the job requested.

**F163. Coordinated galvo-and-gantry processing** — H, R

Combine fast local mirror motion with a larger mechanical stage, maintaining a shared coordinate system through field transitions.

**F164. Guided galvo-lens correction** — H

Mark and measure a calibration pattern, calculate distortion corrections, and save them against the installed lens. LightBurn documents this general calibration workflow.

**F165. Source-specific pulse control** — H

Expose supported pulse duration, repetition frequency, and power combinations for compatible laser sources, rejecting combinations outside the source’s documented operating envelope.

**F166. Calibrated depth engraving** — R

Convert a relief model into removal passes using a measured material/process response, instead of assuming grayscale value directly equals engraving depth.

**F167. Conveyor “marking on the fly”** — H, R

Track a conveyor encoder and continually transform marking coordinates so supported parts can be marked while moving.

**F168. Color-marking recipe development** — H, R

Generate controlled test matrices and record measured results under consistent lighting to help reproduce color effects on suitable materials.

**F169. Oversized-sheet tiling** — H

Divide a design into reachable sections and guide material repositioning, including overlap checks and explicit registration error at each seam.

**F170. Markerless batch placement** — H, R

Locate recognizable blanks scattered across a tray, propose their poses, and place the approved artwork on each without dedicated fiducial marks.


## 171–180: Other fabrication processes

**F171. Tangential-knife control**

Rotate a knife to follow the cutting direction, compensate its geometry, and lift or swivel at corners according to the material.

**F172. Oscillating-knife process control** — H

Coordinate reciprocation, feed, and corner behavior for supported foam, gasket, or corrugated-material cutting heads.

**F173. Four-axis hot-wire cutting** — H, R

Coordinate both ends of a heated wire for tapered shapes, including calibrated kerf, wire-lag, and sag compensation.

**F174. EDM gap-control mode** — H, R

Adjust feed and withdrawal from isolated discharge feedback while a dedicated power unit handles pulse generation.

**F175. Two-component dispensing** — H

Maintain the required resin/hardener delivery ratio, monitor dispensing conditions, and track mixer dwell time and approved purge procedures.

**F176. Pick-and-place operation** — H, R

Import component placement data, coordinate feeders and vacuum pickup, and use vision to correct supported component alignment.

**F177. Verified adhesive or solder-paste deposition** — H, R

Inspect deposited dots or beads and compare their position and size against the required pattern before proceeding.

**F178. Welding-seam tracking** — H, R

Use a suitable sensor to adjust the programmed weld path within a qualified welding-cell configuration, with bounded correction and lost-seam handling.

**F179. Plasma bevel preparation** — H, R

Generate supported tilted-torch paths with angle-dependent offsets and process settings for weld-preparation edges.

**F180. Waterjet taper and trail compensation** — H, R

Coordinate supported head tilt and feed using a calibrated cutting model, with pressure and abrasive delivery handled by dedicated equipment.


## 181–190: Machine and shop services

**F181. Shared-compressor coordination** — H

Request the pressure and airflow needed for the next operation, delay starting until available, and coordinate competing machine demands through a defined shop interface.

**F182. Automatic dust-extraction zoning** — H

Open the appropriate blast gates for the active machine or tool, verify the requested airflow, and close unused branches.

**F183. Coolant-mixture monitoring** — H

Record concentration, temperature, and tank level, then guide or control an approved replenishment process rather than adding water by guesswork.

**F184. Automatically aimed coolant nozzles** — H

Position motorized nozzles according to the selected tool and cutting location, with teachable aim points and collision limits.

**F185. Chip-conveyor jam management** — H

Detect abnormal conveyor load, perform only an approved bounded recovery sequence, and stop before repeated retries damage the mechanism.

**F186. Geometry-aware vacuum zoning** — H, R

Select workholding zones based on stock placement and the cutting sequence, maintaining verified holding conditions as pieces become separated.

**F187. Shop electrical-load scheduling** — H

Stagger approved heater, compressor, and spindle startup requests within a configured power budget, without unexpectedly interrupting an active process.

**F188. Part genealogy**

Link each finished part to its material lot, job revision, machine configuration, tools, calibration state, and recorded inspection results.

**F189. Actual cost-per-good-part reporting**

Combine measured cycle time, energy, material use, tool consumption, and scrap using user-entered cost rates rather than reporting only machine hours.

**F190. Cross-machine operation tracking**

Carry a part’s production record from printing to milling to engraving, preventing an unfinished or incorrectly revised part from silently advancing to the next operation.


## 191–200: Maintainability and extension

**F191. Sandboxed extensions**

Give plugins explicit permissions and resource limits; deny direct access to motion outputs unless commands pass through the controller’s authorized interface.

**F192. Signed production jobs**

Verify who approved a job and whether its toolpaths, settings, or setup requirements changed afterward, without requiring a cloud account.

**F193. Local operator permissions** — configuration foundation

Separate setup, operation, maintenance, and development privileges so an operator can run approved work without accidentally changing machine geometry.

**F194. Consent-based remote support**

Start remote sessions read-only, make access visible and time-limited, and require local authorization for permitted control actions.

**F195. Controlled configuration experiments** — configuration foundation

Compare candidate settings through the same bounded test, retain the measured results, and activate a selected configuration only while disarmed.

**F196. Visual HAL signal editor**

Connect supported control components graphically, display signal types and execution relationships, and flag incompatible connections or problematic dependency loops.

**F197. Automated hardware regression testing** — H

Use a test fixture to verify supported inputs, outputs, encoder channels, pulse timing, and fault behavior after hardware or firmware changes.

**F198. Offline fault replay** — R

Feed recorded input events into a simulation to investigate a failure and test a proposed fix without energizing the real machine.

**F199. Expansion-module development kit** — first plasma module demonstration

Publish interface definitions, example drivers, virtual devices, and conformance tests so third parties can build compatible accessories without reverse-engineering the board.

**F200. Capability-based job exchange** — configuration foundation

Attach explicit machine requirements to a portable job package, explain incompatibilities before transfer, and require validated conversion rather than blindly replaying another machine’s G-code.

