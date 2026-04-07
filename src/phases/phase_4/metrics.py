from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MetricsStore:
    total_requests: int = 0
    success_requests: int = 0
    failed_requests: int = 0

    def mark_success(self) -> None:
        self.total_requests += 1
        self.success_requests += 1

    def mark_failure(self) -> None:
        self.total_requests += 1
        self.failed_requests += 1

    def snapshot(self) -> dict[str, int]:
        return {
            "total_requests": self.total_requests,
            "success_requests": self.success_requests,
            "failed_requests": self.failed_requests,
        }
