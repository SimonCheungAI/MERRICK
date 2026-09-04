"""Read-only, path-scoped local document library for MERRICK"""

from __future__ import annotations

import hashlib
import json
import os
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree


DEFAULT_WORKSPACE_DOCUMENTS_ROOT = Path(
    os.getenv(
        "JARVIS_WORKSPACE_DIR",
        Path.home()
        / "Library"
        / "Application Support"
        / "JarvisStark"
        / "Workspace"
        / "Documents",
    )
)
# Kept as an alias so existing callers do not need to know that the reader and
# writer now share one user-visible folder.
DEFAULT_LIBRARY_ROOT = DEFAULT_WORKSPACE_DOCUMENTS_ROOT
DEFAULT_CACHE_ROOT = Path.home() / "Library" / "Application Support" / "JarvisStark" / "DocumentCache"
ALLOWED_SUFFIXES = frozenset({".pdf", ".docx", ".md", ".txt", ".csv", ".json"})
INTERNAL_WORKSPACE_FILENAMES = frozenset(
    {
        "agents.md",
        "bootstrap.md",
        "heartbeat.md",
        "identity.md",
        "knowledge.md",
        "soul.md",
        "tools.md",
        "user.md",
        "openclaw-workspace-state.json",
        "jarvis-codex-ready.md",
    }
)
MAX_DOCUMENT_BYTES = 40 * 1024 * 1024
MAX_TEXT_CHARS = 240_000
MAX_DOCUMENTS = 300
CHUNK_CHARS = 2_200
CHUNK_OVERLAP = 260


class LibraryError(RuntimeError):
    """A controlled local-library failure safe to show to the user."""


@dataclass(frozen=True)
class LibraryDocument:
    relative_path: str
    title: str
    text: str
    chunks: tuple[str, ...]


def create_workspace_markdown(root: Path, source_title: str, content: str) -> Path:
    """Create one non-overwriting Markdown summary in the unified workspace.

    This is a trusted host operation used only after the model has summarized a
    user-authorized local document. It deliberately has no update, delete,
    rename, or arbitrary-path capability.
    """
    cleaned = content.replace("\x00", "").strip()
    if not cleaned:
        raise LibraryError("I could not produce a summary to save.")
    if len(cleaned) > MAX_TEXT_CHARS:
        cleaned = cleaned[:MAX_TEXT_CHARS].rstrip()
    workspace = root.expanduser().resolve()
    workspace.mkdir(mode=0o700, parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", source_title.casefold()).strip("-")
    slug = slug[:60] or "document"
    for index in range(1, 100):
        suffix = "" if index == 1 else f"-{index}"
        candidate = workspace / f"{slug}-summary{suffix}.md"
        try:
            descriptor = os.open(
                candidate,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError:
            continue
        except OSError as exc:
            raise LibraryError("I could not save that summary in the workspace.") from exc
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(cleaned + "\n")
        return candidate
    raise LibraryError("There are too many existing summaries with that name.")


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", value.casefold()))


def _chunk_text(text: str) -> tuple[str, ...]:
    cleaned = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not cleaned:
        return ()
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + CHUNK_CHARS)
        if end < len(cleaned):
            boundary = max(
                cleaned.rfind("\n\n", start + CHUNK_CHARS // 2, end),
                cleaned.rfind(". ", start + CHUNK_CHARS // 2, end),
            )
            if boundary > start:
                end = boundary + 1
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return tuple(chunks)


class ReadOnlyLibrary:
    """A deliberately small reader rooted at one user-owned document folder."""

    def __init__(
        self,
        root: Path = DEFAULT_LIBRARY_ROOT,
        cache_root: Path = DEFAULT_CACHE_ROOT,
    ) -> None:
        self.root = root.expanduser()
        self.cache_root = cache_root.expanduser()

    def ensure_root(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root

    def _safe_path(self, candidate: Path) -> Path:
        root = self.ensure_root().resolve()
        try:
            resolved = candidate.expanduser().resolve(strict=True)
        except (FileNotFoundError, OSError) as exc:
            raise LibraryError("That library file is no longer available.") from exc
        if resolved == root or root not in resolved.parents:
            raise LibraryError("That file is outside the MERRICK Library folder.")
        if not resolved.is_file():
            raise LibraryError("That library item is not a readable file.")
        if resolved.suffix.casefold() not in ALLOWED_SUFFIXES:
            raise LibraryError("MERRICK can read PDF, Word, Markdown, text, CSV, and JSON files there.")
        if resolved.name.casefold() in INTERNAL_WORKSPACE_FILENAMES:
            raise LibraryError("That item is an internal MERRICK workspace file, not a user document.")
        size = resolved.stat().st_size
        if size <= 0 or size > MAX_DOCUMENT_BYTES:
            raise LibraryError("That document is empty or exceeds the 40 MB reading limit.")
        return resolved

    def list_documents(self) -> list[dict[str, str]]:
        root = self.ensure_root().resolve()
        entries: list[dict[str, str]] = []
        for candidate in sorted(root.rglob("*")):
            if len(entries) >= MAX_DOCUMENTS:
                break
            try:
                safe = self._safe_path(candidate)
            except (LibraryError, FileNotFoundError, OSError):
                continue
            relative = safe.relative_to(root).as_posix()
            entries.append({"path": relative, "title": safe.stem})
        return entries

    def choose_document(self, request: str, active_path: str | None = None) -> Path:
        documents = self.list_documents()
        if not documents:
            raise LibraryError(
                "Your MERRICK workspace document folder is empty. Put a PDF, DOCX, Markdown, text, CSV, or JSON file in Workspace/Documents first."
            )
        requested = _tokens(request)
        ignored = {
            "read", "review", "summarize", "summarise", "analyse", "analyze",
            "explain", "paper", "document", "file", "article", "this", "that",
            "please", "jarvis", "library", "research", "thesis", "pdf",
        }
        requested -= ignored
        scored: list[tuple[int, str]] = []
        for entry in documents:
            haystack = _tokens(f"{entry['title']} {entry['path']}")
            scored.append((len(requested & haystack), entry["path"]))
        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        if scored and scored[0][0] > 0 and (
            len(scored) == 1 or scored[0][0] > scored[1][0]
        ):
            return self._safe_path(self.root / scored[0][1])
        if active_path and any(entry["path"] == active_path for entry in documents):
            return self._safe_path(self.root / active_path)
        if len(documents) == 1:
            return self._safe_path(self.root / documents[0]["path"])
        names = ", ".join(entry["title"] for entry in documents[:4])
        raise LibraryError(f"Which document should I read, sir? I found: {names}.")

    def read_document(self, path: Path) -> LibraryDocument:
        safe = self._safe_path(path)
        relative = safe.relative_to(self.root.resolve()).as_posix()
        fingerprint = self._fingerprint(safe)
        cached = self._load_cache(fingerprint)
        if cached is not None:
            return LibraryDocument(relative, safe.stem, cached, _chunk_text(cached))
        suffix = safe.suffix.casefold()
        if suffix == ".pdf":
            text = self._read_pdf(safe)
        elif suffix == ".docx":
            text = self._read_docx(safe)
        else:
            text = safe.read_text(encoding="utf-8", errors="replace")
        text = text.replace("\x00", "").strip()[:MAX_TEXT_CHARS]
        if not text:
            raise LibraryError("I could not extract readable text from that document.")
        self._store_cache(fingerprint, text)
        return LibraryDocument(relative, safe.stem, text, _chunk_text(text))

    def relevant_context(self, document: LibraryDocument, question: str) -> dict[str, object]:
        question_tokens = _tokens(question)
        ranked: list[tuple[int, int, str]] = []
        for index, chunk in enumerate(document.chunks):
            chunk_tokens = _tokens(chunk)
            score = len(question_tokens & chunk_tokens)
            if index == 0:
                score += 2
            ranked.append((score, -index, chunk))
        ranked.sort(reverse=True)
        selected: list[str] = []
        total = 0
        for _, _, chunk in ranked:
            if total + len(chunk) > 11_000 and selected:
                break
            selected.append(chunk)
            total += len(chunk)
            if len(selected) >= 5:
                break
        return {
            "kind": "local_document",
            "title": document.title[:240],
            "source": document.relative_path[:1_024],
            "excerpt_count": len(selected),
            "text": "\n\n--- next selected passage ---\n\n".join(selected),
        }

    def _fingerprint(self, path: Path) -> str:
        stat = path.stat()
        value = f"{path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}".encode("utf-8")
        return hashlib.sha256(value).hexdigest()

    def _cache_path(self, fingerprint: str) -> Path:
        return self.cache_root / f"{fingerprint}.json"

    def _load_cache(self, fingerprint: str) -> str | None:
        try:
            raw = json.loads(self._cache_path(fingerprint).read_text(encoding="utf-8"))
            text = raw.get("text") if isinstance(raw, dict) else None
            return text if isinstance(text, str) and text else None
        except (FileNotFoundError, OSError, ValueError):
            return None

    def _store_cache(self, fingerprint: str, text: str) -> None:
        try:
            self.cache_root.mkdir(parents=True, exist_ok=True)
            target = self._cache_path(fingerprint)
            temporary = target.with_suffix(".tmp")
            temporary.write_text(json.dumps({"text": text}, ensure_ascii=False), encoding="utf-8")
            os.replace(temporary, target)
        except OSError:
            # Caching improves latency but must never block a requested read.
            return

    @staticmethod
    def _read_docx(path: Path) -> str:
        try:
            with zipfile.ZipFile(path) as archive:
                xml = archive.read("word/document.xml")
            root = ElementTree.fromstring(xml)
        except (KeyError, OSError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
            raise LibraryError("I could not read that Word document.") from exc
        paragraphs: list[str] = []
        namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        for paragraph in root.iter(f"{namespace}p"):
            words = [node.text or "" for node in paragraph.iter(f"{namespace}t")]
            value = "".join(words).strip()
            if value:
                paragraphs.append(value)
        return "\n\n".join(paragraphs)

    @staticmethod
    def _read_pdf(path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise LibraryError("The local PDF reader is not installed yet.") from exc
        try:
            reader = PdfReader(str(path))
            pages = reader.pages[:120]
            return "\n\n".join((page.extract_text() or "") for page in pages)
        except Exception as exc:
            raise LibraryError("I could not extract text from that PDF. It may be scanned or protected.") from exc
