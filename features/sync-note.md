# Feature: Knowledge Notes → GitHub Sync

LifeOS can push Knowledge Notes (subjects → chapters → sections) to a GitHub repository as Markdown, including inline images, in **one atomic commit** per section sync.

---

## Overview

| Capability | Description |
|------------|-------------|
| **Config UI** | Integrations page: PAT (eye toggle), `owner/repo`, branch, base path |
| **Section push** | ↗ button on a note section → save locally → push to GitHub |
| **Atomic commit** | Git Data API: blobs → tree → one commit → update branch |
| **Incremental** | Content hash skip (“Already up to date”); updates overwrite; deletes remove tracked files |
| **Notifications** | Optional separate toggles: in-app and/or Telegram |

Credentials (PAT) are stored encrypted. All GitHub calls run on the **backend** only.

---

## Setup

### 1. Create a GitHub repo + PAT

1. Create a repo (e.g. `lifeos-notes`), empty or with a default branch.
2. Create a fine-grained PAT with **Contents: Read and write** on that repo  
   (or a classic PAT with `repo` for private repos).
3. Copy the token.

### 2. Connect in LifeOS

1. Open **Integrations** → **GitHub**.
2. Paste **Personal Access Token** (masked; use 👁 to reveal when editing).
3. Set **Repository** as `owner/repo` or a clone URL (`https://github.com/owner/repo.git`), **Branch** (default `main`), **Base path** leave blank for repo root (`python/`, `system-design/` …).
4. Enable **GitHub sync**.
5. Optionally:
   - **Notify in-app on GitHub sync**
   - **Notify via Telegram on GitHub sync** (Telegram must also be configured)
6. Click **Save**, then **Test connection** (checks token, repo, branch, write access).

---

## How to sync now

1. Open **Knowledge Notes** → pick a subject → open a section.
2. Edit content if needed (autosave / Save).
3. Click **↗** next to Export (↓) in the section toolbar.
4. Wait until the button finishes (second clicks are ignored while syncing).
5. Check:
   - Success/error text in the docbar
   - Your GitHub repo for a new commit
   - **Notifications** / Telegram if those toggles are on

**Tips**

- Sync is disabled / blocked while a save is in progress; the button saves first if there are unsaved edits.
- Syncing the same content again returns **Already up to date** (no new commit).
- After edits, sync again → same path updated in **one** commit (markdown + assets).

---

## Repo layout

With **Base path** blank (default), subjects land at the repo root:

```
lifeos-notes/
  python/
    variables/
      intro.md
      assets/
        <file-id>-image.png
  system-design/
    ...
```

Optional: set Base path to e.g. `notes` if you want a wrapper folder.
