# Analysis workflows / 分析工作流

## Strict comparison plan

```json
{
  "models": ["MSIS2", "MSIS00"],
  "inputs": {
    "year": 2020,
    "day_of_year": 172,
    "utsec": 43200,
    "alt_km": {"start": 100, "stop": 500, "step": 10, "num": null},
    "lat_deg": 35,
    "lon_deg": 116,
    "f107a": 150,
    "f107": 150
  },
  "quantities": ["T_local_K", "O_cm3"],
  "baseline": "MSIS2",
  "metrics": [
    "bias",
    "mae",
    "rmse",
    "max_abs_difference",
    "mean_relative_difference_percent",
    "mean_ratio"
  ],
  "language": "zh",
  "title": "MSIS 温度与原子氧对比"
}
```

Run an installed package:

```text
upperatmpy-analysis compare --plan plan.json --format markdown --output-file report.md
upperatmpy-analysis compare --plan plan.json --format json --output-file report.json
```

Programmatic equivalent:

```python
import json
from upperatmpy_analysis import AnalysisPlan, execute_plan

with open("plan.json", encoding="utf-8") as stream:
    plan = AnalysisPlan.from_dict(json.load(stream))
report = execute_plan(plan)
print(report.to_markdown())
```

## One-factor sensitivity

Hold all other inputs scalar and vary one parameter:

```text
upperatmpy-analysis sensitivity --model MSIS2 --base-inputs base.json --parameter f107 --values 70,100,150,200 --quantities T_local_K,O_cm3
```

This reports the sampled outputs, minimum, maximum, range, endpoint absolute
change, and endpoint percent change. It does not infer causal importance from a
single-factor sweep.

## Natural-language planning

The deterministic rule planner refuses missing inputs instead of inventing
them:

```text
upperatmpy-analysis plan --query "比较 MSIS2 和 MSIS00：年份 2020，第 172 天，12:00 UT，高度 100 到 500 km，步长 10 km，纬度 35，经度 116，F10.7a=150，F10.7=150，比较局地温度"
```

For optional AI planning and evidence-only explanation:

```text
upperatmpy-analysis ask --provider openai --ai-model YOUR_MODEL --query "..."
```

This mode requires the `upperatmpy[ai]` optional dependency and normal provider
credentials. Do not put API keys in plans, reports, prompts, or the Skill.

## Metric interpretation

For candidate `C` and baseline `B`, the engine computes `C - B`.

- `bias`: mean signed difference.
- `mae`: mean absolute difference.
- `rmse`: root mean squared difference.
- `max_abs_difference`: largest absolute point difference.
- `mean_relative_difference_percent`: mean `(C-B)/abs(B)*100` over points with
  non-zero baseline.
- `mean_ratio`: mean `C/B` over points with non-zero baseline.

JSON uses `null` where a point ratio or relative difference has a zero
denominator. Summary metrics remain finite.
