# Generated by Django 5.0.7 on 2024-07-21 10:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0127_alter_multitenantuser_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('US/Eastern', 'US/Eastern'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('ROK', 'ROK'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('Africa/Dakar', 'Africa/Dakar'), ('Australia/Hobart', 'Australia/Hobart'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('Asia/Damascus', 'Asia/Damascus'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('Australia/West', 'Australia/West'), ('America/Yakutat', 'America/Yakutat'), ('Pacific/Wallis', 'Pacific/Wallis'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Africa/Juba', 'Africa/Juba'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('America/Nassau', 'America/Nassau'), ('America/Recife', 'America/Recife'), ('Cuba', 'Cuba'), ('Asia/Dacca', 'Asia/Dacca'), ('Asia/Urumqi', 'Asia/Urumqi'), ('Etc/GMT+5', 'Etc/GMT+5'), ('Asia/Chita', 'Asia/Chita'), ('Asia/Macao', 'Asia/Macao'), ('GMT', 'GMT'), ('America/Noronha', 'America/Noronha'), ('Australia/Tasmania', 'Australia/Tasmania'), ('US/East-Indiana', 'US/East-Indiana'), ('America/Rainy_River', 'America/Rainy_River'), ('Europe/Moscow', 'Europe/Moscow'), ('EST5EDT', 'EST5EDT'), ('America/Godthab', 'America/Godthab'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Etc/GMT', 'Etc/GMT'), ('Europe/Rome', 'Europe/Rome'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('Pacific/Midway', 'Pacific/Midway'), ('Europe/Bucharest', 'Europe/Bucharest'), ('America/Belem', 'America/Belem'), ('Asia/Riyadh', 'Asia/Riyadh'), ('Africa/Gaborone', 'Africa/Gaborone'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Asia/Muscat', 'Asia/Muscat'), ('Asia/Jakarta', 'Asia/Jakarta'), ('GMT-0', 'GMT-0'), ('Atlantic/Canary', 'Atlantic/Canary'), ('Europe/Budapest', 'Europe/Budapest'), ('Canada/Pacific', 'Canada/Pacific'), ('America/Havana', 'America/Havana'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Asia/Kabul', 'Asia/Kabul'), ('Asia/Gaza', 'Asia/Gaza'), ('America/Goose_Bay', 'America/Goose_Bay'), ('Africa/Niamey', 'Africa/Niamey'), ('Pacific/Majuro', 'Pacific/Majuro'), ('America/Anchorage', 'America/Anchorage'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('Asia/Thimbu', 'Asia/Thimbu'), ('Asia/Almaty', 'Asia/Almaty'), ('Canada/Mountain', 'Canada/Mountain'), ('Navajo', 'Navajo'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Indian/Mahe', 'Indian/Mahe'), ('Africa/Bangui', 'Africa/Bangui'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('America/Monterrey', 'America/Monterrey'), ('Asia/Bangkok', 'Asia/Bangkok'), ('America/Grand_Turk', 'America/Grand_Turk'), ('Africa/Banjul', 'Africa/Banjul'), ('America/Paramaribo', 'America/Paramaribo'), ('America/Ensenada', 'America/Ensenada'), ('America/Guyana', 'America/Guyana'), ('Asia/Dubai', 'Asia/Dubai'), ('America/Louisville', 'America/Louisville'), ('America/St_Thomas', 'America/St_Thomas'), ('Israel', 'Israel'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('Europe/Madrid', 'Europe/Madrid'), ('Iran', 'Iran'), ('WET', 'WET'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('Europe/Athens', 'Europe/Athens'), ('America/Martinique', 'America/Martinique'), ('Etc/GMT+7', 'Etc/GMT+7'), ('Greenwich', 'Greenwich'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('America/Cordoba', 'America/Cordoba'), ('America/Moncton', 'America/Moncton'), ('Asia/Seoul', 'Asia/Seoul'), ('America/Miquelon', 'America/Miquelon'), ('America/Montevideo', 'America/Montevideo'), ('Australia/Perth', 'Australia/Perth'), ('America/Ojinaga', 'America/Ojinaga'), ('America/Guadeloupe', 'America/Guadeloupe'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('Europe/London', 'Europe/London'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Europe/Skopje', 'Europe/Skopje'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('MET', 'MET'), ('America/St_Vincent', 'America/St_Vincent'), ('Pacific/Efate', 'Pacific/Efate'), ('Etc/UCT', 'Etc/UCT'), ('America/Tortola', 'America/Tortola'), ('America/Bogota', 'America/Bogota'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('Etc/GMT-3', 'Etc/GMT-3'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('GB-Eire', 'GB-Eire'), ('Etc/GMT-12', 'Etc/GMT-12'), ('UCT', 'UCT'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('America/Lower_Princes', 'America/Lower_Princes'), ('NZ', 'NZ'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('America/Phoenix', 'America/Phoenix'), ('Africa/Asmera', 'Africa/Asmera'), ('Europe/Andorra', 'Europe/Andorra'), ('Africa/Accra', 'Africa/Accra'), ('Australia/North', 'Australia/North'), ('Australia/Eucla', 'Australia/Eucla'), ('US/Pacific', 'US/Pacific'), ('Asia/Jayapura', 'Asia/Jayapura'), ('America/Barbados', 'America/Barbados'), ('America/Dominica', 'America/Dominica'), ('Asia/Yangon', 'Asia/Yangon'), ('America/Matamoros', 'America/Matamoros'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('MST7MDT', 'MST7MDT'), ('Hongkong', 'Hongkong'), ('US/Samoa', 'US/Samoa'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('Africa/Malabo', 'Africa/Malabo'), ('America/Cayman', 'America/Cayman'), ('Africa/Kigali', 'Africa/Kigali'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('Pacific/Gambier', 'Pacific/Gambier'), ('America/Chihuahua', 'America/Chihuahua'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Pacific/Apia', 'Pacific/Apia'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('America/St_Lucia', 'America/St_Lucia'), ('Europe/Samara', 'Europe/Samara'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('HST', 'HST'), ('Europe/Vaduz', 'Europe/Vaduz'), ('Asia/Kuching', 'Asia/Kuching'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Etc/GMT+0', 'Etc/GMT+0'), ('Asia/Istanbul', 'Asia/Istanbul'), ('America/Caracas', 'America/Caracas'), ('Africa/Monrovia', 'Africa/Monrovia'), ('Etc/GMT-1', 'Etc/GMT-1'), ('Etc/GMT-10', 'Etc/GMT-10'), ('America/Rosario', 'America/Rosario'), ('Etc/GMT-11', 'Etc/GMT-11'), ('US/Mountain', 'US/Mountain'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Etc/UTC', 'Etc/UTC'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Chile/Continental', 'Chile/Continental'), ('US/Michigan', 'US/Michigan'), ('Australia/Queensland', 'Australia/Queensland'), ('America/Mexico_City', 'America/Mexico_City'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('Europe/Monaco', 'Europe/Monaco'), ('Africa/Lome', 'Africa/Lome'), ('America/Antigua', 'America/Antigua'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Asia/Magadan', 'Asia/Magadan'), ('Asia/Hovd', 'Asia/Hovd'), ('Zulu', 'Zulu'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Antarctica/Troll', 'Antarctica/Troll'), ('America/Toronto', 'America/Toronto'), ('America/Catamarca', 'America/Catamarca'), ('America/Los_Angeles', 'America/Los_Angeles'), ('Europe/Berlin', 'Europe/Berlin'), ('America/Mazatlan', 'America/Mazatlan'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Pacific/Niue', 'Pacific/Niue'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('Australia/South', 'Australia/South'), ('Universal', 'Universal'), ('Asia/Calcutta', 'Asia/Calcutta'), ('America/Metlakatla', 'America/Metlakatla'), ('America/New_York', 'America/New_York'), ('America/Anguilla', 'America/Anguilla'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('Africa/Bamako', 'Africa/Bamako'), ('America/Vancouver', 'America/Vancouver'), ('Indian/Reunion', 'Indian/Reunion'), ('America/St_Johns', 'America/St_Johns'), ('Australia/LHI', 'Australia/LHI'), ('Europe/Guernsey', 'Europe/Guernsey'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('Europe/Prague', 'Europe/Prague'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('America/Eirunepe', 'America/Eirunepe'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Europe/Helsinki', 'Europe/Helsinki'), ('Africa/Maputo', 'Africa/Maputo'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('Indian/Mauritius', 'Indian/Mauritius'), ('Africa/Casablanca', 'Africa/Casablanca'), ('America/Nipigon', 'America/Nipigon'), ('America/Marigot', 'America/Marigot'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('Asia/Kolkata', 'Asia/Kolkata'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('America/Porto_Velho', 'America/Porto_Velho'), ('America/Jujuy', 'America/Jujuy'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('Canada/Atlantic', 'Canada/Atlantic'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Europe/Nicosia', 'Europe/Nicosia'), ('America/Scoresbysund', 'America/Scoresbysund'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Europe/Belgrade', 'Europe/Belgrade'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('America/Fortaleza', 'America/Fortaleza'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('Africa/Luanda', 'Africa/Luanda'), ('Asia/Hebron', 'Asia/Hebron'), ('Australia/ACT', 'Australia/ACT'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('MST', 'MST'), ('Europe/Sofia', 'Europe/Sofia'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Asia/Omsk', 'Asia/Omsk'), ('Turkey', 'Turkey'), ('America/Asuncion', 'America/Asuncion'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('Jamaica', 'Jamaica'), ('America/Lima', 'America/Lima'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('Africa/Bissau', 'Africa/Bissau'), ('America/Guayaquil', 'America/Guayaquil'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Canada/Yukon', 'Canada/Yukon'), ('Egypt', 'Egypt'), ('Asia/Amman', 'Asia/Amman'), ('GB', 'GB'), ('Kwajalein', 'Kwajalein'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('America/Porto_Acre', 'America/Porto_Acre'), ('Asia/Anadyr', 'Asia/Anadyr'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Europe/Kiev', 'Europe/Kiev'), ('Europe/Jersey', 'Europe/Jersey'), ('Europe/Brussels', 'Europe/Brussels'), ('Pacific/Auckland', 'Pacific/Auckland'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Asia/Singapore', 'Asia/Singapore'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('Indian/Maldives', 'Indian/Maldives'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('Asia/Chungking', 'Asia/Chungking'), ('Etc/GMT-9', 'Etc/GMT-9'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('GMT+0', 'GMT+0'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('Etc/GMT+2', 'Etc/GMT+2'), ('Asia/Saigon', 'Asia/Saigon'), ('America/Swift_Current', 'America/Swift_Current'), ('Africa/Douala', 'Africa/Douala'), ('Etc/GMT-14', 'Etc/GMT-14'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('America/Shiprock', 'America/Shiprock'), ('Etc/Greenwich', 'Etc/Greenwich'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('Portugal', 'Portugal'), ('Europe/Tallinn', 'Europe/Tallinn'), ('America/Panama', 'America/Panama'),
                                   ('EST', 'EST'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Etc/GMT-6', 'Etc/GMT-6'), ('America/Sitka', 'America/Sitka'), ('Asia/Baku', 'Asia/Baku'), ('Mexico/General', 'Mexico/General'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Europe/Riga', 'Europe/Riga'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Europe/Volgograd', 'Europe/Volgograd'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('UTC', 'UTC'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('America/Guatemala', 'America/Guatemala'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Africa/Maseru', 'Africa/Maseru'), ('Pacific/Yap', 'Pacific/Yap'), ('America/Boise', 'America/Boise'), ('Africa/Tunis', 'Africa/Tunis'), ('Asia/Qatar', 'Asia/Qatar'), ('Australia/Canberra', 'Australia/Canberra'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('Canada/Central', 'Canada/Central'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('America/Montserrat', 'America/Montserrat'), ('Europe/Simferopol', 'Europe/Simferopol'), ('Asia/Barnaul', 'Asia/Barnaul'), ('America/Nome', 'America/Nome'), ('Asia/Nicosia', 'Asia/Nicosia'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Australia/Sydney', 'Australia/Sydney'), ('Etc/GMT+3', 'Etc/GMT+3'), ('Etc/GMT+10', 'Etc/GMT+10'), ('America/Boa_Vista', 'America/Boa_Vista'), ('Iceland', 'Iceland'), ('America/Whitehorse', 'America/Whitehorse'), ('Europe/Warsaw', 'Europe/Warsaw'), ('Africa/Asmara', 'Africa/Asmara'), ('Europe/Tirane', 'Europe/Tirane'), ('Asia/Macau', 'Asia/Macau'), ('America/Knox_IN', 'America/Knox_IN'), ('America/Winnipeg', 'America/Winnipeg'), ('Europe/Zurich', 'Europe/Zurich'), ('Australia/NSW', 'Australia/NSW'), ('GMT0', 'GMT0'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('Europe/Vienna', 'Europe/Vienna'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Australia/Victoria', 'Australia/Victoria'), ('Africa/Nairobi', 'Africa/Nairobi'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('America/Thule', 'America/Thule'), ('PRC', 'PRC'), ('Etc/GMT-7', 'Etc/GMT-7'), ('America/Pangnirtung', 'America/Pangnirtung'), ('Asia/Colombo', 'Asia/Colombo'), ('Pacific/Johnston', 'Pacific/Johnston'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Europe/Paris', 'Europe/Paris'), ('Antarctica/Casey', 'Antarctica/Casey'), ('Europe/Kirov', 'Europe/Kirov'), ('NZ-CHAT', 'NZ-CHAT'), ('Africa/Lusaka', 'Africa/Lusaka'), ('America/Inuvik', 'America/Inuvik'), ('America/Cancun', 'America/Cancun'), ('Asia/Thimphu', 'Asia/Thimphu'), ('Australia/Currie', 'Australia/Currie'), ('America/Indianapolis', 'America/Indianapolis'), ('Indian/Mayotte', 'Indian/Mayotte'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('Etc/GMT0', 'Etc/GMT0'), ('America/El_Salvador', 'America/El_Salvador'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('America/Menominee', 'America/Menominee'), ('America/Hermosillo', 'America/Hermosillo'), ('Indian/Cocos', 'Indian/Cocos'), ('America/Resolute', 'America/Resolute'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Etc/GMT+11', 'Etc/GMT+11'), ('Etc/Universal', 'Etc/Universal'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('America/Juneau', 'America/Juneau'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('ROC', 'ROC'), ('America/Jamaica', 'America/Jamaica'), ('Eire', 'Eire'), ('Asia/Vientiane', 'Asia/Vientiane'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('Asia/Dhaka', 'Asia/Dhaka'), ('America/Dawson', 'America/Dawson'), ('Pacific/Truk', 'Pacific/Truk'), ('Asia/Dili', 'Asia/Dili'), ('CST6CDT', 'CST6CDT'), ('Etc/GMT+9', 'Etc/GMT+9'), ('America/Tijuana', 'America/Tijuana'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('Australia/Lindeman', 'Australia/Lindeman'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Singapore', 'Singapore'), ('Africa/Mbabane', 'Africa/Mbabane'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Asia/Oral', 'Asia/Oral'), ('US/Central', 'US/Central'), ('Indian/Christmas', 'Indian/Christmas'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('Africa/Freetown', 'Africa/Freetown'), ('Africa/Abidjan', 'Africa/Abidjan'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('Europe/Belfast', 'Europe/Belfast'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('America/Santarem', 'America/Santarem'), ('Asia/Rangoon', 'Asia/Rangoon'), ('America/Kralendijk', 'America/Kralendijk'), ('Pacific/Ponape', 'Pacific/Ponape'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Asia/Famagusta', 'Asia/Famagusta'), ('Europe/Busingen', 'Europe/Busingen'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('Europe/Vatican', 'Europe/Vatican'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Etc/GMT+6', 'Etc/GMT+6'), ('Europe/Kyiv', 'Europe/Kyiv'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Indian/Chagos', 'Indian/Chagos'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('Pacific/Palau', 'Pacific/Palau'), ('Pacific/Fiji', 'Pacific/Fiji'), ('America/Managua', 'America/Managua'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('Africa/Harare', 'Africa/Harare'), ('Africa/Khartoum', 'Africa/Khartoum'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('America/Atka', 'America/Atka'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Pacific/Chatham', 'Pacific/Chatham'), ('America/Virgin', 'America/Virgin'), ('Etc/GMT-4', 'Etc/GMT-4'), ('America/Edmonton', 'America/Edmonton'), ('Africa/Kampala', 'Africa/Kampala'), ('Europe/Dublin', 'Europe/Dublin'), ('America/Santiago', 'America/Santiago'), ('Africa/Conakry', 'Africa/Conakry'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('America/Manaus', 'America/Manaus'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Asia/Kuwait', 'Asia/Kuwait'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('Etc/Zulu', 'Etc/Zulu'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('America/Belize', 'America/Belize'), ('Europe/Podgorica', 'Europe/Podgorica'), ('America/La_Paz', 'America/La_Paz'), ('Africa/Tripoli', 'Africa/Tripoli'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Asia/Shanghai', 'Asia/Shanghai'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('Asia/Brunei', 'Asia/Brunei'), ('Asia/Bahrain', 'Asia/Bahrain'), ('America/Campo_Grande', 'America/Campo_Grande'), ('Atlantic/Azores', 'Atlantic/Azores'), ('America/Cuiaba', 'America/Cuiaba'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('America/Grenada', 'America/Grenada'), ('Europe/Saratov', 'Europe/Saratov'), ('US/Arizona', 'US/Arizona'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('America/Rio_Branco', 'America/Rio_Branco'), ('US/Alaska', 'US/Alaska'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('America/Montreal', 'America/Montreal'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('America/St_Kitts', 'America/St_Kitts'), ('America/Denver', 'America/Denver'), ('Poland', 'Poland'), ('America/Yellowknife', 'America/Yellowknife'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Pacific/Easter', 'Pacific/Easter'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Indian/Comoro', 'Indian/Comoro'), ('Pacific/Guam', 'Pacific/Guam'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('America/Merida', 'America/Merida'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Asia/Harbin', 'Asia/Harbin'), ('America/Iqaluit', 'America/Iqaluit'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Europe/Malta', 'Europe/Malta'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('Etc/GMT-2', 'Etc/GMT-2'), ('Africa/Algiers', 'Africa/Algiers'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Etc/GMT+8', 'Etc/GMT+8'), ('Africa/Cairo', 'Africa/Cairo'), ('America/Maceio', 'America/Maceio'), ('Canada/Eastern', 'Canada/Eastern'), ('Africa/Lagos', 'Africa/Lagos'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('Libya', 'Libya'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('America/Creston', 'America/Creston'), ('Japan', 'Japan'), ('America/Regina', 'America/Regina'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('PST8PDT', 'PST8PDT'), ('America/Aruba', 'America/Aruba'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('Asia/Samarkand', 'Asia/Samarkand'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('Europe/Minsk', 'Europe/Minsk'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Asia/Tashkent', 'Asia/Tashkent'), ('US/Hawaii', 'US/Hawaii'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('America/Araguaina', 'America/Araguaina'), ('CET', 'CET'), ('America/Chicago', 'America/Chicago'), ('Factory', 'Factory'), ('Europe/Zagreb', 'Europe/Zagreb'), ('Asia/Atyrau', 'Asia/Atyrau'), ('Asia/Beirut', 'Asia/Beirut'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Brazil/East', 'Brazil/East'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('US/Aleutian', 'US/Aleutian'), ('Asia/Makassar', 'Asia/Makassar'), ('Etc/GMT-0', 'Etc/GMT-0'), ('Asia/Manila', 'Asia/Manila'), ('Australia/Adelaide', 'Australia/Adelaide'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('Australia/Darwin', 'Australia/Darwin'), ('Europe/San_Marino', 'Europe/San_Marino'), ('America/Mendoza', 'America/Mendoza'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('America/Detroit', 'America/Detroit'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('Pacific/Wake', 'Pacific/Wake'), ('America/Atikokan', 'America/Atikokan'), ('America/Bahia', 'America/Bahia'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Europe/Oslo', 'Europe/Oslo'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('America/Glace_Bay', 'America/Glace_Bay'), ('EET', 'EET'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('Asia/Karachi', 'Asia/Karachi'), ('Brazil/Acre', 'Brazil/Acre'), ('Brazil/West', 'Brazil/West'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('America/Halifax', 'America/Halifax'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('America/Adak', 'America/Adak'), ('Asia/Kashgar', 'Asia/Kashgar'), ('W-SU', 'W-SU'), ('Africa/Ceuta', 'Africa/Ceuta'), ('Asia/Tehran', 'Asia/Tehran'), ('Asia/Aden', 'Asia/Aden'), ('Europe/Chisinau', 'Europe/Chisinau'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('America/Nuuk', 'America/Nuuk'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Asia/Taipei', 'Asia/Taipei'), ('Asia/Baghdad', 'Asia/Baghdad'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('America/Curacao', 'America/Curacao'), ('America/Cayenne', 'America/Cayenne'), ('Africa/Libreville', 'Africa/Libreville'), ('Etc/GMT-13', 'Etc/GMT-13'), ('Etc/GMT+1', 'Etc/GMT+1')], default='Europe/London', max_length=35),
        ),
    ]
