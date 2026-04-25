from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_MANUFACTURER, DOMAIN
from .hub import AmpereStorageProModbusHub

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities) -> bool:
    """Set up Ampere Modbus binary sensors from a config entry."""
    hub_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)

    if not hub_data or "hub" not in hub_data:
        _LOGGER.error(
            "Cannot set up binary sensors for %s entry %s: hub data missing.",
            DOMAIN,
            entry.entry_id,
        )
        return False

    hub: AmpereStorageProModbusHub = hub_data["hub"]
    hub_name = hub_data.get("name") or entry.data.get(CONF_NAME) or entry.title or DOMAIN

    device_info = {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": hub_name,
        "manufacturer": ATTR_MANUFACTURER,
    }

    entities: list[AmpereBinarySensor] = [
        AmpereBinarySensor(
            entry_id=entry.entry_id,
            platform_name=hub_name,
            hub=hub,
            device_info=device_info,
            description=description,
        )
        for description in BINARY_SENSOR_TYPES.values()
    ]

    _LOGGER.debug("Adding %s Ampere Modbus binary sensors", len(entities))
    async_add_entities(entities)

    return True


class AmpereBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of an Ampere Storage Pro Modbus binary sensor."""

    entity_description: "AmpereModbusBinarySensorEntityDescription"

    def __init__(
        self,
        entry_id: str,
        platform_name: str,
        hub: AmpereStorageProModbusHub,
        device_info: dict[str, Any],
        description: "AmpereModbusBinarySensorEntityDescription",
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator=hub)

        self._entry_id = entry_id
        self._platform_name = platform_name
        self._attr_device_info = device_info
        self.entity_description = description

        self._attr_name = f"{self._platform_name} {self.entity_description.name}"
        self._attr_unique_id = f"{DOMAIN}_{self._entry_id}_binary_{self.entity_description.key}"

    @property
    def available(self) -> bool:
        """Return whether the binary sensor has usable coordinator data."""
        return bool(
            self.coordinator.last_update_success
            and self.coordinator.data
            and (
                self.entity_description.key in self.coordinator.data
                or "devicestatus_raw" in self.coordinator.data
            )
        )

    @property
    def is_on(self) -> Optional[bool]:
        """Return the binary sensor state.

        Prefer explicit boolean values from coordinator data. Fall back to the
        raw device status for compatibility with older hub data.
        """
        data = self.coordinator.data or {}
        key = self.entity_description.key

        explicit_value = data.get(key)
        if isinstance(explicit_value, bool):
            return explicit_value

        raw_status = data.get("devicestatus_raw")
        if raw_status in (None, "", "unknown", "Unknown", "unavailable", "Unavailable"):
            return None

        try:
            raw_status_int = int(raw_status)
        except (TypeError, ValueError):
            _LOGGER.debug(
                "Ignoring non-integer devicestatus_raw for binary sensor %s: %r",
                key,
                raw_status,
            )
            return None

        if key == "island_mode":
            return raw_status_int == 3

        if key == "grid_mode":
            return raw_status_int == 4

        return None


@dataclass(frozen=True, kw_only=True)
class AmpereModbusBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Description for Ampere Modbus binary sensor entities."""


BINARY_SENSOR_TYPES: dict[str, AmpereModbusBinarySensorEntityDescription] = {
    "IslandMode": AmpereModbusBinarySensorEntityDescription(
        name="Island Mode",
        key="island_mode",
        icon="mdi:transmission-tower-off",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "GridMode": AmpereModbusBinarySensorEntityDescription(
        name="Grid Mode",
        key="grid_mode",
        icon="mdi:transmission-tower",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
}
