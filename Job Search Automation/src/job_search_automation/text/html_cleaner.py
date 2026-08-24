from __future__ import annotations

import html
import re


class HTMLCleaner:

    TAG_RE = re.compile(r"<[^>]+>")

    MULTIPLE_NEWLINES = re.compile(
        r"\n{3,}"
    )

    MULTIPLE_SPACES = re.compile(
        r"[ \t]{2,}"
    )

    @classmethod
    def clean(
        cls,
        text: str | None,
    ) -> str:

        if not text:

            return ""

        cleaned = html.unescape(
            text
        )

        replacements = {

            "</p>": "\n\n",
            "</div>": "\n",
            "</section>": "\n",
            "</li>": "\n",
            "<br>": "\n",
            "<br/>": "\n",
            "<br />": "\n",
            "</h1>": "\n\n",
            "</h2>": "\n\n",
            "</h3>": "\n\n",
            "</h4>": "\n\n",
            "</ul>": "\n",
            "</ol>": "\n",
        }

        for old, new in replacements.items():

            cleaned = cleaned.replace(
                old,
                new,
            )

        cleaned = cls.TAG_RE.sub(
            "",
            cleaned,
        )

        cleaned = cls.MULTIPLE_SPACES.sub(
            " ",
            cleaned,
        )

        cleaned = cls.MULTIPLE_NEWLINES.sub(
            "\n\n",
            cleaned,
        )

        return cleaned.strip()