# Generated by Django 5.0.2 on 2024-06-10 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0094_alter_multitenantuser_onboarding_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('MST7MDT', 'MST7MDT'), ('America/Godthab', 'America/Godthab'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Pacific/Niue', 'Pacific/Niue'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('Asia/Riyadh', 'Asia/Riyadh'), ('Etc/GMT-9', 'Etc/GMT-9'), ('Africa/Gaborone', 'Africa/Gaborone'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('Asia/Anadyr', 'Asia/Anadyr'), ('Etc/GMT-0', 'Etc/GMT-0'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('Asia/Chita', 'Asia/Chita'), ('America/Regina', 'America/Regina'), ('US/Pacific', 'US/Pacific'), ('America/Martinique', 'America/Martinique'), ('America/Halifax', 'America/Halifax'), ('Asia/Aden', 'Asia/Aden'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('America/Nome', 'America/Nome'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Africa/Mbabane', 'Africa/Mbabane'), ('GMT-0', 'GMT-0'), ('Australia/North', 'Australia/North'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('Etc/Zulu', 'Etc/Zulu'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Etc/GMT+10', 'Etc/GMT+10'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('Africa/Bamako', 'Africa/Bamako'), ('Europe/Kiev', 'Europe/Kiev'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('Kwajalein', 'Kwajalein'), ('Etc/GMT+0', 'Etc/GMT+0'), ('Europe/Kirov', 'Europe/Kirov'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('Africa/Abidjan', 'Africa/Abidjan'), ('Africa/Asmera', 'Africa/Asmera'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('America/Bahia', 'America/Bahia'), ('Europe/Samara', 'Europe/Samara'), ('Brazil/East', 'Brazil/East'), ('Antarctica/Casey', 'Antarctica/Casey'), ('Brazil/Acre', 'Brazil/Acre'), ('Singapore', 'Singapore'), ('America/Inuvik', 'America/Inuvik'), ('America/Grand_Turk', 'America/Grand_Turk'), ('America/Whitehorse', 'America/Whitehorse'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Africa/Casablanca', 'Africa/Casablanca'), ('America/Grenada', 'America/Grenada'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('America/Chicago', 'America/Chicago'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('America/Guatemala', 'America/Guatemala'), ('Pacific/Apia', 'Pacific/Apia'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Asia/Singapore', 'Asia/Singapore'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('W-SU', 'W-SU'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('America/Jujuy', 'America/Jujuy'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Libya', 'Libya'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('Europe/Vienna', 'Europe/Vienna'), ('Pacific/Efate', 'Pacific/Efate'), ('Europe/Zagreb', 'Europe/Zagreb'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('Europe/London', 'Europe/London'), ('Australia/LHI', 'Australia/LHI'), ('America/Anchorage', 'America/Anchorage'), ('America/Merida', 'America/Merida'), ('America/Monterrey', 'America/Monterrey'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Australia/NSW', 'Australia/NSW'), ('Africa/Accra', 'Africa/Accra'), ('Indian/Cocos', 'Indian/Cocos'), ('America/Hermosillo', 'America/Hermosillo'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Europe/Berlin', 'Europe/Berlin'), ('America/Campo_Grande', 'America/Campo_Grande'), ('Pacific/Auckland', 'Pacific/Auckland'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('America/Metlakatla', 'America/Metlakatla'), ('America/Cordoba', 'America/Cordoba'), ('Asia/Damascus', 'Asia/Damascus'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Asia/Baku', 'Asia/Baku'), ('EET', 'EET'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('Europe/Skopje', 'Europe/Skopje'), ('Asia/Barnaul', 'Asia/Barnaul'), ('America/El_Salvador', 'America/El_Salvador'), ('Etc/GMT-1', 'Etc/GMT-1'), ('America/Creston', 'America/Creston'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Etc/GMT+8', 'Etc/GMT+8'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('America/Lower_Princes', 'America/Lower_Princes'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('Africa/Bangui', 'Africa/Bangui'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('Etc/GMT+5', 'Etc/GMT+5'), ('Europe/Paris', 'Europe/Paris'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('ROK', 'ROK'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('Europe/Madrid', 'Europe/Madrid'), ('PST8PDT', 'PST8PDT'), ('Europe/Athens', 'Europe/Athens'), ('Africa/Kigali', 'Africa/Kigali'), ('Africa/Asmara', 'Africa/Asmara'), ('Africa/Libreville', 'Africa/Libreville'), ('US/Michigan', 'US/Michigan'), ('Etc/GMT-10', 'Etc/GMT-10'), ('Australia/Eucla', 'Australia/Eucla'), ('Asia/Jayapura', 'Asia/Jayapura'), ('Asia/Qatar', 'Asia/Qatar'), ('Etc/GMT+2', 'Etc/GMT+2'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('America/St_Johns', 'America/St_Johns'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('Europe/Prague', 'Europe/Prague'), ('Eire', 'Eire'), ('America/Swift_Current', 'America/Swift_Current'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Europe/Volgograd', 'Europe/Volgograd'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('America/Goose_Bay', 'America/Goose_Bay'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('Poland', 'Poland'), ('America/Los_Angeles', 'America/Los_Angeles'), ('Asia/Nicosia', 'Asia/Nicosia'), ('America/Manaus', 'America/Manaus'), ('America/Edmonton', 'America/Edmonton'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('Asia/Makassar', 'Asia/Makassar'), ('US/Samoa', 'US/Samoa'), ('Africa/Freetown', 'Africa/Freetown'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('America/Panama', 'America/Panama'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Asia/Dubai', 'Asia/Dubai'), ('Asia/Karachi', 'Asia/Karachi'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Europe/Tallinn', 'Europe/Tallinn'), ('Jamaica', 'Jamaica'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('America/Bogota', 'America/Bogota'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('America/Mazatlan', 'America/Mazatlan'), ('America/Ojinaga', 'America/Ojinaga'), ('Africa/Luanda', 'Africa/Luanda'), ('Pacific/Nauru', 'Pacific/Nauru'), ('GMT+0', 'GMT+0'), ('Pacific/Ponape', 'Pacific/Ponape'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('America/Havana', 'America/Havana'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('Asia/Chungking', 'Asia/Chungking'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Europe/Simferopol', 'Europe/Simferopol'), ('America/Rainy_River', 'America/Rainy_River'), ('America/Mendoza', 'America/Mendoza'), ('Asia/Seoul', 'Asia/Seoul'), ('Pacific/Johnston', 'Pacific/Johnston'), ('America/Matamoros', 'America/Matamoros'), ('Australia/Canberra', 'Australia/Canberra'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('Asia/Brunei', 'Asia/Brunei'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('GB-Eire', 'GB-Eire'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('America/Cancun', 'America/Cancun'), ('Asia/Hebron', 'Asia/Hebron'), ('Etc/Universal', 'Etc/Universal'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Asia/Kuching', 'Asia/Kuching'), ('Asia/Oral', 'Asia/Oral'), ('EST5EDT', 'EST5EDT'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Africa/Juba', 'Africa/Juba'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('America/Thule', 'America/Thule'), ('Australia/Victoria', 'Australia/Victoria'), ('America/Kralendijk', 'America/Kralendijk'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Africa/Dakar', 'Africa/Dakar'), ('Canada/Mountain', 'Canada/Mountain'), ('America/St_Lucia', 'America/St_Lucia'), ('Europe/Vaduz', 'Europe/Vaduz'), ('Pacific/Truk', 'Pacific/Truk'), ('America/St_Kitts', 'America/St_Kitts'), ('Australia/Perth', 'Australia/Perth'), ('Etc/GMT+6', 'Etc/GMT+6'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('America/Tortola', 'America/Tortola'), ('America/Yellowknife', 'America/Yellowknife'), ('MST', 'MST'), ('America/St_Thomas', 'America/St_Thomas'), ('America/Louisville', 'America/Louisville'), ('America/Belize', 'America/Belize'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Indian/Mahe', 'Indian/Mahe'), ('America/La_Paz', 'America/La_Paz'), ('Europe/Andorra', 'Europe/Andorra'), ('Africa/Cairo', 'Africa/Cairo'), ('Europe/Oslo', 'Europe/Oslo'), ('America/Jamaica', 'America/Jamaica'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Etc/Greenwich', 'Etc/Greenwich'), ('America/Porto_Velho', 'America/Porto_Velho'), ('Africa/Conakry', 'Africa/Conakry'), ('Europe/Monaco', 'Europe/Monaco'), ('Africa/Lome', 'Africa/Lome'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('Australia/South', 'Australia/South'), ('America/Porto_Acre', 'America/Porto_Acre'), ('EST', 'EST'), ('PRC', 'PRC'), ('Asia/Tomsk', 'Asia/Tomsk'), ('America/Maceio', 'America/Maceio'), ('America/Catamarca', 'America/Catamarca'), ('US/Arizona', 'US/Arizona'), ('America/Tijuana', 'America/Tijuana'), ('Australia/Hobart', 'Australia/Hobart'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('America/Rio_Branco', 'America/Rio_Branco'), ('GB', 'GB'), ('Africa/Monrovia', 'Africa/Monrovia'), ('Europe/Belfast', 'Europe/Belfast'), ('Etc/GMT-2', 'Etc/GMT-2'), ('Hongkong', 'Hongkong'), ('Iceland', 'Iceland'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('UCT', 'UCT'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Canada/Central', 'Canada/Central'), ('Asia/Atyrau', 'Asia/Atyrau'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('Asia/Calcutta', 'Asia/Calcutta'), ('NZ-CHAT', 'NZ-CHAT'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('Africa/Tripoli', 'Africa/Tripoli'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('Africa/Khartoum', 'Africa/Khartoum'), ('MET', 'MET'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('America/Asuncion', 'America/Asuncion'), ('WET', 'WET'), ('America/Phoenix', 'America/Phoenix'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Indian/Mauritius', 'Indian/Mauritius'), ('US/Mountain', 'US/Mountain'), ('build/etc/localtime', 'build/etc/localtime'), ('Europe/Minsk', 'Europe/Minsk'), ('Asia/Omsk', 'Asia/Omsk'), ('Pacific/Kanton', 'Pacific/Kanton'), ('America/Boa_Vista', 'America/Boa_Vista'), ('America/Montreal', 'America/Montreal'), ('Asia/Dili', 'Asia/Dili'), ('Asia/Vientiane', 'Asia/Vientiane'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('America/Shiprock', 'America/Shiprock'), ('America/Cayman', 'America/Cayman'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Europe/Brussels', 'Europe/Brussels'), ('Europe/Chisinau', 'Europe/Chisinau'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('Atlantic/Canary', 'Atlantic/Canary'), ('Australia/ACT', 'Australia/ACT'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('America/Montevideo', 'America/Montevideo'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Europe/Busingen', 'Europe/Busingen'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('GMT', 'GMT'), ('ROC', 'ROC'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Canada/Pacific', 'Canada/Pacific'), ('Asia/Bangkok', 'Asia/Bangkok'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Africa/Harare', 'Africa/Harare'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('America/Miquelon', 'America/Miquelon'), ('Greenwich', 'Greenwich'), ('Asia/Harbin', 'Asia/Harbin'), ('Asia/Thimbu', 'Asia/Thimbu'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('Cuba', 'Cuba'), ('Pacific/Majuro', 'Pacific/Majuro'), ('Asia/Macao', 'Asia/Macao'), ('Etc/GMT0', 'Etc/GMT0'), ('Europe/Sofia', 'Europe/Sofia'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('Africa/Malabo', 'Africa/Malabo'), ('Indian/Chagos', 'Indian/Chagos'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('Indian/Maldives', 'Indian/Maldives'), ('Asia/Baghdad', 'Asia/Baghdad'), ('Asia/Kuwait', 'Asia/Kuwait'), ('America/Scoresbysund', 'America/Scoresbysund'), ('US/Hawaii', 'US/Hawaii'), ('Africa/Algiers', 'Africa/Algiers'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Europe/Moscow', 'Europe/Moscow'), ('Africa/Maseru', 'Africa/Maseru'), ('America/Marigot', 'America/Marigot'), ('Africa/Tunis', 'Africa/Tunis'), ('Turkey', 'Turkey'), ('Brazil/West', 'Brazil/West'), ('Etc/GMT-14', 'Etc/GMT-14'), ('Etc/GMT-3', 'Etc/GMT-3'), ('America/Atka', 'America/Atka'), ('Israel', 'Israel'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('America/Caracas', 'America/Caracas'), ('Pacific/Chatham', 'Pacific/Chatham'), ('America/Eirunepe', 'America/Eirunepe'), ('America/Nassau', 'America/Nassau'), ('America/Dominica', 'America/Dominica'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('Etc/GMT-13', 'Etc/GMT-13'), ('Australia/Adelaide', 'Australia/Adelaide'), ('Pacific/Easter', 'Pacific/Easter'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Asia/Macau', 'Asia/Macau'), ('America/Santarem', 'America/Santarem'), ('Etc/GMT+7', 'Etc/GMT+7'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Asia/Almaty', 'Asia/Almaty'), ('Asia/Kolkata', 'Asia/Kolkata'), ('Europe/Tirane', 'Europe/Tirane'), ('US/Central', 'US/Central'), ('Europe/Belgrade', 'Europe/Belgrade'), ('America/Vancouver', 'America/Vancouver'), ('America/Paramaribo', 'America/Paramaribo'), ('America/New_York', 'America/New_York'), ('Indian/Mayotte', 'Indian/Mayotte'), ('Zulu', 'Zulu'), ('America/Moncton', 'America/Moncton'), ('America/Cuiaba', 'America/Cuiaba'), ('Asia/Amman', 'Asia/Amman'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Asia/Khandyga', 'Asia/Khandyga'), ('America/Chihuahua', 'America/Chihuahua'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('America/Yakutat', 'America/Yakutat'), ('Australia/Darwin', 'Australia/Darwin'), ('Chile/Continental', 'Chile/Continental'), ('Europe/San_Marino', 'Europe/San_Marino'), ('Africa/Niamey', 'Africa/Niamey'), ('Africa/Maputo', 'Africa/Maputo'), ('Canada/Atlantic', 'Canada/Atlantic'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('Etc/GMT', 'Etc/GMT'), ('NZ', 'NZ'), ('America/Boise', 'America/Boise'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('America/Sitka', 'America/Sitka'), ('Australia/Queensland', 'Australia/Queensland'), ('Asia/Samarkand', 'Asia/Samarkand'), ('America/Adak', 'America/Adak'), ('Australia/West', 'Australia/West'), ('Europe/Zurich', 'Europe/Zurich'), ('America/Antigua', 'America/Antigua'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('America/Belem', 'America/Belem'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('Asia/Muscat', 'Asia/Muscat'), ('HST', 'HST'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('Asia/Istanbul', 'Asia/Istanbul'), ('America/Araguaina', 'America/Araguaina'), ('Egypt', 'Egypt'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('America/Lima', 'America/Lima'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('Africa/Douala', 'Africa/Douala'), ('America/Rosario', 'America/Rosario'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('Australia/Sydney', 'Australia/Sydney'), ('Etc/UTC', 'Etc/UTC'), ('Asia/Tehran', 'Asia/Tehran'), ('CET', 'CET'), ('Asia/Urumqi', 'Asia/Urumqi'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Asia/Dacca', 'Asia/Dacca'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('America/Montserrat', 'America/Montserrat'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('Europe/Jersey', 'Europe/Jersey'), ('Africa/Ceuta', 'Africa/Ceuta'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('Europe/Vatican', 'Europe/Vatican'), ('Asia/Gaza', 'Asia/Gaza'), ('Asia/Kabul', 'Asia/Kabul'), ('America/Cayenne', 'America/Cayenne'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Etc/GMT+11', 'Etc/GMT+11'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Asia/Jakarta', 'Asia/Jakarta'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('Asia/Taipei', 'Asia/Taipei'), ('Europe/Warsaw', 'Europe/Warsaw'), ('America/Managua', 'America/Managua'), ('America/Nuuk', 'America/Nuuk'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('Pacific/Wallis', 'Pacific/Wallis'), ('Etc/UCT', 'Etc/UCT'), ('Indian/Comoro', 'Indian/Comoro'), ('Etc/GMT-4', 'Etc/GMT-4'), ('America/Detroit', 'America/Detroit'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('Africa/Lagos', 'Africa/Lagos'), ('Iran', 'Iran'), ('Etc/GMT+1', 'Etc/GMT+1'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('UTC', 'UTC'), ('America/Guyana', 'America/Guyana'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('US/Aleutian', 'US/Aleutian'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Indian/Christmas', 'Indian/Christmas'), ('Africa/Nairobi', 'Africa/Nairobi'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('Europe/Nicosia', 'Europe/Nicosia'), ('Europe/Bucharest', 'Europe/Bucharest'), ('Canada/Eastern', 'Canada/Eastern'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Pacific/Midway', 'Pacific/Midway'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('Europe/Budapest', 'Europe/Budapest'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('America/Guadeloupe', 'America/Guadeloupe'), ('Asia/Colombo', 'Asia/Colombo'), ('America/Barbados', 'America/Barbados'), ('America/Aruba', 'America/Aruba'), ('Asia/Yangon', 'Asia/Yangon'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('Asia/Thimphu', 'Asia/Thimphu'), ('America/Santiago', 'America/Santiago'), ('America/Guayaquil', 'America/Guayaquil'), ('America/St_Vincent', 'America/St_Vincent'), ('America/Fortaleza', 'America/Fortaleza'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('Japan', 'Japan'), ('Asia/Beirut', 'Asia/Beirut'), ('Europe/Riga', 'Europe/Riga'), ('Factory', 'Factory'), ('Europe/Malta', 'Europe/Malta'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('America/Recife', 'America/Recife'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('America/Knox_IN', 'America/Knox_IN'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('America/Winnipeg', 'America/Winnipeg'), ('Asia/Manila', 'Asia/Manila'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('Indian/Reunion', 'Indian/Reunion'), ('Asia/Magadan', 'Asia/Magadan'), ('CST6CDT', 'CST6CDT'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('Africa/Bissau', 'Africa/Bissau'), ('Pacific/Wake', 'Pacific/Wake'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('Portugal', 'Portugal'), ('America/Curacao', 'America/Curacao'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('Asia/Shanghai', 'Asia/Shanghai'), ('America/Denver', 'America/Denver'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('Canada/Yukon', 'Canada/Yukon'), ('America/Virgin', 'America/Virgin'), ('GMT0', 'GMT0'), ('Pacific/Palau', 'Pacific/Palau'), ('America/Dawson', 'America/Dawson'), ('Asia/Rangoon', 'Asia/Rangoon'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Australia/Tasmania', 'Australia/Tasmania'), ('Etc/GMT-6', 'Etc/GMT-6'), ('America/Atikokan', 'America/Atikokan'), ('Europe/Saratov', 'Europe/Saratov'), ('Europe/Podgorica', 'Europe/Podgorica'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('Universal', 'Universal'), ('Pacific/Yap', 'Pacific/Yap'), ('Asia/Famagusta', 'Asia/Famagusta'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('America/Indianapolis', 'America/Indianapolis'), ('America/Nipigon', 'America/Nipigon'), ('Australia/Currie', 'Australia/Currie'), ('Navajo', 'Navajo'), ('Europe/Bratislava', 'Europe/Bratislava'), ('America/Juneau', 'America/Juneau'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('Etc/GMT-11', 'Etc/GMT-11'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('Asia/Hovd', 'Asia/Hovd'), ('America/Pangnirtung', 'America/Pangnirtung'), ('America/Mexico_City', 'America/Mexico_City'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Europe/Rome', 'Europe/Rome'), ('America/Noronha', 'America/Noronha'), ('Etc/GMT+9', 'Etc/GMT+9'), ('Asia/Qostanay', 'Asia/Qostanay'), ('America/Resolute', 'America/Resolute'), ('Mexico/General', 'Mexico/General'), ('US/East-Indiana', 'US/East-Indiana'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Europe/Helsinki', 'Europe/Helsinki'), ('US/Eastern', 'US/Eastern'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('Europe/Kyiv', 'Europe/Kyiv'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('Pacific/Guam', 'Pacific/Guam'), ('America/Iqaluit', 'America/Iqaluit'), ('US/Alaska', 'US/Alaska'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Europe/Dublin', 'Europe/Dublin'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Africa/Kampala', 'Africa/Kampala'), ('America/Anguilla', 'America/Anguilla'), ('Asia/Saigon', 'Asia/Saigon'), ('America/Toronto', 'America/Toronto'), ('Asia/Kashgar', 'Asia/Kashgar'), ('America/Ensenada', 'America/Ensenada'), ('Africa/Banjul', 'Africa/Banjul'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('Pacific/Gambier', 'Pacific/Gambier'), ('America/Menominee', 'America/Menominee'), ('Etc/GMT+3', 'Etc/GMT+3'), ('Etc/GMT-12', 'Etc/GMT-12'), ('Africa/Lusaka', 'Africa/Lusaka'), ('Antarctica/Troll', 'Antarctica/Troll')], default='Europe/London', max_length=35),
        ),
    ]