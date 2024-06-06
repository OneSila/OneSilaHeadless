# Generated by Django 5.0.2 on 2024-05-30 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0058_alter_multitenantuser_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('Asia/Jayapura', 'Asia/Jayapura'), ('America/Havana', 'America/Havana'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Indian/Chagos', 'Indian/Chagos'), ('Africa/Algiers', 'Africa/Algiers'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('Etc/GMT+1', 'Etc/GMT+1'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('America/Godthab', 'America/Godthab'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('America/Ojinaga', 'America/Ojinaga'), ('ROC', 'ROC'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('Etc/GMT-1', 'Etc/GMT-1'), ('Mexico/General', 'Mexico/General'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Africa/Maseru', 'Africa/Maseru'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('Etc/GMT+2', 'Etc/GMT+2'), ('Etc/Zulu', 'Etc/Zulu'), ('America/Cordoba', 'America/Cordoba'), ('America/Montreal', 'America/Montreal'), ('Etc/GMT-9', 'Etc/GMT-9'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('Europe/Moscow', 'Europe/Moscow'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('Etc/GMT-10', 'Etc/GMT-10'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Europe/Tallinn', 'Europe/Tallinn'), ('Africa/Lusaka', 'Africa/Lusaka'), ('America/Atka', 'America/Atka'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Canada/Eastern', 'Canada/Eastern'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('Indian/Mauritius', 'Indian/Mauritius'), ('UCT', 'UCT'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Africa/Juba', 'Africa/Juba'), ('America/Ensenada', 'America/Ensenada'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('America/Swift_Current', 'America/Swift_Current'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('Europe/Warsaw', 'Europe/Warsaw'), ('Canada/Pacific', 'Canada/Pacific'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('Europe/Vaduz', 'Europe/Vaduz'), ('US/Hawaii', 'US/Hawaii'), ('Iran', 'Iran'), ('Pacific/Truk', 'Pacific/Truk'), ('America/Adak', 'America/Adak'), ('Asia/Almaty', 'Asia/Almaty'), ('Africa/Monrovia', 'Africa/Monrovia'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Europe/Kiev', 'Europe/Kiev'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('America/Miquelon', 'America/Miquelon'), ('Europe/Dublin', 'Europe/Dublin'), ('Pacific/Majuro', 'Pacific/Majuro'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('Asia/Istanbul', 'Asia/Istanbul'), ('Iceland', 'Iceland'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('America/Cayenne', 'America/Cayenne'), ('Europe/Belgrade', 'Europe/Belgrade'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Africa/Kampala', 'Africa/Kampala'), ('America/Metlakatla', 'America/Metlakatla'), ('Pacific/Nauru', 'Pacific/Nauru'), ('GMT0', 'GMT0'), ('Africa/Cairo', 'Africa/Cairo'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('Africa/Kigali', 'Africa/Kigali'), ('Asia/Gaza', 'Asia/Gaza'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('Asia/Manila', 'Asia/Manila'), ('Asia/Pontianak', 'Asia/Pontianak'), ('America/Halifax', 'America/Halifax'), ('Pacific/Palau', 'Pacific/Palau'), ('Asia/Tokyo', 'Asia/Tokyo'), ('US/Eastern', 'US/Eastern'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('Asia/Dacca', 'Asia/Dacca'), ('America/Thule', 'America/Thule'), ('EST5EDT', 'EST5EDT'), ('Europe/Brussels', 'Europe/Brussels'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('Indian/Mayotte', 'Indian/Mayotte'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Asia/Anadyr', 'Asia/Anadyr'), ('Portugal', 'Portugal'), ('Brazil/Acre', 'Brazil/Acre'), ('America/Tortola', 'America/Tortola'), ('America/Bogota', 'America/Bogota'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Asia/Harbin', 'Asia/Harbin'), ('Asia/Tehran', 'Asia/Tehran'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('Europe/Budapest', 'Europe/Budapest'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('Europe/Simferopol', 'Europe/Simferopol'), ('Asia/Chungking', 'Asia/Chungking'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('Australia/LHI', 'Australia/LHI'), ('America/Montserrat', 'America/Montserrat'), ('America/Panama', 'America/Panama'), ('Europe/Tirane', 'Europe/Tirane'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('Europe/Jersey', 'Europe/Jersey'), ('Africa/Conakry', 'Africa/Conakry'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('America/Maceio', 'America/Maceio'), ('Africa/Bangui', 'Africa/Bangui'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('Israel', 'Israel'), ('America/Los_Angeles', 'America/Los_Angeles'), ('UTC', 'UTC'), ('Africa/Freetown', 'Africa/Freetown'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('Pacific/Efate', 'Pacific/Efate'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('America/Resolute', 'America/Resolute'), ('Africa/Windhoek', 'Africa/Windhoek'), ('America/Cuiaba', 'America/Cuiaba'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('America/Lima', 'America/Lima'), ('Asia/Dili', 'Asia/Dili'), ('Etc/GMT-13', 'Etc/GMT-13'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Europe/Bucharest', 'Europe/Bucharest'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('America/Anguilla', 'America/Anguilla'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Indian/Comoro', 'Indian/Comoro'), ('Africa/Casablanca', 'Africa/Casablanca'), ('Indian/Mahe', 'Indian/Mahe'), ('Asia/Taipei', 'Asia/Taipei'), ('America/Rio_Branco', 'America/Rio_Branco'), ('Etc/Greenwich', 'Etc/Greenwich'), ('America/Cancun', 'America/Cancun'), ('Kwajalein', 'Kwajalein'), ('Etc/GMT+11', 'Etc/GMT+11'), ('Australia/NSW', 'Australia/NSW'), ('Etc/GMT0', 'Etc/GMT0'), ('Asia/Thimbu', 'Asia/Thimbu'), ('Libya', 'Libya'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('America/Boise', 'America/Boise'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('America/Jujuy', 'America/Jujuy'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Etc/GMT+10', 'Etc/GMT+10'), ('Europe/Helsinki', 'Europe/Helsinki'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Australia/Adelaide', 'Australia/Adelaide'), ('GMT', 'GMT'), ('Asia/Oral', 'Asia/Oral'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('America/Chicago', 'America/Chicago'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('America/Goose_Bay', 'America/Goose_Bay'), ('America/St_Vincent', 'America/St_Vincent'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('America/Martinique', 'America/Martinique'), ('America/Nipigon', 'America/Nipigon'), ('America/Menominee', 'America/Menominee'), ('America/Porto_Acre', 'America/Porto_Acre'), ('America/Managua', 'America/Managua'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Asia/Kashgar', 'Asia/Kashgar'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('EST', 'EST'), ('Africa/Maputo', 'Africa/Maputo'), ('Africa/Douala', 'Africa/Douala'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('America/Cayman', 'America/Cayman'), ('Asia/Macao', 'Asia/Macao'), ('America/Monterrey', 'America/Monterrey'), ('US/Michigan', 'US/Michigan'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('build/etc/localtime', 'build/etc/localtime'), ('Etc/GMT+0', 'Etc/GMT+0'), ('America/Bahia', 'America/Bahia'), ('America/Pangnirtung', 'America/Pangnirtung'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('America/Boa_Vista', 'America/Boa_Vista'), ('Australia/Darwin', 'Australia/Darwin'), ('Europe/Vatican', 'Europe/Vatican'), ('America/Nassau', 'America/Nassau'), ('America/Yellowknife', 'America/Yellowknife'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('Asia/Nicosia', 'Asia/Nicosia'), ('Etc/GMT-12', 'Etc/GMT-12'), ('Europe/San_Marino', 'Europe/San_Marino'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('America/Creston', 'America/Creston'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Etc/UCT', 'Etc/UCT'), ('Africa/Asmera', 'Africa/Asmera'), ('US/Mountain', 'US/Mountain'), ('ROK', 'ROK'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('America/Rosario', 'America/Rosario'), ('GMT-0', 'GMT-0'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('America/Belem', 'America/Belem'), ('Etc/GMT-4', 'Etc/GMT-4'), ('Australia/Canberra', 'Australia/Canberra'), ('Europe/Guernsey', 'Europe/Guernsey'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('Pacific/Ponape', 'Pacific/Ponape'), ('Europe/Zagreb', 'Europe/Zagreb'), ('Asia/Amman', 'Asia/Amman'), ('NZ-CHAT', 'NZ-CHAT'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Etc/UTC', 'Etc/UTC'), ('Europe/Chisinau', 'Europe/Chisinau'), ('America/Catamarca', 'America/Catamarca'), ('America/Mazatlan', 'America/Mazatlan'), ('Asia/Damascus', 'Asia/Damascus'), ('America/La_Paz', 'America/La_Paz'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('Antarctica/Casey', 'Antarctica/Casey'), ('America/Asuncion', 'America/Asuncion'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('PRC', 'PRC'), ('Europe/London', 'Europe/London'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Asia/Macau', 'Asia/Macau'), ('Chile/Continental', 'Chile/Continental'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('US/Alaska', 'US/Alaska'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Pacific/Chatham', 'Pacific/Chatham'), ('America/Indianapolis', 'America/Indianapolis'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('America/Winnipeg', 'America/Winnipeg'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Asia/Riyadh', 'Asia/Riyadh'), ('Etc/Universal', 'Etc/Universal'), ('CST6CDT', 'CST6CDT'), ('Indian/Maldives', 'Indian/Maldives'), ('Europe/Minsk', 'Europe/Minsk'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('Europe/Oslo', 'Europe/Oslo'), ('America/Caracas', 'America/Caracas'), ('Africa/Khartoum', 'Africa/Khartoum'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Asia/Kolkata', 'Asia/Kolkata'), ('Etc/GMT+7', 'Etc/GMT+7'), ('Europe/Skopje', 'Europe/Skopje'), ('Africa/Ceuta', 'Africa/Ceuta'), ('America/Scoresbysund', 'America/Scoresbysund'), ('America/Marigot', 'America/Marigot'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('Universal', 'Universal'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Africa/Accra', 'Africa/Accra'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('Pacific/Wake', 'Pacific/Wake'), ('America/Montevideo', 'America/Montevideo'), ('GMT+0', 'GMT+0'), ('Zulu', 'Zulu'), ('Africa/Gaborone', 'Africa/Gaborone'), ('Etc/GMT-3', 'Etc/GMT-3'), ('America/St_Lucia', 'America/St_Lucia'), ('Europe/Busingen', 'Europe/Busingen'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('Etc/GMT+3', 'Etc/GMT+3'), ('Africa/Bamako', 'Africa/Bamako'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Asia/Yangon', 'Asia/Yangon'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('America/Vancouver', 'America/Vancouver'), ('Africa/Tripoli', 'Africa/Tripoli'), ('America/Manaus', 'America/Manaus'), ('Pacific/Auckland', 'Pacific/Auckland'), ('Asia/Kuching', 'Asia/Kuching'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('Etc/GMT-11', 'Etc/GMT-11'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('Europe/Paris', 'Europe/Paris'), ('Canada/Central', 'Canada/Central'), ('EET', 'EET'), ('Australia/South', 'Australia/South'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Europe/Samara', 'Europe/Samara'), ('W-SU', 'W-SU'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('Asia/Baghdad', 'Asia/Baghdad'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Europe/Vienna', 'Europe/Vienna'), ('America/Dawson', 'America/Dawson'), ('America/Eirunepe', 'America/Eirunepe'), ('Australia/Queensland', 'Australia/Queensland'), ('America/Detroit', 'America/Detroit'), ('Singapore', 'Singapore'), ('America/Knox_IN', 'America/Knox_IN'), ('America/Belize', 'America/Belize'), ('America/Chihuahua', 'America/Chihuahua'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Asia/Rangoon', 'Asia/Rangoon'), ('Africa/Bissau', 'Africa/Bissau'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Asia/Atyrau', 'Asia/Atyrau'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Asia/Dubai', 'Asia/Dubai'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('US/East-Indiana', 'US/East-Indiana'), ('Europe/Podgorica', 'Europe/Podgorica'), ('America/New_York', 'America/New_York'), ('America/Yakutat', 'America/Yakutat'), ('America/Rainy_River', 'America/Rainy_River'), ('Pacific/Johnston', 'Pacific/Johnston'), ('Australia/Victoria', 'Australia/Victoria'), ('Etc/GMT+8', 'Etc/GMT+8'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Pacific/Gambier', 'Pacific/Gambier'), ('Australia/Tasmania', 'Australia/Tasmania'), ('Asia/Magadan', 'Asia/Magadan'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('America/El_Salvador', 'America/El_Salvador'), ('America/Matamoros', 'America/Matamoros'), ('America/Louisville', 'America/Louisville'), ('America/Virgin', 'America/Virgin'), ('Asia/Famagusta', 'Asia/Famagusta'), ('America/Phoenix', 'America/Phoenix'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('Europe/Riga', 'Europe/Riga'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('America/Hermosillo', 'America/Hermosillo'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Etc/GMT-6', 'Etc/GMT-6'), ('Brazil/East', 'Brazil/East'), ('Europe/Monaco', 'Europe/Monaco'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('US/Arizona', 'US/Arizona'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('Australia/Hobart', 'Australia/Hobart'), ('America/Shiprock', 'America/Shiprock'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Pacific/Midway', 'Pacific/Midway'), ('Europe/Andorra', 'Europe/Andorra'), ('Etc/GMT+9', 'Etc/GMT+9'), ('America/Mendoza', 'America/Mendoza'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('US/Pacific', 'US/Pacific'), ('America/Nome', 'America/Nome'), ('America/Grand_Turk', 'America/Grand_Turk'), ('Asia/Aden', 'Asia/Aden'), ('GB', 'GB'), ('Asia/Colombo', 'Asia/Colombo'), ('WET', 'WET'), ('US/Aleutian', 'US/Aleutian'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Hongkong', 'Hongkong'), ('Indian/Reunion', 'Indian/Reunion'), ('Europe/Berlin', 'Europe/Berlin'), ('Europe/Nicosia', 'Europe/Nicosia'), ('Turkey', 'Turkey'), ('America/Campo_Grande', 'America/Campo_Grande'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('Egypt', 'Egypt'), ('Africa/Lagos', 'Africa/Lagos'), ('Etc/GMT+6', 'Etc/GMT+6'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Factory', 'Factory'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('America/Juneau', 'America/Juneau'), ('Asia/Chita', 'Asia/Chita'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('Africa/Abidjan', 'Africa/Abidjan'), ('Europe/Athens', 'Europe/Athens'), ('Europe/Madrid', 'Europe/Madrid'), ('Atlantic/Canary', 'Atlantic/Canary'), ('America/Tijuana', 'America/Tijuana'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('Asia/Qostanay', 'Asia/Qostanay'), ('America/Recife', 'America/Recife'), ('Asia/Baku', 'Asia/Baku'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('Africa/Libreville', 'Africa/Libreville'), ('Africa/Niamey', 'Africa/Niamey'), ('Pacific/Niue', 'Pacific/Niue'), ('America/Regina', 'America/Regina'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Eire', 'Eire'), ('Asia/Bangkok', 'Asia/Bangkok'), ('America/Paramaribo', 'America/Paramaribo'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('Etc/GMT', 'Etc/GMT'), ('Africa/Nairobi', 'Africa/Nairobi'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('America/Whitehorse', 'America/Whitehorse'), ('Asia/Kuwait', 'Asia/Kuwait'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Asia/Thimphu', 'Asia/Thimphu'), ('PST8PDT', 'PST8PDT'), ('Australia/West', 'Australia/West'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Brazil/West', 'Brazil/West'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('Africa/Tunis', 'Africa/Tunis'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('America/St_Johns', 'America/St_Johns'), ('America/Araguaina', 'America/Araguaina'), ('America/Iqaluit', 'America/Iqaluit'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('Greenwich', 'Greenwich'), ('America/Fortaleza', 'America/Fortaleza'), ('America/Guadeloupe', 'America/Guadeloupe'), ('Africa/Banjul', 'Africa/Banjul'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('America/Santiago', 'America/Santiago'), ('Africa/Mbabane', 'Africa/Mbabane'), ('Europe/Volgograd', 'Europe/Volgograd'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Europe/Malta', 'Europe/Malta'), ('Africa/Luanda', 'Africa/Luanda'), ('Europe/Sofia', 'Europe/Sofia'), ('America/St_Thomas', 'America/St_Thomas'), ('Asia/Omsk', 'Asia/Omsk'), ('Europe/Rome', 'Europe/Rome'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Asia/Hebron', 'Asia/Hebron'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('America/Aruba', 'America/Aruba'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('America/Curacao', 'America/Curacao'), ('Europe/Kyiv', 'Europe/Kyiv'), ('Asia/Jakarta', 'Asia/Jakarta'), ('Canada/Yukon', 'Canada/Yukon'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('Africa/Lome', 'Africa/Lome'), ('America/Guyana', 'America/Guyana'), ('America/Merida', 'America/Merida'), ('Australia/ACT', 'Australia/ACT'), ('Europe/Saratov', 'Europe/Saratov'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Europe/Prague', 'Europe/Prague'), ('America/Denver', 'America/Denver'), ('America/Guatemala', 'America/Guatemala'), ('US/Samoa', 'US/Samoa'), ('America/Edmonton', 'America/Edmonton'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('Etc/GMT-0', 'Etc/GMT-0'), ('Navajo', 'Navajo'), ('America/Mexico_City', 'America/Mexico_City'), ('Pacific/Yap', 'Pacific/Yap'), ('America/Jamaica', 'America/Jamaica'), ('America/Grenada', 'America/Grenada'), ('Australia/Perth', 'Australia/Perth'), ('America/Inuvik', 'America/Inuvik'), ('Africa/Malabo', 'Africa/Malabo'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('America/Nuuk', 'America/Nuuk'), ('Asia/Yerevan', 'Asia/Yerevan'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('America/Dominica', 'America/Dominica'), ('MST7MDT', 'MST7MDT'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Europe/Belfast', 'Europe/Belfast'), ('Asia/Seoul', 'Asia/Seoul'), ('America/Guayaquil', 'America/Guayaquil'), ('America/Antigua', 'America/Antigua'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('Asia/Qatar', 'Asia/Qatar'), ('America/Anchorage', 'America/Anchorage'), ('Australia/Currie', 'Australia/Currie'), ('MET', 'MET'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('Asia/Brunei', 'Asia/Brunei'), ('Poland', 'Poland'), ('America/Atikokan', 'America/Atikokan'), ('Pacific/Easter', 'Pacific/Easter'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('America/Santarem', 'America/Santarem'), ('America/Toronto', 'America/Toronto'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Etc/GMT+5', 'Etc/GMT+5'), ('Australia/Eucla', 'Australia/Eucla'), ('Australia/Sydney', 'Australia/Sydney'), ('America/Barbados', 'America/Barbados'), ('Cuba', 'Cuba'), ('Asia/Saigon', 'Asia/Saigon'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('Etc/GMT-14', 'Etc/GMT-14'), ('America/St_Kitts', 'America/St_Kitts'), ('Japan', 'Japan'), ('NZ', 'NZ'), ('Canada/Atlantic', 'Canada/Atlantic'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('Canada/Mountain', 'Canada/Mountain'), ('Pacific/Wallis', 'Pacific/Wallis'), ('CET', 'CET'), ('Asia/Hovd', 'Asia/Hovd'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('GB-Eire', 'GB-Eire'), ('Africa/Asmara', 'Africa/Asmara'), ('America/Kralendijk', 'America/Kralendijk'), ('Africa/Harare', 'Africa/Harare'), ('Europe/Kirov', 'Europe/Kirov'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('Etc/GMT-2', 'Etc/GMT-2'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('Asia/Urumqi', 'Asia/Urumqi'), ('HST', 'HST'), ('Asia/Karachi', 'Asia/Karachi'), ('Europe/Zurich', 'Europe/Zurich'), ('US/Central', 'US/Central'), ('Asia/Vientiane', 'Asia/Vientiane'), ('Indian/Christmas', 'Indian/Christmas'), ('Asia/Muscat', 'Asia/Muscat'), ('Etc/GMT-8', 'Etc/GMT-8'), ('America/Porto_Velho', 'America/Porto_Velho'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Indian/Cocos', 'Indian/Cocos'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Pacific/Guam', 'Pacific/Guam'), ('Asia/Barnaul', 'Asia/Barnaul'), ('Pacific/Apia', 'Pacific/Apia'), ('Asia/Beirut', 'Asia/Beirut'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('Asia/Samarkand', 'Asia/Samarkand'), ('Africa/Dakar', 'Africa/Dakar'), ('America/Lower_Princes', 'America/Lower_Princes'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Asia/Kabul', 'Asia/Kabul'), ('Jamaica', 'Jamaica'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('America/Noronha', 'America/Noronha'), ('MST', 'MST'), ('Australia/North', 'Australia/North'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('Asia/Makassar', 'Asia/Makassar'), ('America/Moncton', 'America/Moncton'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('America/Sitka', 'America/Sitka'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Asia/Singapore', 'Asia/Singapore')], default='Europe/London', max_length=35),
        ),
    ]