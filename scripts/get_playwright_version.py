"""Print the Playwright version resolved in the project lockfile."""

from pathlib import Path
import tomllib


def main() -> int:
    """Read and print the unique Playwright package version from uv.lock."""
    lock_path = Path(__file__).resolve().parents[1] / "uv.lock"
    lock_data = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    versions = [
        package["version"]
        for package in lock_data.get("package", [])
        if package.get("name") == "playwright"
    ]
    if len(versions) != 1:
        raise SystemExit(
            f"Expected one Playwright package in {lock_path}, found {len(versions)}."
        )

    print(versions[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
