# Deploy Academic Sludge Line

Academic Sludge Line is a local Python CLI pipeline. Deploying it means:

1. Install the `asl` command in a Python environment.
2. Verify the command works.
3. Create a paper workspace.
4. Run the pipeline in offline mode or with configured model keys.

It does not require a database, queue, Docker, cloud service, or web server.
The web UI is optional and runs locally.

## One-Command Local Deploy

From the repository root:

```bash
sh scripts/deploy_local.sh
```

This creates `.venv/`, installs the package in editable mode, verifies
`asl --version`, and runs an offline smoke test in a temporary directory.

After the script finishes:

```bash
. .venv/bin/activate
asl init \
  --slug demo-policy-paper \
  --title "Demo Policy Paper" \
  --topic "a policy question that still needs verified evidence" \
  --brief-file examples/topic_brief.md

asl run papers/demo-policy-paper --cycles 1 --offline
```

Open the generated HTML report:

```bash
open papers/demo-policy-paper/v1/html/index.html
```

On Linux, use `xdg-open` instead of `open`.

## Manual Deploy

Use this path when you do not want to run the script:

```bash
git clone https://github.com/MattSureham/academic-sludge-line.git
cd academic-sludge-line
python3.11 -m venv .venv  # or any Python 3.10+ command
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
asl --version
```

If `python3` is not available, install Python 3.10 or newer first.

## Optional LLM Mode

Offline mode works without API keys:

```bash
asl run papers/demo-policy-paper --cycles 1 --offline
```

To call an LLM, configure the relevant key and omit `--offline`:

```bash
export OPENAI_API_KEY="..."
asl run papers/demo-policy-paper --cycles 1 --model openai:gpt-4.1-mini
```

If an API call fails, ASL records the error and falls back to offline templates.

## Optional Local UI

Start the local UI:

```bash
. .venv/bin/activate
asl ui --open
```

Without `--open`, visit:

```text
http://127.0.0.1:8765
```

## Optional Document Loading

The core pipeline has no runtime dependencies beyond Python. Loading PDFs, DOCX,
and mixed document folders is optional and uses the adjacent `smart-loader`
project when available. If it is not available, ASL still runs with briefs and
plain Markdown/text inputs.

## Agent Instructions

When an automation agent is asked to "deploy this pipeline", do this:

1. Run `sh scripts/deploy_local.sh`.
2. If the user wants a real project, run the demo offline cycle shown above.
3. Report the generated `papers/<slug>/v1/html/index.html` path for that real project.

Do not provision cloud infrastructure unless explicitly requested.
