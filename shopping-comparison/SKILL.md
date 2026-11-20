---
name: shopping-comparison
description: Compare products or seller listings, verify price and availability, and rank offers against the buyer's criteria.
---

# Compare seller offers

Start from the supplied shortlist or product links. Use shopping search for discovery when the user needs candidates. A search result is a lead. A recommendation needs evidence from the seller's listing.

Read the actual link destinations. The same product name can appear at several sellers. Carry the URLs from the browser's link read into your checks. Building a URL from a host, product name or list position can silently point to a different offer. Keep each exact URL alongside its seller, observed details and availability. On a marketplace, several sellers can share one hostname. Use the seller shown on the listing when available.

For an unfamiliar seller, sample up to two distinct listings before queuing the rest. You can sample multiple sellers in one browser call. Return those samples and inspect the results before building the next batch. A script that only prints page reads will navigate to every queued URL before you can react. If both samples show the same seller error, skip the remaining links at that seller and describe the limitation. If a listing has ended, continue with other listings. An error page cannot establish that an item sold out. Inspect the remaining accessible candidates that could change the result.

Save the shortlist links before navigating away. In Blink, reuse the research tab across script calls with `const page = browser.page(id)` and `await page.goto(url)` using the observed page ID. Each `browser.open(url)` creates another tab. Open an additional tab when you need to preserve an interactive page or the user asks for it. When the user is watching, keep the listing being checked in the foreground.

Build the answer from the verified records. Compute the requested measure for each qualifying offer, sort the records by that value, and render the rows with the URLs you collected. Check the order, link destinations, and any qualification that affects the decision, such as shipping or condition. If a seller went unchecked, say so and limit the conclusion to the sources you reached.
