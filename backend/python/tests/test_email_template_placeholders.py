"""Guards the Jinja2 placeholders baked into the exported email templates.

The templates under ``app/templates`` are generated from the React Email
sources in ``frontend/emails`` via ``pnpm run email:export``. Those sources
render the placeholders as literal ``{{ Name }}`` text, so the export is
idempotent -- but nothing in the frontend toolchain knows which names the
backend actually substitutes. These tests are that link: if a regenerated
template loses a placeholder, gains one, or renames it, the mismatch fails
here instead of shipping an email that reads "Hi Driver_Name_To_Replace,".
"""

import re
from pathlib import Path

import pytest

from app.constants.email_config import EMAIL_TEMPLATES

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "app" / "templates"

# ``{{ Name }}`` as react-email emits it, tolerating arbitrary inner whitespace.
JINJA_PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")

# Every placeholder name any template may legitimately use. Used to detect a
# name that survived export as bare text rather than a Jinja2 expression.
ALL_PLACEHOLDER_NAMES = {
    name for config in EMAIL_TEMPLATES.values() for name in config["required_context"]
}


def _read_template(email_type: str) -> str:
    path = TEMPLATE_DIR / EMAIL_TEMPLATES[email_type]["filename"]
    assert path.is_file(), f"Template file missing for {email_type}: {path}"
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("email_type", sorted(EMAIL_TEMPLATES))
def test_template_placeholders_match_required_context(email_type: str) -> None:
    """The template's ``{{ ... }}`` names are exactly its declared context."""
    html = _read_template(email_type)
    found = set(JINJA_PLACEHOLDER_RE.findall(html))
    expected = set(EMAIL_TEMPLATES[email_type]["required_context"])

    assert found == expected, (
        f"{email_type}: template placeholders do not match required_context in "
        f"app/constants/email_config.py.\n"
        f"  missing from template: {sorted(expected - found)}\n"
        f"  unexpected in template: {sorted(found - expected)}\n"
        f"If the template was just regenerated, check that the React Email "
        f"source in frontend/emails/ still emits the literal {{{{ Name }}}} text."
    )


@pytest.mark.parametrize("email_type", sorted(EMAIL_TEMPLATES))
def test_template_has_no_bare_placeholder_identifiers(email_type: str) -> None:
    """No placeholder name appears outside ``{{ }}``.

    This is the specific failure mode of re-running ``pnpm run email:export``
    against sources that render bare identifiers: the name is still in the
    HTML, so a "is the name present?" check passes, but Jinja2 never
    substitutes it and the recipient sees the raw identifier.
    """
    html = _read_template(email_type)
    stripped = JINJA_PLACEHOLDER_RE.sub("", html)

    bare = sorted(name for name in ALL_PLACEHOLDER_NAMES if name in stripped)
    assert not bare, (
        f"{email_type}: placeholder name(s) {bare} appear outside a "
        f"{{{{ ... }}}} expression, so Jinja2 will not substitute them and "
        f"recipients would see the raw identifier. Fix the React Email source "
        f"in frontend/emails/, then run ./scripts/sync-email-templates.sh."
    )


@pytest.mark.parametrize("email_type", sorted(EMAIL_TEMPLATES))
def test_template_renders_without_leftover_placeholders(email_type: str) -> None:
    """Rendering with the declared context leaves no placeholder syntax behind."""
    from app.templates.email_renderer import TemplateRenderer

    context = {
        name: f"value-for-{name}"
        for name in EMAIL_TEMPLATES[email_type]["required_context"]
    }
    rendered = TemplateRenderer(template_dir=str(TEMPLATE_DIR)).render(
        EMAIL_TEMPLATES[email_type]["filename"], context
    )

    assert not JINJA_PLACEHOLDER_RE.search(rendered), (
        f"{email_type}: rendered output still contains {{{{ ... }}}} syntax"
    )
    for name in EMAIL_TEMPLATES[email_type]["required_context"]:
        assert f"value-for-{name}" in rendered, (
            f"{email_type}: context value for {name} did not reach the output"
        )
