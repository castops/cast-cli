# CAST Strict Security Policy
# Blocks on HIGH or CRITICAL findings (SARIF level "error" or "warning").
# Activate: set CAST_POLICY=strict

package main

import future.keywords.if
import future.keywords.in

# Deny on CRITICAL findings (SARIF "error")
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

# Deny on HIGH findings (SARIF "warning")
deny[msg] if {
    run := input.runs[_]
    result := run.results[_]
    result.level == "warning"
    tool := run.tool.driver.name
    msg := sprintf("[HIGH] %s — %s (rule: %s)", [
        tool,
        result.message.text,
        result.ruleId,
    ])
}
