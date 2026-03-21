# CAST Permissive Security Policy
# Never blocks the pipeline — all findings are reported as warnings only.
# Useful for audit/visibility runs without enforcement.
# Activate: set CAST_POLICY=permissive

package main

import future.keywords.if
import future.keywords.in

# Emit warnings for all findings but never deny (no deny rules).
warn[msg] if {
    run := input.runs[_]
    result := run.results[_]
    tool := run.tool.driver.name
    msg := sprintf("[%s] %s — %s (rule: %s)", [
        upper(result.level),
        tool,
        result.message.text,
        result.ruleId,
    ])
}
