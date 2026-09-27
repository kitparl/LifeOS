"""Per-language build/run settings for the go-judge sandbox.

Commands run inside the sandbox (no shell unless explicitly `/bin/sh -c`); toolchains come from
`infra/judge/Dockerfile`. `time_factor` scales a problem's per-test time limit; `memory_overhead_mb`
is added to the sandbox memory limit for the runtime itself (JVM, interpreter); `startup_ms` is
CPU time allowed once per run for process/runtime start-up.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LanguageId = Literal["python", "cpp", "java", "javascript"]


@dataclass(frozen=True)
class LanguageSpec:
    id: LanguageId
    label: str
    source_file: str
    # None: interpreted, the source file itself is copied into the run step.
    compile_args: tuple[str, ...] | None
    # File produced by compilation and cached in go-judge for the run step.
    artifact: str | None
    time_factor: float
    memory_overhead_mb: int
    startup_ms: int
    proc_limit: int

    def run_args(self, memory_limit_mb: int) -> list[str]:
        if self.id == "python":
            return ["/usr/bin/python3", "-X", "utf8", "main.py"]
        if self.id == "javascript":
            return ["/usr/local/bin/node", "--stack-size=65500", "main.js"]
        if self.id == "cpp":
            return ["./main"]
        return [
            "/usr/bin/java",
            f"-Xmx{memory_limit_mb}m",
            "-XX:+UseSerialGC",
            "-XX:TieredStopAtLevel=1",
            "-Xshare:auto",
            "-cp",
            "main.jar",
            "Main",
        ]


LANGUAGES: dict[str, LanguageSpec] = {
    "python": LanguageSpec("python", "Python 3", "main.py", None, None, 3.0, 64, 500, 4),
    "javascript": LanguageSpec("javascript", "JavaScript (Node.js)", "main.js", None, None, 2.0, 96, 500, 16),
    "cpp": LanguageSpec(
        "cpp",
        "C++17",
        "main.cpp",
        ("/usr/bin/g++", "-O2", "-std=c++17", "-pipe", "-o", "main", "main.cpp"),
        "main",
        1.0,
        16,
        200,
        4,
    ),
    "java": LanguageSpec(
        "java",
        "Java 17",
        "Main.java",
        (
            "/bin/sh",
            "-c",
            "mkdir -p out && /usr/bin/javac -encoding UTF-8 -J-Xmx512m -d out Main.java"
            " && /usr/bin/jar cf main.jar -C out .",
        ),
        "main.jar",
        2.0,
        320,
        1500,
        64,
    ),
}

LANGUAGE_IDS: tuple[str, ...] = tuple(LANGUAGES)
