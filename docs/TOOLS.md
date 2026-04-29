# External Tool Configuration

Gaming Laptop Checker keeps benchmark tools outside the repository.

Configure tools in `config.py` under `TOOL_MANIFEST`. Each entry can define:

- `display_name`
- `url`
- `homepage`
- `exe_patterns`
- `archive`
- `required_for`

If a tool is missing or not configured, its benchmark module returns `SKIP` with a clear note in the report.

This behavior is intentional because several benchmark vendors require EULA acceptance, activation, or installer-specific flows.
