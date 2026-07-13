from dataclasses import dataclass, field


@dataclass
class PaySlip:
    employee_name: str
    total_vencimentos: str
    source_file: str = ""


@dataclass
class IgnoredRecord:
    page: int
    reason: str
    source_file: str = ""


@dataclass
class ProcessResult:
    records: list[PaySlip] = field(default_factory=list)
    ignored_details: list[IgnoredRecord] = field(default_factory=list)
    total_pages: int = 0
    total_records: int = 0
    ignored_records: int = 0
    warnings: list[str] = field(default_factory=list)
