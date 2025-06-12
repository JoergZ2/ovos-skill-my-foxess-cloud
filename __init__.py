from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.decorators import intent_handler
from ovos_workshop.skills import OVOSSkill
from ovos_bus_client.session import SessionManager
from ovos_date_parser import extract_datetime
import datetime as dt
from threading import Event
import foxesscloud.openapi as f
import json
#Just a comment
today = dt.date.today()
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
        self.pv = f.power_vars
        self.bv = f.battery_vars
        self.ev = f.energy_vars
        self.rv = f.report_vars
        self.lang_specifics = self.settings.get("lang_specifics", None)

    def on_settings_changed(self):
        """This method is called when the skill settings are changed."""
    
    #Main FoxESS functions
    def realdata(self,vars=None):
        """Returns all data since last datalogger sendings to cloud. This
        function is specified by intents. vars could be None, a single FoxESS
        var or a list of FoxESS vars."""
        if vars == None:
            result = f.get_real()
        else:
            result = f.get_real(vars)
        #result = json.loads(result)
        return result
    
    #Helpers
    def current_day(self, today):
        """
        Returns date of today as string.
        """
        day = today.strftime("%Y-%m-%d")
        return day

    def yesterday(self, today):
        """
        Returns date of yesterday as string.
        """
        day = today.replace(day=today.day-1)
        day = day.strftime("%Y-%m-%d")
        return day

    def round3_realdata(self,result):
        """Function rounds long float to 3 digits after decimal point"""
        if len(result) == 1:
            result = round(result[0]['value'], 3)
            return result
        i = 0
        while i < len(result):
            result[i]['value'] = round(result[i]['value'], 3)
            i += 1
        return result
    
    def round3_reportdata(self,result):
        """Function rounds long float to 3 digits after decimal point"""
        if len(result) == 1:
            result[0]['total'] = round(result[0]['total'], 3)
            return result
        i = 0
        while i < len(result):
            if len(result[i]['values']) > 0:
                result[i]['values'] = round(result[i]['values'], 3)
            if result[i]['total'] > 0:
                result[i]['total'] = round(result[i]['total'], 3)
            i += 1
        return result
           
    def prepare_values(self, selection,values):
        """Function for localization and to prepare a dict of values for TTS"""
        LOG.debug("Vars selection are: " +str(selection))
        LOG.debug("Vars values are: " + str(values))
        result = {}
        i = 0
        while i < len(selection):
            if values[i]['values']:
                new_value = values[i]['values']
                new_value = str(new_value).replace(".",self.lang_specifics['decimal_char'])
                values[i]['values'] = new_value
                result.update({selection[i]: str(values[i]['values'])})
                i += 1
            if values[i]['total']:
                LOG.info("Field total is processed")
                new_value = values[i]['total']
                new_value = str(new_value).replace(".",self.lang_specifics['decimal_char'])
                values[i]['total'] = new_value
                result.update({selection[i]: str(values[i]['total'])})
                i += 1
        return result

    def datareport(self,selection, day):
        result = f.get_report("day", day,selection,2)
        return result

    def calculate_reportdate(self,result):
        """Function which calcualtes quotes of self use and self consumption"""

    #Intents
    @intent_handler('energy_yesterday.intent')
    def handle_energy_yesterday(self, message):
        """Returns energy production, consumption and export/import from yesterday"""
        selection = self.rv
        day = self.yesterday(today)
        result = self.datareport(selection, day)
        values = self.round3_reportdata(result)
        values = self.prepare_values(selection, values)
        LOG.debug("Values from HANDLE_ENERGY_YESTERDAY intent: " + str(values))
        self.speak_dialog('energy_yesterday', {'chargeEnergyTotal': values['chargeEnergyToTal'], \
                                               'loads': values['loads'], 'gridConsumption': values['gridConsumption'], \
                                                'dischargeEnergyTotal': values['dischargeEnergyToTal'], 'generation': values['generation'], \
                                                    'feedin': values['feedin'], 'PVEnergyTotal': values['PVEnergyTotal']})

    @intent_handler('current_pvpower.intent')
    def handle_current_pvpower(self, message):
        """Returns photovoltaic output data"""
        selection = "pvPower"
        result = self.realdata(selection)
        value = str(result[0]['value']).replace(".",self.lang_specifics['decimal_char'])
        self.speak_dialog('current_pvpower',{'current_energy': value})
    
    @intent_handler('current_delivery.intent')
    def handle_current_delivery(self, message):
        """Returns power export data"""
        selection = "feedinPower"
        result = self.realdata(selection)
        value = self.round3_realdata(result)
        value = str(value).replace(".",self.lang_specifics['decimal_char'])
        self.speak_dialog('current_delivery', {'energy_delivery': value})

    @intent_handler('current_consumption.intent')
    def handle_current_consumption(self, message):
        """Returns current energy consumption data"""
        selection = "loadsPower"
        result = self.realdata(selection)
        value = self.round3_realdata(result)
        value = str(value).replace(".",self.lang_specifics['decimal_char'])
        self.speak_dialog('current_loads', {'current_loads': value})

    @intent_handler('current_bat_level.intent')
    def handle_current_bat_level(self, message):
        """Returns filling level of battery"""
        selection = "SoC"
        result = self.realdata(selection)
        value = str(result[0]['value']).replace(".",self.lang_specifics['decimal_char'])
        self.speak_dialog('current_bat_level', {'bat_level': value})

    @intent_handler('current_grid_consumption.intent')
    def handle_current_grid_consumption(self, message):
        """Returns current power import from grid"""
        selection = "gridConsumptionPower"
        result = self.realdata(selection)
        value = self.round3_realdata(result)
        value = str(value).replace(".",self.lang_specifics['decimal_char'])
        self.speak_dialog('current_grid_consumption', {'grid_consumption': value})
    
    @intent_handler('current_efficiency_of_inverter.intent')
    def handle_current_inverter_efficiency(self, message):
        """Returns production and generation date and calculates efficiency"""
        selection = ["pvPower", "generationPower", "batChargePower", "feedinPower"]
        result = self.realdata(selection)
        efficiency = round((result[1]['value']+result[2]['value']+result[3]['value'])/result[0]['value']*100, 0)
        values = self.round3_realdata(result)
        values = self.prepare_values(selection, values)
        self.speak_dialog('current_efficiency_of_inverter', {'efficiency': efficiency})

    @intent_handler('current_inv_bat_charge.intent')
    def handle_current_inv_bat_charge(self, message):
        """Returns current battery fill state"""
        selection = "batChargePower"
        result = self.realdata(selection)
        value = str(result[0]['value']).replace(".",self.lang_specifics['decimal_char'])
        self.speak_dialog('current_inv_bat_charge', {'batChargePower': value})


    @intent_handler('current_energy_balance.intent')
    def handle_current_energy_balance(self, message):
        """Returns current data of prduction, consumption, state of battery..."""
        selection = ['generationPower', 'feedinPower', 'loadsPower', 'gridConsumptionPower', 'batChargePower', 'batDischargePower', 'pvPower']
        result = self.realdata(selection)
        values = self.round3_realdata(result)
        values = self.prepare_values(selection, values)
        self.speak_dialog('current_energy_balance', {'pvPower': values['pvPower'], 'batChargePower': values['batChargePower'], \
                                                     'loadsPower': values['loadsPower'], 'gridConsumptionPower': values['gridConsumptionPower'], \
                                                        'batDischargePower': values['batDischargePower'], 'generationPower': values['generationPower'], \
                                                            'feedinPower': values['feedinPower']})
        
    @intent_handler('values_from_past.intent')
    def handle_past_values(self, message):
        """Returns sums of prodauction, loads and export/import from a single day in the past < one year"""
        selection = self.rv
        day = message.data.get('day')
        day = extract_datetime(day, lang="de")
        day = day[0].strftime("%Y-%m-%d")
        result = self.datareport(selection, day)
        values = self.round3_reportdata(result)
        values = self.prepare_values(selection, values)
        LOG.info("Values from HANDLE_PAST_VALUES intent: " + str(values))
        #self.speak_dialog('values_from_past', {"value": value})