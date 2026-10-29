# tuned-daikin

Home Assistant's built-in Daikin integration from **2026.10.1**, with three changes for BRP084 Wi-Fi
adapters:

1. **A pydaikin build with fixes meant for upstream.** It's upstream pydaikin 2.21.0 plus these changes
   ([`ha-build-2.21`](https://github.com/pfgcoder/pydaikin/tree/ha-build-2.21)):
   - BRP084 requests are retried (3 attempts of 15 seconds) instead of failing on one 5-second timeout, and
     each adapter gets one request at a time. A request keeps its turn while it retries, so an older command
     can't land after a newer one and undo it. Errors name the device and say when the cause was a timeout.
   - A blank, missing or garbled value from a BRP084 adapter no longer crashes the update or the setup.
   - A device given as an IP address no longer triggers a network discovery broadcast, which stalled Home
     Assistant for at least a second at every setup.
   - Smaller BRP084 fixes: a failed command names the device, a reply cut off part-way through is retried,
     and commands are packaged correctly whatever order their settings come in.
2. **Retry tuning** (`custom_components/daikin/tuning.py`). Some adapters stop answering for a minute or
   more while staying on Wi-Fi, so the integration keeps trying for about 100 seconds instead. Each attempt
   gets 10 seconds. After a failure it waits 2, 4, 8 and then 16 seconds before trying again, so a
   struggling adapter isn't flooded with requests. No new attempt starts after 100 seconds, so a request
   gives up within 110. The first retry of each request is logged as a warning ("Retrying request to ..."),
   so the log shows how often retries happen.
3. **Setup retries after any HTTP error** (`custom_components/daikin/__init__.py`). An error such as
   429 Too Many Requests from a struggling adapter leaves the unit "not ready yet", so Home Assistant keeps
   retrying. The built-in integration only does that for connection errors, so a 429 left the unit failed
   until it was reloaded.

## Install (HACS)

1. HACS → ⋮ → Custom repositories → add this repository as an **Integration**.
2. Download it and restart Home Assistant.

Because it uses the same domain (`daikin`), it replaces the built-in integration automatically. Existing
Daikin entries, entities and automations are kept. Home Assistant logs a "custom integration not tested"
warning for `daikin`, which is expected.

Home Assistant reinstalls the pinned pydaikin from GitHub on every start, so startup needs internet access.

## Remove

Remove it in HACS and restart. The built-in integration takes over again with the same entities.

## Keeping in step with Home Assistant

This is a copy of 2026.10.1's integration. Before upgrading Home Assistant, re-copy the integration from
the new version and reapply the tuning and the setup change. 2026.11 adds demand-control services and
pins pydaikin 2.20.0.

Once a Home Assistant release includes a pydaikin with these fixes and the setup change, this no longer
needs to replace the built-in integration. It can shrink to a separate add-on that only applies the tuning.
