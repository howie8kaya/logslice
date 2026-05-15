# Timeline

The **timeline** feature groups log entries into fixed-width time buckets and
displays an activity bar chart. It is useful for spotting bursts of errors or
unusual quiet periods at a glance.

## CLI Usage

```
logslice [options] --timeline [--timeline-bucket BUCKET] [--timeline-fill] [--timeline-json]
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--timeline` | off | Enable timeline mode |
| `--timeline-bucket` | `minute` | Bucket size: `second`, `minute`, `hour`, `day` |
| `--timeline-fill` | off | Insert zero-count buckets for missing intervals |
| `--timeline-json` | off | Output as JSON instead of a bar chart |

## Examples

### Plain bar chart (per hour)

```
logslice app.log --timeline --timeline-bucket hour
```

Output:

```
2024-03-01 08:00:00  ########                                  12
2024-03-01 09:00:00  ########################################  60
2024-03-01 10:00:00  ####################                      30
```

### JSON output with gap filling

```
logslice app.log --timeline --timeline-bucket minute --timeline-fill --timeline-json
```

Output:

```json
[
  {"timestamp": "2024-03-01T09:00:00", "count": 5, "levels": {"INFO": 4, "WARN": 1}},
  {"timestamp": "2024-03-01T09:01:00", "count": 0, "levels": {}},
  {"timestamp": "2024-03-01T09:02:00", "count": 3, "levels": {"ERROR": 3}}
]
```

## Programmatic API

```python
from logslice.timeline import build_timeline

buckets = build_timeline(entries, bucket="hour", fill_gaps=True)
for b in buckets:
    print(b.timestamp, b.count, b.levels)
```

### `build_timeline(entries, bucket="minute", fill_gaps=False)`

Returns a sorted list of `TimelineBucket` objects.

- **entries** – list of `LogEntry` objects (entries without timestamps are skipped)
- **bucket** – one of `second`, `minute`, `hour`, `day`
- **fill_gaps** – when `True`, zero-count buckets are inserted for every missing
  interval between the first and last observed timestamp

### `TimelineBucket`

| Attribute | Type | Description |
|-----------|------|-------------|
| `timestamp` | `datetime` | Floor of the bucket interval |
| `count` | `int` | Number of entries in this bucket |
| `levels` | `dict[str, int]` | Per-level counts within this bucket |
| `as_dict()` | `dict` | JSON-serialisable representation |
