---
name: nexalloy-patch-importer
description: >-
  A reusable Antigravity skill that imports Morphe/ReVanced patch sources, translates them into NexAlloyNext Xposed hooks, builds `.nxb` bundles, and optionally creates per‑app standalone bundles.
version: 1.0.0
---

# Overview
The **nexalloy‑patch‑importer** skill automates the full lifecycle of integrating third‑party patch repositories into the NexAlloyNext ecosystem.

It provides a single CLI (`nexalloy_importer.py`) with the following high‑level sub‑commands:

| Sub‑command | Purpose |
|-------------|---------|
| `scan`      | Detects all applications and associated patch files in a given source repository. |
| `import`    | Translates detected patches into Kotlin runtime hooks, adds them to a target bundle, and updates `NOTICE`. |
| `build`     | Invokes Gradle to assemble the specified bundle, handling compile‑time failures with fail‑safe hooks. |
| `pipeline`  | End‑to‑end orchestration: clone source → scan → import → build → produce a JSON report.

The skill is installed under `.agents/skills/nexalloy-patch-importer/` and can be invoked from the Antigravity terminal with `uv run ...`.

---

## Directory Layout
```
.nexalloy-patch-importer/
├─ SKILL.md               # ← this file
└─ scripts/
   └─ nexalloy_importer.py   # CLI implementation
```
The skill does **not** require external Python dependencies beyond the project’s existing runtime.

---

## CLI Usage
```bash
# Basic pipeline (default bundle "nxb_extended")
uv run .agents/skills/nexalloy-patch-importer/scripts/nexalloy_importer.py \
    pipeline \
    --url https://morphe.software/add-source?github=dh6k/morphe-patches

# Specify a custom bundle name
uv run .agents/skills/nexalloy-patch-importer/scripts/nexalloy_importer.py \
    pipeline \
    --url https://morphe.software/add-source?github=dh6k/morphe-patches \
    --bundle nxb_extended

# Generate per‑app standalone bundles
uv run .agents/skills/nexalloy-patch-importer/scripts/nexalloy_importer.py \
    pipeline \
    --url https://morphe.software/add-source?github=dh6k/morphe-patches \
    --standalone
```

### Options
- `--url <MORPHE_URL>` – URL pointing to a Morphe patch source (required).
- `--bundle <NAME>` – Target bundle module name (default: `nxb_extended`).
- `--standalone` – When supplied, a separate Gradle module is created under `bundles/<app‑name>` for each detected app.
- `--output <PATH>` – Path to write a JSON report summarising imported apps, any compile failures, and the location of the final `.nxb`.
- `--max‑retries <N>` – Maximum retry attempts for compile‑time failures (default = 3).

---

## How It Works
1. **Parse URL** – Extracts the GitHub `owner/repo` slug from any Morphe URL or plain `owner/repo` string.
2. **Canonicalise** – Calls the GitHub API (rate‑limited) to resolve redirects and obtain the canonical repository name.
3. **Clone** – Performs a shallow `git clone --depth 1` into a temporary directory.
4. **Scan** – Walks the cloned repo, locating Kotlin patch files (`*Patch.kt`) and optional `Constants.kt` for package names / target versions.
5. **Translate** – For each patch:
   - Generates a Kotlin `runCatching { … }` block that wraps the original hook.
   - On failure, logs via `PatcherLog.info { "<Hook> skipped: $it" }` – this satisfies the *fail‑safe runtime hook* requirement.
   - If the patch cannot be auto‑translated, a stub hook with the same name is emitted that only logs the skip.
6. **Bundle Integration** – Updates the target bundle’s `NxbExtendedPatches.kt` (or a generated per‑app file) and appends the new entries to `NOTICE`.
7. **Build & Retry** – Executes `./gradlew :bundles:<bundle>:assembleBundle`.
   - On compilation errors, the offending Kotlin file is identified, the failing block is commented out, a safe stub is inserted, and the build is retried up to `--max‑retries`.
   - All compiler stack traces are captured and reported in the final JSON output.
8. **Release** – The GitHub Action (see `.github/workflows/import-and-release.yml`) calls the `pipeline` sub‑command, uploads the resulting `.nxb` as a release asset, and posts a summary comment.

---

## Fail‑Safe Hook Template
The generated hooks follow this pattern:
```kotlin
val <HookName> = runCatching {
    // Translated runtime hook implementation
    // ...
}.onFailure { 
    PatcherLog.info { "<HookName> skipped: $it" }
}
```
If the script cannot generate a functional body, it emits:
```kotlin
val <HookName> = runCatching {
    // Unable to translate – placeholder for manual implementation.
}.onFailure { 
    PatcherLog.info { "<HookName> skipped: $it" }
}
```
This guarantees the build never crashes because of an unconvertible patch.

---

## GitHub Action Integration
The repository already contains `.github/workflows/import-and-release.yml`. The workflow simply runs:
```yaml
- name: Run import pipeline
  run: |
    uv run .agents/skills/nexalloy-patch-importer/scripts/nexalloy_importer.py pipeline \
      --url ${{ inputs.patch_source_url }} \
      --bundle ${{ inputs.bundle_name }} \
      --output pipeline_report.json
```
The action expects the following **workflow inputs** (exposed in the UI):
- `patch_source_url` – the Morphe URL.
- `bundle_name` – defaults to `nxb_extended`.
- `standalone` – optional boolean flag.

The step then publishes the generated `.nxb` as a release asset using the standard `actions/upload-release-asset` action.

---

## Extensibility
Because the skill is built on top‑level variables (`--url`, `--bundle`, `--standalone`), the same logic works for any future patch source. To add new behaviours (e.g., custom post‑processing of generated Kotlin), adjust `scripts/nexalloy_importer.py` – the skill will automatically pick up the changes.

---

## Development Tips
- Run `uv run ... pipeline --url <URL> --output debug.json` locally to see the full report.
- The temporary clone directory is removed automatically after the pipeline finishes.
- For debugging compilation failures, inspect `pipeline_report.json` → `failed_files` array.

---

## License
This skill is released under the Apache‑2.0 license, matching the rest of the NexAlloyNext project.
