from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .version import SCHEMA_VERSION


@dataclass(frozen=True)
class IntensitySegment:
    start: float
    end: float
    intensity_score: float
    spike_count: int
    cluster_density: float
    ding_hit_count: int = 0
    max_ding_confidence: float = 0.0

    @property
    def length(self) -> float:
        return max(0.0, self.end - self.start)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IntensitySegment":
        return cls(
            start=float(data["start"]),
            end=float(data["end"]),
            intensity_score=float(data["intensity_score"]),
            spike_count=int(data.get("spike_count", 0)),
            cluster_density=float(data.get("cluster_density", 0.0)),
            ding_hit_count=int(data.get("ding_hit_count", 0)),
            max_ding_confidence=float(data.get("max_ding_confidence", 0.0)),
        )


@dataclass(frozen=True)
class ClipAnalysis:
    schema_version: str
    clip_id: str
    duration: float
    intensity_segments: tuple[IntensitySegment, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClipAnalysis":
        return cls(
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
            clip_id=str(data["clip_id"]),
            duration=float(data["duration"]),
            intensity_segments=tuple(
                IntensitySegment.from_dict(item)
                for item in data.get("intensity_segments", [])
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "clip_id": self.clip_id,
            "duration": self.duration,
            "intensity_segments": [asdict(item) for item in self.intensity_segments],
        }


@dataclass(frozen=True)
class BeatStrengthPoint:
    time: float
    strength: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BeatStrengthPoint":
        return cls(time=float(data["time"]), strength=float(data["strength"]))


@dataclass(frozen=True)
class DropSection:
    start: float
    end: float
    energy_score: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DropSection":
        return cls(
            start=float(data["start"]),
            end=float(data["end"]),
            energy_score=float(data.get("energy_score", 0.0)),
        )


@dataclass(frozen=True)
class MusicAnalysis:
    schema_version: str
    song: str
    song_duration: float
    tempo: float
    beat_count: int
    beats: tuple[float, ...]
    beat_strength: tuple[BeatStrengthPoint, ...]
    drop_sections: tuple[DropSection, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MusicAnalysis":
        beats = tuple(float(b) for b in data.get("beats", []))
        return cls(
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
            song=str(data["song"]),
            song_duration=float(data["song_duration"]),
            tempo=float(data["tempo"]),
            beat_count=int(data.get("beat_count", len(beats))),
            beats=beats,
            beat_strength=tuple(
                BeatStrengthPoint.from_dict(item)
                for item in data.get("beat_strength", [])
            ),
            drop_sections=tuple(
                DropSection.from_dict(item) for item in data.get("drop_sections", [])
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "song": self.song,
            "song_duration": self.song_duration,
            "tempo": self.tempo,
            "beat_count": self.beat_count,
            "beats": list(self.beats),
            "beat_strength": [asdict(item) for item in self.beat_strength],
            "drop_sections": [asdict(item) for item in self.drop_sections],
        }


@dataclass(frozen=True)
class TimelineEntry:
    clip_id: str
    clip_start: float
    clip_end: float
    song_start: float
    song_end: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimelineEntry":
        return cls(
            clip_id=str(data["clip_id"]),
            clip_start=float(data["clip_start"]),
            clip_end=float(data["clip_end"]),
            song_start=float(data["song_start"]),
            song_end=float(data["song_end"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TimelinePlan:
    schema_version: str
    timeline: tuple[TimelineEntry, ...]
    total_duration: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimelinePlan":
        return cls(
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
            timeline=tuple(
                TimelineEntry.from_dict(item) for item in data.get("timeline", [])
            ),
            total_duration=float(data["total_duration"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "timeline": [item.to_dict() for item in self.timeline],
            "total_duration": self.total_duration,
        }
