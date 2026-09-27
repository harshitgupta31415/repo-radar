# Repo Radar

Repo Radar turns a project directory into a clear, actionable repository-health report. It checks the basics that make an open-source project understandable and maintainable without uploading source code or calling an external service.

## What it checks

- README and licence presence
- generated-file protection through `.gitignore`
- GitHub Actions configuration
- automated test coverage signals
- dependency manifests or lockfiles
- unexpectedly large source files

The result is available as readable terminal output, JSON for automation, or Markdown for issue and pull-request summaries.

## Quick start

```bash
python -m repo_radar /path/to/project
python -m repo_radar . --format markdown --output health.md
python -m repo_radar . --format json --fail-under 80
python -m repo_radar --version
```

Install it as a local command when developing the package:

```bash
python -m pip install -e .
repo-radar .
```

`--fail-under` returns a non-zero exit status when the score is below the requested percentage, making the tool suitable for CI. Use `--max-file-kb` to adjust the large-file threshold.

## Example

```text
Repo Radar — /work/my-project
Score: 80/100 (80%)

[PASS] Project documentation — Found README.md
[MISS] Continuous integration — No GitHub Actions workflow found
       Fix: Run tests or validation automatically for pushes and pull requests.
```

## Development

The project uses only the Python standard library at runtime.

```bash
python -m unittest discover -s tests -v
python -m repo_radar . --fail-under 100
```

## Privacy

Repo Radar inspects file names and sizes locally. It does not read environment values, transmit files, or execute project code.

## Licence

[MIT](LICENSE)
