# Kie AI Multimedia Orchestrator

A reusable **Claude Code skill** for orchestrating image, video, music, speech, and multi-step multimedia generation through the [Kie AI](https://kie.ai/) API.

The skill is intentionally **model-agnostic and docs-driven**. Instead of baking in model IDs, endpoints, or payload schemas that can become stale, it instructs Claude Code to read the current Kie AI documentation, select an appropriate model for each modality, build the request, handle asynchronous task execution, download results, and fall back when a model is degraded or unavailable.

> This is a community project and is not affiliated with or endorsed by Anthropic or Kie AI.

## What it does

The skill can help Claude Code plan and execute workflows such as:

- text-to-image and image editing
- text-to-video and image-to-video
- AI music generation
- text-to-speech and voiceovers
- multi-step media pipelines such as image → video → music → local merge
- cost-aware drafts and fallbacks between currently available Kie AI models

It is designed around Kie AI's live documentation, because available models, API parameters, pricing, limits, and endpoints can change over time.

## Repository structure

```text
kie-ai-multimedia-orchestrator/
├── SKILL.md
├── scripts/
│   └── kie_client.py
├── evals/
│   └── evals.json
├── examples/
│   └── README.md
├── .gitignore
├── LICENSE
└── README.md
```

## Requirements

- [Claude Code](https://code.claude.com/docs/)
- Python 3
- `curl`
- a Kie AI account and API key
- optional: `ffmpeg` for locally combining generated audio and video

Claude Code must also be able to reach Kie AI's documentation and API endpoints.

## Install

### Personal skill — macOS, Linux, or WSL

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/cjgl23/kie-ai-multimedia-orchestrator.git \
  ~/.claude/skills/kie-ai-multimedia-orchestrator
```

### Personal skill — Windows PowerShell

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
git clone https://github.com/cjgl23/kie-ai-multimedia-orchestrator.git `
  "$HOME\.claude\skills\kie-ai-multimedia-orchestrator"
```

Claude Code discovers skills from the `skills/<name>/SKILL.md` structure. A personal installation under `~/.claude/skills/` makes the skill available across projects.

For a project-specific installation, place this repository under:

```text
<your-project>/.claude/skills/kie-ai-multimedia-orchestrator/
```

## Configure your Kie AI API key

Create your own API key in Kie AI. **Never commit it to GitHub or paste it into `SKILL.md`.**

macOS/Linux/WSL:

```bash
export KIE_API_KEY="your-api-key"
```

Windows PowerShell for the current session:

```powershell
$env:KIE_API_KEY="your-api-key"
```

The included helper reads `KIE_API_KEY` from the environment. It does not contain a hardcoded API key.

## Use it

Start Claude Code normally:

```bash
claude
```

Then describe the media outcome you want. For example:

```text
Create a cinematic 10-second trailer of a lone astronaut crossing a red desert
at dusk, with epic orchestral music. Use Kie AI and keep the cost reasonable.
```

Claude Code can select the skill automatically from its description. You can also invoke it explicitly:

```text
/kie-ai-multimedia-orchestrator
```

More prompts are available in [examples/README.md](examples/README.md).

## How the skill works

The workflow encoded in `SKILL.md` is:

1. **Decompose** the request into image, video, audio, and local-processing stages.
2. **Discover** current Kie AI capabilities from the live documentation.
3. **Select** a model for each modality based on the user's constraints.
4. **Build** model-specific prompts and payloads from the current docs.
5. **Run** Kie AI's asynchronous task lifecycle and download the results.
6. **Fallback** to an appropriate alternative when a model is degraded or fails for a model-side reason.
7. **Report** model choices, task IDs, assets, costs, uploads, and any fallbacks.

The skill deliberately avoids hardcoding Kie AI model IDs or API schemas in `SKILL.md`.

## Helper script

`scripts/kie_client.py` is a small generic task runner used after Claude Code has discovered the current endpoint and response fields from the Kie AI docs.

It can:

- create a generation task
- poll the documented status endpoint
- detect success or failure states
- extract generated asset URLs
- download generated files locally

Example shape:

```bash
python3 scripts/kie_client.py run \
  --base-url <base-url-from-current-docs> \
  --create-path <create-path-from-current-docs> \
  --status-path <status-path-from-current-docs> \
  --body-file request.json \
  --out ~/Downloads/kie-output
```

The placeholders are intentional. Use the values from the **current model documentation** rather than copying stale API details from an old example.

## Cost and privacy

Generation can consume Kie AI credits, especially video generation. The skill instructs Claude Code to:

- prefer lower-cost drafts when appropriate
- inspect credit usage where supported
- ask before obviously expensive multi-video or high-resolution runs
- avoid blindly resubmitting an asynchronous task after a timeout

Some workflows require uploading a local file so Kie AI can access it by URL. The skill tells Claude Code to check Kie AI's current upload documentation before doing so and to explain temporary storage/retention implications to the user.

Generated assets and temporary download URLs should be saved promptly because retention and URL lifetime are service-controlled and may change.

## Evals

`evals/evals.json` contains example evaluation prompts and assertions for checking core skill behavior, including:

- multimodal dependency planning
- live documentation lookup
- model-selection rationale
- asynchronous task handling
- fallback behavior
- dry-run behavior when no API key is available

These evals are development aids rather than guarantees that every third-party model or API behavior will remain unchanged.

## Security

- Never commit `KIE_API_KEY`.
- Treat generated or uploaded URLs according to the current Kie AI retention policy.
- Review generated payloads before running expensive jobs.
- Do not disable TLS certificate verification to work around network errors.
- Rotate an API key immediately if it is accidentally exposed.

## Updating

Because this is installed with Git, updating is straightforward:

```bash
cd ~/.claude/skills/kie-ai-multimedia-orchestrator
git pull
```

## License

MIT License. See [LICENSE](LICENSE).

## References

- Claude Code documentation: https://code.claude.com/docs/
- Kie AI documentation: https://docs.kie.ai/
- Kie AI model market: https://kie.ai/market
