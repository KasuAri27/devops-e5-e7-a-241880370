"""Student extension: generated project headers must survive path filtering."""
import tempfile
import unittest
from pathlib import Path

from buildchecker.fullcheck import analyze


class TestGeneratedHeader(unittest.TestCase):
    def test_header_from_another_recipe_is_kept_and_checked(self):
        with tempfile.TemporaryDirectory() as folder:
            trace = Path(folder) / "trace"
            trace.mkdir()
            transcripts = {
                "t.10": (
                    'execve("/usr/bin/make", ["make", "unit.o"], []) = 0\n'
                    'clone(child_stack=NULL, flags=SIGCHLD) = 11\n'
                    'clone(child_stack=NULL, flags=SIGCHLD) = 12\n'
                ),
                "t.11": (
                    'execve("/usr/bin/generator", ["generator"], []) = 0\n'
                    'openat(AT_FDCWD, "template.in", O_RDONLY) = 3\n'
                    'openat(AT_FDCWD, "generated.h", O_WRONLY|O_CREAT|O_TRUNC, 0666) = 4\n'
                ),
                "t.12": (
                    'execve("/usr/bin/cc", ["cc", "-c", "unit.c"], []) = 0\n'
                    'openat(AT_FDCWD, "unit.c", O_RDONLY) = 3\n'
                    'openat(AT_FDCWD, "generated.h", O_RDONLY) = 4\n'
                    'openat(AT_FDCWD, "unit.o", O_WRONLY|O_CREAT|O_TRUNC, 0666) = 5\n'
                ),
            }
            for name, text in transcripts.items():
                (trace / name).write_text(text, encoding="utf-8")
            database = Path(folder) / "make-db.txt"
            database.write_text(
                "# Files\ngenerated.h: template.in\n"
                "unit.o: unit.c generated.h\n# files hash-table stats:\n",
                encoding="utf-8",
            )
            result = analyze(trace, database, "/course/project")
            self.assertEqual(
                {(edge["target"], edge["dependency"]) for edge in result["actual_graph"]},
                {("generated.h", "template.in"), ("unit.o", "unit.c"),
                 ("unit.o", "generated.h")},
            )
            self.assertEqual(result["findings"], [])

            database.write_text(
                "# Files\ngenerated.h: template.in\n"
                "unit.o: unit.c\n# files hash-table stats:\n",
                encoding="utf-8",
            )
            missing = analyze(trace, database, "/course/project")
            self.assertEqual(
                {(item["type"], item["target"], item["dependency"])
                 for item in missing["findings"]},
                {("MISSING", "unit.o", "generated.h")},
            )


if __name__ == "__main__":
    unittest.main()
