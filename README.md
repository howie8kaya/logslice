# logslice

Fast log file parser and filter utility with regex support and structured output formats.

## Installation

```bash
pip install logslice
```

## Usage

Parse and filter log files with regex patterns and export results in structured formats.

```bash
# Filter logs by pattern and output as JSON
logslice parse app.log --pattern "ERROR|WARN" --output json

# Slice logs by time range
logslice parse app.log --from "2024-01-01 08:00" --to "2024-01-01 09:00"

# Use in Python
from logslice import LogParser

parser = LogParser("app.log")
results = parser.filter(pattern=r"ERROR", output_format="json")
print(results)
```

### Options

| Flag | Description |
|------|-------------|
| `--pattern` | Regex pattern to match log lines |
| `--output` | Output format: `json`, `csv`, or `text` (default) |
| `--from` | Start timestamp for time-based filtering |
| `--to` | End timestamp for time-based filtering |
| `--tail` | Process only the last N lines |

## License

MIT