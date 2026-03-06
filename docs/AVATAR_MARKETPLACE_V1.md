# Avatar Provider Directory / Marketplace v1

## Product intent
A curated directory of real people (providers) who license avatar usage to customers.
Customers can purchase avatar usage outside plan limits; provider receives payout per licensed usage.

## v1 scope implemented

- API scaffolding for marketplace:
  - `POST /v1/avatar-marketplace/providers` (admin-key protected)
  - `POST /v1/avatar-marketplace/listings` (admin-key protected)
  - `GET /v1/avatar-marketplace/listings`
  - `POST /v1/avatar-marketplace/purchases` (workspace role protected)
- Data models:
  - `avatar_providers`
  - `avatar_listings`
  - `avatar_purchases`

## Security / control

- Set env key for admin operations:
  - `AVATAR_MARKETPLACE_ADMIN_KEY=<strong-random-key>`
- Provider/listing creation requires `X-Admin-Key` header.
- Purchases require authenticated workspace user (`editor+`).

## Legal rails required before public launch

1. Identity verification of provider
2. Signed consent + likeness release packet (versioned)
3. Allowed/prohibited use categories (stored per provider)
4. Revocation/takedown workflow and SLA
5. Audit log of every render usage tied to purchase
6. Payout ledger + dispute hold periods

## v1 operational policy

- Launch curated private beta (manual provider vetting)
- US region only initially (`legalRegion=US`)
- Restricted categories disallowed by default: political, medical claims, deceptive endorsements
- Manual payout exports monthly until payout engine is built

## Next engineering steps

1. Attach `avatar_listing_id` to video render jobs when purchased listing is used
2. Enforce purchase balance/validity at render time
3. Add usage ledger and provider payout accrual entries
4. Add operator UI: provider/listing create + purchase audit
5. Add customer UI: browse directory + purchase flow
