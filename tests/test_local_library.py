import tempfile
import unittest
from pathlib import Path

from server.library import LibraryError, ReadOnlyLibrary, create_workspace_markdown


class LocalLibraryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name) / "Merrick Library"
        self.library = ReadOnlyLibrary(root=root, cache_root=Path(self.temp.name) / "cache")
        root.mkdir(parents=True)
        (root / "attention-paper.md").write_text(
            "# Attention paper\n\nThe method uses a sparse attention layer.\n\n"
            "## Results\n\nThe experiment improves accuracy by ten percent.",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_only_reads_files_inside_the_dedicated_library(self) -> None:
        selected = self.library.choose_document("Read the attention paper")
        document = self.library.read_document(selected)
        self.assertEqual(document.relative_path, "attention-paper.md")
        self.assertIn("sparse attention", document.text)
        with self.assertRaises(LibraryError):
            self.library.read_document(Path(self.temp.name) / "outside.txt")

    def test_context_is_ranked_and_bounded(self) -> None:
        document = self.library.read_document(
            self.library.choose_document("review attention paper")
        )
        context = self.library.relevant_context(document, "What are the experimental results?")
        self.assertEqual(context["kind"], "local_document")
        self.assertIn("Results", str(context["text"]))
        self.assertLessEqual(len(str(context["text"])), 11_000)

    def test_pdf_text_is_extracted_locally(self) -> None:
        pdf = self.library.root / "local-paper.pdf"
        _write_simple_pdf(pdf, "MERRICK extracted this PDF result")
        document = self.library.read_document(pdf)
        self.assertIn("MERRICK extracted this PDF result", document.text)

    def test_ambiguous_library_does_not_guess(self) -> None:
        (self.library.root / "vision-paper.md").write_text("vision", encoding="utf-8")
        with self.assertRaises(LibraryError):
            self.library.choose_document("Read the paper")

    def test_internal_workspace_files_are_not_documents(self) -> None:
        (self.library.root / "AGENTS.md").write_text("internal", encoding="utf-8")
        (self.library.root / "openclaw-workspace-state.json").write_text("{}", encoding="utf-8")

        self.assertEqual(
            self.library.list_documents(),
            [{"path": "attention-paper.md", "title": "attention-paper"}],
        )
        with self.assertRaises(LibraryError):
            self.library.read_document(self.library.root / "AGENTS.md")

    def test_workspace_summary_creation_is_new_file_only(self) -> None:
        first = create_workspace_markdown(
            self.library.root, "Attention Paper", "# Summary\n\nFirst result."
        )
        second = create_workspace_markdown(
            self.library.root, "Attention Paper", "# Summary\n\nSecond result."
        )
        self.assertEqual(first.name, "attention-paper-summary.md")
        self.assertEqual(second.name, "attention-paper-summary-2.md")
        self.assertIn("First result.", first.read_text(encoding="utf-8"))
        self.assertIn("Second result.", second.read_text(encoding="utf-8"))


def _write_simple_pdf(path: Path, text: str) -> None:
    """Create a minimal text PDF without a second PDF-generation dependency."""
    stream = f"BT /F1 18 Tf 72 720 Td ({text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, value in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(value)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(output)


if __name__ == "__main__":
    unittest.main()
