# emSign CA incident: reusable Python and container remediation briefing

This briefing is for an AI assistant working in a Python repository that uses `uv`, pip, or Python containers. Use it as incident context, then inspect the target repository and its instructions before changing anything. Do not assume its Dockerfile, Compose files, package manager, service names, lockfiles, or host operating system match the example paths below.

## Incident and patched minimums

The eMudhra/emSign incident involved compromised intermediate certificate private keys. Trusting the affected emSign root can let an on-path attacker impersonate a TLS site. Python tools may ship their own CA bundles, so updating only the operating system trust store is insufficient.

The Python.org announcement lists these minimum patched versions:

- `uv` 0.13.4
- `pip` 26.2.2
- `certifi` 2026.10.19

Check the current official advisories before acting, since later releases may supersede these minimums:

- [Python.org incident announcement](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576)
- [uv security advisory](https://github.com/astral-sh/uv/security/advisories/GHSA-hq85-5cpj-mr62)
- [certifi security advisory](https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2)

Keep version constraints as minimums for pip and certifi. For a Docker image, pin uv to a specific patched release for reproducible builds and configure the repository's dependency bot to propose version updates. Do not leave the image on a floating installer URL: it can install an older release than expected.

## Procedure

### 1. Inspect the target repository

Start at its root. Read its `AGENTS.md` instructions and inspect:

- Which Dockerfile builds the Python application image.
- How that Dockerfile installs uv and pip, refreshes the OS CA certificates, and installs project dependencies.
- Whether the application uses `uv.lock`, another lockfile, or a requirements file.
- The Compose file, environment-file options, and service name used for the application.
- Whether Renovate or another dependency bot already tracks build-tool versions.

Do not copy this repository's commands verbatim when the target has different Compose arguments or service names.

### 2. Update the WSL host once

For an Astral standalone uv installation on Ubuntu/WSL:

```bash
uv self update
uv --version
sudo apt update
sudo apt install --only-upgrade ca-certificates
```

Confirm uv is at least 0.13.4. If uv is managed by another package manager, update it through that manager instead. A host Python without pip does not need pip installed just for this incident. Do not bypass PEP 668 with `--break-system-packages`.

For an existing project virtual environment, update its dependencies using the repository's normal lockfile workflow. A patched uv executable does not automatically update certifi inside an already-created environment.

### 3. Update the project dependency lock

If the project has `uv.lock` and certifi appears in its dependency graph, run from the repository root:

```bash
uv lock --upgrade-package certifi
uv sync
```

Review and commit the resulting lockfile change. The Docker build must install from that updated lockfile; otherwise a later locked sync can restore the old certifi version. If the repository uses another dependency manager, update certifi with that manager. Do not add certifi as a direct dependency unless the project needs it or its dependency policy calls for it.

### 4. Update the Dockerfile

For a Debian/Ubuntu-based image, ensure the Dockerfile runs `apt-get update` before installing/upgrading `ca-certificates`. Use the corresponding package-manager operation for other base distributions.

Add a version argument near the Dockerfile's other tool-version arguments. If Renovate is configured for regex custom managers, use its matching annotation; otherwise configure the repository's dependency bot to track this argument.

```dockerfile
# renovate: datasource=github-releases depName=astral-sh/uv versioning=semver
ARG UV_VERSION=0.13.4
```

Replace the floating uv installer command with the versioned release URL, retaining any existing installation-copy commands:

```dockerfile
# Pin uv to a patched release; the dependency bot tracks UV_VERSION.
RUN curl --proto '=https' --tlsv1.2 -LsSf https://releases.astral.sh/github/uv/releases/download/${UV_VERSION}/uv-installer.sh | sh && \
    install -Dm755 /root/.local/bin/uv /usr/local/bin/uv && \
    install -Dm755 /root/.local/bin/uvx /usr/local/bin/uvx
```

Immediately after installing uv, ensure pip is upgraded before the project dependencies are installed:

```dockerfile
# Use the refreshed OS CA store while bootstrapping pip.
RUN UV_SYSTEM_CERTS=true uv pip install --system "pip>=26.2.2"
```

Use a later patched minimum if the official advisory has changed. Do not hardcode a pip wheel URL when a maintained version constraint is sufficient.

### 5. Rebuild and start only the application service

Containers can be down before this step. Use the target repository's usual Compose file and environment-file arguments. Do not pull unrelated database, cache, admin, or sidecar services just to rebuild the application image.

First, use Compose's service listing to confirm the application service name:

```bash
docker compose [the repository's usual Compose and env-file options] config --services
```

Then substitute that service name and the same Compose options in these commands:

```bash
docker compose [the repository's usual Compose and env-file options] build --no-cache APPLICATION_SERVICE
docker compose [the repository's usual Compose and env-file options] up -d APPLICATION_SERVICE
```

`--no-cache` ensures the Dockerfile's package and installer steps are rerun. Starting the application service also starts its declared dependencies when Compose requires them.

### 6. Verify in the running application container

Substitute the same Compose options and application service name:

```bash
docker compose [the repository's usual Compose and env-file options] exec APPLICATION_SERVICE sh -lc 'uv --version && python -m pip --version && python -c "import certifi; print(certifi.__version__)"'
```

Confirm the reported versions meet the patched minimums. If a command fails because that image does not include pip or certifi, inspect its actual Python environment and dependency graph; do not assume a package exists just because another repository installs it.

## Example from django_powercrud

The implementation in this repository is a reference, not a template for blindly copying paths or service names:

- Dockerfile and uv/pip setup: `/home/mfo/projects/packages/django_powercrud/docker/dockerfile_django`
- Locked Python dependencies, including certifi: `/home/mfo/projects/packages/django_powercrud/uv.lock`
- Renovate custom-manager configuration: `/home/mfo/projects/packages/django_powercrud/renovate.json`
- Compose service definitions: `/home/mfo/projects/packages/django_powercrud/docker/docker-compose.yml`

For this repository, the application service is `powercrud`, and the Compose options are:

```bash
-f docker/docker-compose.yml --env-file docker/.env --env-file docker/dev/dev.secret
```

An AI working elsewhere should use that repository's own instructions, paths, and Compose configuration.
