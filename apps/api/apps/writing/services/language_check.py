"""
Wrapper around LanguageTool (self-hosted server, see the `languagetool`
service added to docker-compose.yml).

LanguageTool finds both spelling and grammar issues in a single pass; we
split them after the fact using `rule_issue_type`/`category`, the same way
LanguageTool itself does: rule_issue_type == "misspelling" (usually
category == "TYPOS") is orthography, everything else is grammar (including
tense agreement, word order, punctuation, style, etc.).

Known limitation (always surfaced via WritingResult.limitations):
LanguageTool is a rule-based tool. It does not understand meaning, so it:
  - misses semantically wrong but grammatically valid phrases;
  - can miss errors that require deeper context;
  - the quality of the spelling/grammar split depends on LanguageTool's own
    internal rule classification, not on a separate heuristic of ours.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

import language_tool_python
from django.conf import settings

logger = logging.getLogger(__name__)

# LanguageTool rules that are technically flagged "misspelling" but are
# genuinely orthography (word spelling) issues rather than grammar.
_SPELLING_ISSUE_TYPES = {"misspelling"}
_SPELLING_CATEGORIES = {"TYPOS"}


@dataclass(frozen=True)
class SpellingIssue:
    word: str
    suggestion: str
    error_type: str
    start_offset: int
    end_offset: int


@dataclass(frozen=True)
class GrammarIssue:
    fragment: str
    suggestion: str
    short_description: str
    rule_id: str
    category: str
    start_offset: int
    end_offset: int


@dataclass(frozen=True)
class LanguageCheckResult:
    spelling_issues: list[SpellingIssue]
    grammar_issues: list[GrammarIssue]


class LanguageCheckError(RuntimeError):
    """Could not get a response from the LanguageTool server."""


@lru_cache(maxsize=1)
def _get_tool() -> "language_tool_python.LanguageTool":
    remote_url = getattr(settings, "LANGUAGETOOL_SERVER_URL", "")
    if remote_url:
        return language_tool_python.LanguageTool("en-US", remote_server=remote_url)

    # No remote server configured (LANGUAGETOOL_SERVER_URL is empty) - fall
    # back to language_tool_python's own auto-managed local server. This is
    # the no-Docker local dev path: on first use it downloads LanguageTool
    # (~200 MB) and starts it as a local Java process, so it requires a
    # JRE 17+ on PATH and can take a couple of minutes the first time only
    # (cached under ~/.cache afterwards). This is NOT meant for
    # staging/production - use the `languagetool` docker-compose service
    # (i.e. set LANGUAGETOOL_SERVER_URL) there instead, see
    # apps/writing/README.md.
    logger.info(
        "LANGUAGETOOL_SERVER_URL is not set - starting an auto-managed "
        "local LanguageTool instance (requires Java; first run downloads "
        "~200 MB and may take a while)."
    )
    return language_tool_python.LanguageTool("en-US")


def _is_spelling_match(match) -> bool:
    issue_type = (getattr(match, "rule_issue_type", "") or "").lower()
    category = getattr(match, "category", "") or ""
    return issue_type in _SPELLING_ISSUE_TYPES or category in _SPELLING_CATEGORIES


def check_text(text: str) -> LanguageCheckResult:
    """
    Runs the text through LanguageTool and returns separate spelling and
    grammar finding lists.
    """
    if not text or not text.strip():
        return LanguageCheckResult(spelling_issues=[], grammar_issues=[])

    try:
        tool = _get_tool()
        matches = tool.check(text)
    except Exception as exc:  # noqa: BLE001 - network/protocol errors from the external service
        logger.exception("LanguageTool check failed")
        raise LanguageCheckError(str(exc)) from exc

    spelling: list[SpellingIssue] = []
    grammar: list[GrammarIssue] = []

    for match in matches:
        offset = match.offset
        length = getattr(match, "error_length", 0) or 0
        end_offset = offset + length
        fragment = text[offset:end_offset]
        replacements = getattr(match, "replacements", []) or []
        suggestion = replacements[0] if replacements else ""

        if _is_spelling_match(match):
            spelling.append(
                SpellingIssue(
                    word=fragment,
                    suggestion=suggestion,
                    error_type=getattr(match, "rule_id", "") or "",
                    start_offset=offset,
                    end_offset=end_offset,
                )
            )
        else:
            grammar.append(
                GrammarIssue(
                    fragment=fragment,
                    suggestion=suggestion,
                    short_description=getattr(match, "message", "") or "",
                    rule_id=getattr(match, "rule_id", "") or "",
                    category=getattr(match, "category", "") or "",
                    start_offset=offset,
                    end_offset=end_offset,
                )
            )

    return LanguageCheckResult(spelling_issues=spelling, grammar_issues=grammar)
