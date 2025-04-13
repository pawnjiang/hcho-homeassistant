import logging
from datetime import datetime
from homeassistant.helpers.entity import Entity
from .const import DOMAIN, DEVICE_NAME, MANUFACTURER

_LOGGER = logging.getLogger(__name__)
MIN_UPDATE_INTERVAL = 60  # 至少60秒更新一次

class MultiParameterSensor(Entity):
    """多参数传感器实体"""
    
    def __init__(self, hass, device_id, param_type):
        self._hass = hass
        self._param_type = param_type
        self._device_id = device_id
        self._state = None
        self._attributes = {"last_update": None}
        
        # 参数配置
        self._config = {
            "hcho": {
                "name": "甲醛浓度",
                "unit": "mg/m³",
                "icon": "mdi:chemical-weapon"
            },
            "humidity": {
                "name": "湿度",
                "unit": "%",
                "icon": "mdi:water-percent"
            },
            "temperature": {
                "name": "温度",
                "unit": "°C",
                "icon": "mdi:thermometer"
            }
        }
        
        self._attr_unique_id = f"{DEVICE_NAME} {self._config[param_type]['name']}"
        self._attr_name = f"{DEVICE_NAME} {self._config[param_type]['name']}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": DEVICE_NAME,
            "manufacturer": MANUFACTURER
        }
        self._attr_native_unit_of_measurement = self._config[param_type]["unit"]
        self._attr_icon = self._config[param_type]["icon"]

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    def update_data(self, value):
        """更新传感器数据"""
        try:
            self._state = round(float(value), 2)
            self._attributes["last_update"] = datetime.now().isoformat()
      
            # 强制触发状态更新（即使值变化很小）
            self.async_write_ha_state()
        
            # 记录历史（可选）
            self.hass.states.async_set(
                self.entity_id,
                self._state,
                self._attributes,
                force_update=True,  # 强制记录，即使值变化很小
            )
        except Exception as e:
            _LOGGER.error(f"更新传感器数据出错: {e}")

async def async_setup_entry(hass, config_entry, async_add_entities):
    """设置传感器平台"""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    
    sensors = [
        MultiParameterSensor(hass, entry_data["device_id"], "hcho"),
        MultiParameterSensor(hass, entry_data["device_id"], "humidity"),
        MultiParameterSensor(hass, entry_data["device_id"], "temperature")
    ]
    
    # 存储传感器引用以便更新
    entry_data["sensors"] = sensors
    async_add_entities(sensors, True)