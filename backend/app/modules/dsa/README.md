# DSA practice module

Pattern-based coding practice at `/dsa`. The 29 patterns contain problems, and each problem is judged in a sandbox.
The catalog (patterns, problems, test cases) is global and editable by admins. Submissions and progress are per user.

```
Browser ─► FastAPI /api/v1/dsa ─► JudgeQueue (asyncio, N workers) ─► Runner ─► go-judge (127.0.0.1:5050)
                 │                                                               privileged container,
                 └─► dsa_* tables  ◄── seeder ◄── seeds/*.json ◄── content build   per-run namespaces + cgroups
```

## Judge setup

The judge is [go-judge](https://github.com/criyle/go-judge). It is the sandbox that Hydro's own judge daemon uses, driven here headlessly through its REST API.
The Hydro server itself is not used, because `hydrojudge` only pulls tasks from a full Hydro server. See `aidlc-docs/inception/application-design/application-design-dsa.md`.

**Host requirements:**
- Linux with Docker. cgroup v2 is fine. With kernel 5.19 or newer, memory peaks are exact.
- The container runs `privileged`.
- Docker Desktop on macOS works for development.

1. Pick a token and start the judge. It never starts without a token, and it listens on localhost only.
   ```bash
   export DSA_JUDGE_TOKEN=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
   cd infra && docker compose --profile judge up -d --build judge
   ```
2. Point the backend at it in `backend/.env`:
   ```
   DSA_JUDGE_URL=http://127.0.0.1:5050
   DSA_JUDGE_TOKEN=<same token>
   ```
   If `DSA_JUDGE_URL` is empty, browsing still works, but Run and Submit return `503`.
3. **Run a single uvicorn worker.** The queue, the Run results, and the rate limiters live in process memory, which is the same assumption `core/rate_limit.py` makes.

Optional live check covering all 4 languages, verdicts, and the no-network rule:
```bash
cd backend && DSA_JUDGE_URL=http://127.0.0.1:5050 DSA_JUDGE_TOKEN=$DSA_JUDGE_TOKEN pytest app/tests/test_dsa_judge_live.py
```

## Admins

```bash
cd backend
python -m app.modules.dsa.cli grant-admin <username>
python -m app.modules.dsa.cli revoke-admin <username>
```
Admins see an **Edit** link on each problem. It lets them change the statement, signature, limits, compare mode, status, and test cases.
Every admin save sets `edited_in_ui` on the problem, so the next seed run leaves that problem alone (see below).

## Adding a problem end to end

1. **Catalog.** The problem's title must already exist in `seeds/catalog.json`, which holds the 29 patterns and all titles.
   To add a brand-new title, add an entry there with `pattern`, `slug`, `title`, `difficulty`, `tags`, and `order`.
2. **Source.** Add a `ProblemSource` to `content/sources/pNN_<pattern-slug>.py`. Create the file if it doesn't exist; it exports `PATTERN_NUMBER` and `PROBLEMS`.
   ```python
   from app.modules.dsa.content.model import Example, ProblemSource, function, ints


   def _pair_sum(nums: list[int], target: int) -> bool: ...  # the reference solution


   PAIR_SUM = ProblemSource(
       title="Pair Sum",  # must match the catalog title
       statement="...original wording...",  # markdown; never copied from other sites
       constraints="- `0 <= nums.length <= 10^4`",
       signature=function("pairSum", [("nums", "int[]"), ("target", "int")], "bool"),
       reference=_pair_sum,
       examples=[Example([[1, 2, 4], 6], "2 + 4 = 6."), Example([[1, 2], 5])],  # 2-3; shown to users
       edge_cases=[[[], 0], [[5], 10]],  # hidden
       generator=lambda rng: [
           sorted(ints(rng, rng.randint(0, 10_000), -(10**4), 10**4)),
           rng.randint(-2 * 10**4, 2 * 10**4),
       ],
       random_count=8,  # hidden, seeded
       compare="exact",
   )
   ```
3. **Build.** `python -m app.modules.dsa.content.build --pattern NN`. This runs the reference solution on every input and writes `seeds/pNN-<slug>.json`.
   The build fails if any of these happen:
   - the reference crashes or is not deterministic
   - an input or output doesn't match the signature
   - there are more than 40 tests or more than 1 MB of test JSON

   `--check` verifies that the committed seed files are up to date. `test_dsa_content_seed.py` also enforces this.
4. **Seed.** `python -m app.modules.dsa.seeder`. It upserts by slug, publishes problems that have content, and keeps every other catalog title as a draft ("Coming soon").
   It skips problems edited in the admin UI, and `--force` overwrites them. It also skips unchanged problems (`content_hash`).
5. **Verify.** Open `/dsa/problems/<slug>` and check that the reference approach is Accepted in at least one language.

## Signatures and test data

| Type | JSON |
|---|---|
| `int`, `long`, `double`, `bool`, `string`, `char` | number / bool / string (a `char` is a one-character string) |
| `T[]`, `T[][]` | arrays |
| `ListNode` | `[1,2,3]` |
| `ListNode[]` | `[[1,4],[2]]` |
| `TreeNode` | level order with `null`, e.g. `[3,9,20,null,null,15,7]` |
| `void` | return type only. Use it with `mutates="param"` for in-place problems; the mutated argument is then the output. |

- **Function problems:** the user writes `class Solution` with the method in Python, C++, and Java, or a plain function in JavaScript. A test input is the list of arguments.
- **Design problems** use `design(name, constructor, methods)`. A test input is `ops(("LRUCache", [2]), ("put", [1, 1]), ("get", [1]))`, and the output is one value per operation, with `null` for the constructor and for `void` methods.
- Problems that need other pointer structures, such as graph nodes or random pointers, are defined over arrays or adjacency lists in their statements.

**Compare modes:**
- `exact`
- `unordered`: top-level order is ignored
- `unordered_nested`: inner lists are sorted, then the outer list
- `float_tolerance`: 1e-5
- `checker`: a named function in `judge/compare.py`, registered with `@checker("name")`, for problems with several valid answers

**Starter code and drivers** are generated per language from the signature (`judge/drivers/`).
The driver runs every test in one process, writes one JSON line per test to `result.jsonl`, and the backend compares the results.
The sandbox receives test **inputs only**, never expected outputs.

## Limits and verdicts

**Limits:**
- The per-test limit is `time_limit_ms` multiplied by a language factor: C++ ×1, Java ×2, JS ×2, Python ×3.
- Each run gets a CPU cap of min(per-test limit × number of tests, 10 s) plus start-up time.
- Memory is `memory_limit_mb` plus runtime overhead.
- Code is at most 64 KB. There are at most 3 custom Run inputs.
- Rate limits are `DSA_RUN_PER_MINUTE` and `DSA_SUBMIT_PER_MINUTE`, with one active Run per user.
- Output is capped.

**Verdicts:**
- The verdict is decided by the first failing test, in test order: samples first, then hidden tests.
- If the judge is unreachable or misbehaves, the verdict is **Internal Error**, never Accepted. Progress is left untouched.

**What a Submit reveals:**
- Hidden tests are never shown. A Submit reveals only which hidden case failed.
- A runtime error past the samples shows only its exception type.
- stdout and stderr are shown for Run only.
