"""Collect the structural facts needed by the frontend accessibility checks."""

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
