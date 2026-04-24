from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

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


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Ampere Modbus binary sensors from config entry."""
    hub_name = entry.data[CONF_NAME]
    hub = hass.data[DOMAIN][hub_name]["hub"]

    device_info = {
        "identifiers": {(DOMAIN, hub_name)},
        "name": hub_name,
        "manufacturer": ATTR_MANUFACTURER,
    }

    entities = [
        AmpereBinarySensor(hub_name, hub, device_info, description)
        for description in BINARY_SENSOR_TYPES.values()
    ]

    _LOGGER.debug("Adding %s Ampere Modbus binary sensors", len(entities))
    async_add_entities(entities, True)

    return True


class AmpereBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of an Ampere Storage Pro Modbus binary sensor."""

    def __init__(
        self,
        platform_name: str,
        hub: AmpereStorageProModbusHub,
        device_info,
        description: AmpereModbusBinarySensorEntityDescription,
    ):
        self._platform_name = platform_name
        self._attr_device_info = device_info
        self.entity_description = description

        super().__init__(coordinator=hub)

    @property
    def name(self) -> str:
        return f"{self._platform_name} {self.entity_description.name}"

    @property
    def unique_id(self) -> Optional[str]:
        return f"{self._platform_name}_binary_{self.entity_description.key}"

    @property
    def is_on(self) -> Optional[bool]:
        raw_status = self.coordinator.data.get("devicestatus_raw")

        if raw_status is None:
            return None

        if self.entity_description.key == "island_mode":
            return raw_status == 3

        if self.entity_description.key == "grid_mode":
            return raw_status == 4

        return None


@dataclass
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
