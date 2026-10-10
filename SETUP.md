# Install the automatic GitHub profile projects section

1. In `Yassine-Jemi01/Yassine-Jemi01`, replace the repository's `README.md` with the one in this folder.
2. Add `scripts/update_projects.py` and `.github/workflows/update-projects.yml` at the same paths.
3. Keep the existing `whoami.svg` file in the profile repository; the README references it as `./whoami.svg`.
4. Commit and push these files to the repository's default branch.
5. Open the repository's **Actions** tab and run **Update profile projects** once using **Run workflow** if you want to refresh the list immediately. The workflow will also run weekly.
6. In **Settings → Actions → General → Workflow permissions**, make sure workflows are allowed to read and write repository contents if GitHub doesn't allow the workflow to push the generated README update.

The project list excludes the profile repository itself, forks, archived repositories, disabled repositories, and private repositories. It selects up to five repositories using this score:

`score = (stars × 2) + recency bonus`

The recency bonus starts at 30 and decreases by one point per day since the last push, reaching zero after 30 days. This intentionally balances community interest and recent maintenance; it is not a formal assessment of source-code quality.

The workflow only commits when the generated section changes. The `whoami.svg` section and the rest of the README are outside the generated markers and are preserved.
