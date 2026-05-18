# Trend Analysis

The `--trend` flag computes the **rate-of-change** of log entries across
consecutive time buckets, helping you spot sudden spikes or drops in activity.

## Usage

```
logslice parse app.log --trend [OPTIONS]
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--trend` | off | Enable trend analysis |
| `--trend-resolution` | `minute` | Bucket size: `minute`, `hour`, `day` |
| `--trend-level LEVEL` | all levels | Restrict to a specific log level |
| `--trend-json` | off | Emit JSON instead of plain text |

## Examples

### Plain output (per-minute)

```
$ logslice parse app.log --trend
[trend] resolution=minute  level=ALL
  Bucket                Count    Delta    Delta%
  ------------------------------------------------
  2024-03-10T14:01          3       --        --
  2024-03-10T14:02          7       +4   +133.3%
  2024-03-10T14:03          2       -5    -71.4%
```

### Filter by level

```
$ logslice parse app.log --trend --trend-level ERROR --trend-resolution hour
[trend] resolution=hour  level=ERROR
  Bucket                Count    Delta    Delta%
  ------------------------------------------------
  2024-03-10T13             1       --        --
  2024-03-10T14             4       +3   +300.0%
```

### JSON output

```
$ logslice parse app.log --trend --trend-json
{
  "resolution": "minute",
  "level_filter": null,
  "points": [
    {"bucket": "2024-03-10T14:01", "count": 3, "delta": null, "delta_pct": null},
    {"bucket": "2024-03-10T14:02", "count": 7, "delta": 4, "delta_pct": 133.33}
  ]
}
```

## Notes

- Entries **without a timestamp** are silently ignored.
- `delta_pct` is `null` when the previous bucket had zero entries (division by zero).
- The first bucket always has `delta: null` and `delta_pct: null`.
