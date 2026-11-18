"""Connection errors of BRP084 units, kept in Home Assistant's history."""

from typing import override

from pydaikin.daikin_brp084 import DaikinBRP084

from homeassistant.components.event import EventEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import DaikinConfigEntry, DaikinCoordinator
from .entity import DaikinEntity
from .tuning import ERROR_KINDS, describe_error, error_kind, listen_for_errors


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DaikinConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the connection error entity of a BRP084 unit."""
    coordinator = entry.runtime_data
    # The errors come from the retry tuning, which only BRP084 adapters get.
    if isinstance(coordinator.device, DaikinBRP084):
        async_add_entities([DaikinConnectionErrorEvent(coordinator)])


class DaikinConnectionErrorEvent(DaikinEntity, EventEntity):
    """A failed request to the unit that is being retried.

    It records the same errors as the "Retrying request" warning, one per
    request. Unlike the log, its history survives restarts and updates.
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_event_types = list(ERROR_KINDS)
    _attr_translation_key = "connection_error"

    def __init__(self, coordinator: DaikinCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self.device.mac}-connection_error"

    @property
    @override
    def available(self) -> bool:
        """Stay available while the unit doesn't answer, as that's when errors come."""
        return True

    @override
    async def async_added_to_hass(self) -> None:
        """Start recording the unit's errors."""
        await super().async_added_to_hass()
        self.async_on_remove(listen_for_errors(self.device, self._async_record))

    @callback
    def _async_record(self, error: BaseException) -> None:
        """Record a request error, with the system's reason for it."""
        self._trigger_event(error_kind(error), {"error": describe_error(error)})
        self.async_write_ha_state()
