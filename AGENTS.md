## Agent Behaviour Rules

### General Behavior

- MUST: Ask for clarification when requirements are ambiguous
- MUST: Verify all changes work before confirming completion
- SHOULD: Run tests before committing code
- SHOULD: Provide clear explanations for complex changes
- SHOULD NOT: Make assumptions about file locations or project structure

### Error Handling

- MUST: Report errors with full context to the user
- MUST: Continue processing other items when individual items fail
- SHOULD: Suggest solutions when errors occur
- SHOULD: Validate inputs before processing
- SHOULD NOT: Silently ignore errors or warnings

## USER-FILES Protection Rules

### ABSOLUTE FORBIDDEN - USER-FILES/04.INPUT/
- MUST NEVER: Create, delete, modify, move, or rename ANY files in USER-FILES/04.INPUT/
- CAN ONLY: Read files from USER-FILES/04.INPUT/

### General USER-FILES Rules
- MUST: Never create, delete, modify, move, or rename files in USER-FILES/ without explicit permission
- MUST: Ask before any operation in USER-FILES/
- SHOULD: Only read from USER-FILES/04.INPUT/ and write to USER-FILES/05.OUTPUT/
- SHOULD NOT: Implement any auto-cleanup or archiving features

## Project Structure Rules

- MUST: Read inputs only from USER-FILES/04.INPUT/
- MUST: Write outputs only to USER-FILES/05.OUTPUT/ with timestamps (YYMMDD_HHMMSS format)
- SHOULD: Preserve input directory structure in outputs

## Python Code Standards

- MUST: Use type hints for all function signatures
- MUST: Use pathlib.Path for file operations (not os.path)
- SHOULD: Keep functions under 50 lines
- SHOULD: Format with black and lint with ruff
- SHOULD: Add docstrings for all public functions

## Testing Standards

- MUST: Write tests for critical functionality
- SHOULD: Test happy paths and edge cases
- SHOULD: Mock external dependencies
- SHOULD: Keep tests fast and focused

## Configuration Management

- MUST: Use environment variables for sensitive data
- MUST: Validate configuration at startup
- SHOULD: Provide sensible defaults

## Dependency Management

- MUST: Pin exact versions in requirements.txt
- MUST: Use virtual environments
- SHOULD: Keep dependencies minimal

---

## Architecture: Direct Replicate SDK (Pre-Engine Migration)

### Current State
vid-to-vid is a **video-to-video motion control Vehicle** that currently
imports the Replicate SDK directly — it has NOT yet been migrated to the
Engine interface. The Engine migration (following FC/MC patterns) is a pending
task.

"The Vehicle orchestrates. Currently the SDK is called directly. After
migration, the Engine will execute and the profile will configure."

### Core Capability
Takes markdown bullet files containing:
- Line 1: Motion description (prompt)
- Line 3: Embedded image URL `![](url)` — character pose reference
- Line 5: Embedded video URL `![video](url)` — motion reference video

Processes these through Replicate's Kling 2.6 Motion Control model to generate
output videos.

### Processing Flow (Current, Pre-Migration)

Standalone mode:
```
main() → _run()
  → validate_environment()        # check REPLICATE_API_TOKEN
  → validate_input_directories()  # verify USER-FILES/04.INPUT/ and profiles
  → ReplicateClient(config)       # direct SDK client instantiation
  → ProcessingContext(client, ...) # context assembly
  → process_files_verbose()       # main processing loop
    → discover_markdown_jobs()    # find .md files in input dir
    → load_active_profile()       # single YAML profile from 03.PROFILES/
    → _process_video_verbose()    # per-bullet: build params → predict → poll → download
  → create_success_report()       # output generation
  → create_cost_report()
  → archive_and_cleanup_logs()
```

### Input Format (vid-to-vid specific)
Unlike FC/MC which parse line-1 prompt + reference image URLs, vid-to-vid
expects a 6-line markdown format:
```
Motion description text            ← line 1 (prompt)
                                   ← line 2 (empty/ignored)
![](https://example.com/image.png) ← line 3 (character reference image)
                                   ← line 4 (empty/ignored)
![video](https://example.com/vid.mp4) ← line 5 (motion reference video)
                                   ← line 6 (end)
```

Key differences from standard FC/MC bullets:
- Two reference media URLs (image for pose + video for motion) instead of one
- Images use standard `![](url)` syntax
- Videos use labeled `![video](url)` syntax
- No `frames:` override support (duration comes from profile config only)

### Output Structure
Each generation creates:
- `{filename}_YYMMDD_HHMMSS.mp4` — generated video with timestamp
- `VIDEO_REPORT.md` — human-readable report
- `generation_payload.json` — complete API request/response
- `generation.log` — verbose generation log
- `source_*.md` — copy of input markdown file

### Multiple Processing Modes
Three parallel processor implementations exist (pre-migration duplication):

| Entry Point | Processor | Mode |
|-------------|-----------|------|
| `main.py` | `processor.py` → `process_files()` | Synchronous, single-threaded |
| `main_verbose.py` | `verbose_processor.py` → `process_files_verbose()` | Asynchronous with polling |
| `main_hybrid.py` | `hybrid_processor.py` → `process_files_hybrid()` | Hybrid async with progress |

### Pending Engine Migration
This Vehicle should be migrated to the Engine interface following the FC
(Phase 5) and MC (Phase 6) patterns:
1. Remove direct `import replicate` from `api/client.py`
2. Vendor `engine_loader.py` from studiolot `pipeline/engine_loader.py`
3. Add `--input_dir`, `--output_dir`, `--profile` CLI flags
4. Build `InputFile` objects with metadata carrying video-specific fields
5. Replace `process_files_verbose()` with `engine.run(inputs)`
6. Delete dead code: `api/`, `processing/` (except bullet parsing), `models/`,
   `output/`, `utils/epic_progress.py`, `utils/hybrid_progress.py`,
   `utils/verbose_output.py`, `utils/enhanced_logging.py`, `validation/`

---

## Source File Map (current, pre-migration)

### Active Entry Point Chain (`main_verbose.py`)

| File | Purpose |
|------|---------|
| `src/main_verbose.py` | Primary entry point — verbose async mode |
| `src/api/client.py` | `ReplicateClient` — direct Replicate SDK wrapper |
| `src/api/base_async_client.py` | `BaseAsyncReplicateClient` — shared async polling + retry |
| `src/api/async_client_enhanced.py` | `AsyncReplicateClientEnhanced` — enhanced async client |
| `src/api/response_parser.py` | Shared `extract_video_url()` utility |
| `src/auth/__init__.py` | `authenticate()` — env + .env API key resolution |
| `src/auth/env.py` | `.env` file loading helper |
| `src/config/settings.py` | `INPUT_DIR`, `PROFILES_DIR`, `OUTPUT_DIR` — hardcoded paths |
| `src/config/constants.py` | Shared constants (emojis, retry config, etc.) |
| `src/processing/verbose_processor.py` | `process_files_verbose()` — async main processing loop |
| `src/processing/processor.py` | `process_files()` — sync alternative (324 lines) |
| `src/processing/hybrid_processor.py` | `process_files_hybrid()` — hybrid alternative |
| `src/processing/input_discovery.py` | `discover_markdown_jobs()` — find .md bullet files |
| `src/processing/profile_loader.py` | `load_active_profile()` — single profile YAML loading |
| `src/processing/profile_validator.py` | Profile schema validation |
| `src/processing/cost_calculator.py` | `calculate_cost_from_params()` — cost estimation |
| `src/processing/output_generator.py` | Video output file generation |
| `src/processing/video_downloader.py` | `download_video()` — download from prediction URL |
| `src/processing/generation_logger.py` | Per-generation logging |
| `src/models/processing.py` | `ProcessingContext`, `GenerationContext` dataclasses |
| `src/models/video_processing.py` | `APIClientConfig`, `VideoProcessingContext`, `VideoRequest` |
| `src/models/generation.py` | `InputTriplet` legacy model |
| `src/models/triplet.py` | Triplet data structures |
| `src/output/reporter.py` | `create_success_report()`, `create_cost_report()` |
| `src/output/json_generator.py` | JSON payload output |
| `src/output/markdown_generator.py` | Markdown report output |
| `src/output/log_generator.py` | Log file output |
| `src/output/file_manager.py` | Timestamped directory creation |
| `src/utils/verbose_output.py` | `VerboseProgress`, `log_stage_emoji()` |
| `src/utils/enhanced_logging.py` | `setup_dual_logging()` — dual file + console logging |
| `src/utils/error_handling.py` | `run_with_error_handling()` — shared error wrapper |
| `src/utils/cleanup.py` | `archive_and_cleanup_logs()` |
| `src/utils/logging.py` | Basic logging setup |
| `src/utils/filename_utils.py` | `extract_timestamp_from_filename()`, `_sanitize_for_filename()` |
| `src/validation/environment.py` | `validate_environment()`, `validate_input_directories()` |
| `src/exceptions.py` | Custom exception hierarchy |

### Alternative Entry Points (not the primary path)

| File | Purpose |
|------|---------|
| `src/main.py` | Sync entry point — uses `processor.py` |
| `src/main_hybrid.py` | Hybrid entry point — uses `hybrid_processor.py` |
| `src/utils/epic_progress.py` (266 lines) | `EpicProgress` — alive-progress wrapper |
| `src/utils/hybrid_progress.py` (223 lines) | `HybridProgress` — hybrid progress wrapper |

---

## Configuration

- **Profiles**: YAML files in `USER-FILES/03.PROFILES/` — single profile per run
- **Profile format**: `project`, `Model.endpoint`, `pricing`, `params`, `paths` (legacy pre-Engine format)
- **API keys**: `REPLICATE_API_TOKEN` env var or `.env` file
- **Paths**: Hardcoded in `config/settings.py` (`INPUT_DIR`, `PROFILES_DIR`, `OUTPUT_DIR`)
- **Single-profile enforcement**: Exactly one YAML file required in `03.PROFILES/`; 0 or >1 fail fast

## Session History

### 2026-08-05 — AGENTS.md rewrite
- Replaced legacy 1020-line documentation with modern FC-pattern AGENTS.md
- Added Architecture: Direct Replicate SDK section documenting current pre-migration state
- Added Source File Map covering all files in the `main_verbose.py` import chain
- Documented vid-to-vid specific input format (6-line markdown with dual media URLs)
- Documented pending Engine migration following FC/MC patterns

---

## Known Issues & Technical Debt

### High Priority (pre-migration)
- **Not yet Engine-migrated**: Direct `import replicate` in `api/client.py` — needs
  Engine interface per VEHICLE_CONTRACT.md §2
- **Three parallel processors**: `processor.py` (324 lines), `verbose_processor.py`
  (277 lines), `hybrid_processor.py` — ~600 lines of near-identical code. Engine
  migration eliminates all three.
- **No CLI flags**: Hardcoded paths in `config/settings.py` — no `--input_dir`,
  `--output_dir`, `--profile` support
- **No `engine_loader.py`**: Engine discovery/loading not vendored

### Medium Priority
- **Three progress bar systems**: `epic_progress.py` (266 lines), `hybrid_progress.py`
  (223 lines), `verbose_output.py` — will be deleted after Engine migration
- **Three entry points**: `main.py`, `main_verbose.py`, `main_hybrid.py` — should
  consolidate to single Engine-based entry point like FC/MC
- **Legacy profile format**: Uses `Model.endpoint` instead of Engine-interface
  `platform` + `endpoint` — needs `normalize_legacy_profile()` like MC

### Low Priority
- `src/reporting/` directory empty (`.gitkeep` only) — safe to delete
- No test files exist — zero test coverage
- `alive-progress` dependency used only by progress bars that will be deleted
