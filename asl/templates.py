"""Prompts and offline fallbacks for the drafting pipeline."""

from __future__ import annotations

from textwrap import dedent


SYSTEM_POLICY = dedent(
    """
    You are assisting with transparent academic drafting. Do not invent data,
    sources, citations, quotes, empirical results, institutional facts, or
    statistical significance. If evidence is missing, mark it as TODO. Prefer
    explicit uncertainty over polish.
    """
).strip()


def plan_prompt(manifest: dict, brief: str, previous: str | None = None) -> str:
    prior = f"\n\nPrevious draft to improve:\n{previous[:6000]}" if previous else ""
    return dedent(
        f"""
        Create a research plan for a paper draft.

        Title: {manifest["title"]}
        Topic: {manifest["topic"]}
        Research question: {manifest.get("research_question", "TODO")}

        Brief:
        {brief}

        Return sections:
        1. Claim boundary
        2. Required evidence
        3. Data or source plan
        4. Method plan
        5. Outline
        6. Risks and TODOs
        {prior}
        """
    ).strip()


def draft_prompt(manifest: dict, plan: str, brief: str, previous: str | None = None) -> str:
    prior = f"\n\nPrevious draft to revise:\n{previous[:8000]}" if previous else ""
    return dedent(
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

        Brief:
        {brief}

        Research plan:
        {plan}
        {prior}
        """
    ).strip()


def review_prompt(manifest: dict, draft: str, reviewer: str) -> str:
    return dedent(
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

        Draft:
        {draft[:10000]}
        """
    ).strip()


def revision_prompt(manifest: dict, draft: str, reviews: list[str]) -> str:
    joined = "\n\n---\n\n".join(reviews)
    return dedent(
        f"""
        Create a concrete revision plan.

        Title: {manifest["title"]}

        Draft:
        {draft[:8000]}

        Reviews:
        {joined[:10000]}

        Return:
        1. Non-negotiable fixes
        2. Evidence to collect
        3. Structural edits
        4. Claims to soften or remove
        5. Next-version checklist
        """
    ).strip()


def offline_plan(manifest: dict, brief: str, previous: str | None = None) -> str:
    revision_note = "This version should respond to the previous review cycle." if previous else "This is the initial plan."
    return dedent(
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
        {brief[:1200]}
        """
    ).strip()


def offline_draft(manifest: dict, plan: str, brief: str, previous: str | None = None) -> str:
    version_note = "This draft incorporates a prior version and should be tightened against reviewer comments." if previous else "This is a first-pass scaffold."
    return dedent(
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
        {brief[:1000]}

        ## Plan Used
        {plan[:1000]}
        """
    ).strip()


def offline_review(manifest: dict, draft: str, reviewer: str) -> str:
    return dedent(
        f"""
        # {reviewer.title()} Review

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
        """
    ).strip()


def offline_revision(manifest: dict, draft: str, reviews: list[str]) -> str:
    return dedent(
        """
        # Revision Plan

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
        """
    ).strip()

