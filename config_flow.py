from homeassistant import config_entries
import voluptuous as vol

from .const import DOMAIN

class KonkeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="Konke Gateway",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required("host"): str,
                vol.Required("port", default=5000): int,
                vol.Required("username", default="admin"): str,
                vol.Required("password", default="admin"): str,
                vol.Required("zkid"): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)
