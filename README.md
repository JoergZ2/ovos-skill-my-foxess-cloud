# <img src="https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/list.svg" card_color="#22A7F0" width="50" height="50" style="vertical-align:bottom"/>
# ovos-skill-my-foxess-cloud
OVOS skill to fetch data from FoxESS cloud.
## Summary
This skill currently only uses a small part of the information collected by the FoxESS cloud. At present, only current data is retrieved. Retrieving cumulative data from the past is planned but not yet implemented. English and German intents and dialogs have been created for the skill. Other languages must be added yourself.
## Which intents are used (examples)
"What does the photovoltaic system deliver (just|current|)" - current power production from solar panels in kW
"How much electricity is (currently|) (used|consumed|in the house|by us|)" - current consumption of all devices in kW
"Current feed-in power" - current export to grid in kW
"(What is the|) efficiency of the inverter" - calculates the lost of the system 

There are some more intents. You can find then in ```locale/en-us/intents``` folder.
## Known issues
During installing the neccessary libraries from a fresh version of numpy (2.2.5) ist installed. This produced a conflict message with ovos-classifiers. The maintainer of OVOS told me that doesn't matter.
## Setup
You have to edit settings.json of the skill. You will find it in your config folder in ```...skills/ovos-skill-my-foxess-cloud.joergz2/settings.json``` It looks like:
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
https://github.com/macxq/foxess-ha/wiki/Understand-PV-string-power-generation-using-foxess-ha/
https://foxesscommunity.com/
## Questions and issues
Use "Issues" from this github pages.
