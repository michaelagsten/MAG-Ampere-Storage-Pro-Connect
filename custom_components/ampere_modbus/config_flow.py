from __future__ import annotations

import ipaddress
import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_UNIT,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT,
    DOMAIN,
    CONF_BATTERY_NOMINAL_CAPACITY_KWH,
    CONF_PV_NOMINAL_POWER_KW,
    CONF_INVERTER_NOMINAL_POWER_KW,
    CONF_PV_FEED_IN_LIMIT_PERCENT,
    CONF_BASE_LOAD_W,
    CONF_FLEXIBLE_LOAD_AVAILABLE_W,
    CONF_MAX_STORAGE_CHARGE_POWER_W,
    CONF_CLIPPING_SAFETY_RESERVE_W,
    DEFAULT_BATTERY_NOMINAL_CAPACITY_KWH,
    DEFAULT_PV_NOMINAL_POWER_KW,
    DEFAULT_INVERTER_NOMINAL_POWER_KW,
    DEFAULT_PV_FEED_IN_LIMIT_PERCENT,
    DEFAULT_BASE_LOAD_W,
    DEFAULT_FLEXIBLE_LOAD_AVAILABLE_W,
    DEFAULT_MAX_STORAGE_CHARGE_POWER_W,
    DEFAULT_CLIPPING_SAFETY_RESERVE_W,
)


def _default_for_required_string(
    defaults: dict[str, Any], key: str, fallback: str | None = None
) -> str | type[vol.UNDEFINED]:
    """Return a valid default for a required string field."""
    value = defaults.get(key, fallback)
    if value is None:
        return vol.UNDEFINED
    return str(value)


def _data_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the config/options schema with optional defaults."""
    defaults = defaults or {}

    return vol.Schema(
        {
            vol.Required(
                CONF_NAME,
                default=_default_for_required_string(defaults, CONF_NAME, DEFAULT_NAME),
            ): cv.string,
            vol.Required(
                CONF_HOST,
                default=_default_for_required_string(defaults, CONF_HOST, None),
            ): cv.string,
            vol.Required(
                CONF_PORT,
                default=defaults.get(CONF_PORT, DEFAULT_PORT),
            ): cv.port,
            vol.Optional(
                CONF_UNIT,
                default=defaults.get(CONF_UNIT, DEFAULT_UNIT),
            ): cv.positive_int,
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): cv.positive_int,

            # Technical system parameters
            vol.Optional(
                CONF_BATTERY_NOMINAL_CAPACITY_KWH,
                default=defaults.get(
                    CONF_BATTERY_NOMINAL_CAPACITY_KWH,
                    DEFAULT_BATTERY_NOMINAL_CAPACITY_KWH,
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=0)),
            vol.Optional(
                CONF_PV_NOMINAL_POWER_KW,
                default=defaults.get(
                    CONF_PV_NOMINAL_POWER_KW,
                    DEFAULT_PV_NOMINAL_POWER_KW,
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=0)),
            vol.Optional(
                CONF_INVERTER_NOMINAL_POWER_KW,
                default=defaults.get(
                    CONF_INVERTER_NOMINAL_POWER_KW,
                    DEFAULT_INVERTER_NOMINAL_POWER_KW,
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=0)),
            vol.Optional(
                CONF_PV_FEED_IN_LIMIT_PERCENT,
                default=defaults.get(
                    CONF_PV_FEED_IN_LIMIT_PERCENT,
                    DEFAULT_PV_FEED_IN_LIMIT_PERCENT,
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
            vol.Optional(
                CONF_BASE_LOAD_W,
                default=defaults.get(
                    CONF_BASE_LOAD_W,
                    DEFAULT_BASE_LOAD_W,
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=0)),
            vol.Optional(
                CONF_FLEXIBLE_LOAD_AVAILABLE_W,
                default=defaults.get(
                    CONF_FLEXIBLE_LOAD_AVAILABLE_W,
                    DEFAULT_FLEXIBLE_LOAD_AVAILABLE_W,
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=0)),
            vol.Optional(
                CONF_MAX_STORAGE_CHARGE_POWER_W,
                default=defaults.get(
                    CONF_MAX_STORAGE_CHARGE_POWER_W,
                    DEFAULT_MAX_STORAGE_CHARGE_POWER_W,
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=0)),
            vol.Optional(
                CONF_CLIPPING_SAFETY_RESERVE_W,
                default=defaults.get(
                    CONF_CLIPPING_SAFETY_RESERVE_W,
                    DEFAULT_CLIPPING_SAFETY_RESERVE_W,
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=0)),
        }
    )


DATA_SCHEMA = _data_schema()


def host_valid(host: str) -> bool:
    """Return True if hostname or IP address is valid."""
    if not host or not isinstance(host, str):
        return False

    host = host.strip()

    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass

    disallowed = re.compile(r"[^a-zA-Z\d-]")
    labels = host.split(".")

    return all(
        label
        and len(label) <= 63
        and not label.startswith("-")
        and not label.endswith("-")
        and not disallowed.search(label)
        for label in labels
    )


def _normalize_user_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Normalize user-provided config values."""
    normalized = dict(user_input)

    if CONF_HOST in normalized and isinstance(normalized[CONF_HOST], str):
        normalized[CONF_HOST] = normalized[CONF_HOST].strip()

    if CONF_NAME in normalized and isinstance(normalized[CONF_NAME], str):
        normalized[CONF_NAME] = normalized[CONF_NAME].strip() or DEFAULT_NAME

    float_defaults = {
        CONF_BATTERY_NOMINAL_CAPACITY_KWH: DEFAULT_BATTERY_NOMINAL_CAPACITY_KWH,
        CONF_PV_NOMINAL_POWER_KW: DEFAULT_PV_NOMINAL_POWER_KW,
        CONF_INVERTER_NOMINAL_POWER_KW: DEFAULT_INVERTER_NOMINAL_POWER_KW,
        CONF_PV_FEED_IN_LIMIT_PERCENT: DEFAULT_PV_FEED_IN_LIMIT_PERCENT,
        CONF_BASE_LOAD_W: DEFAULT_BASE_LOAD_W,
        CONF_FLEXIBLE_LOAD_AVAILABLE_W: DEFAULT_FLEXIBLE_LOAD_AVAILABLE_W,
        CONF_MAX_STORAGE_CHARGE_POWER_W: DEFAULT_MAX_STORAGE_CHARGE_POWER_W,
        CONF_CLIPPING_SAFETY_RESERVE_W: DEFAULT_CLIPPING_SAFETY_RESERVE_W,
    }

    for key, default in float_defaults.items():
        if key not in normalized or normalized[key] in (None, ""):
            normalized[key] = float(default)
        else:
            normalized[key] = float(normalized[key])

    return normalized


class AmpereModbusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Ampere Storage Pro Modbus config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input = _normalize_user_input(user_input)

            if not host_valid(user_input[CONF_HOST]):
                errors[CONF_HOST] = "invalid_host"
            else:
                unique_id = (
                    f"{user_input[CONF_HOST]}:"
                    f"{user_input[CONF_PORT]}:"
                    f"{user_input.get(CONF_UNIT, DEFAULT_UNIT)}"
                )

                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow handler for this config entry."""
        return AmpereModbusOptionsFlowHandler(config_entry)


class AmpereModbusOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Ampere Modbus options changes."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow.

        Do not assign to self.config_entry.
        In current Home Assistant versions OptionsFlow already exposes
        config_entry as a read-only property.
        """
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage integration options."""
        errors: dict[str, str] = {}

        current_values = {
            **self._config_entry.data,
            **self._config_entry.options,
        }

        if user_input is not None:
            user_input = _normalize_user_input(user_input)

            if not host_valid(user_input[CONF_HOST]):
                errors[CONF_HOST] = "invalid_host"
            else:
                new_data = dict(self._config_entry.data)
                new_data.update(user_input)

                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    title=user_input[CONF_NAME],
                    data=new_data,
                    options={},
                )

                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=_data_schema(current_values),
            errors=errors,
        )
