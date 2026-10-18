# Independent shell review

The current shell was reviewed without editing its sources. The new handler
wraps the existing configuration web service; the original handler remains
responsible for Host/origin validation, session token, CSP and API actions.
Assets are restricted to exact routes and the workbench is rendered by that
same handler. No new transport, paid-provider invocation or physical backend
is introduced.

The homepage reads context and readiness, checks disconnected guards and
compares store ID, epoch, revision, generation, configuration SHA and draft
SHA. Unavailable/inconsistent status clears current evidence labels. The
workbench Home control uses the existing guarded save. Its one exception is
the exact untouched initial provisional template, allowing browsing to end
without initializing a machine or AI allowance. Edits and stale-save errors
continue through the shared service guard; errors preserve answers and prevent
navigation. Route selection waits for initial context and introduces no
independent setup state.

No remaining actionable defect was found in these reviewed boundaries.
[The receipt](shell-review-r01.json) binds the actual source and supporting
evidence. Five HTTP contract tests were executed by root, six inert Node VM
regressions by the hardware reviewer, and four real browser viewports plus
service-loss/restart and edited/untouched navigation by root. Those are
attributed execution evidence, not browser actions repeated by this reviewer.
This reviewer separately executed the staged shell on isolated Linux through
the OS run-r03 control, checking inherited Host/token/CSP and unchanged
read-only existing settings.

The shell remains a development interface. Its machine illustration and
fitted-interface inventory are not machine observation or readiness evidence.
No physical boot, target graphics performance, physical commissioning,
firmware qualification or motion authority follows from this review.
