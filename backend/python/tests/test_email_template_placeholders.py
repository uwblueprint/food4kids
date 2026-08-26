"""Guards the Jinja2 placeholders baked into the exported email templates.

The templates under ``app/templates`` are generated from the React Email
sources in ``frontend/emails`` via ``pnpm run email:export``. Those sources
render the placeholders as literal ``{{ Name }}`` text, so the export is
idempotent -- but nothing in the frontend toolchain knows which names the
backend actually substitutes. These tests are that link: if a regenerated
template loses a placeholder, gains one, or renames it, the mismatch fails
here instead of shipping an email that reads "Hi Driver_Name_To_Replace,".
"""

import logging
import re
from pathlib import Path

import pytest

from app.constants.email_config import EMAIL_TEMPLATES, FOOTER_CONTEXT_KEYS

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "app" / "templates"

# ``{{ Name }}`` as react-email emits it, tolerating arbitrary inner whitespace.
JINJA_PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")

# ``{% if Name %}`` / ``{% endif %}``. The footer wraps each optional contact
# link in one of these, so a name can legitimately appear inside a statement
# tag rather than an expression -- Jinja2 still evaluates it, so it is not a
# "bare identifier" leak.
JINJA_STATEMENT_RE = re.compile(r"\{%.*?%\}", re.DOTALL)

# Every placeholder name any template may legitimately use. Used to detect a
# name that survived export as bare text rather than a Jinja2 expression.
ALL_PLACEHOLDER_NAMES = {
    name for config in EMAIL_TEMPLATES.values() for name in config["required_context"]
} | set(FOOTER_CONTEXT_KEYS)


def _expected_placeholders(email_type: str) -> set[str]:
    """What a template may reference: its own context, plus the shared footer.

    The footer lives in the layout every template wraps itself in, so its
    variables appear in all four files while belonging to none of their
    ``required_context`` -- the dispatcher supplies those, not the caller.
    """
    return set(EMAIL_TEMPLATES[email_type]["required_context"]) | set(
        FOOTER_CONTEXT_KEYS
    )


def _read_template(email_type: str) -> str:
    path = TEMPLATE_DIR / EMAIL_TEMPLATES[email_type]["filename"]
    assert path.is_file(), f"Template file missing for {email_type}: {path}"
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("email_type", sorted(EMAIL_TEMPLATES))
def test_template_placeholders_match_required_context(email_type: str) -> None:
    """The template's ``{{ ... }}`` names are exactly its declared context."""
    html = _read_template(email_type)
    found = set(JINJA_PLACEHOLDER_RE.findall(html))
    expected = _expected_placeholders(email_type)

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
    stripped = JINJA_STATEMENT_RE.sub("", JINJA_PLACEHOLDER_RE.sub("", html))

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

    context = {name: f"value-for-{name}" for name in _expected_placeholders(email_type)}
    rendered = TemplateRenderer(template_dir=str(TEMPLATE_DIR)).render(
        EMAIL_TEMPLATES[email_type]["filename"], context
    )

    assert not JINJA_PLACEHOLDER_RE.search(rendered), (
        f"{email_type}: rendered output still contains {{{{ ... }}}} syntax"
    )
    for name in _expected_placeholders(email_type):
        assert f"value-for-{name}" in rendered, (
            f"{email_type}: context value for {name} did not reach the output"
        )


@pytest.mark.parametrize("email_type", sorted(EMAIL_TEMPLATES))
def test_footer_omits_links_the_org_has_not_configured(email_type: str) -> None:
    """A blank social URL drops its icon rather than rendering a dead link.

    The org may have no Facebook or Twitter -- the columns are nullable, and the
    design shows those fields empty. Rendering `href=""` would ship a link that
    silently goes nowhere, so the layout guards each one with `{% if %}`.
    """
    from app.templates.email_renderer import TemplateRenderer

    context = {
        name: f"value-for-{name}"
        for name in EMAIL_TEMPLATES[email_type]["required_context"]
    }
    context.update(dict.fromkeys(FOOTER_CONTEXT_KEYS, ""))

    rendered = TemplateRenderer(template_dir=str(TEMPLATE_DIR)).render(
        EMAIL_TEMPLATES[email_type]["filename"], context
    )

    assert 'href=""' not in rendered
    # The icons live inside the guarded blocks, so they go with the links.
    # Only the <img> matters: react-email also emits a <link rel="preload">
    # for every asset in <head>, and those are not conditional. A preload for
    # an image the body never shows is wasted bytes, not a broken link.
    for asset in ("facebook.png", "instagram.png", "x-logo.png"):
        assert f'src="/static/{asset}"' not in rendered, (
            f"{email_type}: {asset} icon rendered despite no configured URL"
        )


@pytest.mark.asyncio
async def test_footer_lookup_failure_does_not_fail_the_send(mocker: object) -> None:
    """A settings-read problem omits the footer rather than losing the email.

    The lookup is new: before it, nothing about dispatch touched the database,
    so a transient DB fault could not stop an email that was otherwise fine.
    That property is worth keeping -- the footer is decorative, the email is not.
    """
    from app.services.implementations.email_dispatcher import EmailDispatcher

    dispatcher = EmailDispatcher(
        email_service=mocker.MagicMock(),  # type: ignore[attr-defined]
        template_renderer=mocker.MagicMock(),  # type: ignore[attr-defined]
        logger=logging.getLogger("test"),
    )
    mocker.patch(  # type: ignore[attr-defined]
        "app.models.async_session_maker_instance",
        side_effect=RuntimeError("database is down"),
    )

    context = await dispatcher._org_contact_context()

    assert context == dict.fromkeys(FOOTER_CONTEXT_KEYS, "")

    # Emphatically NOT cached. get_email_dispatcher is @lru_cache'd, so there is
    # one dispatcher per process: caching the failure would leave every email
    # footerless until restart, long after the database recovered.
    assert getattr(dispatcher, "_org_contact", None) is None


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        ("https://facebook.com/F4K", "https://facebook.com/F4K"),
        ("http://facebook.com/F4K", "http://facebook.com/F4K"),
        # What an admin actually types when they do not paste a full URL.
        ("facebook.com/F4K", "https://facebook.com/F4K"),
        ("www.food4kidswr.ca", "https://www.food4kidswr.ca"),
        ("  facebook.com/F4K  ", "https://facebook.com/F4K"),
        (None, ""),
        ("", ""),
    ],
)
def test_social_urls_are_absolute(stored: str | None, expected: str) -> None:
    """A social link without a scheme is relative, and dead in every mail client.

    Nothing validates these on save: the column is a plain string and the admin
    form's `type="url"` never runs, because saving goes through a button
    handler rather than native form submission.
    """
    from app.services.implementations.email_dispatcher import _absolute_url

    assert _absolute_url(stored) == expected
