# Log Clustering

The `--cluster` flag groups similar log lines together by replacing variable
tokens (numbers, IP addresses, hex strings, timestamps) with a `<VAR>`
placeholder and then bucketing lines that share the same resulting *signature*.

## Quick start

```bash
# Print clusters in human-readable form
logslice app.log --cluster

# Only show patterns that appear at least 5 times
logslice app.log --cluster --cluster-min 5

# Output as JSON (useful for piping to jq)
logslice app.log --cluster --cluster-format json | jq '.[0]'

# Ignore log level when building the signature
logslice app.log --cluster --cluster-ignore-level
```

## CLI options

| Flag | Default | Description |
|---|---|---|
| `--cluster` | off | Enable clustering mode |
| `--cluster-min N` | 1 | Minimum entries per cluster to display |
| `--cluster-ignore-level` | off | Exclude log level from the cluster key |
| `--cluster-format {text,json}` | text | Output format |

## Text output format

```
[    42x]  [INFO] user <VAR> logged in
           sample: 2024-01-15 12:00:01 INFO user 7 logged in

[     3x]  [ERROR] disk full on /dev/<VAR>
           sample: 2024-01-15 11:58:44 ERROR disk full on /dev/sda1
```

## JSON output format

```json
[
  {
    "pattern": "[INFO] user <VAR> logged in",
    "count": 42,
    "sample": "2024-01-15 12:00:01 INFO user 7 logged in"
  }
]
```

## Python API

```python
from logslice.cluster import cluster_entries

clusters = cluster_entries(entries, min_count=5, use_level=True)
for c in clusters:
    print(c.count, c.pattern)
```
