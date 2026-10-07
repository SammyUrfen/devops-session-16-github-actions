# CI/CD & GitHub Actions Homework — Session 16

Bibek Jyoti Charah — 24bcs10112 (GitHub: SammyUrfen)

Environment: Fedora 44 laptop, Docker 29.6.2, gh 2.97.0, Python 3.12. No Kubernetes cluster is needed for this
session. The pipelines run on GitHub-hosted `ubuntu-latest` runners. All output below is pasted as printed; long
output is cut with `...`.

The course folder `session-16-github-actions/10-final-cicd-pipeline` exists, and this project is based on it. I kept
its calculator and pytest tests. I added a small Flask HTTP layer, a Dockerfile, a test-report artifact, a secret
demo, and a separate CD workflow that pushes the image to GHCR.

## What is in the repo

| File | Purpose |
|---|---|
| `app/calculator.py` | `add`, `subtract`, `multiply`, `divide` (same as the course folder) |
| `app/main.py` | Flask app: `GET /health` and `GET /<op>?a=..&b=..` |
| `tests/test_app.py` | 8 pytest unit tests: 4 for the functions, 4 for the HTTP routes |
| `requirements.txt` / `requirements-dev.txt` | runtime deps (Flask, gunicorn) / test deps (pytest) |
| `Dockerfile` | `python:3.12-slim`, runs gunicorn on port 5000 as user `nobody` |
| `.github/workflows/ci.yml` | CI workflow: test, upload report, use secret, build and smoke-test the image |
| `.github/workflows/cd.yml` | CD workflow: after CI passes on `main`, build and push to `ghcr.io/sammyurfen/devops-session-16-github-actions` |

Run it locally:

```
$ pytest -q
........                                                                 [100%]
8 passed in 0.16s
$ docker build -t s16-calc .
$ docker run -d --rm --memory=512m --memory-swap=512m --name s16calc -p 41600:5000 s16-calc
$ curl -s localhost:41600/health
{"status":"ok"}
$ curl -s "localhost:41600/divide?a=10&b=4"
{"result":2.5}
```

## The concepts, tied to these files

**CI vs CD**

| | CI (Continuous Integration) | CD (Continuous Delivery / Deployment) |
|---|---|---|
| Question it answers | "Does this change work?" | "Get the working change to where it runs." |
| When it runs here | every push to `main`, every PR to `main`, or by hand | only after CI succeeds on a push to `main` |
| What it does here | install, unit test, upload report, build image, smoke-test it | build the image and push it to GHCR |
| File | `ci.yml` | `cd.yml` |
| Output | pass/fail + `test-report` artifact | image `:latest` and `:<commit sha>` in GHCR |

Here CD stops at the registry (continuous *delivery*). Continuous *deployment* would also start the new image on a
server. There is no server in this homework.

- **Pipeline** — the full path from a `git push` to a published image: CI (test, then build) followed by CD (push).
  In this repo it is two workflows chained by the `workflow_run` trigger in `cd.yml`.
- **Workflow** — one YAML file in `.github/workflows/`. It has a `name`, triggers under `on:`, and jobs.
  `ci.yml` triggers on `push`, `pull_request` and `workflow_dispatch`. `cd.yml` triggers on `workflow_run` of `CI`.
- **Job** — a group of steps that runs on one fresh runner. `ci.yml` has two jobs, `test` and `docker-build`.
  `needs: test` makes `docker-build` wait for `test` and skip if it fails. Jobs do not share files, so each one
  checks out the code again.
- **Step** — one item in a job's `steps:` list. It is either `uses:` (a ready-made action, such as
  `actions/checkout@v4`) or `run:` (a shell command, such as `pytest -v ...`). Steps run in order. The first failing
  step fails the job.
- **Runner** — the machine that runs a job. `runs-on: ubuntu-latest` asks GitHub for a new hosted Ubuntu VM per job.
  It has Python and Docker already. A self-hosted runner would be your own machine.
- **Secret** — an encrypted value stored in the repo settings (`gh secret set DEMO_SECRET ...`). A workflow reads it
  as `${{ secrets.DEMO_SECRET }}`. GitHub replaces the value with `***` in logs. The "Use a repository secret" step
  prints it on purpose to prove that. `cd.yml` also uses the automatic secret `GITHUB_TOKEN` to log in to GHCR; the
  `permissions: packages: write` block lets that token push images.
- **Artifact** — a file a job saves after the runner is deleted. The `test` job writes JUnit XML to
  `test-results/results.xml` and `actions/upload-artifact@v4` saves it as `test-report` for 7 days.
  `if: always()` uploads it even when tests fail, which is when you need it most.
- **Build** — turning the source into something that runs: `docker build` in the `docker-build` job (CI) and in
  the `push-image` job (CD).
- **Test** — `pytest -v` runs the 8 unit tests. In CI the container is also started and hit with `curl` (a smoke
  test), so a broken Dockerfile fails CI, not CD.
- **Pipeline execution** — a push to `main` starts `CI`. `test` runs, then `docker-build`. When `CI` completes,
  GitHub fires `workflow_run` and `CD` starts. Its job runs only if
  `github.event.workflow_run.conclusion == 'success'` and the CI event was a `push` (not a PR). It checks out
  `workflow_run.head_sha`, the exact commit that CI tested.

## Setup commands

```
$ gh repo create SammyUrfen/devops-session-16-github-actions --public --source . --description "Session 16: Flask app with GitHub Actions CI and CD to GHCR"
https://github.com/SammyUrfen/devops-session-16-github-actions
$ gh secret set DEMO_SECRET --body demo-value-not-real -R SammyUrfen/devops-session-16-github-actions
$ git push -u origin main
...
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
```

I set the secret before the first push so the first CI run could read it. The value is a fake demo value.

## Pipeline execution — real output

```
$ gh run list
completed	success	CD	CD	main	workflow_run	37638725300	31s	2026-10-07T14:40:46Z
completed	success	Add Flask calculator with CI and CD workflows	CI	main	push	37638587621	55s	2026-10-07T14:39:49Z
```

### CI run

```
$ gh run view 37638587621

✓ main CI · 37638587621
Triggered via push about 1 minute ago

JOBS
✓ Test in 30s (ID 112851231069)
✓ Build Docker image in 17s (ID 112851500069)

ANNOTATIONS
! Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4, actions/setup-python@v5, actions/upload-artifact@v4. ...
Test: .github#2
...

ARTIFACTS
test-report

For more information about a job, try: gh run view --job=<job-id>
View this run on GitHub: https://github.com/SammyUrfen/devops-session-16-github-actions/actions/runs/37638587621
```

Log excerpt (`gh run view 37638587621 --log`, filtered with grep, timestamps removed):

```
Test	Run unit tests tests/test_app.py::test_add PASSED                                       [ 12%]
Test	Run unit tests tests/test_app.py::test_subtract PASSED                                  [ 25%]
Test	Run unit tests tests/test_app.py::test_multiply PASSED                                  [ 37%]
Test	Run unit tests tests/test_app.py::test_divide_by_zero PASSED                            [ 50%]
Test	Run unit tests tests/test_app.py::test_health PASSED                                    [ 62%]
Test	Run unit tests tests/test_app.py::test_divide_endpoint PASSED                           [ 75%]
Test	Run unit tests tests/test_app.py::test_divide_by_zero_endpoint PASSED                   [ 87%]
Test	Run unit tests tests/test_app.py::test_unknown_op PASSED                                [100%]
Test	Run unit tests ============================== 8 passed in 0.22s ===============================
Test	Upload test report Artifact test-report.zip successfully finalized. Artifact ID 11491277747
Test	Upload test report Artifact test-report has been successfully uploaded! Final size is 398 bytes. Artifact ID is 11491277747
...
Test	Use a repository secret Secret value printed directly: ***
Test	Use a repository secret Secret length: 19
Build Docker image	Smoke test the container {"status":"ok"}
Build Docker image	Smoke test the container {"result":5.0}
```

The secret is masked as `***`. The length line (19 = `demo-value-not-real`) shows the job really received it.

### CD run

```
$ gh run view 37638725300

✓ main CD · 37638725300
Triggered via workflow_run less than a minute ago

JOBS
✓ Push image to GHCR in 26s (ID 112851701192)

ANNOTATIONS
! Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4. ...
...
View this run on GitHub: https://github.com/SammyUrfen/devops-session-16-github-actions/actions/runs/37638725300
```

Log excerpt:

```
Push image to GHCR	Log in to GHCR Login Succeeded
Push image to GHCR	Push image 95f4e450f45067ba5f6bc2c7f5062ab3e4b5ae27: digest: sha256:1ce275ecf0c80e6eb2d57e02136aefab03c0d42b3b500f59329ef112f63084ba size: 1990
Push image to GHCR	Push image latest: digest: sha256:1ce275ecf0c80e6eb2d57e02136aefab03c0d42b3b500f59329ef112f63084ba size: 1990
```

Pulling the published image back and running it:

```
$ docker pull ghcr.io/sammyurfen/devops-session-16-github-actions:latest
...
Digest: sha256:1ce275ecf0c80e6eb2d57e02136aefab03c0d42b3b500f59329ef112f63084ba
Status: Downloaded newer image for ghcr.io/sammyurfen/devops-session-16-github-actions:latest
ghcr.io/sammyurfen/devops-session-16-github-actions:latest
$ docker run -d --rm --memory=512m --memory-swap=512m --name s16ghcr -p 41601:5000 ghcr.io/sammyurfen/devops-session-16-github-actions:latest
11a9187468841402f91e335e054468ad0fbea9aeee562a2c328e8fa0ce1633bf
$ curl -s "localhost:41601/multiply?a=6&b=7"
{"result":42.0}
```

The digest matches the one CD pushed.

## Findings

- Both workflows passed on the first run; nothing had to be fixed.
- GitHub warns that `actions/checkout@v4`, `setup-python@v5` and `upload-artifact@v4` target Node.js 20 and are
  forced onto Node.js 24. The runs still pass. The course folder already uses `checkout@v6` / `setup-python@v7`;
  bumping to those would remove the warning.
- The course folder's `tests/test_calculator.py` edits `sys.path` to import `app`. I used `pytest.ini` with
  `pythonpath = .` instead, which does the same in one line.
- A `workflow_run` workflow runs even when CI fails, so `cd.yml` needs the `conclusion == 'success'` check. Without
  it, a broken commit would still be pushed to GHCR.
- My local `gh` token lacks the `read:packages` scope, so `gh api /users/SammyUrfen/packages/...` returned HTTP 403.
  I checked the image with `docker pull` instead.
