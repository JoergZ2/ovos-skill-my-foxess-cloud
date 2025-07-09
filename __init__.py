from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.decorators import intent_handler
from ovos_workshop.skills import OVOSSkill
from ovos_bus_client.session import SessionManager
from ovos_date_parser import extract_datetime, nice_date
import datetime as dt
from threading import Event
import foxesscloud.openapi as f
import json
##Just a comment
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
            internet_before_load=True,
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
    
    def datareport(self,duration, selection, summary, day_str):
        result = f.get_report(duration, day_str,selection,summary)
        return result

    #Helpers
    ##Date helpers
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

    def day_before_yesterday(self, today):
        """
        Returns date of day before yesterday as string.
        """
        day = today.replace(day=today.day-2)
        day = day.strftime("%Y-%m-%d")
        return day

    def previous_week_last_day(self, today):
        """
        Returns date of last day (Sunday) of previous week as string.
        """
        day = today.weekday()
        day = dt.timedelta(days=day)
        day = today - day
        day = day.replace(day=day.day-1)
        day = day.strftime("%Y-%m-%d")
        return day

    def optional_day_from_past(self, today, number):
        """
        Returns date of a past day announcing an optional number of past days. Number \
        must be less than 365.
        """
        number = int(number)
        today_ordinal = today.timetuple().tm_yday
        current_year = today.year
        if number < today_ordinal:
            year = current_year
            number = today_ordinal - number
        if number >= today_ordinal:
            year = current_year - 1
            number = today_ordinal - number + 365
        day = dt.date.fromordinal(number)
        day = day.replace(year=year)
        day = day.strftime("%Y-%m-%d")
        return day
    
    ##Formatting helpers
    def round_and_prepare_realdata(self, result):
        """Function rounds long float to 3 digits after decimal point and prepares a dict of values for TTS"""
        new_result = {}
        if len(result) == 1:
            result = str(round(result[0]['value'], 3)).replace(".",self.lang_specifics['decimal_char'])
            return result
        i = 0
        while i < len(result):
            result[i]['value'] = round(result[i]['value'], 3)
            key = result[i]['variable']
            value = str(result[i]['value']).replace(".",self.lang_specifics['decimal_char'])
            new_result.update({key: value})
            i += 1
        return new_result
    
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
    
    def round_and_prepare_reportdata(self, duration, result):
        """Function rounds long float to 3 digits after decimal point and prepares a dict of values for TTS"""
        new_result = {}
        if duration == "week" or duration == "month" or duration == "year":
            for i in range(len(result)):
                key = result[i]['variable']
                rounded = round(result[i]['sum'], 3)
                result[i]['sum'] = str(rounded).replace(".",self.lang_specifics['decimal_char'])
                value = result[i]['sum']
                new_result.update({key: value})
            return new_result
        if duration == "day":
            for i in range(len(result)):
                key = result[i]['variable']
                rounded = round(result[i]['total'], 3)
                result[i]['total'] = str(rounded).replace(".",self.lang_specifics['decimal_char'])
                value = result[i]['total']
                new_result.update({key: value})
            return new_result

    def round3_reportdata(self, duration, result):
        """Function rounds long float to 3 digits after decimal point"""
        if len(result) == 1:
            result[0]['total'] = round(result[0]['total'], 3)
            return result
        i = 0
        while i < len(result):
            if len(result[i]['values']) > 0:
                for ii in result[i]['values']:
                    ii = round(ii, 3)
            if result[i]['total'] > 0:
                result[i]['total'] = round(result[i]['total'], 3)
            i += 1
        return result
           
    def prepare_values(self, selection,values):
        """Function for localization and to prepare a dict of values for TTS"""
        result = {}
        for i in range(len(selection)):
            if values[i]['values']:
                new_value = values[i]['values']
                new_value = str(new_value).replace(".",self.lang_specifics['decimal_char'])
                values[i]['values'] = new_value
                result.update({selection[i]: str(values[i]['values'])})
            if values[i]['total'] != None:
                new_value = values[i]['total']
                new_value = str(new_value).replace(".",self.lang_specifics['decimal_char'])
                values[i]['total'] = new_value
                result.update({values[i]['variable']: str(values[i]['total'])})
        return result

    def calculate_reportdate(self,result):
        """Todo: Function which calcualtes quotes of self use and self consumption"""

    
    #Intents
    @intent_handler('energy_yesterday.intent')
    def handle_energy_yesterday(self, message):
        """Returns energy production, consumption and export/import from yesterday"""
        selection = self.rv
        duration = "day"
        summary = 2
        day_str = self.yesterday(today)
        result = self.datareport(duration, selection, summary, day_str)
        values = self.round_and_prepare_reportdata(duration, result)
        LOG.debug("Values from HANDLE_ENERGY_YESTERDAY intent: " + str(values))
        self.speak_dialog('energy_yesterday', {'chargeEnergyToTal': values['chargeEnergyToTal'], \
                                               'loads': values['loads'], 'gridConsumption': values['gridConsumption'], \
                                                'dischargeEnergyToTal': values['dischargeEnergyToTal'], 'generation': values['generation'], \
                                                    'feedin': values['feedin'], 'PVEnergyTotal': values['PVEnergyTotal']})

    @intent_handler('energy_day_before_yesterday.intent')
    def handle_energy_day_before_yesterday(self, message):
        """Returns energy production, consumption and export/import from yesterday"""
        selection = self.rv
        duration = "day"
        summary = 2
        day_str = self.day_before_yesterday(today)
        result = self.datareport(duration, selection, summary, day_str)
        values = self.round_and_prepare_reportdata(duration, result)
        LOG.debug("Values from HANDLE_ENERGY_YESTERDAY intent: " + str(values))
        self.speak_dialog('energy_day_before_yesterday', {'chargeEnergyToTal': values['chargeEnergyToTal'], \
                                               'loads': values['loads'], 'gridConsumption': values['gridConsumption'], \
                                                'dischargeEnergyToTal': values['dischargeEnergyToTal'], 'generation': values['generation'], \
                                                    'feedin': values['feedin'], 'PVEnergyTotal': values['PVEnergyTotal']})

    @intent_handler('energy_optional_day.intent')
    def handle_energy_optional_day(self, message):
        """Returns energy production, consumption and export/import from a single day in the past <= 365 (days)"""
        selection = self.rv
        duration = "day"
        summary = 2
        number = int(message.data.get('number'))
        if number <= 365:
            day_str = self.optional_day_from_past(today, number)
            result = self.datareport(duration, selection, summary, day_str)
            values = self.round_and_prepare_reportdata(duration, result)
            LOG.debug("Values from HANDLE_ENERGY_OPTIONAL_DAY intent: " + str(values))
            self.speak_dialog('energy_optional_day', {'number': number, 'loads': values['loads'], 'gridConsumption': values['gridConsumption'], 'generation': values['generation'], \
                                                        'dischargeEnergyToTal': values['dischargeEnergyToTal'], 'chargeEnergyToTal': values['chargeEnergyToTal'], 'feedin': values['feedin']})
        else:
            LOG.info("Number of requested day must be equal or less than 365.")
            self.speak_dialog('energy_optional_day_error', {'today': today.day})    
        
    @intent_handler('energy_last_week.intent')
    def handle_energy_last_week(self, message):
        """Returns energy production, consumption and export/import from last week"""
        selection = self.rv
        duration = "week"
        summary = 2
        day_str = self.previous_week_last_day(today)
        result = self.datareport(duration, selection, summary, day_str)
        values = self.round_and_prepare_reportdata(duration, result)
        LOG.debug("Result from HANDLE_ENERGY_LAST_WEEK intent: " + str(values))
        self.speak_dialog('energy_last_week', {'loads': values['loads'], 'gridConsumption': values['gridConsumption'], 'generation': values['generation'], \
                                                'dischargeEnergyToTal': values['dischargeEnergyToTal'], 'chargeEnergyToTal': values['chargeEnergyToTal'], 'feedin': values['feedin']})

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
        value = self.round_and_prepare_realdata(result)
        self.speak_dialog('current_delivery', {'energy_delivery': value})

    @intent_handler('current_consumption.intent')
    def handle_current_consumption(self, message):
        """Returns current energy consumption data"""
        selection = "loadsPower"
        result = self.realdata(selection)
        value = self.round_and_prepare_realdata(result)
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
        value = self.round_and_prepare_realdata(result)
        self.speak_dialog('current_grid_consumption', {'grid_consumption': value})
    
    @intent_handler('current_efficiency_of_inverter.intent')
    def handle_current_inverter_efficiency(self, message):
        """Returns production and generation date and calculates efficiency"""
        selection = ["pvPower", "generationPower", "batChargePower", "feedinPower"]
        result = self.realdata(selection)
        efficiency = round((result[1]['value']+result[2]['value']+result[3]['value'])/result[0]['value']*100, 0)
        values = self.round_and_prepare_realdata(result)
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
        values = self.round_and_prepare_realdata(result)
        self.speak_dialog('current_energy_balance', {'pvPower': values['pvPower'], 'batChargePower': values['batChargePower'], \
                                                     'loadsPower': values['loadsPower'], 'gridConsumptionPower': values['gridConsumptionPower'], \
                                                        'batDischargePower': values['batDischargePower'], 'generationPower': values['generationPower'], \
                                                            'feedinPower': values['feedinPower']})
        
    @intent_handler('values_of_date.intent')
    def handle_past_values(self, message):
        """Returns sums of prodauction, loads and export/import from a single day in the past < one year"""
        selection = self.rv
        duration = "day"
        summary = 2
        day = message.data.get('day')
        day = extract_datetime(day, lang=self.lang)
        day = day[0].strftime("%Y-%m-%d")
        day_to_speak = dt.datetime.strptime(day, "%Y-%m-%d")
        day_to_speak = nice_date(day_to_speak, lang=self.lang)
        result = self.datareport(duration, selection, summary, day)
        values = self.round_and_prepare_reportdata(duration, result)
        LOG.debug("Values from HANDLE_PAST_VALUES intent: " + str(values))
        self.speak_dialog('values_of_date', {'day': day_to_speak,'gridConsumption': values['gridConsumption'], 'generation': values['generation'], \
                                                            'feedin': values['feedin'], 'loads': values['loads']})
