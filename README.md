# Daikin AC (patched pydaikin)

Home Assistant's built-in Daikin integration from **2026.10.1**, unchanged except that it uses a patched
[pydaikin](https://github.com/pfgcoder/pydaikin/tree/brp084-timeout-retry).

## Why

BRP084 Wi-Fi adapters sometimes take longer than 5 seconds to answer, or stop answering for a minute or
more while staying on Wi-Fi. pydaikin 2.19.1 gave them a hard 5-second timeout with no retry, so one slow
reply made Home Assistant mark the unit unavailable until the next poll two minutes later. The patched
pydaikin makes up to 10 attempts of 10 seconds each on timeouts and connection errors, about 110 seconds
in all, which fits inside Home Assistant's 120-second polling interval. Its errors name the device and say
when the cause was a timeout.

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

This is a copy of 2026.10.1's integration. Remove it once a Home Assistant release includes a pydaikin
with the fix, or re-copy the integration from the Home Assistant version you're running.
