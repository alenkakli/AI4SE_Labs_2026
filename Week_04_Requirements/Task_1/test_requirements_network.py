import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pydantic import ValidationError

from requirements_network import (
    Evidence,
    ExtractionResult,
    NetworkSettings,
    RequirementDraft,
    ReconciliationResult,
    ReviewFinding,
    ReviewResult,
    SourceDocument,
    build_graph,
    chunk_sources,
    discover_sources,
    render_markdown,
    route_after_review,
    validate_and_assign_ids,
    _load_api_key,
)


class RequirementsNetworkOfflineTests(unittest.TestCase):
    def test_credentials_load_from_dotenv_without_printing_them(self):
        with tempfile.TemporaryDirectory() as temporary:
            dotenv_path = Path(temporary) / ".env"
            dotenv_path.write_text(
                "OPENAI_API_KEY=test-only-placeholder\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(
                    _load_api_key(dotenv_path),
                    "test-only-placeholder",
                )

    def test_discovery_is_recursive_and_preserves_relative_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "nested").mkdir()
            (root / "nested" / "thread.eml").write_text(
                "From: reader@example.test\nSubject: Report needs\n\n"
                "A report must show active items for each branch.\n",
                encoding="utf-8",
            )
            (root / "readme.md").write_text("not supported", encoding="utf-8")
            documents, errors = discover_sources(root)

        self.assertEqual(errors, [])
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].path, "nested/thread.eml")
        self.assertEqual(documents[0].subject, "Report needs")

    def test_chunking_retains_filename_heading_lines_and_email_boundaries(self):
        document = SourceDocument(
            source_id="SRC-EXAMPLE",
            path="nested/thread.eml",
            status="read",
            text=(
                "Subject: Reports\n\n"
                "MISSING ITEMS\n"
                "The system shall report all missing items by branch, including "
                "their current status and the last date on which the item was seen.\n\n"
                "===\n"
                "IN-TRANSIT ITEMS\n"
                "The system shall list items that have remained in transit longer "
                "than the configured number of days.\n"
            ),
        )
        chunks, errors = chunk_sources([document], max_chars=110, overlap_chars=20)

        self.assertEqual(errors, [])
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.path == "nested/thread.eml" for chunk in chunks))
        self.assertTrue(all(chunk.locator.startswith("lines ") for chunk in chunks))
        self.assertTrue(any("MISSING ITEMS" in chunk.text for chunk in chunks))
        self.assertTrue(any("IN-TRANSIT ITEMS" in chunk.text for chunk in chunks))
        self.assertTrue(all(chunk.chunk_id.startswith("CHUNK-") for chunk in chunks))

    def test_stable_ids_ignore_candidate_completion_order(self):
        document = SourceDocument(
            source_id="SRC-1",
            path="notes.txt",
            status="read",
            text="The system shall retain an audit history for every change.",
        )
        chunks, _ = chunk_sources([document])
        evidence = Evidence(
            source_id=document.source_id,
            chunk_id=chunks[0].chunk_id,
            quote="retain an audit history for every change",
        )
        first = RequirementDraft(
            short_name="Audit history",
            explanation=(
                "The system shall retain an audit history for every change made "
                "to a record, including the actor and time of the change."
            ),
            priority="Unassigned",
            priority_rationale="The evidence does not assign a stakeholder priority.",
            evidence=[evidence],
        )
        second = RequirementDraft(
            short_name="Search reports",
            explanation=(
                "The system shall allow authorized staff to search available reports "
                "by title and filter results by branch."
            ),
            priority="Medium",
            priority_rationale="The source requests this function without urgency.",
            evidence=[evidence],
        )

        result_one, _, _ = validate_and_assign_ids([first, second], [], [], chunks)
        result_two, _, _ = validate_and_assign_ids([second, first], [], [], chunks)
        ids_one = {item.short_name: item.req_id for item in result_one}
        ids_two = {item.short_name: item.req_id for item in result_two}
        self.assertEqual(ids_one, ids_two)
        self.assertEqual(len(set(ids_one.values())), 2)

    def test_invalid_provenance_is_excluded_and_disclosed(self):
        chunks = []
        bad_requirement = RequirementDraft(
            short_name="Unsupported item",
            explanation=(
                "The system shall provide an unsupported behavior that has no "
                "corresponding evidence in the source documents."
            ),
            priority="Low",
            priority_rationale="The source presents this as optional.",
            evidence=[
                Evidence(
                    source_id="SRC-UNKNOWN",
                    chunk_id="CHUNK-UNKNOWN",
                    quote="unsupported evidence quote",
                )
            ],
        )
        errors = []
        records, _, _ = validate_and_assign_ids(
            [bad_requirement], [], [], chunks, errors=errors
        )

        self.assertEqual(records, [])
        self.assertTrue(any("Invalid evidence reference" in error for error in errors))
        self.assertTrue(any("Excluded requirement candidate" in error for error in errors))

    def test_evidence_validation_accepts_line_wrapped_verbatim_quotes(self):
        source = SourceDocument(
            source_id="SRC-WRAPPED",
            path="wrapped.txt",
            status="read",
            text="Staff can search\nreports by branch.",
        )
        chunks, _ = chunk_sources([source])
        requirement = RequirementDraft(
            short_name="Branch report search",
            explanation=(
                "The system shall allow staff to search reports by branch. "
                "Search results shall be limited to reports the staff member may access."
            ),
            priority="Unassigned",
            priority_rationale="The source does not specify a stakeholder priority.",
            evidence=[
                Evidence(
                    source_id=source.source_id,
                    chunk_id=chunks[0].chunk_id,
                    quote="Staff can search reports by branch",
                )
            ],
        )

        records, _, _ = validate_and_assign_ids(
            [requirement], [], [], chunks
        )

        self.assertEqual(len(records), 1)

    def test_requirement_schema_rejects_missing_paragraph_or_evidence(self):
        with self.assertRaises(ValidationError):
            RequirementDraft(
                short_name="Short",
                explanation="Too short.",
                priority="High",
                priority_rationale="This is explicitly high priority.",
                evidence=[],
            )

    def test_rendering_has_one_document_traceability_blacklist_and_status(self):
        source = SourceDocument(
            source_id="SRC-1",
            path="notes.txt",
            status="read",
            text="Staff need a search feature for their daily work.",
        )
        chunks, _ = chunk_sources([source])
        evidence = Evidence(
            source_id=source.source_id,
            chunk_id=chunks[0].chunk_id,
            quote="Staff need a search feature for their daily work",
        )
        requirement, _, _ = validate_and_assign_ids(
            [
                RequirementDraft(
                    short_name="Search records",
                    explanation=(
                        "The system shall let authorized staff search records using "
                        "the supported fields required for their daily work."
                    ),
                    priority="Unassigned",
                    priority_rationale="The source does not specify a priority.",
                    evidence=[evidence],
                )
            ],
            [],
            [],
            chunks,
        )
        markdown, status = render_markdown(
            source_files=[source],
            chunks=chunks,
            requirements=requirement,
            discarded=[],
            conflicts=[],
            findings=[],
            processing_errors=[],
            correction_rounds=0,
            max_correction_rounds=2,
            coverage_completed={chunks[0].chunk_id},
            independent_completed={chunks[0].chunk_id},
            reviewed_chunk_ids={chunks[0].chunk_id},
        )

        self.assertEqual(status, "complete")
        self.assertIn("## Requirements", markdown)
        self.assertIn("## Blacklist / discarded candidates", markdown)
        self.assertIn("## Coverage and processing status", markdown)
        self.assertIn("`notes.txt`", markdown)
        self.assertIn(requirement[0].req_id, markdown)
        self.assertIn("### Chunk-level coverage", markdown)
        self.assertIn(chunks[0].chunk_id, markdown)
        self.assertIn("1/1; 1/1; 1/1", markdown)

    def test_feedback_loop_stops_at_configured_cap(self):
        state = {
            "correction_rounds": 1,
            "findings": [
                {"actionable": True, "chunk_ids": ["CHUNK-1"]}
            ],
        }
        self.assertEqual(route_after_review(state, 2), "correct")
        state["correction_rounds"] = 2
        self.assertEqual(route_after_review(state, 2), "render")
        self.assertEqual(route_after_review(state, 0), "render")

    def test_settings_keep_retries_concurrency_and_feedback_bounded(self):
        with self.assertRaises(ValidationError):
            NetworkSettings(max_retries=6)
        with self.assertRaises(ValidationError):
            NetworkSettings(max_correction_rounds=3)

    def test_graph_runs_full_feedback_cycle_with_fake_clients_only(self):
        evidence_quote = "The system shall show a report for each branch."
        requirement = RequirementDraft(
            short_name="Branch report",
            explanation=(
                "The system shall show a report for each branch. Authorized staff "
                "shall be able to review the report for their assigned location."
            ),
            priority="Unassigned",
            priority_rationale="The source does not specify a stakeholder priority.",
            evidence=[
                Evidence(
                    source_id="SRC-placeholder",
                    chunk_id="CHUNK-placeholder",
                    quote=evidence_quote,
                )
            ],
        )

        class FakeExtractor:
            def invoke(self, messages):
                payload = json.loads(messages[1][1])
                chunk = payload["evidence_chunk"]
                item = requirement.model_copy(
                    update={
                        "evidence": [
                            Evidence(
                                source_id=chunk["source_id"],
                                chunk_id=chunk["chunk_id"],
                                quote=evidence_quote,
                            )
                        ]
                    }
                )
                return ExtractionResult(requirements=[item])

        class FakeReconciler:
            def invoke(self, messages):
                payload = json.loads(messages[1][1])
                if "candidates" in payload:
                    candidate = RequirementDraft.model_validate(payload["candidates"][0])
                else:
                    candidate_data = dict(payload["requirements"][0])
                    candidate_data.pop("req_id", None)
                    candidate_data.pop("review_status", None)
                    candidate = RequirementDraft.model_validate(candidate_data)
                return ReconciliationResult(
                    requirements=[candidate],
                    discarded=[],
                    conflicts=[],
                )

        class FakeReviewer:
            def __init__(self):
                self.calls = 0

            def invoke(self, messages):
                if not messages:
                    raise AssertionError("Expected review prompt messages")
                self.calls += 1
                if self.calls == 1:
                    return ReviewResult(
                        findings=[
                            ReviewFinding(
                                category="quality",
                                description="The requirement needs a final editorial check.",
                                proposed_fix="Recheck the cited sentence.",
                            )
                        ]
                    )
                return ReviewResult(findings=[])

        reviewer = FakeReviewer()
        fake_clients = SimpleNamespace(
            coverage=FakeExtractor(),
            independent=FakeExtractor(),
            reconciliation=FakeReconciler(),
            review=reviewer,
        )
        settings = NetworkSettings(max_correction_rounds=1)

        with tempfile.TemporaryDirectory() as temporary:
            input_dir = Path(temporary)
            (input_dir / "requirements.txt").write_text(
                evidence_quote, encoding="utf-8"
            )
            result = build_graph(settings, fake_clients).invoke(
                {"input_dir": str(input_dir), "correction_rounds": 0}
            )

        self.assertEqual(result["correction_rounds"], 1)
        self.assertEqual(reviewer.calls, 2)
        self.assertEqual(result["run_status"], "complete")
        self.assertIn("Branch report", result["document"])


if __name__ == "__main__":
    unittest.main()
