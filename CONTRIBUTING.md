# Contributing to Repo Radar

Contributions should make repository feedback more accurate, actionable, or portable.

## Local verification

```bash
python -m unittest discover -s tests -v
python -m repo_radar . --fail-under 100
```

New checks must be deterministic, avoid executing audited project code, and explain both the evidence found and the action a maintainer can take. Add tests for complete and incomplete repositories. Keep runtime dependencies at zero unless a proposed check cannot safely use the standard library.

Pull requests should document score-weight changes because they may affect CI thresholds in downstream projects.
