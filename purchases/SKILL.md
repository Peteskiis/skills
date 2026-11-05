---
name: purchases
description: Complete a requested online purchase using the browser and saved vault payment and shipping records. Use for buying, ordering, or completing checkout; browsing and price comparisons alone do not authorize an order.
---
# Purchases

Carry the user's requested purchase through checkout and verify the order. Use
information and authorization already given in the conversation. Ask only for a
missing decision that materially changes the purchase.

## Product and cart

Open the user's product link directly. Match its selected variant with their
size, color, quantity, and other constraints. A more specific site label for the
same linked variant is not a substitution: “Heathered Grey” can refer to the
linked “Heathered Core Ultra Light Grey.” If the actual variant conflicts with
the request, resolve that conflict before buying.

Inspect an existing cart before adding anything. Reuse the requested item when
it is already present and keep the intended quantity. Use standard shipping
unless the user specifies otherwise. Skip optional subscriptions, donations,
marketing signups, protection plans, and other extras. A coupon field alone is
not a reason to stop and ask a question.

## Saved records and private input

Use the browser tool's available schema. In Build CLI, Blink exposes `cards` and
`contacts` for saved vault metadata and `fill_card` and `fill_contact` for native
filling. Select the requested/default record; one matching saved record needs
no extra confirmation. Ask which to use only when several plausible records
remain and the conversation and labels do not resolve the choice.

Take a fresh snapshot and target a field in the intended checkout section with
its `element` reference. Pass the `document`, `record_id`, and `revision` from
the matching vault listing. Fill the shipping section, then the payment section
when it is available. A new card/contact listing replaces the previous listing's
document reference. The browser resolves private values; do not extract card
numbers or vault secrets through shell, page evaluation, or generic HTTP calls.

Treat embedded payment inputs as fields to interact with, not as an automatic
reason to hand off. Use the capabilities the installed browser actually exposes.
If a field is not yet visible, open its checkout step and inspect again. After a
stale reference or changed-document result, refresh the snapshot/listing and
retarget. Do not repeat an unchanged failing fill indefinitely.

When a genuinely missing value requires the user, use the available private-input
UI. Do not claim that a private form exists if the current tools/client lack it.
For a bank/device approval or an unsupported widget, identify the specific step
requiring the user. A successful private-fill receipt is enough to continue;
there is no need to ask the user to type “done” again.

## Finish the checkout

Filling is not submission. Inspect the page's validation state and click the
appropriate Continue, Log in, or purchase control to advance the authorized
task. Do not ask the user to click a button the browser tool can operate.

Check the final item, quantity, shipping method, tax, fees, and total against the
request and any budget. State the total. When the user has authorized this
purchase and its constraints are met, submit it without asking for that same
authorization again. Ask about material departures, not routine checkout steps.

After a timeout or uncertain payment response, inspect confirmation or order
status before retrying. A successful user payment handoff may already have placed
the order. Never turn an uncertain response into a duplicate purchase.

Report the confirmed order number, total, and delivery estimate when shown. If
blocked, distinguish a browser/tool failure from missing user information and
state whether an order was placed. Keep private payment and address values out
of chat, reports, and verification screenshots.
