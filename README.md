# ovos-skill-my-foxess-cloud
OVOS skill to fetch data from FoxESS cloud from H3 inverter series users.
## Summary
This skill provides an announcement of current (real data) or historical aggregated data (report data) from a FoxESS photovoltaic system with a H3 series inverter. English and German intents and dialogs have been created for the skill. Other languages must be added yourself.
## Requirements
You must have an account on www.foxesscloud.com. This is usually set up by the installer. In your user profile, go to API Management and generate an API key. You'll also need the inverter's serial number. You can also obtain this from your installer or from the documentation provided. You must enter key and serial number in the skill setup file (see below). Python requirements are installed during installing this skill. Installing with ```pip install git+https://github.com/JoergZ2/ovos-skill-my-foxess-cloud```.
## Which intents are used (examples)
"What does the photovoltaic system deliver (just|current|)" - current power production from solar panels in kW  
"How much electricity is (currently|) (used|consumed|in the house|by us|)" - current consumption of all devices in kW  
"Current feed-in power" - current export to grid in kW  
"(What is the|) efficiency of the inverter" - calculates the lost of the system.
"Energy balance from yesterday" - aggregated values of the previous day.
"Energy balance from {date}" - aggregated of the day in question (within the last year).
There are more intents. You can find then in ```locale/en-us/intents``` folder.
## Known issues
During installing the neccessary libraries from a fresh version of numpy (2.2.5) ist installed. This produced a conflict message with ovos-classifiers. The maintainer of OVOS told me that doesn't matter.
## Setup
You have to edit settings.json of the skill. You will find it in your config folder in ```~/.config/mycroft/skills/ovos-skill-my-foxess-cloud.joergz2/settings.json``` It looks like:
```
{
    "__mycroft_skill_firstrun": false,
    "api_key": "12345678-9876-3541...",
    "device_sn": "60SH......",
    "time_zone": "Europe/Berlin",
    "lang_specifics": {
        "decimal_char": ","
    }
}
```
## Notes
"api_key": Your supplier or installer should give access data for foxesscloud.com. After you configured an account go to User profile and API Management. You can generate your own api key(s).  
"device_sn": ask your supplier or installer.  
"time_zone": self explaining, isn't it?  
"lang_specifics": In this skill only "decimal_char" is used. All digit values from FoxESS cloud are of type 'float'. For some countries - e. g. Germany - the decimal point is a comma (,). For correct speaking the point from float has to change to comma. If you don't need replacing, let "." as decimal point (default).  
## Sources and more information
https://github.com/TonyM1958/FoxESS-Cloud/  
https://github.com/macxq/foxess-ha/wiki/understand-PV-string-power-generation-using-foxess-ha/  
https://foxesscommunity.com/  
## Questions and issues
Use "Issues" from this github pages.
## Further explanations
A lot of data is collected in the FoxESS cloud. There are currently 109 parameters in total, which are reported to the cloud by the inverter every 5 minutes and stored there for at least 1 year. 

Fundamentally, the question arises as to how much information someone can actually absorb when it's spoken. Some queries that report on seven parameters are already too many for me.

As it depends on the respective configuration which of these parameters are used (and for reasons of possible combinations for queries), the skill only uses a selection of general and in most cases relevant parameters such as real-time data on the power of the PV system, electricity consumption in the house, grid consumption or grid feed-in and battery charging or discharging. This data can be called up as a whole or individually. This data is given in kilowatts (kW). Incidentally, "real-time" means the last data transmission within the last 5 minutes.

A second group of intents provides information on energy totals in kilowatt hours (kWh) in relation to a time period. The aggregated values from yesterday, the day before yesterday or any day within the past year (calculated from the date of the current day) can be called up.

Time periods can be grouped (last week, last month, last year). The script for communication with the FoxessCloud interprets week as a period of 7 days before the transmitted date and including the specified date. Example: The intent "Energy balance of the week from 07.02.2025" would deliver the data from 01.02.2025 00:00 to 07.02.2025 23:59.

The OVOS date_parser and the ovos_skill_date_time are very good but not perfect. In German, there are definitely major problems with formulations such as "gestern" (yesterday), "vorgestern" (day before yesterday) or (probably only possible in German language) "vorvorgestern" (= "two days before yesterday"). The skill or parser does not seem to be able to handle the past well. The skill solves this problem with the help of corresponding intents, in which the required trigger words are stored, and specified functions which perform the calculation of the date. I do not know in which languages there are comparable special words for (relative) time specifications.

The interpretation of specifically named days works reliably in this respect. In English an utterance as "March 2 20 25" is well recognized. However - especielly in German - these must be spoken in the long form: "Energiebilanz vom 2. März 2025". This is not possible: "Energiebilanz vom 2.3.2025 ('vom zweiten dritten 2025')" and other short forms of the date.

Feel free to make a fork, expand, and improve this repository.