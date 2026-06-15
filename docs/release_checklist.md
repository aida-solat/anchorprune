# Release checklist

The exact, repeatable steps to cut an AnchorPrune release. v1.0 is a
**stabilization** release: it freezes public surfaces and adds no new method.

## 1. Pre-flight (must all pass)

```bash
pytest                                   # full suite green
ruff check .                             # lint clean
anchorprune pack --out /tmp/bench --window 2   # deterministic benchmark
diff -rq benchmarks /tmp/bench           # byte-identical to committed benchmark
anchorprune real-eval --provider mock --model mock-deterministic \
  --scenarios coding_agent --trials 1 --out /tmp/real_eval_smoke   # offline
anchorprune doctor                       # install diagnostics
```

Dashboard:

```bash
cd dashboard && npm ci && npm run typecheck && npm run build
```

## 2. Versioning

- Bump `version` in `pyproject.toml`.
- Bump `__version__` in `anchorprune/__init__.py`.
- Bump `version` in `dashboard/package.json` (+ `package-lock.json`).
- Confirm `/health`, `anchorprune doctor`, and the wheel all report the version.

## 3. Build + packaging verification

```bash
python -m build
twine check dist/*
pip install dist/anchorprune-<version>-py3-none-any.whl
python -c "import anchorprune; print(anchorprune.__version__)"
anchorprune packs list
```

Verify the wheel ships built-in policy-pack YAMLs and excludes
`real_eval_results`, `.next`, and `node_modules`.

## 4. Docs

- `README.md` one-liner + "what it is / is not" current.
- `RELEASE_NOTES.md` has the new version section.
- `docs/index.md` links all major docs.
- `docs/claims.md` and `docs/api_stability.md` present and current.

## 5. One-button demo

```bash
make demo            # or: bash scripts/demo_v1.sh
```

## 6. Commit, tag, push

```bash
git add .
git commit -m "Release AnchorPrune v<version>"
git tag -f v<version>
git push origin main --tags
```

## 7. Post-release sanity

- `git status` clean, branch `main`.
- `git tag --list --sort=creatordate` shows the new tag.
- `origin/main` updated.
