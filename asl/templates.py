"""Prompts and offline fallbacks for the drafting pipeline."""

from __future__ import annotations

from textwrap import dedent


def _excerpt(text: str, limit: int) -> str:
    return text[:limit].strip() or "TODO"


SYSTEM_POLICY = dedent(
    """
    You are assisting with transparent academic drafting. Do not invent data,
    sources, citations, quotes, empirical results, institutional facts, or
    statistical significance. If evidence is missing, mark it as TODO. Prefer
    explicit uncertainty over polish.
    """
).strip()


NO_TOOLS_POLICY = dedent(
    """
    You are running in non-interactive text-generation mode and have NO tools.
    Do NOT read files, write or create files, or run shell commands, and do NOT
    describe tool calls. Output the COMPLETE requested deliverable directly and in
    full as your text response (for example, the entire Markdown document inline).
    Your whole response is captured verbatim as the deliverable.
    """
).strip()


def plan_prompt(manifest: dict, brief: str, previous: str | None = None) -> str:
    prompt = dedent(
        f"""
        Create a research plan for a paper draft.

        Title: {manifest["title"]}
        Topic: {manifest["topic"]}
        Research question: {manifest.get("research_question", "TODO")}

        Brief:
        """
    ).strip()
    prompt = f"{prompt}\n{brief.strip() or 'TODO'}"

    prompt += "\n\n" + dedent(
        """
        Return sections:
        1. Claim boundary
        2. Required evidence
        3. Data or source plan
        4. Method plan
        5. Outline
        6. Risks and TODOs
        """
    ).strip()
    if previous:
        prompt += f"\n\nPrevious draft to improve:\n{_excerpt(previous, 6000)}"
    return prompt


def _focus_instruction(focus: tuple[str, ...] | list[str]) -> str:
    if not focus:
        return ""
    names = ", ".join(focus)
    return dedent(
        f"""
        Focus references for this draft: {names}
        Each of these files' text is included in the Brief below. Engage them
        substantively (define, attribute, and use their content), prioritising
        any the previous draft has not yet analysed.
        """
    ).strip()


_AVAILABILITY_RULE = (
    "- Any reference whose text appears in the Brief below is available evidence; "
    'never describe a provided reference as unavailable, missing, not extractable, '
    'or "text-pending". If you choose not to use one, give a specific reason.'
)


def draft_prompt(
    manifest: dict, plan: str, brief: str, previous: str | None = None,
    focus: tuple[str, ...] | list[str] = (),
) -> str:
    prompt = dedent(
        f"""
        Write a cautious academic working-paper draft in Markdown.

        Title: {manifest["title"]}
        Topic: {manifest["topic"]}

        Rules:
        - Use [TODO: citation] instead of fake citations.
        - Use [TODO: evidence] instead of unsupported empirical claims.
        - Do not report results unless they are supplied in the brief or plan.
        - Include an Evidence Ledger section listing every factual claim that
          needs verification.
        {_AVAILABILITY_RULE}
        """
    ).strip()
    focus_block = _focus_instruction(focus)
    if focus_block:
        prompt += f"\n\n{focus_block}"
    prompt += f"\n\nBrief:\n{brief.strip() or 'TODO'}"

    prompt += f"\n\nResearch plan:\n{plan.strip() or 'TODO'}"
    if previous:
        prompt += f"\n\nPrevious draft to revise:\n{_excerpt(previous, 8000)}"
    return prompt


def iterative_draft_prompt(
    manifest: dict,
    plan: str,
    brief: str,
    previous_draft: str,
    review_summary: str,
    revision_plan: str,
    focus: tuple[str, ...] | list[str] = (),
) -> str:
    prompt = dedent(
        f"""
        Improve this academic working-paper draft in Markdown. This is an
        iteration cycle — a previous draft was reviewed and you should make
        targeted improvements, not rewrite from scratch.

        Title: {manifest["title"]}
        Topic: {manifest["topic"]}

        Rules:
        - Use [TODO: citation] instead of fake citations.
        - Use [TODO: evidence] instead of unsupported empirical claims.
        - Do not report results unless they are supplied in the brief or plan.
        - Preserve content that reviewers did not flag as problematic.
        - Focus improvement effort on the review findings and revision checklist
          below, and on integrating this cycle's focus references, rather than
          reorganising sections that reviewers accepted.
        {_AVAILABILITY_RULE}
        """
    ).strip()
    focus_block = _focus_instruction(focus)
    if focus_block:
        prompt += f"\n\n{focus_block}"
    prompt += f"\n\nReview findings:\n{_excerpt(review_summary, 4000)}"
    prompt += f"\n\nRevision checklist:\n{_excerpt(revision_plan, 3000)}"
    prompt += f"\n\nBrief:\n{brief.strip() or 'TODO'}"
    prompt += f"\n\nResearch plan:\n{plan.strip() or 'TODO'}"
    prompt += f"\n\nPrevious draft to improve:\n{_excerpt(previous_draft, 16000)}"
    return prompt


def review_prompt(manifest: dict, draft: str, reviewer: str) -> str:
    prompt = dedent(
        f"""
        Review this draft as the {reviewer} reviewer.

        Title: {manifest["title"]}

        Prioritize:
        - unsupported claims
        - missing citations or evidence
        - causal identification weaknesses
        - overclaiming
        - unclear structure

        Output:
        1. Major issues
        2. Minor issues
        3. Required revisions
        4. Accept/revise/reject recommendation
        5. Underused references: <comma-separated source filenames (e.g. 4.pdf, 19.pdf) that are named or relevant but not substantively engaged, and that the next revision should draw on; write "none" if all are well used>

        Draft:
        """
    ).strip()
    return f"{prompt}\n{_excerpt(draft, 10000)}"


def revision_prompt(manifest: dict, draft: str, reviews: list[str]) -> str:
    joined = "\n\n---\n\n".join(reviews)
    prompt = dedent(
        f"""
        Create a concrete revision plan.

        Title: {manifest["title"]}

        Draft:
        """
    ).strip()
    prompt = f"{prompt}\n{_excerpt(draft, 8000)}\n\nReviews:\n{_excerpt(joined, 10000)}"

    prompt += "\n\n" + dedent(
        """
        Return:
        1. Non-negotiable fixes
        2. Evidence to collect
        3. Structural edits
        4. Claims to soften or remove
        5. Next-version checklist
        """
    ).strip()
    return prompt


def topic_discovery_prompt(manifest: dict, brief: str, count: int = 3) -> str:
    prompt = dedent(
        f"""
        You are given a corpus of references, each shown with its source filename.
        Survey ALL of them, then propose {count} distinct, defensible research
        topics the corpus could support.

        Workspace title: {manifest["title"]}

        For EACH topic return exactly this block (best topic first):
        ## Topic <n>
        Topic: <one sentence topic>
        Research question: <one focused research question>
        Anchor papers: <3-5 source filenames this topic centres on, comma-separated, e.g. 10.pdf, 12.pdf, 18.pdf>
        Rationale: <why the corpus supports it; which papers are central vs peripheral>

        After the {count} blocks add one line:
        Evidence boundary: <what the corpus can and cannot support overall>

        Centre each topic on papers that have substantive text in the corpus; a
        paper shown only as a title or a single line is a weak anchor. Use the exact
        filenames as they appear in the source material.

        Source material (all references, briefly):
        """
    ).strip()
    return f"{prompt}\n{_excerpt(brief, 28000)}"


def score_prompt(manifest: dict, previous_draft: str, candidate_draft: str) -> str:
    prompt = dedent(
        f"""
        Compare a candidate paper draft against the currently accepted draft.

        Title: {manifest["title"]}
        Topic: {manifest["topic"]}

        Criteria:
        - better evidence discipline and fewer unsupported claims
        - clearer research question and contribution
        - more coherent structure
        - stronger handling of limitations
        - no invented citations, data, results, or overclaiming

        Return only JSON with keys:
        verdict: "better", "same", or "worse"
        previous_score: integer 1-10
        candidate_score: integer 1-10
        rationale: concise explanation

        Accepted draft:
        """
    ).strip()
    return f"{prompt}\n{_excerpt(previous_draft, 9000)}\n\nCandidate draft:\n{_excerpt(candidate_draft, 9000)}"


def offline_topic_discovery(manifest: dict, brief: str, count: int = 3) -> str:
    topic = manifest.get("topic") or "evidence-led topic from supplied materials"
    if "TODO: discover" in topic:
        topic = "Evidence-led topic from supplied data and references"
    anchors = ", ".join(_first_filenames(brief, 3)) or "TODO: anchor papers"
    blocks = []
    for index in range(1, max(1, count) + 1):
        blocks.append(
            dedent(
                f"""
                ## Topic {index}
                Topic: {topic} (angle {index})
                Research question: What question can be responsibly answered with the supplied data and references (angle {index})?
                Anchor papers: {anchors}
                Rationale: Reviewed offline; anchor papers chosen as those with the most substantive supplied text. Treat all claims as provisional.
                """
            ).strip()
        )
    body = "\n\n".join(blocks)
    return f"{body}\n\nEvidence boundary: Treat all claims as provisional until the loaded materials are mapped into an evidence ledger.\n\nMaterial snapshot:\n{_excerpt(brief, 1200)}"


def _first_filenames(text: str, limit: int) -> list[str]:
    import re

    seen: list[str] = []
    for match in re.findall(r"[\w.\-]+\.(?:pdf|docx?|md|txt|csv|xlsx?)", text):
        if match not in seen:
            seen.append(match)
        if len(seen) >= limit:
            break
    return seen


def offline_score(manifest: dict, previous_draft: str, candidate_draft: str) -> str:
    previous_score = _heuristic_draft_score(previous_draft)
    candidate_score = _heuristic_draft_score(candidate_draft)
    if candidate_score > previous_score:
        verdict = "better"
    elif candidate_score < previous_score:
        verdict = "worse"
    else:
        verdict = "same"
    return (
        "{\n"
        f'  "verdict": "{verdict}",\n'
        f'  "previous_score": {previous_score},\n'
        f'  "candidate_score": {candidate_score},\n'
        '  "rationale": "Offline heuristic rewards structure, evidence ledgers, and fewer unresolved TODO markers."\n'
        "}"
    )


def offline_plan(manifest: dict, brief: str, previous: str | None = None) -> str:
    revision_note = "This version should respond to the previous review cycle." if previous else "This is the initial plan."
    template = dedent(
        f"""
        # Research Plan

        ## Claim Boundary
        This project will draft a working paper about **{manifest["topic"]}**. {revision_note}
        Claims must remain provisional until the evidence ledger is filled.

        ## Required Evidence
        - Primary sources or datasets for the core institutional facts.
        - A reproducible data-cleaning path if empirical claims are made.
        - A citation ledger mapping each non-obvious claim to a source.

        ## Data Or Source Plan
        Start with public sources listed in the topic brief. If none are listed,
        create `sources.json` before treating any factual claim as established.

        ## Method Plan
        Use descriptive synthesis by default. Escalate to causal language only
        after the design, assumptions, sample construction, and robustness checks
        are documented.

        ## Outline
        1. Introduction and research question
        2. Background and institutional setting
        3. Evidence and data
        4. Method
        5. Findings or expected analyses
        6. Limitations
        7. Conclusion

        ## Risks And TODOs
        - [TODO: citation] for all institutional claims.
        - [TODO: evidence] for all empirical claims.
        - Avoid fake precision, fake references, and unverified quotes.

        ## Topic Brief Snapshot
        """
    ).strip()
    return f"{template}\n{_excerpt(brief, 1200)}"


def offline_draft(manifest: dict, plan: str, brief: str, previous: str | None = None) -> str:
    version_note = "This draft incorporates a prior version and should be tightened against reviewer comments." if previous else "This is a first-pass scaffold."
    template = dedent(
        f"""
        # {manifest["title"]}

        ## Abstract
        {version_note} The paper examines {manifest["topic"]}. The current version is a transparent
        drafting artifact: factual claims, citations, and empirical results remain marked as TODO
        until verified.

        ## 1. Introduction
        The motivating question is: **{manifest.get("research_question", "TODO")}**.
        This section should explain why the question matters without asserting unverified results.
        [TODO: citation]

        ## 2. Background
        The institutional or literature background belongs here. Each claim about policy timing,
        prior studies, or mechanisms should be linked to the evidence ledger. [TODO: evidence]

        ## 3. Evidence And Data
        This version does not assume that data have already been collected. Add dataset names,
        access dates, construction rules, and known limitations before reporting results.

        ## 4. Method
        The default design is descriptive synthesis. If a causal strategy is used, document the
        identifying assumption, unit of analysis, treatment timing, comparison group, and failure
        modes before writing causal conclusions.

        ## 5. Draft Findings
        No findings are reported yet. Replace this paragraph only after analyses are reproducible
        and tables or figures have been generated by code.

        ## 6. Limitations
        Current limitations include missing verified sources, missing data provenance, and no
        completed empirical checks.

        ## 7. Conclusion
        The next iteration should collect evidence, resolve TODOs, and narrow claims rather than
        adding polish ahead of substance.

        ## Evidence Ledger
        - Claim: Topic importance. Status: [TODO: citation]
        - Claim: Institutional background. Status: [TODO: source]
        - Claim: Empirical relationship. Status: [TODO: evidence]

        ## Brief Used
        """
    ).strip()
    return f"{template}\n{_excerpt(brief, 1000)}\n\n## Plan Used\n{_excerpt(plan, 1000)}"


def offline_review(manifest: dict, draft: str, reviewer: str) -> str:
    template = dedent(
        f"""
        # {reviewer.title()} Review

        Draft: **{manifest["title"]}**
        Topic: **{manifest["topic"]}**

        ## Major Issues
        - The draft contains TODO markers that must be resolved before it can be treated as a paper.
        - The evidence ledger is present, but sources and data provenance are incomplete.
        - Any causal language should remain conditional until an identification design is specified.

        ## Minor Issues
        - The introduction should separate motivation from claims.
        - The method section should name the intended unit of analysis.

        ## Required Revisions
        - Add a `sources.json` or equivalent citation ledger.
        - Replace unsupported claims with sourced statements or remove them.
        - Add reproducible analysis code before reporting results.

        ## Recommendation
        Revise.

        ## Draft Snapshot
        """
    ).strip()
    return f"{template}\n{_excerpt(draft, 1000)}"


def offline_revision(manifest: dict, draft: str, reviews: list[str]) -> str:
    joined_reviews = "\n\n---\n\n".join(reviews)
    template = dedent(
        f"""
        # Revision Plan

        Paper: **{manifest["title"]}**
        Topic: **{manifest["topic"]}**
        Review count: {len(reviews)}

        ## Non-Negotiable Fixes
        - Fill the evidence ledger before strengthening claims.
        - Keep unverifiable statements marked as TODO or remove them.
        - Add analysis scripts before reporting empirical results.

        ## Evidence To Collect
        - Primary institutional sources.
        - Public data documentation.
        - Prior literature with stable bibliographic metadata.

        ## Structural Edits
        - Move speculative mechanisms into a clearly labeled theory section.
        - Keep findings separate from proposed analyses.

        ## Claims To Soften Or Remove
        - Any causal claim without a stated design.
        - Any numerical claim without a reproducible source.

        ## Next-Version Checklist
        - [ ] Add sources.
        - [ ] Add data plan or analysis code.
        - [ ] Resolve TODO markers.
        - [ ] Re-run reviewer cycle.

        ## Draft Snapshot
        """
    ).strip()
    return f"{template}\n{_excerpt(draft, 1200)}\n\n## Review Signals\n{_excerpt(joined_reviews, 1600)}"


def _heuristic_draft_score(draft: str) -> int:
    text = draft.lower()
    score = 5
    score += min(2, text.count("##") // 3)
    if "evidence ledger" in text:
        score += 1
    if "limitations" in text:
        score += 1
    todo_count = text.count("[todo")
    score -= min(3, todo_count // 4)
    if len(draft) < 1200:
        score -= 1
    return max(1, min(10, score))
