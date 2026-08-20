---
name: upperatmpy-atmospheric-analysis
description: "Use when a user asks to choose, compare, sensitivity-test, validate, or explain compatible UpperAtmPy neutral-atmosphere or internal-geomagnetic models, or requests a reproducible bilingual Chinese/English atmospheric analysis report. Use deterministic UpperAtmPy calculations for every scientific value; optional AI may only plan and explain evidence. Do not use for unrelated weather forecasting or to compare scientifically incompatible model groups."
---

# UpperAtmPy Atmospheric Analysis

Produce a reproducible analysis from the public `upperatmpy_analysis` API or the
`upperatmpy-analysis` CLI. Match the user's Chinese or English unless they ask
for another language.

## Workflow

1. Locate the UpperAtmPy checkout or installed package. Confirm that
   `upperatmpy-analysis catalog` works before attempting native calculations.
2. Read [model groups](references/model-groups.md) to select models from one
   compatibility group and identify required inputs and common quantities.
3. Extract only values the user supplied. Ask for any required scientific
   inputs that are still missing; never invent date, location, solar flux,
   altitude, or model version.
4. Create an `AnalysisPlan`. Validate the plan before loading model DLLs.
5. Execute deterministic comparison or one-factor sensitivity analysis. Do not
   use an LLM, calculator improvisation, or web snippets to produce model values.
6. Return the answer-first finding, metric table, validity-domain warnings,
   citations, and reproducible code. Retain evidence keys such as
   `[MSIS00:T_local_K]` in AI-assisted explanations.

Read [analysis workflows](references/analysis-workflows.md) when constructing a
plan, choosing CLI flags, or interpreting metrics.

## Scientific boundaries

- Compare only models in the same catalog group. A neutral-atmosphere result
  and a geomagnetic result may be used in one broader study, but they are not
  interchangeable quantities and must not be differenced.
- Use the catalog's validity intersection. Do not extrapolate to make models
  overlap.
- Coordinate alignment uses exact shared coordinates and performs no hidden
  interpolation.
- Treat a difference as an observation, not proof of its physical cause.
- Preserve all warnings for historical-epoch geomagnetic models and restricted
  altitude ranges.

## Optional AI

Default to the rule-based planner and deterministic explainer. Use the optional
OpenAI provider only when the user explicitly requests AI planning or narrative
interpretation and the environment is configured with `upperatmpy[ai]`, an API
key, and an explicit model name. The AI may generate a strict plan or explain a
compact evidence object; it must never calculate or alter scientific values.

## Source-checkout execution

When the package is installed, prefer the public CLI. In an uninstalled source
checkout, add the repository `src` directory to Python's import path for the
single command, then run `python -m upperatmpy_analysis.cli ...`. Do not copy
private repository files into the Skill and do not install this Skill into a
local Skills directory as part of repository development.
