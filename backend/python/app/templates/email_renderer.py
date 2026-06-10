"""Template rendering utilities using Jinja2"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


class TemplateRenderer:
    """Renders Jinja2 templates with variable substitution"""

    def __init__(
        self,
        template_dir: str = "./app/templates",
        logger: logging.Logger | None = None,
    ):
        """Initialize template renderer"""
        self.logger = logger or logging.getLogger(__name__)
        self.template_dir = Path(template_dir)

        # Create Jinja2 environment with HTML autoescaping enabled for security
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(enabled_extensions=("html", "xml")),
        )

    def render(self, template_name: str, context: dict) -> str:
        """Render a template with context variables
        Raises FileNotFoundError if template file doesn't exist, and jinja2.TemplateError if template rendering fails
        """
        try:
            template = self.env.get_template(template_name)
            rendered = template.render(context)
            # Fallback: replace any literal placeholders (e.g. Date_To_Replace) with context values
            # This supports older templates that used raw tokens instead of Jinja placeholders.
            try:
                for k, v in context.items():
                    # Only replace simple string tokens; convert values to str
                    rendered = rendered.replace(k, str(v))
            except Exception:
                # If replacement fails for any reason, continue with the rendered output
                pass
            self.logger.debug(f"Successfully rendered template: {template_name}")
            return rendered
        except Exception as e:
            self.logger.error(
                f"Failed to render template {template_name}: {e!s}", exc_info=True
            )
            raise
