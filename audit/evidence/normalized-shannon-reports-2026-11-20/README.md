# Run the historical normalized Shannon comparison

The public Rust reports divide finite mutual-information inputs. This comparison checks their numerical fields on 184 fixed calls. GitHub runs the original code and the corrected code under a frozen checker. Two branch names identify the tested code and the checker. Reading the saved observations requires no branch and no write access. A new hosted run requires a maintainer who can publish branches and run GitHub Actions in this repository. [Read back the saved observations](check.py) · [Original and corrected results](receipt.json) · [Scope and inputs](../../research/normalized-shannon-arithmetic/README.md)

## Read the saved result

From the repository root, run the following command. Run it again with `-O` before `-I`.

```sh
python3 -I -S -B audit/evidence/normalized-shannon-reports-2026-11-20/check.py
```

The original code differed on 41 of 184 calls. The corrected code agreed on all seven report fields for all 184 calls. The original Cargo test exited with status 101 and the corrected test with status 0. Each source passed the 16 pre-existing invariant tests. An earlier checker failed to compile and produced zero observations. These counts describe the fixed calls and the named software. [Original hosted run](https://github.com/sepahead/pid-rs/actions/runs/44640265708) · [Corrected hosted run](https://github.com/sepahead/pid-rs/actions/runs/44640966503) · [Earlier compiler failure](https://github.com/sepahead/pid-rs/actions/runs/44638831978)

## Select the two sources

Use a full clone and an authenticated Git remote for `sepahead/pid-rs`. In the commands below, `origin` names that remote. The first commit contains the frozen checker. Its parent contains the original implementation. The second commit changes the two production files. Both commits are ancestors of the default branch. These commit IDs also work while either verification branch is absent.

```sh
checker=a5fe92978a8671c2592191ab9c5b25b6ab46c02b
corrected=03325745f64becf437b9b3042b51a9d925450579
manifest=35439baf58eef626f99a5e10ef2bc42356558c560a10aaab0c496136af084f5c
baseline_name="review/normalized-shannon-baseline-$manifest"
corrected_name="review/normalized-shannon-fix-$checker-$manifest"
baseline_ref="refs/heads/$baseline_name"
corrected_ref="refs/heads/$corrected_name"

git remote get-url --push origin
git fetch --no-tags origin refs/heads/main:refs/remotes/origin/main
git merge-base --is-ancestor "$checker" refs/remotes/origin/main
git merge-base --is-ancestor "$corrected" refs/remotes/origin/main
git rev-parse "$checker^" "$corrected^"
git show "$checker:audit/research/normalized-shannon-ratios/manifest.json" | shasum -a 256
git ls-remote --heads origin "$baseline_ref" "$corrected_ref"
```

Verify that both ancestry checks succeed. The two parents must be `0f3122a96e48a099581ad4faf3e3d5d9138367f6` and the checker commit, in that order. Compare the file digest with `manifest`. Verify the repository, its current branch rules and the authenticated permissions. Get the same branch inventory from Git and the GitHub API. Also check current pull requests, queued and running jobs, and any other known use of the names. Stop on a conflicting commit, a changed permission or an unknown user of the affected name. Save the branch inventory and existing run IDs before each action. [Source checks](https://github.com/sepahead/pid-rs/blob/a5fe92978a8671c2592191ab9c5b25b6ab46c02b/audit/research/normalized-shannon-ratios/judge.py) · [GitHub branch rules](https://docs.github.com/en/rest/repos/rules#get-rules-for-a-branch)

## Run the baseline, then the correction

1. If the baseline branch is absent, publish the checker at its exact baseline name. The empty value after the last colon instructs Git to create the branch only if the name is free. After sending the command, read the advertised ref again. If the name already contains the checker, use it as it stands. An up-to-date push does not show that a new run began. [Git push and leases](https://git-scm.com/docs/git-push)

   ```sh
   git -c push.followTags=false push --atomic --porcelain --no-follow-tags --recurse-submodules=no \
     "--force-with-lease=$baseline_ref:" origin "$checker:$baseline_ref"
   ```

2. Identify the new `Normalized Shannon ratio arithmetic` workflow event by its actual repository, branch, head commit and run ID. The push trigger has a path filter. If the new event is absent and there is no competing run, a maintainer can issue the following dispatch. A dispatch needs the actual branch. After a timeout, read the events before deciding whether another dispatch is necessary. Save the run ID and attempt. [Historical workflow](https://github.com/sepahead/pid-rs/blob/a5fe92978a8671c2592191ab9c5b25b6ab46c02b/.github/workflows/normalized-shannon-ratio.yml) · [GitHub manual workflow runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)

   ```sh
   gh workflow run normalized-shannon-ratio.yml --repo sepahead/pid-rs --ref "$baseline_name"
   ```

3. Read the completed native job and its artifact. The historical environment uses Ubuntu 24.04 on x86-64 and Rust 1.99.1. Check the entry for the selected branch, head, checker, manifest, run and attempt in the artifact. Read the two reference-check outputs, the two control outputs, the tool versions, the commands, their exit codes and all test logs. Compare the 184 recorded rows byte for byte with [original.json](original.json). The checker requires six specified failures within the full set of 41 differences. Keep the ZIP, its digest, its provider identity, the original observation and the full difference list. A missing artifact, canceled job or changed result leaves this attempt incomplete.

4. Keep the baseline branch at the checker commit. When the baseline has passed its qualification, publish the corrected source if its name is free. If the name already contains the corrected commit, use the existing branch. Recover an uncertain push by reading its actual result before another action.

   ```sh
   git -c push.followTags=false push --atomic --porcelain --no-follow-tags --recurse-submodules=no \
     "--force-with-lease=$corrected_ref:" origin "$corrected:$corrected_ref"
   ```

5. Read the actual corrected event as in step 2. If a manual event is necessary, use `--ref "$corrected_name"`. The hosted checkout fetches the branches. The fixed checker reads the resulting baseline tracking ref, `refs/remotes/origin/review/normalized-shannon-baseline-<manifest-sha256>`, and compares its object ID with the frozen checker commit. It runs the original and corrected sources in separate Cargo directories. Compare both whole observation files with [original.json](original.json) and [corrected.json](corrected.json). Verify both 16-test regressions, the toolchain, the two Cargo exits, and the actual result and difference files. Register this new run separately from the original run. Provider artifact IDs, times and archive digests can change. Preserve the new artifacts and the original receipts.

## Release the temporary names

After all jobs and all known readers have finished, confirm that both branch and tag inventories agree with the expected state. Keep copies of the actual accepted artifacts and verify that their contents can be read back. If the names are required by a current job or a standing availability agreement, keep them. With authority for both names and their exact expected heads, the following command removes them in one transaction.

```sh
git -c push.followTags=false push --atomic --porcelain --no-follow-tags --recurse-submodules=no \
  "--force-with-lease=$baseline_ref:$checker" \
  "--force-with-lease=$corrected_ref:$corrected" \
  origin ":$baseline_ref" ":$corrected_ref"
```

Check the advertised heads and tags and the provider event history again. The default branch and other names must agree with the inventory taken before this operation. An uncertain write first needs an observation of actual remote state. While the two branches are absent, readers can check the saved observations and open both immutable Git commits. An authorized maintainer must restore the named branches before a new hosted comparison. Future GitHub permissions, protections, runner images, pinned actions, toolchain downloads and artifact retention can affect that operation.
