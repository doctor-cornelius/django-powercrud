"""Static checks for PowerCRUD release-version policy."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_release_script_allows_only_alpha_and_beta_prereleases():
    """The local release helper should not advertise or accept release candidates."""
    release_script = (PROJECT_ROOT / "new_release.sh").read_text(encoding="utf-8")

    assert "<alpha|beta>" in release_script, (
        "new_release.sh help should advertise only alpha and beta prereleases."
    )
    assert "<alpha|beta|rc>" not in release_script, (
        "new_release.sh help should not advertise rc prereleases."
    )
    assert "alpha|beta|rc" not in release_script, (
        "new_release.sh argument parsing should not accept rc prereleases."
    )
    assert "a|b|rc" not in release_script, (
        "new_release.sh version regexes should not accept rc suffixes."
    )
    assert '"rc": "rc"' not in release_script, (
        "new_release.sh prerelease mapping should not contain an rc suffix."
    )


def test_release_workflows_reject_rc_tags():
    """Release workflows should validate the same alpha/beta policy as the script."""
    publish_workflow = (PROJECT_ROOT / ".github" / "workflows" / "publish.yml")
    docs_workflow = (PROJECT_ROOT / ".github" / "workflows" / "deploy_docs.yml")

    for workflow_path in (publish_workflow, docs_workflow):
        workflow = workflow_path.read_text(encoding="utf-8")
        assert "(?:a|b)\\d+" in workflow, (
            f"{workflow_path.name} should accept only alpha and beta PEP 440 tags."
        )
        assert "a|b|rc" not in workflow, (
            f"{workflow_path.name} should not validate rc tags as publishable."
        )
