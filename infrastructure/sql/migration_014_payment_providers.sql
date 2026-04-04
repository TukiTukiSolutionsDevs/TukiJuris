-- Migration 014: Rename Stripe columns to payment-agnostic + add provider column
-- Sprint 31 — MercadoPago + Culqi integration

-- Organizations
ALTER TABLE organizations RENAME COLUMN stripe_customer_id TO payment_customer_id;
ALTER TABLE organizations RENAME COLUMN stripe_subscription_id TO payment_subscription_id;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS payment_provider VARCHAR(50);

-- Subscriptions
ALTER TABLE subscriptions RENAME COLUMN stripe_subscription_id TO payment_subscription_id;
ALTER TABLE subscriptions RENAME COLUMN stripe_price_id TO payment_plan_id;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS payment_provider VARCHAR(50);
