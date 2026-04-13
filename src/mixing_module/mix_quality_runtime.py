from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .h_kinetics import HMixConfig, HMixSample, step_h


@dataclass
class MixQualityRuntime:
    config: HMixConfig = field(default_factory=HMixConfig)
    batch_id: str | None = None
    active: bool = False
    ready: bool = False
    elapsed_s: float = 0.0
    h: float = 0.0
    samples: list[HMixSample] = field(default_factory=list)

    def new_batch(self, batch_id: str) -> None:
        self.batch_id = batch_id
        self.active = True
        self.ready = False
        self.elapsed_s = 0.0
        self.h = 0.0
        self.samples = []

    def stop_batch(self) -> None:
        self.active = False

    def ingest(self, *, n: float, d: float, w: float, q_s: float, p: float | None = None) -> HMixSample:
        if not self.active:
            raise RuntimeError("batch is not active")
        self.h, k_mix = step_h(
            self.config,
            h_prev=self.h,
            n=n,
            d=d,
            w=w,
            q_s=q_s,
            p=p,
        )
        self.elapsed_s += self.config.ts_s
        if self.h >= self.config.h_target:
            self.ready = True
        sample = HMixSample(
            t_s=self.elapsed_s,
            h=self.h,
            k_mix=k_mix,
            n=n,
            d=d,
            w=w,
            q_s=q_s,
            p=0.0 if p is None else p,
            ready=self.ready,
        )
        self.samples.append(sample)
        return sample

    def state_payload(self) -> dict:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "batch_id": self.batch_id,
            "H": self.h,
            "elapsed_s": self.elapsed_s,
            "ready": self.ready,
            "k_mix": self.samples[-1].k_mix if self.samples else 0.0,
        }
