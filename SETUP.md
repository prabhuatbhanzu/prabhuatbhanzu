# Profile graphics

Contribution SVGs are generated from GitHub's real contribution calendar (same source as your profile graph).

## Refresh locally

```bash
cd ~/prabhuatbhanzu
gh auth login   # user token required (private contrib counts)
python3 scripts/generate_profile_graphics.py
git add assets && git commit -m "chore: refresh contribution graphics" && git push
```

## Automated daily refresh

Create a **classic PAT** with at least `read:user` (user identity used for the contribution calendar), then:

Repo → Settings → Secrets → Actions → New secret:

- Name: `PROFILE_GRAPHICS_TOKEN`
- Value: the PAT

`GITHUB_TOKEN` is not enough — it only sees public contributions (~8), not your full profile total (~359).
