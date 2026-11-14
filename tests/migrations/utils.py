import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def cli(project: Path, *args: str) -> str:
    entrypoint = "from rakko.cli import main; main()"
    if os.getenv("RAKKO_TEST_MYSQL_DRIVER") == "aiomysql":
        entrypoint = "import sys; sys.modules['asyncmy'] = None; " + entrypoint
    result = subprocess.run(
        [sys.executable, "-B", "-c", entrypoint, "-c", "settings.RAKKO_ORM", *args],
        cwd=project,
        env={**os.environ, "PYTHONPATH": os.pathsep.join([str(project), str(ROOT)])},
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def run_model_code(project: Path, statements: str) -> None:
    code = (
        "import asyncio\n"
        "from rakko.context import RakkoContext\n"
        "from rakko.exceptions import IntegrityError\n"
        "from sample.models import Account\n"
        "from settings import RAKKO_ORM\n"
        "async def main():\n"
        "    async with RakkoContext() as context:\n"
        "        await context.init(config=RAKKO_ORM)\n"
        + "".join(f"        {line}\n" for line in statements.splitlines())
        + "import sys\n"
        + "asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop if sys.platform == 'win32' else None)\n"
    )
    if os.getenv("RAKKO_TEST_MYSQL_DRIVER") == "aiomysql":
        code = "import sys\nsys.modules['asyncmy'] = None\n" + code
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=project,
        env={**os.environ, "PYTHONPATH": os.pathsep.join([str(project), str(ROOT)])},
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
