# AnMi Ricky firmware implementation plan

> **For agentic workers:** Execute inline with superpowers:executing-plans; do not start a new local SDK build.

**Goal:** Prepare the correct Ricky firmware and a small, reproducible remote-build source package that exports verified flash images.

**Architecture:** Keep the existing XiaoZhi board and CogAI WebSocket bridge. Compile one ESP32-S3 variant on GitHub Actions, with the SDK kept on the remote runner. Deliver binaries, logs and hashes as artifacts; do not flash automatically.

**Tech Stack:** ESP-IDF 6.1, C++23, Python standard library, GitHub Actions, existing FastAPI gateway.

**Spec:** Existing operator-approved flow in `../../KET_NOI_ROBOT_ANMI.md` and hardware observations in `../../KIEM_TRA_ROBOT_ANMI_20261027.md`.

## Global constraints

- ESP32-S3, flash 16 MB, PSRAM 8 MB, USB Serial/JTAG console.
- Motor GPIO39/40/43/44 stay LOW; no movement tools.
- Microphone WS4/SCK5/DIN6; speaker DOUT7/BCLK15/LRCK16; RGB48; button0.
- Optional OLED SDA41/SCL42 must never prevent voice startup.
- No private backups, tokens, Wi-Fi settings, API keys or backend data in remote source.
- No large local SDK/Docker installation, no flashing and no remote publish without configured destination.

## Review focus

- Missing or failing OLED must degrade to NoDisplay, not abort boot.
- Wi-Fi setup must remain reachable without a working screen.
- Package paths must exclude private data and generated build trees.
- Workflow must build only Ricky and upload images only after verification.
- An unconfigured GitHub account is a real blocker for producing binaries, not evidence of build success.

## Tasks

- [ ] Harden optional OLED initialization and provide long-press Wi-Fi setup on GPIO0. Keep board source canonical rather than regenerate it from a template that overwrites fixes.
- [ ] Add a single-board workflow, source packaging tool and regression tests for excluded private files and unsafe archive entries.
- [ ] Verify exported images using explicit errors even with Python optimization; test corrupt hashes, partitions and mismatched merged apps.
- [ ] Run relevant local checks and gateway tests; package source with manifest; document exact remote build and hardware acceptance steps.
- [ ] Run remote build once the operator supplies an authorized repository/connection; verify returned `.bin` files. Remains pending if no destination is available.

## Execution ledger

Ruling: Work directly in the existing non-Git workspace, preserving the user's files. No new worktree or duplicate SDK/source checkout is necessary.
Ruling: The user has already approved the architecture and asked for execution. Do not restart design approval questions. Repository access is missing information, not permission to invent credentials.
