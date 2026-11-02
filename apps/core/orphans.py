"""Find aged unreferenced storage files while preserving every model file reference."""

from dataclasses import dataclass
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.db.models import FileField

from apps.core import clock
from apps.core.exceptions import CapacityConnectError

DEFAULT_MIN_AGE_HOURS = 24
SECONDS_PER_HOUR = 3600


@dataclass(frozen=True, slots=True)
class CleanupReport:
    """Return the same explicit candidates for dry-run and deletion evidence."""

    candidates: tuple[Path, ...]
    deleted: tuple[Path, ...]


def referenced_files() -> set[Path]:
    """Discover FileFields dynamically so future private models are protected too."""
    result = set()
    for model in apps.get_models():
        for field in model._meta.fields:
            if not isinstance(field, FileField):
                continue
            root = Path(field.storage.location).resolve()
            result.update(
                (root / name).resolve()
                for name in model.objects.values_list(field.name, flat=True)
                if name
            )
    return result


def _roots() -> tuple[Path, ...]:
    """Resolve configured storage roots once and avoid scanning duplicates."""
    return tuple(
        dict.fromkeys(
            Path(path).resolve()
            for path in (settings.PRIVATE_MEDIA_ROOT, settings.MEDIA_ROOT)
        )
    )


def _aged_files(root: Path, cutoff: float) -> tuple[Path, ...]:
    """Skip escaped symlinks/junctions before inspecting or deleting any path."""
    return tuple(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.resolve().is_relative_to(root)
        and path.stat().st_mtime <= cutoff
    )


def cleanup_orphans(
    min_age_hours: int = DEFAULT_MIN_AGE_HOURS, delete: bool = False
) -> CleanupReport:
    """Dry-run by default and recheck current references before each removal."""
    if min_age_hours < 0:
        raise CapacityConnectError("Minimum age cannot be negative.")
    protected = referenced_files()
    cutoff = clock.now().timestamp() - min_age_hours * SECONDS_PER_HOUR
    files = tuple(
        path
        for root in _roots()
        for path in _aged_files(root, cutoff)
        if path.resolve() not in protected
    )
    deleted = []
    if delete:
        for path in files:
            if path.resolve() not in referenced_files():
                path.unlink()
                deleted.append(path)
    return CleanupReport(files, tuple(deleted))
