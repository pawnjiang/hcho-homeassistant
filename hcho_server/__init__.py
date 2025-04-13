import logging
import aiohttp
from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
from .const import DOMAIN, DEVICE_NAME, MANUFACTURER, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """设置组件入口"""
    port = entry.data.get("port", DEFAULT_PORT)
    
    # 创建设备注册
    device_registry = dr.async_get(hass)
    device_id = "env_monitor_001"
    
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, device_id)},
        name=DEVICE_NAME,
        manufacturer=MANUFACTURER,
    )

    # 存储共享数据
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "device_id": device_id,
        "hass": hass,
        "port": port
    }

    # 设置Web服务器
    app = web.Application()
    
    
    async def handle_post(request):
        """处理POST请求"""
        try:
            data = await request.json()
            _LOGGER.debug(f"Received data: {data}")
        
            # 验证数据
            required_params = ["hcho", "humidity", "temperature"]
            if not all(k in data for k in required_params):
                return web.json_response(
                    {"error": "Missing required parameters"},
                    status=400,
                )
        
            # 更新所有传感器的数据
            for entry_id, entry_data in hass.data[DOMAIN].items():
                if "sensors" in entry_data:
                    for sensor in entry_data["sensors"]:
                        param = None
                        if sensor._param_type == "hcho":
                            param = "hcho"
                        elif sensor._param_type == "humidity":
                            param = "humidity"
                        elif sensor._param_type == "temperature":
                            param = "temperature"
                    
                        if param and param in data:
                            sensor.update_data(data[param])
        
            return web.json_response({"status": "success"})
    
        except Exception as e:
            _LOGGER.error(f"Request failed: {e}", exc_info=True)
            return web.json_response(
                {"error": "Internal server error"},
                status=500,
            )

    app.add_routes([web.post("/", handle_post)])
    
    # 启动服务器
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    _LOGGER.info(f"HCHO服务器已在端口 {port} 启动")

    # 更新为新的平台加载方式
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    # 存储runner用于卸载
    hass.data[DOMAIN][entry.entry_id]["runner"] = runner

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载组件"""
    if DOMAIN not in hass.data:
        return True

    # 停止Web服务器
    runner = hass.data[DOMAIN][entry.entry_id].get("runner")
    if runner:
        await runner.cleanup()
        _LOGGER.info("HCHO服务器已停止")

    # 卸载传感器平台
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    
    hass.data[DOMAIN].pop(entry.entry_id)
    return True