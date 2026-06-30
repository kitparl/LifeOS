# LifeOS

Personal life operating system project with [AI-DLC](https://github.com/awslabs/aidlc-workflows) (AI-Driven Development Life Cycle) integrated for Cursor.

## AI-DLC Setup

This repo ships with AI-DLC **v1.0.0** configured for Cursor:

- **Rule:** `.cursor/rules/ai-dlc-workflow.mdc`
- **Rule details:** `.aidlc-rule-details/` (symlink to `.aidlc/aidlc-rules/aws-aidlc-rule-details/`)

Verify in **Cursor Settings → Rules** that `ai-dlc-workflow` appears under Project Rules.

### Usage

Start any development task with:

```
Using AI-DLC, <your request>
```

The workflow guides you through Inception → Construction → Operations phases and writes artifacts to `aidlc-docs/` (gitignored).

### Update AI-DLC rules

```bash
chmod +x scripts/setup-aidlc.sh
./scripts/setup-aidlc.sh          # latest release
./scripts/setup-aidlc.sh v1.0.0   # specific version
```

### After cloning

```bash
git clone <repo-url> LifeOS
cd LifeOS
./scripts/setup-aidlc.sh   # re-run if symlinks need refreshing
```

## License

AI-DLC rules are licensed under [MIT-0](https://github.com/awslabs/aidlc-workflows/blob/main/LICENSE).
