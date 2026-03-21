# CAST Default Security Policy
# Blocks on CRITICAL findings (SARIF level "error").
# Activate: set CAST_POLICY=default (or leave unset — this is the default).

package main

import future.keywords.if
import future.keywords.in

# Deny if any SARIF result carries "error" level, which tools map to CRITICAL severity.
deny[msg] if {
    run := input.runs[_]
    result := run.results[_]
    result.level == "error"
    tool := run.tool.driver.name
    msg := sprintf("[CRITICAL] %s — %s (rule: %s)", [
        tool,
        result.message.text,
        result.ruleId,
    ])
}
