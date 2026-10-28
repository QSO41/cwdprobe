# Manual v0.1.0 release procedure

R2 prepares local files only. Every remote creation, push, tag and release below
requires explicit user approval first. No automatic publication workflow.

1. Review `R2_RELEASE_READINESS.zh-CN.md`, `releases/v0.1.0.md`, history and
   checksums. After approval, create one empty GitHub repository named cwdprobe
   in the user's confirmed namespace; do not initialize another README/license.
2. Attach that exact URL and publish HEAD as main:

   ```powershell
   git remote add origin https://github.com/OWNER/cwdprobe.git
   git push -u origin HEAD:main
   ```

   Replace OWNER. If origin exists, inspect it rather than overwriting it.
   The local codex/mvp branch need not be renamed.
3. Observe both Windows Python 3.11/3.12 jobs for that exact main commit. Inspect
   logs/failure artifacts and resolve failures before continuing. Only observed
   successful hosted runs change CI from NOT TESTED to PASS; update public CI
   wording accordingly before tagging the final release commit.
4. Confirm a clean worktree and compare the approved assets:

   ```powershell
   python tools/build.py
   Get-FileHash dist/cwdprobe.pyz -Algorithm SHA256
   Get-FileHash dist/v0.1.0/cwdprobe-0.1.0.pyz -Algorithm SHA256
   Get-Content dist/v0.1.0/SHA256SUMS.txt
   ```

   The versioned copy must match the newly built archive byte for byte. Any core
   change requires new tests/copy/hash/smoke. A checksum detects mismatch; it is
   not a cryptographic signature. Re-run CI on any changed release commit.
5. After CI for the approved commit passes, create and push the version tag:

   ```powershell
   git tag -a v0.1.0 -m 'cwdprobe v0.1.0'
   git push origin v0.1.0
   ```

   In GitHub's Release UI choose that existing tag, copy the release notes and
   attach ONLY the three files under dist/v0.1.0: cwdprobe-0.1.0.pyz,
   SHA256SUMS.txt and LICENSE. Inspect the draft before authorized publication.
   Never upload local-acceptance, reports, raw logs, install targets or the whole
   working directory. GitHub's source archive comes from the reviewed tag.

The name check found no obvious project conflict, not a trademark or namespace
reservation. Recheck the confirmed owner's repository name before creation.
