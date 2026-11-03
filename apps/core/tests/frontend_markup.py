"""Collect the structural facts needed by the frontend accessibility checks."""

from collections import Counter
from html.parser import HTMLParser

CONTROLS = {"input", "select", "textarea", "progress", "meter"}
UNLABELLED_TYPES = {"hidden", "submit", "button", "reset"}
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


class Markup(HTMLParser):
    """Record label associations and enforce local, CSP-compatible assets."""

    def __init__(self) -> None:
        """Start a fresh inventory for each rendered or source document."""
        super().__init__()
        self.lang = ""
        self.headings: list[int] = []
        self.landmarks: set[str] = set()
        self.labels: set[str] = set()
        self.controls: list[str | None] = []
        self.first_body_tag: tuple[str, dict] | None = None
        self.in_body = False
        self.in_label = False
        self.in_script = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Track structure while flagging unsupported presentation at source."""
        values = dict(attrs)
        self._assets(tag, values)
        self._structure(tag, values)
        self._controls(tag, values)

    def _assets(self, tag: str, attrs: dict) -> None:
        assert tag != "style"
        assert not any(key == "style" or key.startswith("on") for key in attrs)
        if tag == "script":
            assert attrs.get("src"), "inline script"
            self.in_script = True
        for key in ("src", "href", "action", "srcset", "poster"):
            value = attrs.get(key) or ""
            assert not value.lower().startswith(("http:", "https:", "//")), value

    def _structure(self, tag: str, attrs: dict) -> None:
        if tag == "html":
            self.lang = attrs.get("lang", "")
        if self.in_body and self.first_body_tag is None:
            self.first_body_tag = (tag, attrs)
        if tag == "body":
            self.in_body = True
        if tag in {"header", "main", "footer", "nav"}:
            self.landmarks.add(tag)
        if tag in HEADINGS:
            self.headings.append(int(tag[1]))
        if tag == "img":
            assert "alt" in attrs

    def _controls(self, tag: str, attrs: dict) -> None:
        if tag == "label":
            self.in_label = True
            if attrs.get("for"):
                self.labels.add(attrs["for"])
        if tag not in CONTROLS or attrs.get("type") in UNLABELLED_TYPES:
            return
        if not self.in_label and not (
            attrs.get("aria-label") or attrs.get("aria-labelledby")
        ):
            self.controls.append(attrs.get("id"))

    def handle_endtag(self, tag: str) -> None:
        """End tracking for nested labels and script bodies."""
        if tag == "label":
            self.in_label = False
        if tag == "script":
            self.in_script = False

    def handle_data(self, data: str) -> None:
        """Reject executable script content even on a script with src."""
        assert not self.in_script or not data.strip()


def assert_accessible_shell(html: str) -> None:
    """Check the required landmarks, heading sequence and label associations."""
    page = Markup()
    page.feed(html)
    assert page.lang == "en"
    assert page.headings and page.headings[0] == 1 and page.headings.count(1) == 1
    assert all(
        next_ <= previous + 1
        for previous, next_ in zip(page.headings, page.headings[1:], strict=False)
    )
    assert {"header", "main", "footer"} <= page.landmarks
    assert page.first_body_tag and page.first_body_tag[0] == "a"
    assert page.first_body_tag[1]["href"] == "#main"
    assert set(page.controls) <= page.labels, set(page.controls) - page.labels


class AuditMarkup(Markup):
    """Check references whose targets may occur later in the document."""

    def __init__(self) -> None:
        """Store ID counts and accessibility references in document order."""
        super().__init__()
        self.ids = Counter()
        self.references = set()
        self.tables = []
        self.fieldsets = []
        self.grouped = []
        self.controls_with_text = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        """Collect unique IDs and local ARIA relationships."""
        super().handle_starttag(tag, attrs)
        values = dict(attrs)
        if values.get("id"):
            self.ids[values["id"]] += 1
        for key in ("aria-labelledby", "aria-describedby"):
            self.references.update((values.get(key) or "").split())
        self._structure_checks(tag, values)

    def _structure_checks(self, tag: str, values: dict) -> None:
        """Record captions, grouped controls and readable control names."""
        self._record_group(tag, values)
        if tag == "table":
            self.tables.append(False)
        if tag == "caption" and self.tables:
            self.tables[-1] = True
        if tag == "th":
            assert values.get("scope") in {"row", "col", "rowgroup", "colgroup"}
        if tag in {"a", "button"}:
            self.controls_with_text.append((tag, values.get("aria-label", "")))
        if tag == "img" and self.controls_with_text:
            self.handle_data(values.get("alt") or "")

    def _record_group(self, tag: str, values: dict) -> None:
        """Track whether grouped controls have an enclosing legend."""
        if tag == "fieldset":
            self.fieldsets.append(False)
        if tag == "legend" and self.fieldsets:
            self.fieldsets[-1] = True
        if tag == "input" and values.get("type") in {"radio", "checkbox"}:
            self.grouped.append(
                (values["type"], values.get("name"), any(self.fieldsets))
            )

    def handle_endtag(self, tag: str) -> None:
        """Require captions and names before closing their elements."""
        super().handle_endtag(tag)
        if tag == "table":
            assert self.tables.pop(), "Missing table caption"
        if tag == "fieldset":
            self.fieldsets.pop()
        if self.controls_with_text and tag == self.controls_with_text[-1][0]:
            assert self.controls_with_text.pop()[1].strip(), f"Unnamed {tag}"

    def handle_data(self, data: str) -> None:
        """Collect visible control text across nested inline tags."""
        super().handle_data(data)
        if self.controls_with_text:
            tag, label = self.controls_with_text[-1]
            self.controls_with_text[-1] = (tag, label + data)
