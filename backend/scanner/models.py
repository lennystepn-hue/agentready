from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone


class CheckStatus(Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class CheckResult:
    name: str
    category: str
    status: CheckStatus
    score: int
    max_score: int
    message: str
    fix_suggestion: str | None = None
    code_snippet: str | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "status": self.status.value,
            "score": self.score,
            "max_score": self.max_score,
            "message": self.message,
            "fix_suggestion": self.fix_suggestion,
            "code_snippet": self.code_snippet,
        }


@dataclass
class ScanReport:
    domain: str
    scan_id: str
    timestamp: str
    total_score: int
    max_score: int
    grade: str
    categories: dict
    checks: list[CheckResult]
    top_fixes: list[CheckResult] = field(default_factory=list)
    site_type: str = "generic"
    site_label: str = "Website"

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "scan_id": self.scan_id,
            "timestamp": self.timestamp,
            "total_score": self.total_score,
            "max_score": self.max_score,
            "grade": self.grade,
            "categories": self.categories,
            "checks": [c.to_dict() for c in self.checks],
            "top_fixes": [c.to_dict() for c in self.top_fixes],
            "site_type": self.site_type,
            "site_label": self.site_label,
        }


def calculate_grade(score: int) -> str:
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 40:
        return "D"
    elif score >= 20:
        return "E"
    else:
        return "F"
