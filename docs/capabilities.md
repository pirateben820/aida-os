# Capabilities — Permission System

## What it is
Every agent action is gated by a capability check.
No agent gets unrestricted access. Default is **deny**.

## How it works
1. `capabilities/model.py` loads `config/agents.yaml` into a `CapabilityRegistry`
2. Module-level singleton: `from capabilities.model import registry`
3. `registry.check(agent, capability)` → bool
4. `registry.require(agent, capability)` → raises `PermissionError` if denied

## Rule
If a capability is not in `can` it is **forbidden**, even if it's not in `cannot`.
The `cannot` list is for making intent explicit — it does not change the default.

## Current capability names

| Capability | Who has it |
|---|---|
| `read_files` | archon |
| `write_files` | archon |
| `execute_shell_sandboxed` | archon |
| `git_operations` | archon |
| `read_user_memory` | hermes |
| `write_user_memory` | hermes |
| `restart_services` | sysadmin |
| `manage_containers` | sysadmin |
| `read_firewall_rules` | security |
| `write_firewall_rules` | security |
| `web_search` | research |
| `network_access_read` | research |
| `read_storage_metrics` | storage |
| `create_backups` | sysadmin, storage |

## Adding a new capability
1. Add the action to `can` in `config/agents.yaml` for the relevant agent
2. Call `self.require("new_capability")` before executing the action in agent code
3. Never skip the check

## Common failures

| Error | Cause | Fix |
|---|---|---|
| `PermissionError` | Capability not in `can` | Add to agents.yaml or don't do it |
| `Unknown agent` | Agent name not in agents.yaml | Add agent entry to agents.yaml |
