"""Fail-closed GPU profiles for preregistered evidence runs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class HardwareProfile:
    profile_id: str
    accepted_name_fragments: tuple[str, ...]
    min_total_vram_gib: float
    max_total_vram_gib: Optional[float]
    min_free_before_load_gib: float
    min_free_after_load_gib: float
    generation_batch_size: int
    disk_budget_gib: float
    disk_ceiling_gib: float
    authorization_date: str

    def identity(self) -> Dict[str, object]:
        payload = asdict(self)
        payload["accepted_name_fragments"] = list(self.accepted_name_fragments)
        payload["owner_authorized"] = True
        return payload

    @property
    def profile_sha256(self) -> str:
        blob = json.dumps(
            self.identity(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(blob).hexdigest()


A800_80GB_PROFILE = HardwareProfile(
    profile_id="nvidia-a800-80gb",
    accepted_name_fragments=("NVIDIA A800",),
    min_total_vram_gib=75.0,
    max_total_vram_gib=82.0,
    min_free_before_load_gib=60.0,
    min_free_after_load_gib=20.0,
    generation_batch_size=32,
    disk_budget_gib=60.0,
    disk_ceiling_gib=70.0,
    authorization_date="2026-08-12",
)

AUTHORIZED_HARDWARE_PROFILES = {
    A800_80GB_PROFILE.profile_id: A800_80GB_PROFILE,
}


def get_authorized_hardware_profile(profile_id: str) -> HardwareProfile:
    try:
        return AUTHORIZED_HARDWARE_PROFILES[str(profile_id)]
    except KeyError as exc:
        raise ValueError(f"unknown or unauthorized hardware profile: {profile_id!r}") from exc


def validate_hardware_profile(
    profile: HardwareProfile,
    *,
    device_name: str,
    total_vram_gib: float,
    free_vram_gib: Optional[float] = None,
    after_load: bool = False,
) -> Dict[str, object]:
    name = str(device_name)
    total = float(total_vram_gib)
    if not any(fragment in name for fragment in profile.accepted_name_fragments):
        raise ValueError(
            f"unauthorized GPU for {profile.profile_id}: device={name!r}"
        )
    if total < profile.min_total_vram_gib:
        raise ValueError(
            f"GPU is smaller than authorized profile: {total:.3f} GiB "
            f"< {profile.min_total_vram_gib:.3f} GiB"
        )
    if profile.max_total_vram_gib is not None and total > profile.max_total_vram_gib:
        raise ValueError(
            f"GPU VRAM exceeds profile identity range: {total:.3f} GiB "
            f"> {profile.max_total_vram_gib:.3f} GiB"
        )
    minimum_free = (
        profile.min_free_after_load_gib
        if after_load
        else profile.min_free_before_load_gib
    )
    if free_vram_gib is not None and float(free_vram_gib) < minimum_free:
        stage = "after load" if after_load else "before load"
        raise ValueError(
            f"insufficient free VRAM {stage}: {float(free_vram_gib):.3f} GiB "
            f"< {minimum_free:.3f} GiB"
        )
    return {
        "profile": profile.identity(),
        "profile_sha256": profile.profile_sha256,
        "device_name": name,
        "total_vram_gib": total,
        "free_vram_gib": None if free_vram_gib is None else float(free_vram_gib),
        "stage": "after_load" if after_load else "before_load",
    }
