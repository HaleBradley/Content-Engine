from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_CONTRACTS_SRC = REPO_ROOT / "engine-contracts" / "src"
if str(ENGINE_CONTRACTS_SRC) not in sys.path:
    sys.path.insert(0, str(ENGINE_CONTRACTS_SRC))

from engine_contracts.validators import (
    validate_clip_analysis_payload,
    validate_music_analysis_payload,
    validate_timeline_payload,
)


def test_legacy_fixture_payloads_still_validate_in_compat_mode() -> None:
    clip_payload = [
        {
            "clip": "legacy.mp4",
            "duration": 10.0,
            "intensity_segments": [
                {"start": 1.0, "end": 3.0, "score": 0.7, "spike_count": 2}
            ],
        }
    ]
    music_payload = {
        "song": "legacy.mp3",
        "duration": 90.0,
        "bpm": 135.0,
        "beat_count": 3,
        "beats": [0.5, 1.0, 1.5],
        "high_energy_sections": [{"start": 20.0, "end": 30.0, "energy_score": 0.8}],
    }
    timeline_payload = {
        "timeline": [
            {
                "clip_id": "legacy.mp4",
                "clip_start": 1.0,
                "clip_end": 3.0,
                "song_start": 4.0,
                "song_end": 6.0,
            }
        ],
        "total_duration": 6.0,
    }

    validate_clip_analysis_payload(clip_payload, strict=False)
    validate_music_analysis_payload(music_payload, strict=False)
    validate_timeline_payload(timeline_payload, strict=False)


def test_canonical_payloads_validate_in_strict_mode() -> None:
    clip_payload = [
        {
            "schema_version": "2.0.0",
            "clip_id": "clip.mp4",
            "duration": 10.0,
            "intensity_segments": [
                {
                    "start": 1.0,
                    "end": 3.0,
                    "intensity_score": 0.8,
                    "spike_count": 3,
                    "cluster_density": 0.1,
                }
            ],
        }
    ]
    music_payload = {
        "schema_version": "2.0.0",
        "song": "song.mp3",
        "song_duration": 120.0,
        "tempo": 140.0,
        "beat_count": 3,
        "beats": [0.5, 1.0, 1.5],
        "beat_strength": [
            {"time": 0.5, "strength": 0.7},
            {"time": 1.0, "strength": 0.8},
            {"time": 1.5, "strength": 0.9},
        ],
        "drop_sections": [{"start": 40.0, "end": 55.0, "energy_score": 0.9}],
    }
    timeline_payload = {
        "schema_version": "2.0.0",
        "timeline": [
            {
                "clip_id": "clip.mp4",
                "clip_start": 1.0,
                "clip_end": 3.0,
                "song_start": 4.0,
                "song_end": 6.0,
            }
        ],
        "total_duration": 6.0,
    }

    validate_clip_analysis_payload(clip_payload, strict=True)
    validate_music_analysis_payload(music_payload, strict=True)
    validate_timeline_payload(timeline_payload, strict=True)
