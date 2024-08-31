# Generated by Django 5.0.2 on 2024-07-16 21:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0114_alter_multitenantuser_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('America/Guyana', 'America/Guyana'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('Poland', 'Poland'), ('America/Manaus', 'America/Manaus'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('Europe/Berlin', 'Europe/Berlin'), ('Etc/GMT-5', 'Etc/GMT-5'), ('America/Noronha', 'America/Noronha'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('America/Asuncion', 'America/Asuncion'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('Asia/Rangoon', 'Asia/Rangoon'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('Etc/GMT-0', 'Etc/GMT-0'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Asia/Amman', 'Asia/Amman'), ('Asia/Anadyr', 'Asia/Anadyr'), ('America/St_Vincent', 'America/St_Vincent'), ('Australia/Hobart', 'Australia/Hobart'), ('Europe/Podgorica', 'Europe/Podgorica'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('America/Atka', 'America/Atka'), ('America/Panama', 'America/Panama'), ('GMT0', 'GMT0'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('Pacific/Johnston', 'Pacific/Johnston'), ('America/Yellowknife', 'America/Yellowknife'), ('America/Tijuana', 'America/Tijuana'), ('Pacific/Chatham', 'Pacific/Chatham'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Africa/Banjul', 'Africa/Banjul'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('America/Antigua', 'America/Antigua'), ('Indian/Cocos', 'Indian/Cocos'), ('Africa/Luanda', 'Africa/Luanda'), ('America/Los_Angeles', 'America/Los_Angeles'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Europe/Kiev', 'Europe/Kiev'), ('Africa/Lusaka', 'Africa/Lusaka'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('Europe/Vienna', 'Europe/Vienna'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('Pacific/Auckland', 'Pacific/Auckland'), ('Iran', 'Iran'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('America/Scoresbysund', 'America/Scoresbysund'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('Etc/GMT+8', 'Etc/GMT+8'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('UCT', 'UCT'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Asia/Pontianak', 'Asia/Pontianak'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('Africa/Tunis', 'Africa/Tunis'), ('Australia/Victoria', 'Australia/Victoria'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Africa/Conakry', 'Africa/Conakry'), ('America/Godthab', 'America/Godthab'), ('Asia/Harbin', 'Asia/Harbin'), ('Africa/Lagos', 'Africa/Lagos'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Pacific/Apia', 'Pacific/Apia'), ('America/Montevideo', 'America/Montevideo'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Israel', 'Israel'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('Antarctica/Troll', 'Antarctica/Troll'), ('MET', 'MET'), ('Africa/Harare', 'Africa/Harare'), ('Asia/Gaza', 'Asia/Gaza'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('CET', 'CET'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Pacific/Majuro', 'Pacific/Majuro'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Asia/Chita', 'Asia/Chita'), ('Africa/Gaborone', 'Africa/Gaborone'), ('ROK', 'ROK'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('US/Samoa', 'US/Samoa'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Kwajalein', 'Kwajalein'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Etc/GMT+11', 'Etc/GMT+11'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('America/Martinique', 'America/Martinique'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('Africa/Asmera', 'Africa/Asmera'), ('America/Rosario', 'America/Rosario'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('Africa/Asmara', 'Africa/Asmara'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Asia/Thimphu', 'Asia/Thimphu'), ('America/Kralendijk', 'America/Kralendijk'), ('America/Phoenix', 'America/Phoenix'), ('America/Winnipeg', 'America/Winnipeg'), ('Etc/GMT-11', 'Etc/GMT-11'), ('Pacific/Easter', 'Pacific/Easter'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('America/Boa_Vista', 'America/Boa_Vista'), ('Africa/Kigali', 'Africa/Kigali'), ('Canada/Pacific', 'Canada/Pacific'), ('America/Jujuy', 'America/Jujuy'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('America/Pangnirtung', 'America/Pangnirtung'), ('Asia/Makassar', 'Asia/Makassar'), ('America/Anchorage', 'America/Anchorage'), ('Europe/Simferopol', 'Europe/Simferopol'), ('Africa/Douala', 'Africa/Douala'), ('America/Menominee', 'America/Menominee'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('America/Matamoros', 'America/Matamoros'), ('America/Eirunepe', 'America/Eirunepe'), ('Europe/Belgrade', 'Europe/Belgrade'), ('US/Hawaii', 'US/Hawaii'), ('Australia/Canberra', 'Australia/Canberra'), ('Etc/GMT-12', 'Etc/GMT-12'), ('Pacific/Niue', 'Pacific/Niue'), ('Europe/Minsk', 'Europe/Minsk'), ('America/Paramaribo', 'America/Paramaribo'), ('Asia/Kashgar', 'Asia/Kashgar'), ('America/Fortaleza', 'America/Fortaleza'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Europe/Bucharest', 'Europe/Bucharest'), ('Asia/Taipei', 'Asia/Taipei'), ('Asia/Dubai', 'Asia/Dubai'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Indian/Christmas', 'Indian/Christmas'), ('US/Mountain', 'US/Mountain'), ('Asia/Bangkok', 'Asia/Bangkok'), ('America/Mexico_City', 'America/Mexico_City'), ('Canada/Eastern', 'Canada/Eastern'), ('Asia/Muscat', 'Asia/Muscat'), ('America/Indianapolis', 'America/Indianapolis'), ('Europe/Jersey', 'Europe/Jersey'), ('Asia/Thimbu', 'Asia/Thimbu'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('America/Shiprock', 'America/Shiprock'), ('Etc/GMT+2', 'Etc/GMT+2'), ('America/Cayenne', 'America/Cayenne'), ('America/Araguaina', 'America/Araguaina'), ('Asia/Famagusta', 'Asia/Famagusta'), ('Europe/Oslo', 'Europe/Oslo'), ('Etc/GMT+9', 'Etc/GMT+9'), ('America/Thule', 'America/Thule'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Africa/Bangui', 'Africa/Bangui'), ('Asia/Baku', 'Asia/Baku'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('NZ-CHAT', 'NZ-CHAT'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('Etc/GMT+4', 'Etc/GMT+4'), ('America/Sitka', 'America/Sitka'), ('Africa/Tripoli', 'Africa/Tripoli'), ('Asia/Istanbul', 'Asia/Istanbul'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Asia/Yangon', 'Asia/Yangon'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('Europe/Dublin', 'Europe/Dublin'), ('Asia/Tokyo', 'Asia/Tokyo'), ('America/Goose_Bay', 'America/Goose_Bay'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('Pacific/Gambier', 'Pacific/Gambier'), ('America/La_Paz', 'America/La_Paz'), ('Asia/Samarkand', 'Asia/Samarkand'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Asia/Almaty', 'Asia/Almaty'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Asia/Jakarta', 'Asia/Jakarta'), ('Australia/Sydney', 'Australia/Sydney'), ('Etc/GMT-4', 'Etc/GMT-4'), ('Portugal', 'Portugal'), ('MST7MDT', 'MST7MDT'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Australia/Perth', 'Australia/Perth'), ('Africa/Mbabane', 'Africa/Mbabane'), ('America/Ojinaga', 'America/Ojinaga'), ('America/Guayaquil', 'America/Guayaquil'), ('US/East-Indiana', 'US/East-Indiana'), ('America/El_Salvador', 'America/El_Salvador'), ('GMT+0', 'GMT+0'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('Asia/Aden', 'Asia/Aden'), ('Asia/Macao', 'Asia/Macao'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Etc/GMT-1', 'Etc/GMT-1'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('Etc/Greenwich', 'Etc/Greenwich'), ('Europe/Chisinau', 'Europe/Chisinau'), ('Etc/Universal', 'Etc/Universal'), ('W-SU', 'W-SU'), ('Europe/Lisbon', 'Europe/Lisbon'), ('UTC', 'UTC'), ('Asia/Vientiane', 'Asia/Vientiane'), ('Africa/Monrovia', 'Africa/Monrovia'), ('Etc/GMT+0', 'Etc/GMT+0'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('Asia/Beirut', 'Asia/Beirut'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('America/Juneau', 'America/Juneau'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('Iceland', 'Iceland'), ('America/St_Lucia', 'America/St_Lucia'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('Asia/Dacca', 'Asia/Dacca'), ('WET', 'WET'), ('Etc/GMT-6', 'Etc/GMT-6'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('GMT', 'GMT'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('Europe/Brussels', 'Europe/Brussels'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Australia/ACT', 'Australia/ACT'), ('Europe/Moscow', 'Europe/Moscow'), ('Europe/Malta', 'Europe/Malta'), ('Etc/UCT', 'Etc/UCT'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('Asia/Colombo', 'Asia/Colombo'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('Etc/GMT', 'Etc/GMT'), ('Asia/Seoul', 'Asia/Seoul'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('America/Toronto', 'America/Toronto'), ('Etc/GMT-9', 'Etc/GMT-9'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('EST5EDT', 'EST5EDT'), ('Etc/GMT-8', 'Etc/GMT-8'), ('America/Montreal', 'America/Montreal'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('America/Glace_Bay', 'America/Glace_Bay'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Pacific/Ponape', 'Pacific/Ponape'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('Australia/Melbourne', 'Australia/Melbourne'), ('America/Iqaluit', 'America/Iqaluit'), ('Asia/Kuching', 'Asia/Kuching'), ('Etc/GMT+7', 'Etc/GMT+7'), ('Cuba', 'Cuba'), ('Europe/Athens', 'Europe/Athens'), ('ROC', 'ROC'), ('Zulu', 'Zulu'), ('Navajo', 'Navajo'), ('America/Barbados', 'America/Barbados'), ('Etc/GMT+6', 'Etc/GMT+6'), ('Africa/Libreville', 'Africa/Libreville'), ('EST', 'EST'), ('America/Guatemala', 'America/Guatemala'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('Mexico/General', 'Mexico/General'), ('Canada/Central', 'Canada/Central'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Europe/Volgograd', 'Europe/Volgograd'), ('America/Chihuahua', 'America/Chihuahua'), ('America/Nome', 'America/Nome'), ('Australia/Currie', 'Australia/Currie'), ('US/Central', 'US/Central'), ('America/Anguilla', 'America/Anguilla'), ('Europe/Andorra', 'Europe/Andorra'), ('Pacific/Guam', 'Pacific/Guam'), ('America/Denver', 'America/Denver'), ('GMT-0', 'GMT-0'), ('America/Catamarca', 'America/Catamarca'), ('Europe/Busingen', 'Europe/Busingen'), ('Pacific/Yap', 'Pacific/Yap'), ('America/Louisville', 'America/Louisville'), ('Europe/Helsinki', 'Europe/Helsinki'), ('America/Adak', 'America/Adak'), ('Asia/Brunei', 'Asia/Brunei'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('Brazil/West', 'Brazil/West'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('Africa/Nairobi', 'Africa/Nairobi'), ('Australia/Queensland', 'Australia/Queensland'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Etc/GMT+5', 'Etc/GMT+5'), ('Asia/Urumqi', 'Asia/Urumqi'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('Indian/Comoro', 'Indian/Comoro'), ('Pacific/Wake', 'Pacific/Wake'), ('America/Mazatlan', 'America/Mazatlan'), ('America/Miquelon', 'America/Miquelon'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Europe/Paris', 'Europe/Paris'), ('Africa/Dakar', 'Africa/Dakar'), ('America/Caracas', 'America/Caracas'), ('America/Knox_IN', 'America/Knox_IN'), ('Europe/San_Marino', 'Europe/San_Marino'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Europe/Saratov', 'Europe/Saratov'), ('Australia/NSW', 'Australia/NSW'), ('Europe/Kyiv', 'Europe/Kyiv'), ('Asia/Singapore', 'Asia/Singapore'), ('Etc/GMT-7', 'Etc/GMT-7'), ('America/Creston', 'America/Creston'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('Europe/Vatican', 'Europe/Vatican'), ('Europe/Riga', 'Europe/Riga'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Atlantic/Canary', 'Atlantic/Canary'), ('America/New_York', 'America/New_York'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('Brazil/Acre', 'Brazil/Acre'), ('America/Aruba', 'America/Aruba'), ('America/Recife', 'America/Recife'), ('Asia/Oral', 'Asia/Oral'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('Africa/Casablanca', 'Africa/Casablanca'), ('Asia/Dhaka', 'Asia/Dhaka'), ('America/Lower_Princes', 'America/Lower_Princes'), ('America/Cordoba', 'America/Cordoba'), ('Europe/Rome', 'Europe/Rome'), ('America/Porto_Velho', 'America/Porto_Velho'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('Australia/Tasmania', 'Australia/Tasmania'), ('America/Nuuk', 'America/Nuuk'), ('Africa/Kampala', 'Africa/Kampala'), ('America/Marigot', 'America/Marigot'), ('Brazil/East', 'Brazil/East'), ('America/Resolute', 'America/Resolute'), ('Canada/Atlantic', 'Canada/Atlantic'), ('America/Tortola', 'America/Tortola'), ('Indian/Chagos', 'Indian/Chagos'), ('America/Atikokan', 'America/Atikokan'), ('America/Merida', 'America/Merida'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('Europe/Samara', 'Europe/Samara'), ('US/Pacific', 'US/Pacific'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('GB-Eire', 'GB-Eire'), ('America/Santarem', 'America/Santarem'), ('Indian/Mahe', 'Indian/Mahe'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('America/Regina', 'America/Regina'), ('Asia/Magadan', 'Asia/Magadan'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('Asia/Omsk', 'Asia/Omsk'), ('HST', 'HST'), ('Etc/UTC', 'Etc/UTC'), ('Canada/Mountain', 'Canada/Mountain'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('Asia/Manila', 'Asia/Manila'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('America/Cancun', 'America/Cancun'), ('Indian/Mayotte', 'Indian/Mayotte'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('Africa/Niamey', 'Africa/Niamey'), ('Indian/Reunion', 'Indian/Reunion'), ('Jamaica', 'Jamaica'), ('Australia/Eucla', 'Australia/Eucla'), ('America/Virgin', 'America/Virgin'), ('Pacific/Midway', 'Pacific/Midway'), ('America/Chicago', 'America/Chicago'), ('Europe/Monaco', 'Europe/Monaco'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('Pacific/Palau', 'Pacific/Palau'), ('Asia/Kabul', 'Asia/Kabul'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('Asia/Baghdad', 'Asia/Baghdad'), ('Europe/Zagreb', 'Europe/Zagreb'), ('Asia/Macau', 'Asia/Macau'), ('Europe/Warsaw', 'Europe/Warsaw'), ('America/Costa_Rica', 'America/Costa_Rica'), ('America/Detroit', 'America/Detroit'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Africa/Bamako', 'Africa/Bamako'), ('GB', 'GB'), ('America/Metlakatla', 'America/Metlakatla'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Africa/Freetown', 'Africa/Freetown'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('America/Santiago', 'America/Santiago'), ('America/Yakutat', 'America/Yakutat'), ('America/Inuvik', 'America/Inuvik'), ('America/Dominica', 'America/Dominica'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('America/Hermosillo', 'America/Hermosillo'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('America/Porto_Acre', 'America/Porto_Acre'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('Pacific/Efate', 'Pacific/Efate'), ('America/Halifax', 'America/Halifax'), ('Europe/Vaduz', 'Europe/Vaduz'), ('Europe/Sofia', 'Europe/Sofia'), ('Africa/Algiers', 'Africa/Algiers'), ('America/Belem', 'America/Belem'), ('US/Eastern', 'US/Eastern'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('America/St_Johns', 'America/St_Johns'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('Etc/GMT-13', 'Etc/GMT-13'), ('America/Curacao', 'America/Curacao'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('PRC', 'PRC'), ('America/Managua', 'America/Managua'), ('Factory', 'Factory'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('MST', 'MST'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('America/Maceio', 'America/Maceio'), ('America/Vancouver', 'America/Vancouver'), ('Asia/Kuwait', 'Asia/Kuwait'), ('America/Rainy_River', 'America/Rainy_River'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('Africa/Bissau', 'Africa/Bissau'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('CST6CDT', 'CST6CDT'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Asia/Riyadh', 'Asia/Riyadh'), ('PST8PDT', 'PST8PDT'), ('Asia/Hebron', 'Asia/Hebron'), ('US/Arizona', 'US/Arizona'), ('Asia/Jayapura', 'Asia/Jayapura'), ('Europe/Budapest', 'Europe/Budapest'), ('Europe/London', 'Europe/London'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('America/Dawson', 'America/Dawson'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('Antarctica/Casey', 'Antarctica/Casey'), ('Hongkong', 'Hongkong'), ('America/Cayman', 'America/Cayman'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('Etc/GMT-2', 'Etc/GMT-2'), ('America/Havana', 'America/Havana'), ('Etc/Zulu', 'Etc/Zulu'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Etc/GMT+3', 'Etc/GMT+3'), ('Egypt', 'Egypt'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Asia/Katmandu', 'Asia/Katmandu'), ('US/Aleutian', 'US/Aleutian'), ('Africa/Malabo', 'Africa/Malabo'), ('Asia/Karachi', 'Asia/Karachi'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('America/Swift_Current', 'America/Swift_Current'), ('Australia/North', 'Australia/North'), ('Chile/Continental', 'Chile/Continental'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('America/Monterrey', 'America/Monterrey'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('America/Boise', 'America/Boise'), ('Europe/Kirov', 'Europe/Kirov'), ('Etc/GMT-14', 'Etc/GMT-14'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Africa/Maseru', 'Africa/Maseru'), ('America/Jamaica', 'America/Jamaica'), ('Universal', 'Universal'), ('Africa/Lome', 'Africa/Lome'), ('America/Lima', 'America/Lima'), ('Japan', 'Japan'), ('Etc/GMT+10', 'Etc/GMT+10'), ('Africa/Maputo', 'Africa/Maputo'), ('US/Michigan', 'US/Michigan'), ('Asia/Qatar', 'Asia/Qatar'), ('America/Moncton', 'America/Moncton'), ('America/Cuiaba', 'America/Cuiaba'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('Africa/Abidjan', 'Africa/Abidjan'), ('Europe/Madrid', 'Europe/Madrid'), ('Australia/Adelaide', 'Australia/Adelaide'), ('EET', 'EET'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Asia/Damascus', 'Asia/Damascus'), ('America/Guadeloupe', 'America/Guadeloupe'), ('Pacific/Truk', 'Pacific/Truk'), ('Africa/Juba', 'Africa/Juba'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('Europe/Tallinn', 'Europe/Tallinn'), ('Africa/Cairo', 'Africa/Cairo'), ('Asia/Tehran', 'Asia/Tehran'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('Etc/GMT-3', 'Etc/GMT-3'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Asia/Nicosia', 'Asia/Nicosia'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Australia/West', 'Australia/West'), ('Canada/Yukon', 'Canada/Yukon'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Asia/Barnaul', 'Asia/Barnaul'), ('Etc/GMT0', 'Etc/GMT0'), ('Pacific/Wallis', 'Pacific/Wallis'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('America/Bogota', 'America/Bogota'), ('America/Ensenada', 'America/Ensenada'), ('Asia/Atyrau', 'Asia/Atyrau'), ('Europe/Zurich', 'Europe/Zurich'), ('Eire', 'Eire'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Africa/Khartoum', 'Africa/Khartoum'), ('Asia/Kolkata', 'Asia/Kolkata'), ('Pacific/Noumea', 'Pacific/Noumea'), ('America/Montserrat', 'America/Montserrat'), ('America/Rio_Branco', 'America/Rio_Branco'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Australia/Darwin', 'Australia/Darwin'), ('Australia/South', 'Australia/South'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('America/Bahia', 'America/Bahia'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Europe/Prague', 'Europe/Prague'), ('Australia/LHI', 'Australia/LHI'), ('Europe/Belfast', 'Europe/Belfast'), ('Europe/Skopje', 'Europe/Skopje'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('Indian/Maldives', 'Indian/Maldives'), ('Greenwich', 'Greenwich'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('Etc/GMT-10', 'Etc/GMT-10'), ('America/Mendoza', 'America/Mendoza'), ('America/Belize', 'America/Belize'), ('America/Whitehorse', 'America/Whitehorse'), ('America/Nipigon', 'America/Nipigon'), ('America/Edmonton', 'America/Edmonton'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Asia/Saigon', 'Asia/Saigon'), ('Asia/Chungking', 'Asia/Chungking'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('America/Nassau', 'America/Nassau'), ('Europe/Nicosia', 'Europe/Nicosia'), ('Africa/Ceuta', 'Africa/Ceuta'), ('NZ', 'NZ'), ('Libya', 'Libya'), ('Africa/Accra', 'Africa/Accra'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Asia/Dili', 'Asia/Dili'), ('US/Alaska', 'US/Alaska'), ('Singapore', 'Singapore'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Etc/GMT+1', 'Etc/GMT+1'), ('Europe/Tirane', 'Europe/Tirane'), ('America/Campo_Grande', 'America/Campo_Grande'), ('build/etc/localtime', 'build/etc/localtime'), ('Asia/Hovd', 'Asia/Hovd'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Indian/Mauritius', 'Indian/Mauritius'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('Turkey', 'Turkey'), ('America/Grand_Turk', 'America/Grand_Turk'), ('America/St_Thomas', 'America/St_Thomas'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('America/Grenada', 'America/Grenada'), ('America/St_Kitts', 'America/St_Kitts'), ('Asia/Ust-Nera', 'Asia/Ust-Nera')], default='Europe/London', max_length=35),
        ),
    ]
