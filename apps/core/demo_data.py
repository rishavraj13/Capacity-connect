"""Group seed graph inputs so service interfaces remain small and explicit."""

from dataclasses import dataclass, field


@dataclass
class DemoGraph:
    """Carry service-created objects between deterministic seed responsibilities."""

    admin: object
    trainers: tuple
    trainees: tuple
    subjects: list = field(default_factory=list)
    skills: list = field(default_factory=list)
    courses: list = field(default_factory=list)
    modules: list = field(default_factory=list)
    enrollments: list = field(default_factory=list)
    quiz: object = None
    question: object = None
    resource: object = None
