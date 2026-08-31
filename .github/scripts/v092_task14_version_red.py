from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_required(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        if new in text:
            return
        raise RuntimeError(f"expected text not found in {path}: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    version = ROOT / "tests" / "test_version.py"
    replace_required(version, 'EXPECTED_VERSION = "0.9.1"', 'EXPECTED_VERSION = "0.9.2"')
    replace_required(version, "test_runtime_version_is_0_9_1", "test_runtime_version_is_0_9_2")
    replace_required(version, "test_project_metadata_version_is_0_9_1", "test_project_metadata_version_is_0_9_2")
    replace_required(version, "test_readme_release_version_is_0_9_1", "test_readme_release_version_is_0_9_2")
    replace_required(version, '"Current version: **0.9.1**."', '"Current version: **0.9.2**."')
    replace_required(version, '"Version: `0.9.1`."', '"Version: `0.9.2`."')
    replace_required(
        version,
        "def test_readme_version_notes_cover_0_9_1_and_0_9_0():\n    readme = Path(\"README.md\").read_text(encoding=\"utf-8\")\n    assert \"- **0.9.1** —\" in readme\n    assert \"- **0.9.0** —\" in readme",
        "def test_readme_version_notes_cover_0_9_2_0_9_1_and_0_9_0():\n    readme = Path(\"README.md\").read_text(encoding=\"utf-8\")\n    assert \"- **0.9.2** —\" in readme\n    assert \"- **0.9.1** —\" in readme\n    assert \"- **0.9.0** —\" in readme",
    )

    packaging = ROOT / "tests" / "test_packaging.py"
    replace_required(packaging, "test_pyproject_version_is_0_9_1", "test_pyproject_version_is_0_9_2")
    replace_required(packaging, '== "0.9.1"', '== "0.9.2"')
    replace_required(packaging, "test_runtime_version_is_0_9_1", "test_runtime_version_is_0_9_2")
    # The previous replace updates only the first literal; update the runtime assertion too.
    text = packaging.read_text(encoding="utf-8")
    text = text.replace('assert engcalc_colab.__version__ == "0.9.1"', 'assert engcalc_colab.__version__ == "0.9.2"')
    packaging.write_text(text, encoding="utf-8")

    parser = ROOT / "tests" / "test_parser.py"
    replace_required(parser, 'assert __version__ == "0.9.1"', 'assert __version__ == "0.9.2"')

    metadata = ROOT / "tests" / "test_packaging_metadata.py"
    text = metadata.read_text(encoding="utf-8")
    marker = '    assert project["Requires-Python"] == ">=3.10"\n'
    assertion = '    assert project["Version"] == "0.9.2"\n'
    if assertion not in text:
        if marker not in text:
            raise RuntimeError("packaging metadata insertion marker not found")
        text = text.replace(marker, assertion + marker, 1)
        metadata.write_text(text, encoding="utf-8")

    print("Materialized Task 14 version expectations for intentional RED.")


if __name__ == "__main__":
    main()
