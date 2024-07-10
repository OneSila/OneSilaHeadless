# Generated by Django 5.0.2 on 2024-06-16 18:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0104_alter_multitenantuser_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('America/Cuiaba', 'America/Cuiaba'), ('America/Matamoros', 'America/Matamoros'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('America/Antigua', 'America/Antigua'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('America/Martinique', 'America/Martinique'), ('Libya', 'Libya'), ('ROC', 'ROC'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Europe/Oslo', 'Europe/Oslo'), ('Pacific/Johnston', 'Pacific/Johnston'), ('Asia/Seoul', 'Asia/Seoul'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Pacific/Apia', 'Pacific/Apia'), ('Etc/GMT+9', 'Etc/GMT+9'), ('Portugal', 'Portugal'), ('ROK', 'ROK'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('Africa/Nairobi', 'Africa/Nairobi'), ('America/Chicago', 'America/Chicago'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('America/New_York', 'America/New_York'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('EST', 'EST'), ('Japan', 'Japan'), ('Pacific/Yap', 'Pacific/Yap'), ('Pacific/Wallis', 'Pacific/Wallis'), ('America/Atikokan', 'America/Atikokan'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Asia/Brunei', 'Asia/Brunei'), ('Etc/GMT+5', 'Etc/GMT+5'), ('America/Inuvik', 'America/Inuvik'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('America/Atka', 'America/Atka'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Europe/Paris', 'Europe/Paris'), ('Indian/Cocos', 'Indian/Cocos'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Etc/GMT-14', 'Etc/GMT-14'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Chile/Continental', 'Chile/Continental'), ('Etc/GMT-9', 'Etc/GMT-9'), ('Asia/Gaza', 'Asia/Gaza'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('America/Mendoza', 'America/Mendoza'), ('Etc/GMT+8', 'Etc/GMT+8'), ('GMT+0', 'GMT+0'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Africa/Tunis', 'Africa/Tunis'), ('Europe/Saratov', 'Europe/Saratov'), ('Etc/UTC', 'Etc/UTC'), ('Israel', 'Israel'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Indian/Mahe', 'Indian/Mahe'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('Africa/Juba', 'Africa/Juba'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('Africa/Bissau', 'Africa/Bissau'), ('America/Iqaluit', 'America/Iqaluit'), ('America/Grand_Turk', 'America/Grand_Turk'), ('Asia/Beirut', 'Asia/Beirut'), ('America/Porto_Acre', 'America/Porto_Acre'), ('Africa/Accra', 'Africa/Accra'), ('Antarctica/Casey', 'Antarctica/Casey'), ('America/Thule', 'America/Thule'), ('America/Anguilla', 'America/Anguilla'), ('Indian/Mayotte', 'Indian/Mayotte'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('Pacific/Truk', 'Pacific/Truk'), ('America/Edmonton', 'America/Edmonton'), ('America/Los_Angeles', 'America/Los_Angeles'), ('Indian/Comoro', 'Indian/Comoro'), ('Australia/Canberra', 'Australia/Canberra'), ('Asia/Thimphu', 'Asia/Thimphu'), ('Singapore', 'Singapore'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('America/Montreal', 'America/Montreal'), ('Etc/GMT0', 'Etc/GMT0'), ('America/Maceio', 'America/Maceio'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Iceland', 'Iceland'), ('Hongkong', 'Hongkong'), ('Africa/Khartoum', 'Africa/Khartoum'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('America/Curacao', 'America/Curacao'), ('America/Catamarca', 'America/Catamarca'), ('Australia/Eucla', 'Australia/Eucla'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('Europe/Tirane', 'Europe/Tirane'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Africa/Cairo', 'Africa/Cairo'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Africa/Mbabane', 'Africa/Mbabane'), ('America/Belize', 'America/Belize'), ('America/Scoresbysund', 'America/Scoresbysund'), ('Etc/GMT+2', 'Etc/GMT+2'), ('Poland', 'Poland'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('America/Jujuy', 'America/Jujuy'), ('America/Bogota', 'America/Bogota'), ('America/Porto_Velho', 'America/Porto_Velho'), ('America/Ojinaga', 'America/Ojinaga'), ('America/Creston', 'America/Creston'), ('Africa/Libreville', 'Africa/Libreville'), ('Pacific/Auckland', 'Pacific/Auckland'), ('America/Virgin', 'America/Virgin'), ('America/St_Vincent', 'America/St_Vincent'), ('US/Arizona', 'US/Arizona'), ('America/Rainy_River', 'America/Rainy_River'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('US/Aleutian', 'US/Aleutian'), ('Etc/GMT-6', 'Etc/GMT-6'), ('Africa/Lome', 'Africa/Lome'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('Europe/San_Marino', 'Europe/San_Marino'), ('Africa/Monrovia', 'Africa/Monrovia'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('Asia/Kashgar', 'Asia/Kashgar'), ('America/Managua', 'America/Managua'), ('Asia/Dacca', 'Asia/Dacca'), ('Africa/Tripoli', 'Africa/Tripoli'), ('Mexico/General', 'Mexico/General'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('Africa/Malabo', 'Africa/Malabo'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('US/Eastern', 'US/Eastern'), ('W-SU', 'W-SU'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('Etc/GMT-13', 'Etc/GMT-13'), ('America/Santiago', 'America/Santiago'), ('America/Miquelon', 'America/Miquelon'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Australia/ACT', 'Australia/ACT'), ('America/Juneau', 'America/Juneau'), ('America/Montevideo', 'America/Montevideo'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('Asia/Thimbu', 'Asia/Thimbu'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('Europe/Volgograd', 'Europe/Volgograd'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('Africa/Luanda', 'Africa/Luanda'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('Asia/Hebron', 'Asia/Hebron'), ('UCT', 'UCT'), ('Etc/Universal', 'Etc/Universal'), ('Europe/Athens', 'Europe/Athens'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Asia/Singapore', 'Asia/Singapore'), ('Asia/Kuching', 'Asia/Kuching'), ('Europe/Simferopol', 'Europe/Simferopol'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('America/Guyana', 'America/Guyana'), ('Australia/Currie', 'Australia/Currie'), ('Pacific/Chatham', 'Pacific/Chatham'), ('Africa/Freetown', 'Africa/Freetown'), ('America/Lima', 'America/Lima'), ('America/Asuncion', 'America/Asuncion'), ('US/Alaska', 'US/Alaska'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('Jamaica', 'Jamaica'), ('America/Montserrat', 'America/Montserrat'), ('Europe/Jersey', 'Europe/Jersey'), ('Etc/GMT+7', 'Etc/GMT+7'), ('America/Recife', 'America/Recife'), ('Europe/Nicosia', 'Europe/Nicosia'), ('Greenwich', 'Greenwich'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Europe/Belfast', 'Europe/Belfast'), ('Europe/Dublin', 'Europe/Dublin'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Etc/GMT-4', 'Etc/GMT-4'), ('Europe/Skopje', 'Europe/Skopje'), ('Africa/Algiers', 'Africa/Algiers'), ('Europe/Tallinn', 'Europe/Tallinn'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('MET', 'MET'), ('Australia/Adelaide', 'Australia/Adelaide'), ('America/Mazatlan', 'America/Mazatlan'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('Indian/Chagos', 'Indian/Chagos'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('US/Central', 'US/Central'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Europe/Belgrade', 'Europe/Belgrade'), ('PRC', 'PRC'), ('Asia/Baku', 'Asia/Baku'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('Australia/Queensland', 'Australia/Queensland'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('Europe/Chisinau', 'Europe/Chisinau'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('Etc/GMT-1', 'Etc/GMT-1'), ('America/Paramaribo', 'America/Paramaribo'), ('America/Manaus', 'America/Manaus'), ('Asia/Magadan', 'Asia/Magadan'), ('Europe/Sofia', 'Europe/Sofia'), ('America/Merida', 'America/Merida'), ('Asia/Dubai', 'Asia/Dubai'), ('Africa/Lusaka', 'Africa/Lusaka'), ('America/Yellowknife', 'America/Yellowknife'), ('WET', 'WET'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Pacific/Gambier', 'Pacific/Gambier'), ('America/Havana', 'America/Havana'), ('Etc/GMT-10', 'Etc/GMT-10'), ('Africa/Banjul', 'Africa/Banjul'), ('Asia/Vientiane', 'Asia/Vientiane'), ('America/Campo_Grande', 'America/Campo_Grande'), ('GMT-0', 'GMT-0'), ('Europe/Busingen', 'Europe/Busingen'), ('Etc/GMT-3', 'Etc/GMT-3'), ('Asia/Barnaul', 'Asia/Barnaul'), ('Etc/GMT+3', 'Etc/GMT+3'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('America/St_Thomas', 'America/St_Thomas'), ('America/Winnipeg', 'America/Winnipeg'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('Asia/Chita', 'Asia/Chita'), ('America/Godthab', 'America/Godthab'), ('America/Adak', 'America/Adak'), ('Etc/GMT-0', 'Etc/GMT-0'), ('Asia/Atyrau', 'Asia/Atyrau'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Europe/Vienna', 'Europe/Vienna'), ('Asia/Aden', 'Asia/Aden'), ('America/Guatemala', 'America/Guatemala'), ('Indian/Mauritius', 'Indian/Mauritius'), ('Pacific/Easter', 'Pacific/Easter'), ('Iran', 'Iran'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('Etc/GMT+1', 'Etc/GMT+1'), ('US/Samoa', 'US/Samoa'), ('America/Metlakatla', 'America/Metlakatla'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Europe/Vatican', 'Europe/Vatican'), ('America/Ensenada', 'America/Ensenada'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Asia/Manila', 'Asia/Manila'), ('GB-Eire', 'GB-Eire'), ('America/Aruba', 'America/Aruba'), ('America/Jamaica', 'America/Jamaica'), ('Asia/Taipei', 'Asia/Taipei'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Factory', 'Factory'), ('America/Tijuana', 'America/Tijuana'), ('Africa/Ceuta', 'Africa/Ceuta'), ('Asia/Saigon', 'Asia/Saigon'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('America/St_Lucia', 'America/St_Lucia'), ('Europe/Budapest', 'Europe/Budapest'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('America/Belem', 'America/Belem'), ('Australia/West', 'Australia/West'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Europe/Berlin', 'Europe/Berlin'), ('Africa/Kampala', 'Africa/Kampala'), ('America/Moncton', 'America/Moncton'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('CET', 'CET'), ('Europe/Kyiv', 'Europe/Kyiv'), ('Asia/Oral', 'Asia/Oral'), ('Etc/GMT-11', 'Etc/GMT-11'), ('America/Hermosillo', 'America/Hermosillo'), ('Navajo', 'Navajo'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('America/Sitka', 'America/Sitka'), ('Indian/Christmas', 'Indian/Christmas'), ('America/La_Paz', 'America/La_Paz'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Europe/Andorra', 'Europe/Andorra'), ('Australia/Hobart', 'Australia/Hobart'), ('America/Lower_Princes', 'America/Lower_Princes'), ('Australia/Perth', 'Australia/Perth'), ('Europe/Riga', 'Europe/Riga'), ('Europe/Prague', 'Europe/Prague'), ('Asia/Macau', 'Asia/Macau'), ('America/Monterrey', 'America/Monterrey'), ('Atlantic/Azores', 'Atlantic/Azores'), ('America/Menominee', 'America/Menominee'), ('America/Nome', 'America/Nome'), ('Asia/Nicosia', 'Asia/Nicosia'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('America/Nuuk', 'America/Nuuk'), ('America/Goose_Bay', 'America/Goose_Bay'), ('Asia/Kolkata', 'Asia/Kolkata'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Etc/GMT+10', 'Etc/GMT+10'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('Asia/Hovd', 'Asia/Hovd'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('America/Araguaina', 'America/Araguaina'), ('Asia/Rangoon', 'Asia/Rangoon'), ('Eire', 'Eire'), ('Atlantic/Canary', 'Atlantic/Canary'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('US/Pacific', 'US/Pacific'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Indian/Maldives', 'Indian/Maldives'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Europe/Rome', 'Europe/Rome'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('America/Cancun', 'America/Cancun'), ('Asia/Almaty', 'Asia/Almaty'), ('Europe/Guernsey', 'Europe/Guernsey'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('Africa/Bangui', 'Africa/Bangui'), ('Asia/Makassar', 'Asia/Makassar'), ('Europe/Monaco', 'Europe/Monaco'), ('America/Caracas', 'America/Caracas'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('America/Vancouver', 'America/Vancouver'), ('Canada/Yukon', 'Canada/Yukon'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('America/Pangnirtung', 'America/Pangnirtung'), ('Africa/Lagos', 'Africa/Lagos'), ('Canada/Pacific', 'Canada/Pacific'), ('America/Phoenix', 'America/Phoenix'), ('Australia/North', 'Australia/North'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('America/Cayenne', 'America/Cayenne'), ('MST', 'MST'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Pacific/Niue', 'Pacific/Niue'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('America/Whitehorse', 'America/Whitehorse'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Etc/UCT', 'Etc/UCT'), ('Africa/Douala', 'Africa/Douala'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Europe/Kirov', 'Europe/Kirov'), ('Europe/Helsinki', 'Europe/Helsinki'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('UTC', 'UTC'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('Europe/Minsk', 'Europe/Minsk'), ('Etc/GMT+0', 'Etc/GMT+0'), ('Africa/Bamako', 'Africa/Bamako'), ('Africa/Djibouti', 'Africa/Djibouti'), ('CST6CDT', 'CST6CDT'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('America/Nassau', 'America/Nassau'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Australia/Tasmania', 'Australia/Tasmania'), ('Pacific/Majuro', 'Pacific/Majuro'), ('Australia/Sydney', 'Australia/Sydney'), ('Asia/Urumqi', 'Asia/Urumqi'), ('America/Chihuahua', 'America/Chihuahua'), ('Asia/Harbin', 'Asia/Harbin'), ('Europe/Warsaw', 'Europe/Warsaw'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('America/Panama', 'America/Panama'), ('America/Rosario', 'America/Rosario'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Etc/GMT-2', 'Etc/GMT-2'), ('Europe/Kiev', 'Europe/Kiev'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Brazil/West', 'Brazil/West'), ('Africa/Niamey', 'Africa/Niamey'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Asia/Dili', 'Asia/Dili'), ('Asia/Tehran', 'Asia/Tehran'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('Africa/Abidjan', 'Africa/Abidjan'), ('America/Guayaquil', 'America/Guayaquil'), ('Egypt', 'Egypt'), ('Canada/Central', 'Canada/Central'), ('Asia/Jakarta', 'Asia/Jakarta'), ('America/Santarem', 'America/Santarem'), ('America/Barbados', 'America/Barbados'), ('America/Louisville', 'America/Louisville'), ('America/Tortola', 'America/Tortola'), ('Africa/Maseru', 'Africa/Maseru'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Canada/Eastern', 'Canada/Eastern'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('US/Michigan', 'US/Michigan'), ('Europe/Podgorica', 'Europe/Podgorica'), ('Pacific/Wake', 'Pacific/Wake'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Europe/Zurich', 'Europe/Zurich'), ('America/Cayman', 'America/Cayman'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Asia/Muscat', 'Asia/Muscat'), ('build/etc/localtime', 'build/etc/localtime'), ('Asia/Karachi', 'Asia/Karachi'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('Europe/Lisbon', 'Europe/Lisbon'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('America/Grenada', 'America/Grenada'), ('EST5EDT', 'EST5EDT'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('Universal', 'Universal'), ('Cuba', 'Cuba'), ('America/Anchorage', 'America/Anchorage'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Pacific/Palau', 'Pacific/Palau'), ('Pacific/Midway', 'Pacific/Midway'), ('America/Regina', 'America/Regina'), ('Asia/Bahrain', 'Asia/Bahrain'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('Europe/Samara', 'Europe/Samara'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('GMT0', 'GMT0'), ('America/Halifax', 'America/Halifax'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('Brazil/East', 'Brazil/East'), ('America/Eirunepe', 'America/Eirunepe'), ('Asia/Jayapura', 'Asia/Jayapura'), ('America/Noronha', 'America/Noronha'), ('America/Cordoba', 'America/Cordoba'), ('Asia/Yangon', 'Asia/Yangon'), ('Asia/Kuwait', 'Asia/Kuwait'), ('Asia/Riyadh', 'Asia/Riyadh'), ('Asia/Tashkent', 'Asia/Tashkent'), ('NZ', 'NZ'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('Africa/Casablanca', 'Africa/Casablanca'), ('Asia/Istanbul', 'Asia/Istanbul'), ('Asia/Anadyr', 'Asia/Anadyr'), ('America/Dawson', 'America/Dawson'), ('Kwajalein', 'Kwajalein'), ('Australia/NSW', 'Australia/NSW'), ('Asia/Kabul', 'Asia/Kabul'), ('America/Shiprock', 'America/Shiprock'), ('America/St_Kitts', 'America/St_Kitts'), ('GB', 'GB'), ('Canada/Mountain', 'Canada/Mountain'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Africa/Asmara', 'Africa/Asmara'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('America/Indianapolis', 'America/Indianapolis'), ('Australia/LHI', 'Australia/LHI'), ('Africa/Kigali', 'Africa/Kigali'), ('MST7MDT', 'MST7MDT'), ('Asia/Damascus', 'Asia/Damascus'), ('Australia/South', 'Australia/South'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('Europe/Malta', 'Europe/Malta'), ('Asia/Amman', 'Asia/Amman'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('Turkey', 'Turkey'), ('NZ-CHAT', 'NZ-CHAT'), ('Europe/London', 'Europe/London'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('America/St_Johns', 'America/St_Johns'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Africa/Dakar', 'Africa/Dakar'), ('Asia/Chungking', 'Asia/Chungking'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('America/Rio_Branco', 'America/Rio_Branco'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('America/Bahia', 'America/Bahia'), ('Africa/Gaborone', 'Africa/Gaborone'), ('America/Nipigon', 'America/Nipigon'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('Australia/Darwin', 'Australia/Darwin'), ('America/Detroit', 'America/Detroit'), ('Europe/Zagreb', 'Europe/Zagreb'), ('America/Boa_Vista', 'America/Boa_Vista'), ('Africa/Harare', 'Africa/Harare'), ('America/Dominica', 'America/Dominica'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Africa/Maputo', 'Africa/Maputo'), ('Zulu', 'Zulu'), ('Europe/Moscow', 'Europe/Moscow'), ('America/Kralendijk', 'America/Kralendijk'), ('GMT', 'GMT'), ('Asia/Famagusta', 'Asia/Famagusta'), ('America/Resolute', 'America/Resolute'), ('Pacific/Ponape', 'Pacific/Ponape'), ('Brazil/Acre', 'Brazil/Acre'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('Asia/Qatar', 'Asia/Qatar'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('Asia/Macao', 'Asia/Macao'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('Etc/Greenwich', 'Etc/Greenwich'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('America/Fortaleza', 'America/Fortaleza'), ('Europe/Bucharest', 'Europe/Bucharest'), ('Etc/Zulu', 'Etc/Zulu'), ('Etc/GMT', 'Etc/GMT'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Africa/Conakry', 'Africa/Conakry'), ('America/El_Salvador', 'America/El_Salvador'), ('America/Swift_Current', 'America/Swift_Current'), ('Europe/Vaduz', 'Europe/Vaduz'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('America/Mexico_City', 'America/Mexico_City'), ('US/East-Indiana', 'US/East-Indiana'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('Etc/GMT+6', 'Etc/GMT+6'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('Indian/Reunion', 'Indian/Reunion'), ('US/Mountain', 'US/Mountain'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('EET', 'EET'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('US/Hawaii', 'US/Hawaii'), ('Etc/GMT-12', 'Etc/GMT-12'), ('Pacific/Efate', 'Pacific/Efate'), ('PST8PDT', 'PST8PDT'), ('HST', 'HST'), ('America/Marigot', 'America/Marigot'), ('Pacific/Guam', 'Pacific/Guam'), ('Australia/Victoria', 'Australia/Victoria'), ('Europe/Madrid', 'Europe/Madrid'), ('Etc/GMT+11', 'Etc/GMT+11'), ('America/Denver', 'America/Denver'), ('Canada/Atlantic', 'Canada/Atlantic'), ('America/Yakutat', 'America/Yakutat'), ('Africa/Asmera', 'Africa/Asmera'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('America/Guadeloupe', 'America/Guadeloupe'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Asia/Bangkok', 'Asia/Bangkok'), ('Asia/Omsk', 'Asia/Omsk'), ('America/Boise', 'America/Boise'), ('Europe/Brussels', 'Europe/Brussels'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('Asia/Baghdad', 'Asia/Baghdad'), ('America/Toronto', 'America/Toronto'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Asia/Colombo', 'Asia/Colombo'), ('Asia/Samarkand', 'Asia/Samarkand'), ('America/Knox_IN', 'America/Knox_IN'), ('Atlantic/Stanley', 'Atlantic/Stanley')], default='Europe/London', max_length=35),
        ),
    ]