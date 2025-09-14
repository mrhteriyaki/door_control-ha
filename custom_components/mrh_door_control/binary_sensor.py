import logging
import voluptuous as vol


from datetime import timedelta
from homeassistant import config_entries
from .coordinator import DoorCoordinator
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "mrh_door_control"
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    name = config_entry.data["name"]
    url = config_entry.data["url"]
    door_pin = config_entry.data["door_input_pin"]
    async_add_entities([MrhDoorControlSensor(coordinator,name,url,door_pin)])

class MrhDoorControlSensor(CoordinatorEntity,BinarySensorEntity):
    
    def __init__(self, coordinator, name, url, door_pin):
        super().__init__(coordinator)
        self._name = name
        self._url = url
        self._uid = url.replace("http://", "").replace("https://","").replace(".", "_") + "_" + str(door_pin)
        self._door_pin = door_pin
        #self._door_state = None

    @property
    def name(self):
        return self._name
        
    @property
    def device_class(self):
        return "door"
        
    @property
    def unique_id(self):
        return self._uid 
        
    @property
    def is_on(self) -> bool:
        if self.coordinator.data == None:
            return None
        door_state_value = self.coordinator.data.get(("DIN" + str(self._door_pin)))
        if door_state_value == 1:
            return True
        elif door_state_value == 0:
            return False
        _LOGGER.warning("Could not get door state value from pin " + str(self._door_pin) + " from: " + self._url)
        return None
                
    @property
    def device_info(self):
        return {
        "identifiers": {(DOMAIN, self._url)},
        "name": self._name + " - Sensor",
        }          
        

        