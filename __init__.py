from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.decorators import intent_handler
from ovos_workshop.skills import OVOSSkill
from ovos_bus_client.session import SessionManager
from threading import Event
import foxesscloud.openapi as f
import json
#Just a comment
power_vars = f.power_vars
battery_vars = f.battery_vars
energy_vars = f.energy_vars
DEFAULT_SETTINGS = {
    "__mycroft_skill_firstrun": "False",
    "api_key": "Your_API_Key",
    "device_sn": "Your_inverter_serial_number",
    "time_zone": "Europe/Berlin",
    "lang_specifics": {
        "decimal_char": "."
    }
}

class FoxESSCloudSkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # be aware that below is executed after `initialize`
        self.override = True

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(
            internet_before_load=False,
            network_before_load=False,
            gui_before_load=False,
            requires_internet=False,
            requires_network=False,
            requires_gui=False,
            no_internet_fallback=True,
            no_network_fallback=True,
            no_gui_fallback=True,
        )
    
    def initialize(self):
        #from template
        self.settings.merge(DEFAULT_SETTINGS, new_only=True)
        self.settings_change_callback = self.on_settings_changed
        f.api_key = self.settings.get("api_key", None)
        f.device_sn = self.settings.get("device_sn", None)
        f.time_zone = self.settings.get("time_zone", None)
        self.lang_specifics = self.settings.get("lang_specifics", None)

    def on_settings_changed(self):
        """This method is called when the skill settings are changed."""
    
    #Main FoxESS functions
    def realdata(self,vars=None):
        """Fetches all data since last datalogger sendings to cloud. This
        function is specified by intents. vars could be None, a single FoxESS
        var or a list of FoxESS vars."""
        if vars == None:
            result = f.get_real()
        else:
            result = f.get_real(vars)
        #result = json.loads(result)
        return result
    #Helpers
    def round3_realdata(self,result):
        """Function rounds long float to 3 digits after decimal point"""
        result = round(result[0]['value'], 3)
        return result
    
    #Intents
    @intent_handler('current_pvpower.intent')
    def handle_current_pvpower(self, message):
        selection = "pvPower"
        result = self.realdata(selection)
        value = str(result[0]['value']).replace(".",self.lang_specifics['decimal_char'])
        LOG.info("Result ist: " + str(result[0]) + " value ist: " + str(value))
        self.speak_dialog('current_pvpower',{'current_energy': value})
    
    @intent_handler('current_delivery.intent')
    def handle_current_delivery(self, message):
        selection = "feedinPower"
        result = self.realdata(selection)
        value = self.round3_realdata(result)
        value = str(value).replace(".",self.lang_specifics['decimal_char'])
        self.speak_dialog('current_delivery', {'energy_delivery': value})

    @intent_handler('current_loads.intent')
    def handle_current_consumption(self, message):
        selection = "loadsPower"
        result = self.realdata(selection)
        value = self.round3_realdata(result)
        value = str(value).replace(".",self.lang_specifics['decimal_char'])
        self.speak_dialog('current_loads', {'current_loads': value})

    @intent_handler('current_bat_level.intent')
    def handle_current_bat_level(self, message):
        selection = "SoC"
        result = self.realdata(selection)
        LOG.info("Result ist: " + str(result))
        value = str(result[0]['value']).replace(".",self.lang_specifics['decimal_char'])
        self.speak_dialog('current_bat_level', {'bat_level': value})

    @intent_handler('current_grid_consumption.intent')
    def handle_current_grid_consumption(self, message):
        selection = "gridConsumptionPower"
        result = self.realdata(selection)
        LOG.info("Result ist: " + str(result))
        value = self.round3_realdata(result)
        value = str(value).replace(".",self.lang_specifics['decimal_char'])
        self.speak_dialog('current_grid_consumption', {'grid_consumption': value})
