# Publish this profile

GitHub shows this README on https://github.com/prabhuatbhanzu when:

1. This repository is named exactly `prabhuatbhanzu`
2. It is **public**
3. `README.md` is on the default branch (`main`)

## One-time push

```bash
cd ~/prabhuatbhanzu
git init
git add .
git commit -m "Add premium GitHub profile README"
gh auth login   # if needed
gh repo create prabhuatbhanzu --public --source=. --remote=origin --push
```

Or create the empty public repo on GitHub first, then:

```bash
git remote add origin git@github.com:prabhuatbhanzu/prabhuatbhanzu.git
git branch -M main
git push -u origin main
```

## Optional profile settings

- Set a short bio, e.g. `Solve. Build. Ship. · Backend & product engineering`
- Pin repos once public projects exist
- Stats widgets already use `prabhuatbhanzu` — no secrets required

## Editing later

| Section | File / location |
|---|---|
| Hero / terminal look | `assets/*.svg` |
| Copy & stack | `README.md` |
| Featured repos | Uncomment the pin cards block in `README.md` |
| Currently building | `## Currently` in `README.md` |
