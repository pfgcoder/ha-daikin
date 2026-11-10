# tuned-daikin

Home Assistant's built-in Daikin integration from **2026.11.0**, with four changes for BRP084 Wi-Fi
adapters:

1. **A pydaikin build with fixes meant for upstream.** It's upstream pydaikin 2.22.1 plus these changes
   ([`ha-build-2.22`](https://github.com/pfgcoder/pydaikin/tree/ha-build-2.22)):
   - BRP084 requests are retried (3 attempts of 15 seconds) instead of failing on one 5-second timeout, and
     each adapter gets one request at a time. A request keeps its turn while it retries, so an older command
     can't land after a newer one and undo it. Errors name the device and say when the cause was a timeout.
   - A blank, missing or garbled value from a BRP084 adapter no longer crashes the update or the setup.
   - A device given as an IP address no longer triggers a network discovery broadcast, which stalled Home
     Assistant for at least a second at every setup.
   - Smaller BRP084 fixes: a failed command names the device, a reply cut off part-way through is retried,
     and commands are packaged correctly whatever order their settings come in.
   - When a unit's energy counters jump (its clock changes, or it's read in the middle of its midnight
     rollover), the power estimate starts again instead of logging "Impossible energy consumption measure"
     every two minutes for six hours.
   - Changing the setpoint, fan or swing of a BRP084 unit that's off is no longer silently dropped. It's
     written for the mode the unit runs in when it's turned back on, and the unit stays off.
   - A BRP084 unit whose louvers only swing up and down shows swing as "Vertical" while it swings. Before,
     it always showed "Off", because the unit has no side-to-side setting and reading it failed. This is
     upstream pull request [#178](https://github.com/fredrike/pydaikin/pull/178).
   - Turning Comfort on or off on a BRP084 unit works. Before, the unit ignored it, because it only acts
     on Comfort when the louver is set at the same time, as the remote does.
   - A BRP084 unit with no side-to-side swing no longer offers "Horizontal" and "3D" swing modes, which
     did nothing on it.
   - pydaikin reads whether a BRP084 indoor unit is itself calling for heat or cooling, which the climate
     card uses (see 4).
   - Fixes for other adapter types: they retry a slow or cut-off reply too, a failed status update reports
     the real error, logs and errors leave out passwords and keys, BRP072C uses its own random uuid when
     none is given, and discovery returns the address it found and no longer sets the wrong HTTP port.
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
4. **Comfort, Econo and Powerful on the climate card, plus switches** (`custom_components/daikin/climate.py`,
   `switch.py`). pydaikin can read and set these modes on BRP084 adapters, but the built-in integration
   doesn't show them.
   - On the climate card, the fan menu offers Auto, Quiet, Comfort and Boost (Powerful). Each of them sets
     the fan, and the unit allows only one at a time: Comfort puts the fan on Auto, and Powerful runs it
     flat out. Google Assistant shows only a thermostat's mode, setpoint and fan speed, so this is also how
     Google Home reaches Comfort and Powerful. The numbered fan speeds are left out; one set from the
     remote shows as its number.
   - Picking Auto or Quiet first ends Comfort or Powerful, as the unit won't change the fan while either
     is on (the remote's fan button does nothing then). Powerful keeps the fan speed it was set to and goes
     back to it when it ends.
   - The swing menu offers Off and Swing. A unit that also swings side to side keeps its Vertical,
     Horizontal and 3D options. The preset menu offers Eco (Econo), which doesn't change the fan.
   - The card's Heating, Cooling or Idle comes from the indoor unit itself. The built-in integration uses
     the compressor, which belongs to the outdoor unit, so on a multi-split every indoor unit on it showed
     "Heating" while any one of them still needed heat.
   - Each of Comfort, Econo, Powerful and the up-and-down swing also appears as a switch, on units that
     report it. The Swing switch does what the remote's swing button does.
   - As on the remote, the unit doesn't allow Powerful together with Comfort or Econo, so turning one side
     on turns the other off. The unit also ends Powerful by itself after about 20 minutes.
   - Comfort stops the swing and moves the louver to its comfort position (down when heating, up when
     cooling), and turning it off leaves the louver in the middle. Starting the swing ends Comfort; the
     fan menu and the Comfort switch show that within one poll, about 2 minutes.

## Install (Marketplace)

Needs Home Assistant 2026.11 or later.

1. Settings → Marketplace → **Add from link**, and enter this repository's URL. Custom repositories need
   a GitHub connection, which the Marketplace asks for the first time.
2. Download it and restart Home Assistant.

Because it uses the same domain (`daikin`), it replaces the built-in integration automatically. Existing
Daikin entries, entities and automations are kept. Home Assistant logs a "custom integration not tested"
warning for `daikin`, which is expected.

The requirement in `manifest.json` names the pinned pydaikin's exact version after the `#`, so Home
Assistant can tell it's already installed and doesn't download it again at every start. It downloads it
from GitHub only when it's missing or the pin changes, such as the first start after an update or after
the container is recreated, so those starts need internet access. Keep that version the same as the
pinned build's `pyproject.toml`; if they differ, Home Assistant reinstalls it at every start.

## Remove

Remove it in the Marketplace and restart. The built-in integration takes over again with the same entities.

## Keeping in step with Home Assistant

This is a copy of 2026.11.0's integration. Before upgrading Home Assistant, re-copy the integration from
the new version and reapply the tuning, the setup change, the climate menus and the mode switches.
2026.11.0's built-in integration pins pydaikin 2.22.1; this one uses the 2.22.1-based build above.
BRP084 adapters don't support 2026.11's new demand-control action, so it reports "not supported" for
them either way.

Once a Home Assistant release includes a pydaikin with these fixes, the setup change, the climate menus
and the mode switches, this no longer needs to replace the built-in integration. It can shrink to a
separate add-on that only applies the tuning.
