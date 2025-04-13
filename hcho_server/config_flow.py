from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

from .const import DOMAIN, DEFAULT_PORT

class HCHOConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """处理配置流（UI 配置）"""

    async def async_step_user(self, user_input=None):
        """用户首次添加集成时调用"""
        if user_input is not None:
            # 检查是否已配置（避免重复）
            await self.async_set_unique_id("hcho_server_1")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="HCHO Server",
                data=user_input,
            )

        # 默认配置（端口可调整）
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional("port", default=DEFAULT_PORT): int,
                }
            ),
        )