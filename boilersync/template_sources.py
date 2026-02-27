import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from boilersync.paths import paths

logger = logging.getLogger(__name__)

SOURCE_RESOLUTION = "source_ref"
LEGACY_RESOLUTION = "legacy_name"


@dataclass(frozen=True)
class TemplateSource:
    ref: str
    resolution: Literal["source_ref", "legacy_name"]
    template_dir: Path
    repo_url: str | None = None
    org: str | None = None
    repo: str | None = None
    subdir: str | None = None
    local_repo_path: Path | None = None

    @property
    def identifier(self) -> str:
        if self.resolution == SOURCE_RESOLUTION:
            return f"source:{self.org}/{self.repo}#{self.subdir}"
        return f"legacy:{self.ref}"


def _normalize_subdir(subdir: str) -> str:
    cleaned = subdir.strip().strip("/")
    if not cleaned:
        raise ValueError("Template source ref must include a non-empty subdir after '#'.")
    if cleaned.startswith("../") or cleaned == ".." or "/../" in cleaned:
        raise ValueError("Template source subdir must stay within the source repository.")
    return cleaned


def parse_repo_locator(repo_locator: str) -> tuple[str, str, str]:
    locator = repo_locator.strip()
    if not locator:
        raise ValueError("Template source repo cannot be empty.")

    if "://" in locator:
        parsed = urlparse(locator)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid template source repo URL: {repo_locator}")
        path = parsed.path.strip("/")
        if path.endswith(".git"):
            path = path[: -len(".git")]
        parts = [part for part in path.split("/") if part]
        if len(parts) < 2:
            raise ValueError(
                "Template source repo URL must include org/repo path segments."
            )
        org = parts[-2]
        repo = parts[-1]
        clone_url = locator
        return org, repo, clone_url

    if locator.startswith("git@"):
        match = re.match(r"^git@[^:]+:(?P<org>[^/]+)/(?P<repo>[^/]+)$", locator)
        if not match:
            raise ValueError(f"Invalid SSH repo format: {repo_locator}")
        org = match.group("org")
        repo = match.group("repo")
        if repo.endswith(".git"):
            repo = repo[: -len(".git")]
        return org, repo, locator

    match = re.match(r"^(?P<org>[^/\s]+)/(?P<repo>[^/\s]+)$", locator)
    if match:
        org = match.group("org")
        repo = match.group("repo")
        clone_url = f"https://github.com/{org}/{repo}.git"
        return org, repo, clone_url

    raise ValueError(
        "Invalid template source repo. Use org/repo, HTTPS URL, or SSH URL."
    )


def _parse_source_ref(template_ref: str) -> tuple[str, str] | None:
    if "#" not in template_ref:
        return None

    repo_locator, subdir = template_ref.split("#", 1)
    repo_locator = repo_locator.strip()
    if not repo_locator:
        raise ValueError("Template source ref must include a repo before '#'.")

    return repo_locator, _normalize_subdir(subdir)


def _ensure_repo_cloned(repo_url: str, repo_path: Path) -> None:
    repo_parent = repo_path.parent
    repo_parent.mkdir(parents=True, exist_ok=True)

    if repo_path.exists():
        if (repo_path / ".git").exists():
            return
        if any(repo_path.iterdir()):
            raise FileExistsError(
                f"Template repo path exists and is not a git repo: {repo_path}"
            )

    subprocess.run(["git", "clone", repo_url, str(repo_path)], check=True)


def _resolve_legacy_template_dir(template_ref: str) -> Path:
    template_root_dir = paths.template_root_dir
    if not template_root_dir.exists():
        raise FileNotFoundError(
            f"Template root directory does not exist: {template_root_dir}"
        )

    direct_dir = template_root_dir / template_ref
    if direct_dir.exists():
        return direct_dir

    candidates: list[Path] = []
    for org_dir in sorted(template_root_dir.iterdir()):
        if not org_dir.is_dir():
            continue
        for repo_dir in sorted(org_dir.iterdir()):
            if not repo_dir.is_dir():
                continue
            candidate = repo_dir / template_ref
            if candidate.exists():
                candidates.append(candidate)

    if len(candidates) == 1:
        logger.warning(
            "Resolved legacy template ref '%s' to nested template path %s",
            template_ref,
            candidates[0],
        )
        return candidates[0]

    if len(candidates) > 1:
        candidate_paths = ", ".join(str(path) for path in candidates)
        raise FileNotFoundError(
            f"Legacy template ref '{template_ref}' is ambiguous across template sources: "
            f"{candidate_paths}. Use a source ref: org/repo#subdir."
        )

    raise FileNotFoundError(
        f"Template '{template_ref}' not found in {template_root_dir}"
    )


def resolve_template_source(
    template_ref: str,
    *,
    clone_missing_repo: bool = True,
    warn_on_legacy: bool = True,
) -> TemplateSource:
    source_ref = _parse_source_ref(template_ref)

    if source_ref is None:
        if warn_on_legacy:
            logger.warning(
                "⚠️  Legacy template refs are deprecated. Use org/repo#subdir format: %s",
                template_ref,
            )
        template_dir = _resolve_legacy_template_dir(template_ref)
        return TemplateSource(
            ref=template_ref,
            resolution=LEGACY_RESOLUTION,
            template_dir=template_dir,
        )

    repo_locator, subdir = source_ref
    org, repo, repo_url = parse_repo_locator(repo_locator)

    local_repo_path = paths.template_root_dir / org / repo
    if clone_missing_repo:
        _ensure_repo_cloned(repo_url, local_repo_path)

    if not (local_repo_path / ".git").exists():
        raise FileNotFoundError(
            f"Template source repository is not initialized at {local_repo_path}. "
            "Run 'boilersync templates init <repo-url>' or use a source ref to auto-clone."
        )

    template_dir = local_repo_path / subdir
    if not template_dir.exists():
        raise FileNotFoundError(
            f"Template subdir '{subdir}' not found in template source repo: {local_repo_path}"
        )

    return TemplateSource(
        ref=template_ref,
        resolution=SOURCE_RESOLUTION,
        repo_url=repo_url,
        org=org,
        repo=repo,
        subdir=subdir,
        local_repo_path=local_repo_path,
        template_dir=template_dir,
    )


def build_source_backlink(source: TemplateSource) -> dict[str, Any] | None:
    if source.resolution != SOURCE_RESOLUTION:
        return None

    assert source.repo_url is not None
    assert source.org is not None
    assert source.repo is not None
    assert source.subdir is not None
    assert source.local_repo_path is not None

    return {
        "ref": source.ref,
        "repo_url": source.repo_url,
        "org": source.org,
        "repo": source.repo,
        "subdir": source.subdir,
        "local_repo_path": str(source.local_repo_path),
        "template_dir": str(source.template_dir),
        "resolution": source.resolution,
    }


def resolve_source_from_boilersync(
    template_ref: str | None,
    source_data: dict[str, Any] | None,
    *,
    clone_missing_repo: bool = True,
) -> TemplateSource:
    if source_data:
        ref_from_source = source_data.get("ref")
        if isinstance(ref_from_source, str) and ref_from_source.strip():
            return resolve_template_source(
                ref_from_source.strip(),
                clone_missing_repo=clone_missing_repo,
                warn_on_legacy=False,
            )

        repo_url = source_data.get("repo_url")
        subdir = source_data.get("subdir")
        if isinstance(repo_url, str) and isinstance(subdir, str):
            return resolve_template_source(
                f"{repo_url}#{subdir}",
                clone_missing_repo=clone_missing_repo,
                warn_on_legacy=False,
            )

    if not template_ref:
        raise ValueError("Template reference missing in .boilersync metadata.")

    return resolve_template_source(
        template_ref,
        clone_missing_repo=clone_missing_repo,
        warn_on_legacy=False,
    )
