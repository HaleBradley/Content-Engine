from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent
SERVICES_DIR = REPO_ROOT / "services"
ENGINE_CONTRACTS_SRC = REPO_ROOT / "engine-contracts" / "src"


def _ensure_paths() -> None:
    if str(ENGINE_CONTRACTS_SRC) not in sys.path:
        sys.path.insert(0, str(ENGINE_CONTRACTS_SRC))

    planner_src = SERVICES_DIR / "montage-planner" / "src"
    if str(planner_src) not in sys.path:
        sys.path.insert(0, str(planner_src))


def _build_env(extra_pythonpath: list[Path] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    if not extra_pythonpath:
        return env
    existing = env.get("PYTHONPATH", "")
    joined = ":".join(str(path) for path in extra_pythonpath)
    env["PYTHONPATH"] = f"{joined}:{existing}" if existing else joined
    return env


def _run_command(
    command: list[str], cwd: Path, extra_pythonpath: list[Path] | None = None
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            env=_build_env(extra_pythonpath),
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else ""
        stdout = exc.stdout.strip() if exc.stdout else ""
        details = stderr or stdout or "No subprocess output captured."
        raise RuntimeError(
            f"Command failed in {cwd}: {' '.join(command)}\n{details}"
        ) from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run all four montage phases in one command.")
    parser.add_argument("--clips", nargs="+", required=True, help="Input clip file paths.")
    parser.add_argument("--music", required=True, help="Input music file path.")
    parser.add_argument(
        "--run-dir",
        default=str(REPO_ROOT / "runs" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")),
        help="Output run directory.",
    )
    parser.add_argument(
        "--output",
        default="final.mp4",
        help="Final rendered output filename (inside run-dir unless absolute).",
    )
    parser.add_argument(
        "--planner-compat-mode",
        action="store_true",
        help="Enable planner compatibility mode for legacy contracts.",
    )
    return parser


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _stage_clips_for_render(
    clip_paths: list[Path], run_dir: Path
) -> tuple[dict[str, str], list[dict[str, str]]]:
    clips_dir = run_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    file_name_counts: dict[str, int] = {}
    remap: dict[str, str] = {}
    artifacts: list[dict[str, str]] = []

    duplicate_names = {path.name for path in clip_paths if sum(1 for p in clip_paths if p.name == path.name) > 1}
    if duplicate_names:
        duplicates = ", ".join(sorted(duplicate_names))
        raise ValueError(
            f"Duplicate clip filenames are not supported by current planner contract: {duplicates}"
        )

    for clip_path in clip_paths:
        stem = clip_path.stem
        suffix = clip_path.suffix
        occurrence = file_name_counts.get(clip_path.name, 0)
        file_name_counts[clip_path.name] = occurrence + 1
        if occurrence == 0:
            staged_name = clip_path.name
        else:
            staged_name = f"{stem}_{occurrence}{suffix}"

        staged_path = clips_dir / staged_name
        if staged_path.exists():
            staged_path.unlink()

        try:
            staged_path.symlink_to(clip_path)
            staged_type = "symlink"
        except OSError:
            shutil.copy2(clip_path, staged_path)
            staged_type = "copy"

        remap[clip_path.name] = f"clips/{staged_name}"
        artifacts.append(
            {
                "source": str(clip_path),
                "staged": str(staged_path),
                "staged_type": staged_type,
            }
        )

    return remap, artifacts


def main() -> int:
    args = _build_parser().parse_args()
    _ensure_paths()

    from engine_contracts.validators import (
        validate_clip_analysis_payload,
        validate_music_analysis_payload,
        validate_timeline_payload,
    )
    from montage_planner import MontagePlanner

    clip_paths = [Path(clip).expanduser().resolve() for clip in args.clips]
    music_path = Path(args.music).expanduser().resolve()
    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    clip_analysis_path = run_dir / "clip-analysis.json"
    music_analysis_path = run_dir / "music-analysis.json"
    timeline_path = run_dir / "timeline.json"
    manifest_path = run_dir / "run-manifest.json"
    final_output = Path(args.output)
    if not final_output.is_absolute():
        final_output = run_dir / final_output

    clip_analyzer_cwd = SERVICES_DIR / "val-content-engine"
    clip_command = [
        sys.executable,
        "-m",
        "val_content_engine.cli",
        *(str(path) for path in clip_paths),
        "--output",
        str(clip_analysis_path),
    ]
    _run_command(
        clip_command,
        cwd=clip_analyzer_cwd,
        extra_pythonpath=[clip_analyzer_cwd / "src", ENGINE_CONTRACTS_SRC],
    )

    clip_payload = json.loads(clip_analysis_path.read_text(encoding="utf-8"))
    validate_clip_analysis_payload(clip_payload, strict=False)

    music_cwd = SERVICES_DIR / "music-analyzer"
    music_command = [sys.executable, "main.py", "--song", str(music_path)]
    music_result = _run_command(music_command, cwd=music_cwd)
    music_payload = json.loads(music_result.stdout)
    _write_json(music_analysis_path, music_payload)
    validate_music_analysis_payload(music_payload, strict=False)

    planner = MontagePlanner(compat_mode=args.planner_compat_mode)
    timeline_payload = planner.build_timeline(clips=clip_payload, music_data=music_payload)
    clip_remap, staged_clip_artifacts = _stage_clips_for_render(clip_paths, run_dir)
    for entry in timeline_payload.get("timeline", []):
        clip_id = entry.get("clip_id")
        if clip_id in clip_remap:
            entry["clip_id"] = clip_remap[clip_id]
    _write_json(timeline_path, timeline_payload)
    validate_timeline_payload(timeline_payload, strict=True)

    render_cwd = SERVICES_DIR / "render-engine"
    render_command = [
        sys.executable,
        "-m",
        "render_engine.cli",
        "--timeline",
        str(timeline_path),
        "--music",
        str(music_path),
        "--output",
        str(final_output),
    ]
    _run_command(render_command, cwd=render_cwd, extra_pythonpath=[ENGINE_CONTRACTS_SRC])

    manifest = {
        "run_started_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": {
            "clip_analysis": str(clip_analysis_path),
            "music_analysis": str(music_analysis_path),
            "timeline": str(timeline_path),
            "final_output": str(final_output),
            "staged_clips": staged_clip_artifacts,
        },
        "planner_compat_mode": bool(args.planner_compat_mode),
    }
    _write_json(manifest_path, manifest)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
