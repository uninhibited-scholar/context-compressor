# Releasing

Releases are published to [PyPI](https://pypi.org/project/context-compressor/)
automatically via **Trusted Publishing** (OIDC) — no API tokens are stored
anywhere. Pushing a `v*` tag triggers `.github/workflows/publish.yml`.

## One-time setup (PyPI side)

1. Create an account at https://pypi.org and verify your email.
2. Go to **Account → Publishing → Add a new pending publisher** and fill in:
   - **PyPI Project Name:** `context-compressor`
   - **Owner:** `uninhibited-scholar`
   - **Repository name:** `context-compressor`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `pypi`
3. Save. (A "pending publisher" lets the very first release create the project.)

## Cutting a release

1. Bump the version in `pyproject.toml` and `src/context_compressor/__init__.py`.
2. Update `CHANGELOG.md`.
3. Commit, then tag and push:

   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

4. The **Publish to PyPI** workflow builds, validates with `twine check`, and
   uploads. Watch it under the repo's **Actions** tab.

## Manual build (local sanity check)

```bash
python -m build
python -m twine check dist/*
```
