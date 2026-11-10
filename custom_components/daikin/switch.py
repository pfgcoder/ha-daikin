"""Support for Daikin AirBase zones."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, override

from pydaikin.daikin_brp084 import DaikinBRP084

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ZONE_NAME_UNCONFIGURED
from .coordinator import DaikinConfigEntry, DaikinCoordinator
from .entity import DaikinEntity

DAIKIN_ATTR_ADVANCED = "adv"
DAIKIN_ATTR_STREAMER = "streamer"
DAIKIN_ATTR_MODE = "mode"


@dataclass(frozen=True, kw_only=True)
class DaikinModeSwitchEntityDescription(SwitchEntityDescription):
    """Describes an on/off mode of a BRP084 unit, such as Comfort."""

    supported_fn: Callable[[DaikinBRP084], bool]
    is_on_fn: Callable[[DaikinBRP084], bool]
    set_fn: Callable[[DaikinBRP084, str], Awaitable[None]]


# pydaikin turns Powerful off when Comfort or Econo is turned on, and the other
# way round, as the unit allows only one side at a time. The unit also ends
# Powerful by itself after about 20 minutes.
MODE_SWITCHES: tuple[DaikinModeSwitchEntityDescription, ...] = (
    DaikinModeSwitchEntityDescription(
        key="comfort",
        translation_key="comfort",
        supported_fn=lambda device: device.support_comfort_mode,
        is_on_fn=lambda device: device.comfort_mode == "on",
        set_fn=lambda device, state: device.set_comfort_mode(state),
    ),
    DaikinModeSwitchEntityDescription(
        key="econo",
        translation_key="econo",
        supported_fn=lambda device: device.support_econo_mode,
        is_on_fn=lambda device: device.econo_mode == "on",
        set_fn=lambda device, state: device.set_econo_mode(state),
    ),
    DaikinModeSwitchEntityDescription(
        key="powerful",
        translation_key="powerful",
        supported_fn=lambda device: device.support_powerful_mode,
        is_on_fn=lambda device: device.powerful_mode == "on",
        set_fn=lambda device, state: device.set_powerful_mode(state),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DaikinConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Daikin climate based on config_entry."""
    daikin_api = entry.runtime_data
    switches: list[SwitchEntity] = []
    if zones := daikin_api.device.zones:
        switches.extend(
            DaikinZoneSwitch(daikin_api, zone_id)
            for zone_id, zone in enumerate(zones)
            if zone[0] != ZONE_NAME_UNCONFIGURED
        )
    if daikin_api.device.support_advanced_modes:
        # It isn't possible to find out from the API responses if a specific
        # device supports the streamer, so assume so if it does support
        # advanced modes.
        switches.append(DaikinStreamerSwitch(daikin_api))
    if isinstance(daikin_api.device, DaikinBRP084):
        # Only the modes this unit reported in its first status update.
        switches.extend(
            DaikinModeSwitch(daikin_api, description)
            for description in MODE_SWITCHES
            if description.supported_fn(daikin_api.device)
        )
    switches.append(DaikinToggleSwitch(daikin_api))
    async_add_entities(switches)


class DaikinZoneSwitch(DaikinEntity, SwitchEntity):
    """Representation of a zone."""

    _attr_translation_key = "zone"

    def __init__(self, coordinator: DaikinCoordinator, zone_id: int) -> None:
        """Initialize the zone."""
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._attr_unique_id = f"{self.device.mac}-zone{zone_id}"

    @property
    @override
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.device.zones[self._zone_id][0]

    @property
    @override
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        return self.device.zones[self._zone_id][1] == "1"

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the zone on."""
        await self.device.set_zone(self._zone_id, "zone_onoff", "1")
        await self.coordinator.async_refresh()

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the zone off."""
        await self.device.set_zone(self._zone_id, "zone_onoff", "0")
        await self.coordinator.async_refresh()


class DaikinStreamerSwitch(DaikinEntity, SwitchEntity):
    """Streamer state."""

    _attr_name = "Streamer"
    _attr_translation_key = "streamer"

    def __init__(self, coordinator: DaikinCoordinator) -> None:
        """Initialize switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self.device.mac}-streamer"

    @property
    @override
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        return DAIKIN_ATTR_STREAMER in self.device.represent(DAIKIN_ATTR_ADVANCED)[1]

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the zone on."""
        await self.device.set_streamer("on")
        await self.coordinator.async_refresh()

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the zone off."""
        await self.device.set_streamer("off")
        await self.coordinator.async_refresh()


class DaikinModeSwitch(DaikinEntity, SwitchEntity):
    """An on/off mode of a BRP084 unit, such as Comfort."""

    entity_description: DaikinModeSwitchEntityDescription
    device: DaikinBRP084

    def __init__(
        self,
        coordinator: DaikinCoordinator,
        description: DaikinModeSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self.device.mac}-{description.key}"

    @property
    @override
    def is_on(self) -> bool:
        """Return whether the mode is on."""
        return self.entity_description.is_on_fn(self.device)

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the mode on."""
        await self.entity_description.set_fn(self.device, "on")
        await self.coordinator.async_refresh()

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the mode off."""
        await self.entity_description.set_fn(self.device, "off")
        await self.coordinator.async_refresh()


class DaikinToggleSwitch(DaikinEntity, SwitchEntity):
    """Switch state."""

    _attr_translation_key = "toggle"

    def __init__(self, coordinator: DaikinCoordinator) -> None:
        """Initialize switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self.device.mac}-toggle"

    @property
    @override
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        return "off" not in self.device.represent(DAIKIN_ATTR_MODE)

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the zone on."""
        await self.device.set({})
        await self.coordinator.async_refresh()

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the zone off."""
        await self.device.set({DAIKIN_ATTR_MODE: "off"})
        await self.coordinator.async_refresh()
