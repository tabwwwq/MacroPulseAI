"""The delegation script must write exactly the file content, whatever fences the model adds."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents"))

from local_task import unwrap


def test_double_wrapped_code_file_loses_its_inner_fence() -> None:
    assert unwrap("```tsx\nconst a = `x`;\n```\n", Path("a.tsx")) == "const a = `x`;\n"


def test_plain_code_is_untouched() -> None:
    assert unwrap("const a = 1;\n", Path("a.tsx")) == "const a = 1;\n"


def test_fence_inside_code_is_content() -> None:
    text = "x\n```ts\ny\n```\n"
    assert unwrap(text, Path("a.ts")) == text


def test_markdown_keeps_its_fences() -> None:
    text = "```bash\nls\n```\n"
    assert unwrap(text, Path("guide.md")) == text
