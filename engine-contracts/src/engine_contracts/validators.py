from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .version import SCHEMA_VERSION


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _load_schema(name: str) -> dict[str, Any]:
    schema_path = Path(__file__).resolve().parent / "schemas" / f"{name}.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def clip_analysis_schema() -> dict[str, Any]:
    return _load_schema("clip_analysis")


def music_analysis_schema() -> dict[str, Any]:
    return _load_schema("music_analysis")


def timeline_schema() -> dict[str, Any]:
    return _load_schema("timeline")


def validate_clip_analysis_payload(payload: Any, strict: bool = True) -> None:
    _assert(isinstance(payload, list), "Clip analysis payload must be a list.")
    for idx, item in enumerate(payload):
        _assert(isinstance(item, dict), f"Clip analysis item {idx} must be an object.")
        if strict:
            _assert(
                item.get("schema_version") == SCHEMA_VERSION,
                f"Clip analysis item {idx} schema_version must be {SCHEMA_VERSION}.",
            )
            _assert("clip_id" in item, f"Clip analysis item {idx} missing clip_id.")
            _assert("duration" in item, f"Clip analysis item {idx} missing duration.")
            _assert(
                isinstance(item.get("intensity_segments"), list),
                f"Clip analysis item {idx} intensity_segments must be a list.",
            )
            for seg_idx, seg in enumerate(item.get("intensity_segments", [])):
                _assert(
                    "intensity_score" in seg,
                    f"Clip analysis item {idx} segment {seg_idx} missing intensity_score.",
                )
        else:
            _assert(
                ("clip_id" in item) or ("clip" in item),
                f"Clip analysis item {idx} missing clip_id/clip alias.",
            )


def validate_music_analysis_payload(payload: Any, strict: bool = True) -> None:
    _assert(isinstance(payload, dict), "Music analysis payload must be an object.")
    if strict:
        _assert(
            payload.get("schema_version") == SCHEMA_VERSION,
            f"Music analysis schema_version must be {SCHEMA_VERSION}.",
        )
        required = ["song", "song_duration", "tempo", "beats", "beat_strength", "drop_sections"]
        for field in required:
            _assert(field in payload, f"Music analysis missing required field: {field}")
    else:
        _assert("song" in payload, "Music analysis missing song.")
        _assert(
            ("song_duration" in payload) or ("duration" in payload),
            "Music analysis missing song_duration/duration alias.",
        )


def validate_timeline_payload(payload: Any, strict: bool = True) -> None:
    _assert(isinstance(payload, dict), "Timeline payload must be an object.")
    if strict:
        _assert(
            payload.get("schema_version") == SCHEMA_VERSION,
            f"Timeline schema_version must be {SCHEMA_VERSION}.",
        )
    _assert(isinstance(payload.get("timeline"), list), "Timeline payload must include timeline list.")
    _assert("total_duration" in payload, "Timeline payload missing total_duration.")
    for idx, item in enumerate(payload["timeline"]):
        required = ["clip_id", "clip_start", "clip_end", "song_start", "song_end"]
        for field in required:
            _assert(field in item, f"Timeline entry {idx} missing field: {field}")
