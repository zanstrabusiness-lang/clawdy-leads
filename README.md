# Clawd

Clawd is the workspace for the Clawdy assistant supporting the trading indicator business at team-smm. The goal is to keep Sven's SaaS for TradingView indicators humming by automating ops, tracking performance, and pushing marketing/idea momentum through Git-based workflows.

## Business context

- **Offering:** Subscription-based TradingView indicators (Pine Script) for retail traders wanting better signals/strategies.
- **Revenue:** Monthly and yearly subscriptions sold via team-smm.com.
- **Stage:** Early growth—MVPs shipped, PoCs brewing, product line expanding.
- **Top priorities:** Build indicator PoCs, ship MVPs fast, and launch new indicators with consistent marketing.

## Workflows that matter

1. **Sales funnel:** Content (YouTube/TikTok/TradingView) → website → subscription → indicator access.
2. **Delivery:** Verify payment, grant access, provide install/use instructions, gather initial feedback.
3. **Support:** Answer install/use questions, access problems, expectation mismatches.
4. **Operations:** Track subscriptions/churn, manage access, update scripts, monitor indicator performance, publish content.

## GitHub setup (what still needs doing)

1. **Create the remote repo.** Run `gh repo create <team-smm>/<repo-name>` or create a repo from the GitHub UI and copy the URL.
2. **Push this workspace.**
   ```bash
   git branch -M main
   git remote add origin <url>
   git push -u origin main
   ```
3. **Protect main.** Add branch protection rules (require PR reviews, pass status checks) before merging.
4. **Document the process.** Keep this README and any operational docs updated so Clawd can keep shipping automation PRs.

## Collaboration guidelines

- Create a new branch per change (`feature/`, `fix/`, `doc/`), run the required checks, and open a draft PR for review.
- Clawd works proactively: expect new PRs for indicator scaffolds, content template generation, automation scripts, docs, and monitoring improvements.
- Keep tooling config inside the repo, avoid touching payment/live deployments without approval, and never push directly to main—PRs only.

## Next GitHub steps

- Hook this workspace to the GitHub repo and enable GitHub Actions for CI/monitoring (when tests exist).
- Add owners or CODEOWNERS if there are submodules or directories with dedicated responsibilities.
- Capture recurring tasks (idea generation, marketing experiments, indicator improvements) as GitHub Issues so Clawd can manage the backlog and hand them off via PRs.
