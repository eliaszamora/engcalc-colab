from importlib import metadata


def test_project_metadata_declares_notebook_runtime_and_python_floor():
    project = metadata.metadata("engcalc-colab")
    assert project["Requires-Python"] == ">=3.10"
    requirements = project.get_all("Requires-Dist") or []
    normalized = {requirement.replace(" ", "").lower() for requirement in requirements}
    assert "ipython>=8.18" in normalized
