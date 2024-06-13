# Generated by Django 5.0.2 on 2024-06-13 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0098_alter_multitenantuser_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('Kwajalein', 'Kwajalein'), ('America/Resolute', 'America/Resolute'), ('Europe/Kirov', 'Europe/Kirov'), ('America/Whitehorse', 'America/Whitehorse'), ('Europe/London', 'Europe/London'), ('NZ', 'NZ'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Canada/Eastern', 'Canada/Eastern'), ('Australia/Canberra', 'Australia/Canberra'), ('America/Bogota', 'America/Bogota'), ('Etc/GMT-14', 'Etc/GMT-14'), ('Pacific/Yap', 'Pacific/Yap'), ('Africa/Asmara', 'Africa/Asmara'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('Etc/GMT+3', 'Etc/GMT+3'), ('Asia/Istanbul', 'Asia/Istanbul'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Libya', 'Libya'), ('Europe/Nicosia', 'Europe/Nicosia'), ('Atlantic/Canary', 'Atlantic/Canary'), ('America/Nome', 'America/Nome'), ('Etc/GMT', 'Etc/GMT'), ('America/New_York', 'America/New_York'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('America/Godthab', 'America/Godthab'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('America/Hermosillo', 'America/Hermosillo'), ('America/Matamoros', 'America/Matamoros'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('ROK', 'ROK'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('Africa/Accra', 'Africa/Accra'), ('Europe/Brussels', 'Europe/Brussels'), ('America/Tijuana', 'America/Tijuana'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('Etc/Greenwich', 'Etc/Greenwich'), ('Asia/Makassar', 'Asia/Makassar'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('EET', 'EET'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Asia/Chita', 'Asia/Chita'), ('Pacific/Efate', 'Pacific/Efate'), ('America/St_Kitts', 'America/St_Kitts'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('Africa/Khartoum', 'Africa/Khartoum'), ('Europe/Vatican', 'Europe/Vatican'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('Australia/NSW', 'Australia/NSW'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Asia/Macau', 'Asia/Macau'), ('US/Samoa', 'US/Samoa'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('Etc/GMT+2', 'Etc/GMT+2'), ('Pacific/Midway', 'Pacific/Midway'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Etc/GMT-0', 'Etc/GMT-0'), ('Indian/Mayotte', 'Indian/Mayotte'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('America/Thule', 'America/Thule'), ('America/Miquelon', 'America/Miquelon'), ('Europe/Sofia', 'Europe/Sofia'), ('Asia/Tehran', 'Asia/Tehran'), ('Asia/Riyadh', 'Asia/Riyadh'), ('CET', 'CET'), ('America/Manaus', 'America/Manaus'), ('Asia/Beirut', 'Asia/Beirut'), ('Asia/Almaty', 'Asia/Almaty'), ('America/Nassau', 'America/Nassau'), ('Etc/GMT-3', 'Etc/GMT-3'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('Africa/Casablanca', 'Africa/Casablanca'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Etc/GMT-11', 'Etc/GMT-11'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('Europe/Moscow', 'Europe/Moscow'), ('Pacific/Apia', 'Pacific/Apia'), ('America/Kralendijk', 'America/Kralendijk'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Asia/Brunei', 'Asia/Brunei'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('America/Yellowknife', 'America/Yellowknife'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Etc/GMT+8', 'Etc/GMT+8'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('America/Adak', 'America/Adak'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('Singapore', 'Singapore'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Asia/Dhaka', 'Asia/Dhaka'), ('America/Moncton', 'America/Moncton'), ('Israel', 'Israel'), ('America/Detroit', 'America/Detroit'), ('GMT+0', 'GMT+0'), ('America/Indianapolis', 'America/Indianapolis'), ('America/Catamarca', 'America/Catamarca'), ('Africa/Monrovia', 'Africa/Monrovia'), ('Europe/Volgograd', 'Europe/Volgograd'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Asia/Yangon', 'Asia/Yangon'), ('America/Caracas', 'America/Caracas'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('America/La_Paz', 'America/La_Paz'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Pacific/Palau', 'Pacific/Palau'), ('America/Rio_Branco', 'America/Rio_Branco'), ('Africa/Malabo', 'Africa/Malabo'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Asia/Baghdad', 'Asia/Baghdad'), ('Asia/Omsk', 'Asia/Omsk'), ('Europe/Jersey', 'Europe/Jersey'), ('Asia/Bishkek', 'Asia/Bishkek'), ('America/Rosario', 'America/Rosario'), ('Asia/Damascus', 'Asia/Damascus'), ('Asia/Amman', 'Asia/Amman'), ('America/Sitka', 'America/Sitka'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('America/Iqaluit', 'America/Iqaluit'), ('Etc/GMT0', 'Etc/GMT0'), ('America/Mazatlan', 'America/Mazatlan'), ('America/Denver', 'America/Denver'), ('America/Campo_Grande', 'America/Campo_Grande'), ('America/Toronto', 'America/Toronto'), ('Zulu', 'Zulu'), ('Canada/Atlantic', 'Canada/Atlantic'), ('America/Asuncion', 'America/Asuncion'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Universal', 'Universal'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('America/Cordoba', 'America/Cordoba'), ('America/Boa_Vista', 'America/Boa_Vista'), ('America/Mexico_City', 'America/Mexico_City'), ('Asia/Oral', 'Asia/Oral'), ('Africa/Bissau', 'Africa/Bissau'), ('America/Merida', 'America/Merida'), ('America/Shiprock', 'America/Shiprock'), ('America/Atka', 'America/Atka'), ('America/Havana', 'America/Havana'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('Indian/Mauritius', 'Indian/Mauritius'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('UTC', 'UTC'), ('Asia/Hebron', 'Asia/Hebron'), ('America/Rainy_River', 'America/Rainy_River'), ('America/Porto_Velho', 'America/Porto_Velho'), ('Asia/Jayapura', 'Asia/Jayapura'), ('HST', 'HST'), ('America/Mendoza', 'America/Mendoza'), ('Etc/GMT-2', 'Etc/GMT-2'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Asia/Magadan', 'Asia/Magadan'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Asia/Thimphu', 'Asia/Thimphu'), ('UCT', 'UCT'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('Mexico/General', 'Mexico/General'), ('EST', 'EST'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Europe/Belfast', 'Europe/Belfast'), ('Europe/Tirane', 'Europe/Tirane'), ('Asia/Thimbu', 'Asia/Thimbu'), ('Africa/Libreville', 'Africa/Libreville'), ('Europe/Athens', 'Europe/Athens'), ('America/Santiago', 'America/Santiago'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('America/Ensenada', 'America/Ensenada'), ('Etc/UCT', 'Etc/UCT'), ('Europe/Helsinki', 'Europe/Helsinki'), ('America/Louisville', 'America/Louisville'), ('Asia/Harbin', 'Asia/Harbin'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('Asia/Qatar', 'Asia/Qatar'), ('PRC', 'PRC'), ('ROC', 'ROC'), ('Etc/GMT+0', 'Etc/GMT+0'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('America/Monterrey', 'America/Monterrey'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('Etc/GMT-7', 'Etc/GMT-7'), ('America/Grenada', 'America/Grenada'), ('Asia/Barnaul', 'Asia/Barnaul'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('Etc/UTC', 'Etc/UTC'), ('Etc/Zulu', 'Etc/Zulu'), ('America/Martinique', 'America/Martinique'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('Africa/Maputo', 'Africa/Maputo'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('America/Swift_Current', 'America/Swift_Current'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('Africa/Juba', 'Africa/Juba'), ('America/Knox_IN', 'America/Knox_IN'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('Asia/Dili', 'Asia/Dili'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('Pacific/Wake', 'Pacific/Wake'), ('America/Porto_Acre', 'America/Porto_Acre'), ('Europe/Dublin', 'Europe/Dublin'), ('PST8PDT', 'PST8PDT'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('Japan', 'Japan'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('EST5EDT', 'EST5EDT'), ('Etc/GMT+11', 'Etc/GMT+11'), ('Europe/Malta', 'Europe/Malta'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('Asia/Bangkok', 'Asia/Bangkok'), ('America/Guyana', 'America/Guyana'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Africa/Harare', 'Africa/Harare'), ('Etc/GMT+5', 'Etc/GMT+5'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('America/Goose_Bay', 'America/Goose_Bay'), ('America/Nuuk', 'America/Nuuk'), ('America/Winnipeg', 'America/Winnipeg'), ('America/Atikokan', 'America/Atikokan'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('America/Belem', 'America/Belem'), ('America/Inuvik', 'America/Inuvik'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('Africa/Gaborone', 'Africa/Gaborone'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Australia/Darwin', 'Australia/Darwin'), ('Pacific/Auckland', 'Pacific/Auckland'), ('Jamaica', 'Jamaica'), ('America/Barbados', 'America/Barbados'), ('Etc/GMT-13', 'Etc/GMT-13'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('America/Edmonton', 'America/Edmonton'), ('Europe/Rome', 'Europe/Rome'), ('Europe/Saratov', 'Europe/Saratov'), ('America/Paramaribo', 'America/Paramaribo'), ('W-SU', 'W-SU'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Pacific/Chatham', 'Pacific/Chatham'), ('America/Montevideo', 'America/Montevideo'), ('Asia/Gaza', 'Asia/Gaza'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Europe/Warsaw', 'Europe/Warsaw'), ('Europe/Bucharest', 'Europe/Bucharest'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('Australia/Currie', 'Australia/Currie'), ('Brazil/West', 'Brazil/West'), ('Asia/Kashgar', 'Asia/Kashgar'), ('America/Boise', 'America/Boise'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('America/Cancun', 'America/Cancun'), ('Asia/Kuching', 'Asia/Kuching'), ('Europe/Andorra', 'Europe/Andorra'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('US/East-Indiana', 'US/East-Indiana'), ('Etc/Universal', 'Etc/Universal'), ('Africa/Mbabane', 'Africa/Mbabane'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Asia/Jakarta', 'Asia/Jakarta'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('America/Guadeloupe', 'America/Guadeloupe'), ('Europe/Zagreb', 'Europe/Zagreb'), ('Africa/Douala', 'Africa/Douala'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('Etc/GMT-9', 'Etc/GMT-9'), ('Etc/GMT-8', 'Etc/GMT-8'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('Etc/GMT-1', 'Etc/GMT-1'), ('Pacific/Majuro', 'Pacific/Majuro'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Asia/Baku', 'Asia/Baku'), ('America/Guatemala', 'America/Guatemala'), ('Asia/Taipei', 'Asia/Taipei'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('Etc/GMT+9', 'Etc/GMT+9'), ('America/Recife', 'America/Recife'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('America/Metlakatla', 'America/Metlakatla'), ('Asia/Famagusta', 'Asia/Famagusta'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('Asia/Macao', 'Asia/Macao'), ('Asia/Manila', 'Asia/Manila'), ('Asia/Seoul', 'Asia/Seoul'), ('Asia/Anadyr', 'Asia/Anadyr'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('Asia/Kuwait', 'Asia/Kuwait'), ('Australia/Eucla', 'Australia/Eucla'), ('Africa/Maseru', 'Africa/Maseru'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('Canada/Yukon', 'Canada/Yukon'), ('Europe/Busingen', 'Europe/Busingen'), ('Etc/GMT+7', 'Etc/GMT+7'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('Africa/Bangui', 'Africa/Bangui'), ('America/Vancouver', 'America/Vancouver'), ('America/Santarem', 'America/Santarem'), ('America/Los_Angeles', 'America/Los_Angeles'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Africa/Lome', 'Africa/Lome'), ('Australia/Perth', 'Australia/Perth'), ('America/Halifax', 'America/Halifax'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('Australia/Sydney', 'Australia/Sydney'), ('Indian/Comoro', 'Indian/Comoro'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('Asia/Chungking', 'Asia/Chungking'), ('US/Arizona', 'US/Arizona'), ('America/Tortola', 'America/Tortola'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Pacific/Truk', 'Pacific/Truk'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Pacific/Wallis', 'Pacific/Wallis'), ('US/Eastern', 'US/Eastern'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('Africa/Abidjan', 'Africa/Abidjan'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('America/Chihuahua', 'America/Chihuahua'), ('America/Juneau', 'America/Juneau'), ('Asia/Urumqi', 'Asia/Urumqi'), ('Africa/Conakry', 'Africa/Conakry'), ('Africa/Kampala', 'Africa/Kampala'), ('CST6CDT', 'CST6CDT'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('America/Cayman', 'America/Cayman'), ('Iran', 'Iran'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('Europe/Kyiv', 'Europe/Kyiv'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('Australia/West', 'Australia/West'), ('Etc/GMT-6', 'Etc/GMT-6'), ('Indian/Reunion', 'Indian/Reunion'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Etc/GMT-12', 'Etc/GMT-12'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('Pacific/Johnston', 'Pacific/Johnston'), ('Africa/Luanda', 'Africa/Luanda'), ('NZ-CHAT', 'NZ-CHAT'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Iceland', 'Iceland'), ('Factory', 'Factory'), ('Asia/Rangoon', 'Asia/Rangoon'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('Pacific/Niue', 'Pacific/Niue'), ('Europe/Oslo', 'Europe/Oslo'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Europe/Berlin', 'Europe/Berlin'), ('America/Jujuy', 'America/Jujuy'), ('Portugal', 'Portugal'), ('Pacific/Gambier', 'Pacific/Gambier'), ('America/Lower_Princes', 'America/Lower_Princes'), ('America/Belize', 'America/Belize'), ('America/El_Salvador', 'America/El_Salvador'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('Australia/Tasmania', 'Australia/Tasmania'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('America/Yakutat', 'America/Yakutat'), ('Africa/Lusaka', 'Africa/Lusaka'), ('Africa/Bamako', 'Africa/Bamako'), ('America/Araguaina', 'America/Araguaina'), ('Asia/Hovd', 'Asia/Hovd'), ('MST7MDT', 'MST7MDT'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Europe/Samara', 'Europe/Samara'), ('Europe/Istanbul', 'Europe/Istanbul'), ('US/Mountain', 'US/Mountain'), ('Europe/Belgrade', 'Europe/Belgrade'), ('US/Pacific', 'US/Pacific'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Indian/Chagos', 'Indian/Chagos'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Africa/Tunis', 'Africa/Tunis'), ('America/St_Johns', 'America/St_Johns'), ('Etc/GMT-4', 'Etc/GMT-4'), ('GMT', 'GMT'), ('America/Fortaleza', 'America/Fortaleza'), ('Indian/Cocos', 'Indian/Cocos'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('Asia/Samarkand', 'Asia/Samarkand'), ('Indian/Mahe', 'Indian/Mahe'), ('US/Central', 'US/Central'), ('GB', 'GB'), ('Europe/Madrid', 'Europe/Madrid'), ('Asia/Colombo', 'Asia/Colombo'), ('America/St_Thomas', 'America/St_Thomas'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('GMT-0', 'GMT-0'), ('America/Marigot', 'America/Marigot'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Europe/Vienna', 'Europe/Vienna'), ('Africa/Ceuta', 'Africa/Ceuta'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Australia/South', 'Australia/South'), ('Australia/LHI', 'Australia/LHI'), ('Australia/Victoria', 'Australia/Victoria'), ('Africa/Cairo', 'Africa/Cairo'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('Greenwich', 'Greenwich'), ('Pacific/Ponape', 'Pacific/Ponape'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('GB-Eire', 'GB-Eire'), ('Brazil/East', 'Brazil/East'), ('Asia/Kabul', 'Asia/Kabul'), ('Canada/Central', 'Canada/Central'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Europe/Monaco', 'Europe/Monaco'), ('Africa/Tripoli', 'Africa/Tripoli'), ('US/Michigan', 'US/Michigan'), ('Africa/Kigali', 'Africa/Kigali'), ('Australia/Adelaide', 'Australia/Adelaide'), ('America/Maceio', 'America/Maceio'), ('Europe/San_Marino', 'Europe/San_Marino'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('Europe/Riga', 'Europe/Riga'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Etc/GMT-10', 'Etc/GMT-10'), ('Europe/Tallinn', 'Europe/Tallinn'), ('Asia/Dubai', 'Asia/Dubai'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Europe/Budapest', 'Europe/Budapest'), ('MET', 'MET'), ('America/Cuiaba', 'America/Cuiaba'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Egypt', 'Egypt'), ('Asia/Atyrau', 'Asia/Atyrau'), ('WET', 'WET'), ('Europe/Prague', 'Europe/Prague'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('Asia/Singapore', 'Asia/Singapore'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('Asia/Vientiane', 'Asia/Vientiane'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('America/Grand_Turk', 'America/Grand_Turk'), ('Pacific/Guam', 'Pacific/Guam'), ('Europe/Simferopol', 'Europe/Simferopol'), ('Australia/Queensland', 'Australia/Queensland'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('Asia/Kolkata', 'Asia/Kolkata'), ('America/Menominee', 'America/Menominee'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('America/Creston', 'America/Creston'), ('Asia/Saigon', 'Asia/Saigon'), ('America/Curacao', 'America/Curacao'), ('Europe/Kiev', 'Europe/Kiev'), ('America/Virgin', 'America/Virgin'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('America/Montreal', 'America/Montreal'), ('Europe/Podgorica', 'Europe/Podgorica'), ('America/Nipigon', 'America/Nipigon'), ('build/etc/localtime', 'build/etc/localtime'), ('America/Dawson', 'America/Dawson'), ('America/Regina', 'America/Regina'), ('Canada/Pacific', 'Canada/Pacific'), ('America/Bahia', 'America/Bahia'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Etc/GMT+10', 'Etc/GMT+10'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('America/Cayenne', 'America/Cayenne'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('America/Chicago', 'America/Chicago'), ('Africa/Lagos', 'Africa/Lagos'), ('America/Lima', 'America/Lima'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('Poland', 'Poland'), ('America/Anchorage', 'America/Anchorage'), ('America/Noronha', 'America/Noronha'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('Asia/Aden', 'Asia/Aden'), ('Indian/Maldives', 'Indian/Maldives'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Africa/Freetown', 'Africa/Freetown'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('America/Aruba', 'America/Aruba'), ('America/Scoresbysund', 'America/Scoresbysund'), ('Europe/Paris', 'Europe/Paris'), ('US/Hawaii', 'US/Hawaii'), ('Navajo', 'Navajo'), ('America/Guayaquil', 'America/Guayaquil'), ('Canada/Mountain', 'Canada/Mountain'), ('America/Anguilla', 'America/Anguilla'), ('Africa/Dakar', 'Africa/Dakar'), ('Indian/Christmas', 'Indian/Christmas'), ('Chile/Continental', 'Chile/Continental'), ('Cuba', 'Cuba'), ('America/Panama', 'America/Panama'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('Australia/North', 'Australia/North'), ('America/Montserrat', 'America/Montserrat'), ('Africa/Banjul', 'Africa/Banjul'), ('Africa/Algiers', 'Africa/Algiers'), ('America/St_Lucia', 'America/St_Lucia'), ('America/Ojinaga', 'America/Ojinaga'), ('America/Eirunepe', 'America/Eirunepe'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Eire', 'Eire'), ('Turkey', 'Turkey'), ('Asia/Karachi', 'Asia/Karachi'), ('GMT0', 'GMT0'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Africa/Asmera', 'Africa/Asmera'), ('Etc/GMT+1', 'Etc/GMT+1'), ('Asia/Nicosia', 'Asia/Nicosia'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('Australia/Hobart', 'Australia/Hobart'), ('Australia/ACT', 'Australia/ACT'), ('MST', 'MST'), ('America/Pangnirtung', 'America/Pangnirtung'), ('America/Jamaica', 'America/Jamaica'), ('Africa/Niamey', 'Africa/Niamey'), ('America/Dominica', 'America/Dominica'), ('America/Managua', 'America/Managua'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Pacific/Easter', 'Pacific/Easter'), ('Brazil/Acre', 'Brazil/Acre'), ('Europe/Zurich', 'Europe/Zurich'), ('America/St_Vincent', 'America/St_Vincent'), ('US/Alaska', 'US/Alaska'), ('Hongkong', 'Hongkong'), ('Etc/GMT+6', 'Etc/GMT+6'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('Africa/Nairobi', 'Africa/Nairobi'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('America/Phoenix', 'America/Phoenix'), ('Europe/Minsk', 'Europe/Minsk'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('US/Aleutian', 'US/Aleutian'), ('Antarctica/Casey', 'Antarctica/Casey'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Asia/Muscat', 'Asia/Muscat'), ('Europe/Vaduz', 'Europe/Vaduz'), ('Asia/Dacca', 'Asia/Dacca'), ('America/Antigua', 'America/Antigua'), ('Europe/Skopje', 'Europe/Skopje'), ('Europe/Chisinau', 'Europe/Chisinau')], default='Europe/London', max_length=35),
        ),
    ]