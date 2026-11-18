# IMG LIVE Studio legal pages — publication checklist

**Status: PRE-PUBLICATION DRAFT.** Created November 3, 2026. This branch does not change the live site or Android repository until merged/deployed. The new HTML pages are visibly marked as drafts and use `noindex,nofollow`. **Do not merge or publish as binding terms until all blockers below are resolved.** No effective dates have been set.

## Added draft pages
- `img-live-studio/terms/index.html` — Global Terms of Service
- `img-live-studio/subscriptions/index.html` — Subscription, Cancellation & Refund Policy
- `img-live-studio/broadcasting-policy/index.html` — Broadcasting & Content Policy
- `img-live-studio/data-retention/index.html` — Data Retention & Deletion Policy
- `img-live-studio/legal/index.html` — centralized legal index

## Previously published pages — identity-only edits staged in this branch
- `img-live-studio/privacy/index.html` — existing Privacy Policy (effective October 26, 2026); a **draft, not-yet-published operator identity paragraph** was added on this branch. Existing effective date preserved.
- `img-live-studio/data-deletion/index.html` — existing data deletion instructions (dated October 26, 2026); a **draft, not-yet-published operator identity paragraph** was added on this branch. Existing date preserved.
- `privacy/index.html` — **different IMG website** privacy/advertising policy; no changes.

## Blocking checks before public release
- [x] Record the business name reported by the operator as Philippine DTI-registered: **IMGRAVION Software Development Services**. **IMGGlobal** is the customer-facing brand; **IMG LIVE Studio** is the product. This check reflects the operator's statement, not independent registration verification.
- [ ] Inspect the DTI certificate and verify exact business-name spelling, registered proprietor's full legal name, registration number and validity; confirm the business/contact address and applicable business/tax registrations without inventing details.
- [ ] Use **IMGRAVION Software Development Services** as the operating business name and **IMGGlobal** as the customer-facing brand in public-facing drafts; do **not publish the proprietor's personal name** in these drafts. A DTI-registered business name does not itself create a corporation or separate liability shield. Before publication, obtain legal advice on whether any applicable contract, e-commerce or regulatory disclosures must identify the proprietor personally. Do not publish terms that omit a legally required disclosure. Confirm governing law, consumer rights and a lawful dispute process.
- [ ] Replace all draft-only registration/proprietor cautions with accurate, documented final details, then obtain legal approval before publication.
- [ ] Confirm contact mailbox `imgglobal@imgofficial.com` is staffed and tested for privacy, abuse and subscription complaints.
- [ ] Confirm actual subscription channels (Google Play, direct website, or other), checkout disclosures, merchant identity, payment processor, tax treatment, any trial length, fees and currencies. **Do not claim billing works until verified.**
- [ ] Implement and test easy online cancellation for each active billing channel, including an in-app account-settings or equivalent cancellation route where platform policy requires. Verify successful cancellation prevents future renewal and properly preserves already-paid entitlements.
- [ ] Verify refund handling and no-voluntary-money-back-guarantee wording against mandatory local consumer rights; seek counsel on EU withdrawal rights and other key markets before accepting subscriptions.
- [ ] Verify precise Android/Cloudflare/Facebook/YouTube data flows, permissions, backend storage, token handling, session deletion behavior, retention periods, hosting logs, backups and subprocessor roles. Resolve discrepancies between existing October 26 privacy disclosures and the released app; specifically verify current IMG account email/password and OTP flows, device/session isolation, broadcast history sync and device-only offline recordings before revising those claims.
- [ ] After the privacy/data-deletion content audit, issue newly approved policy dates and notices where required. The current branch preserves the October 26 dates while staging the operator-identity update; it is **not** a completed privacy-policy revision.
- [ ] Determine whether the proprietor trading as IMGRAVION Software Development Services acts as data controller or processor in each service relationship; obtain applicable data processing agreements and international transfer safeguards.
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
