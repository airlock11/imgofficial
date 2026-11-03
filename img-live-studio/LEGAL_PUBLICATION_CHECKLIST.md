# IMG LIVE Studio legal pages — publication checklist

**Status: PRE-PUBLICATION DRAFT.** Created November 3, 2026. This branch does not change the live site or Android repository until merged/deployed. The new HTML pages are visibly marked as drafts and use `noindex,nofollow`. **Do not merge or publish as binding terms until all blockers below are resolved.** No effective dates have been set.

## Added draft pages
- `img-live-studio/terms/index.html` — Global Terms of Service
- `img-live-studio/subscriptions/index.html` — Subscription, Cancellation & Refund Policy
- `img-live-studio/broadcasting-policy/index.html` — Broadcasting & Content Policy
- `img-live-studio/data-retention/index.html` — Data Retention & Deletion Policy
- `img-live-studio/legal/index.html` — centralized legal index

## Existing published pages intentionally preserved
- `img-live-studio/privacy/index.html` — Privacy Policy (effective October 26, 2026)
- `img-live-studio/data-deletion/index.html` — Data deletion instructions (dated October 26, 2026)
- `privacy/index.html` — **different IMG website** privacy/advertising policy

## Blocking checks before public release
- [ ] Proposed customer-facing operator name: **IMGGlobal** (unverified as a registered legal entity). Verify the **actual contracting operator** and its legal name, physical contact address, jurisdiction, applicable governing law and appropriate dispute process. "IMG LIVE Studio" is a product name, not evidence of incorporation.
- [ ] Confirm contact mailbox `imgglobal@imgofficial.com` is staffed and tested for privacy, abuse and subscription complaints.
- [ ] Confirm actual subscription channels (Google Play, direct website, or other), checkout disclosures, merchant identity, payment processor, tax treatment, any trial length, fees and currencies. **Do not claim billing works until verified.**
- [ ] Implement and test easy online cancellation for each active billing channel, including an in-app account-settings or equivalent cancellation route where platform policy requires. Verify successful cancellation prevents future renewal and properly preserves already-paid entitlements.
- [ ] Verify refund handling and no-voluntary-money-back-guarantee wording against mandatory local consumer rights; seek counsel on EU withdrawal rights and other key markets before accepting subscriptions.
- [ ] Verify precise Android/Cloudflare/Facebook/YouTube data flows, permissions, backend storage, token handling, session deletion behavior, retention periods, hosting logs, backups and subprocessor roles. Resolve discrepancies between existing October 26 privacy disclosures and the released app.
- [ ] Determine whether IMGGlobal (through its actual legal operator) acts as a controller or processor in each service relationship; obtain applicable data processing agreements and international transfer safeguards.
- [ ] Confirm minor/child account eligibility and youth-event notice/consent processes; assess child-privacy rules in target markets.
- [ ] Validate user authorization, content reporting, repeat-infringer policies and formal notice procedures where laws require them.
- [ ] Legal review of aggregate liability cap, indemnification, exclusions, consumer rights, arbitration/forum selection and statutory duties in priority countries. Disclaimers cannot waive non-excludable liabilities.
- [ ] Confirm public site navigation, footer links, accepted-version record keeping, user notification/consent flow, accessibility and link integrity.
- [ ] Replace draft notices with approved effective dates and final verified details only **after** review and authorization.
- [ ] Remove `noindex,nofollow` only if public indexing is desired and the legal pages are finalized.
- [ ] Deploy new pages and verify live URLs separately after merging and deploying; a GitHub PR is not proof of publication.

## Business agreements — separate next phase
Enterprise MSA, appropriate controller–processor DPA, enterprise order forms, and any negotiated SLA should be prepared for qualifying customers rather than automatically applying to ordinary app subscriptions.

## Policy decisions reflected
- Customers may cancel a recurring subscription; future renewal should stop when cancellation is processed in time.
- Cancellation ordinarily leaves premium access available until the paid term ends.
- No voluntary money-back guarantee; refund and consumer remedies remain available when required by law, platform rules, or approved as a documented exception.
- Ordinary subscriber transactions should use customer-facing terms, not automatically an MSA.
