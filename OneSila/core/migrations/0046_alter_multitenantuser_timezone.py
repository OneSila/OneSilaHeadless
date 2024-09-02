# Generated by Django 5.0.2 on 2024-04-10 20:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0045_merge_20240410_1055'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('Australia/Darwin', 'Australia/Darwin'), ('ROC', 'ROC'), ('Asia/Vientiane', 'Asia/Vientiane'), ('America/Rosario', 'America/Rosario'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Africa/Monrovia', 'Africa/Monrovia'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Etc/Zulu', 'Etc/Zulu'), ('America/Araguaina', 'America/Araguaina'), ('America/Grand_Turk', 'America/Grand_Turk'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('America/Campo_Grande', 'America/Campo_Grande'), ('Navajo', 'Navajo'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('Africa/Algiers', 'Africa/Algiers'), ('Africa/Accra', 'Africa/Accra'), ('Asia/Samarkand', 'Asia/Samarkand'), ('Asia/Karachi', 'Asia/Karachi'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('Asia/Bangkok', 'Asia/Bangkok'), ('America/Atka', 'America/Atka'), ('America/Vancouver', 'America/Vancouver'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('Australia/South', 'Australia/South'), ('America/Cuiaba', 'America/Cuiaba'), ('America/Anchorage', 'America/Anchorage'), ('HST', 'HST'), ('Canada/Mountain', 'Canada/Mountain'), ('Asia/Dacca', 'Asia/Dacca'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Africa/Freetown', 'Africa/Freetown'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Africa/Lusaka', 'Africa/Lusaka'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('Europe/Warsaw', 'Europe/Warsaw'), ('US/Eastern', 'US/Eastern'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('America/Belem', 'America/Belem'), ('America/Porto_Acre', 'America/Porto_Acre'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Africa/Harare', 'Africa/Harare'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Canada/Pacific', 'Canada/Pacific'), ('America/Martinique', 'America/Martinique'), ('America/Maceio', 'America/Maceio'), ('America/Godthab', 'America/Godthab'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('Europe/Vatican', 'Europe/Vatican'), ('America/Goose_Bay', 'America/Goose_Bay'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('Pacific/Palau', 'Pacific/Palau'), ('Europe/Paris', 'Europe/Paris'), ('Africa/Gaborone', 'Africa/Gaborone'), ('America/Pangnirtung', 'America/Pangnirtung'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Etc/GMT-10', 'Etc/GMT-10'), ('America/Phoenix', 'America/Phoenix'), ('Europe/Samara', 'Europe/Samara'), ('Africa/Tunis', 'Africa/Tunis'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('America/Recife', 'America/Recife'), ('Asia/Amman', 'Asia/Amman'), ('Asia/Oral', 'Asia/Oral'), ('Africa/Abidjan', 'Africa/Abidjan'), ('Asia/Atyrau', 'Asia/Atyrau'), ('GB-Eire', 'GB-Eire'), ('US/Michigan', 'US/Michigan'), ('Kwajalein', 'Kwajalein'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('Etc/GMT+6', 'Etc/GMT+6'), ('Etc/GMT-0', 'Etc/GMT-0'), ('America/Halifax', 'America/Halifax'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('America/Ojinaga', 'America/Ojinaga'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Africa/Bangui', 'Africa/Bangui'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Europe/Kyiv', 'Europe/Kyiv'), ('Europe/Riga', 'Europe/Riga'), ('Europe/Helsinki', 'Europe/Helsinki'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('Etc/GMT+3', 'Etc/GMT+3'), ('Jamaica', 'Jamaica'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Asia/Aden', 'Asia/Aden'), ('Asia/Riyadh', 'Asia/Riyadh'), ('UCT', 'UCT'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('America/Boise', 'America/Boise'), ('Asia/Harbin', 'Asia/Harbin'), ('Indian/Christmas', 'Indian/Christmas'), ('America/Menominee', 'America/Menominee'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('Etc/GMT+8', 'Etc/GMT+8'), ('America/Bahia', 'America/Bahia'), ('America/Detroit', 'America/Detroit'), ('US/Aleutian', 'US/Aleutian'), ('America/St_Johns', 'America/St_Johns'), ('Etc/GMT-14', 'Etc/GMT-14'), ('America/Virgin', 'America/Virgin'), ('NZ', 'NZ'), ('Singapore', 'Singapore'), ('Etc/GMT-12', 'Etc/GMT-12'), ('Asia/Kolkata', 'Asia/Kolkata'), ('Europe/Nicosia', 'Europe/Nicosia'), ('America/Louisville', 'America/Louisville'), ('America/Metlakatla', 'America/Metlakatla'), ('Atlantic/Canary', 'Atlantic/Canary'), ('America/El_Salvador', 'America/El_Salvador'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Australia/Canberra', 'Australia/Canberra'), ('America/Matamoros', 'America/Matamoros'), ('Asia/Kabul', 'Asia/Kabul'), ('MST7MDT', 'MST7MDT'), ('America/Jamaica', 'America/Jamaica'), ('Etc/GMT-2', 'Etc/GMT-2'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('America/Los_Angeles', 'America/Los_Angeles'), ('Europe/Malta', 'Europe/Malta'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Europe/Belgrade', 'Europe/Belgrade'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Etc/GMT+11', 'Etc/GMT+11'), ('America/Cancun', 'America/Cancun'), ('GMT+0', 'GMT+0'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('America/Mexico_City', 'America/Mexico_City'), ('Europe/Bucharest', 'Europe/Bucharest'), ('Europe/Dublin', 'Europe/Dublin'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Indian/Mayotte', 'Indian/Mayotte'), ('Australia/Eucla', 'Australia/Eucla'), ('Africa/Conakry', 'Africa/Conakry'), ('CET', 'CET'), ('America/Tijuana', 'America/Tijuana'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Australia/West', 'Australia/West'), ('America/Nuuk', 'America/Nuuk'), ('Etc/Greenwich', 'Etc/Greenwich'), ('GB', 'GB'), ('America/Juneau', 'America/Juneau'), ('America/Catamarca', 'America/Catamarca'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Asia/Barnaul', 'Asia/Barnaul'), ('Africa/Bamako', 'Africa/Bamako'), ('Etc/UTC', 'Etc/UTC'), ('America/Rainy_River', 'America/Rainy_River'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('America/Jujuy', 'America/Jujuy'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Etc/GMT+9', 'Etc/GMT+9'), ('US/Central', 'US/Central'), ('America/Mendoza', 'America/Mendoza'), ('America/Belize', 'America/Belize'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('Europe/Monaco', 'Europe/Monaco'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('America/Tortola', 'America/Tortola'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('America/Paramaribo', 'America/Paramaribo'), ('Africa/Lome', 'Africa/Lome'), ('America/Merida', 'America/Merida'), ('America/Shiprock', 'America/Shiprock'), ('Etc/GMT+1', 'Etc/GMT+1'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Asia/Istanbul', 'Asia/Istanbul'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('Asia/Anadyr', 'Asia/Anadyr'), ('Chile/Continental', 'Chile/Continental'), ('Australia/Tasmania', 'Australia/Tasmania'), ('Asia/Jayapura', 'Asia/Jayapura'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('America/Nome', 'America/Nome'), ('ROK', 'ROK'), ('Mexico/General', 'Mexico/General'), ('Europe/Vaduz', 'Europe/Vaduz'), ('WET', 'WET'), ('Asia/Tomsk', 'Asia/Tomsk'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('Australia/NSW', 'Australia/NSW'), ('Asia/Makassar', 'Asia/Makassar'), ('Africa/Dakar', 'Africa/Dakar'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('Asia/Almaty', 'Asia/Almaty'), ('America/Mazatlan', 'America/Mazatlan'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Asia/Baku', 'Asia/Baku'), ('Iceland', 'Iceland'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('Asia/Nicosia', 'Asia/Nicosia'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Asia/Urumqi', 'Asia/Urumqi'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('GMT-0', 'GMT-0'), ('America/Yakutat', 'America/Yakutat'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Asia/Thimbu', 'Asia/Thimbu'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('America/Bogota', 'America/Bogota'), ('Europe/Prague', 'Europe/Prague'), ('Asia/Dubai', 'Asia/Dubai'), ('America/Anguilla', 'America/Anguilla'), ('America/Resolute', 'America/Resolute'), ('America/Thule', 'America/Thule'), ('Europe/Minsk', 'Europe/Minsk'), ('America/Chicago', 'America/Chicago'), ('America/St_Lucia', 'America/St_Lucia'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('US/Arizona', 'US/Arizona'), ('US/Pacific', 'US/Pacific'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Asia/Singapore', 'Asia/Singapore'), ('Australia/Perth', 'Australia/Perth'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('Asia/Macao', 'Asia/Macao'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('Africa/Ceuta', 'Africa/Ceuta'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('GMT0', 'GMT0'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('America/Yellowknife', 'America/Yellowknife'), ('America/Hermosillo', 'America/Hermosillo'), ('PRC', 'PRC'), ('America/Ensenada', 'America/Ensenada'), ('Europe/Belfast', 'Europe/Belfast'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('Africa/Douala', 'Africa/Douala'), ('Asia/Kuwait', 'Asia/Kuwait'), ('Etc/Universal', 'Etc/Universal'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Pacific/Gambier', 'Pacific/Gambier'), ('Australia/LHI', 'Australia/LHI'), ('America/Nassau', 'America/Nassau'), ('Asia/Brunei', 'Asia/Brunei'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('America/Miquelon', 'America/Miquelon'), ('Africa/Cairo', 'Africa/Cairo'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Indian/Mauritius', 'Indian/Mauritius'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Europe/Athens', 'Europe/Athens'), ('Asia/Qatar', 'Asia/Qatar'), ('Etc/GMT+7', 'Etc/GMT+7'), ('Europe/Berlin', 'Europe/Berlin'), ('America/Aruba', 'America/Aruba'), ('Europe/Volgograd', 'Europe/Volgograd'), ('Asia/Hovd', 'Asia/Hovd'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('Africa/Niamey', 'Africa/Niamey'), ('Asia/Magadan', 'Asia/Magadan'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('Africa/Maputo', 'Africa/Maputo'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('America/Havana', 'America/Havana'), ('America/Santiago', 'America/Santiago'), ('Pacific/Chatham', 'Pacific/Chatham'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Etc/GMT+2', 'Etc/GMT+2'), ('Pacific/Niue', 'Pacific/Niue'), ('Europe/Podgorica', 'Europe/Podgorica'), ('America/Porto_Velho', 'America/Porto_Velho'), (
                'Pacific/Efate', 'Pacific/Efate'), ('Asia/Seoul', 'Asia/Seoul'), ('Zulu', 'Zulu'), ('GMT', 'GMT'), ('America/Monterrey', 'America/Monterrey'), ('Africa/Mbabane', 'Africa/Mbabane'), ('Europe/Tallinn', 'Europe/Tallinn'), ('Pacific/Auckland', 'Pacific/Auckland'), ('America/Scoresbysund', 'America/Scoresbysund'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Antarctica/Casey', 'Antarctica/Casey'), ('America/Sitka', 'America/Sitka'), ('Australia/Victoria', 'Australia/Victoria'), ('America/Antigua', 'America/Antigua'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('EST', 'EST'), ('Australia/Adelaide', 'Australia/Adelaide'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('Europe/Madrid', 'Europe/Madrid'), ('Europe/Simferopol', 'Europe/Simferopol'), ('America/Guyana', 'America/Guyana'), ('America/Cayenne', 'America/Cayenne'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Canada/Atlantic', 'Canada/Atlantic'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('Canada/Eastern', 'Canada/Eastern'), ('Europe/Moscow', 'Europe/Moscow'), ('Israel', 'Israel'), ('MET', 'MET'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Universal', 'Universal'), ('America/Marigot', 'America/Marigot'), ('America/Montserrat', 'America/Montserrat'), ('Asia/Manila', 'Asia/Manila'), ('NZ-CHAT', 'NZ-CHAT'), ('America/Fortaleza', 'America/Fortaleza'), ('Etc/GMT-5', 'Etc/GMT-5'), ('America/Denver', 'America/Denver'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('Canada/Yukon', 'Canada/Yukon'), ('America/Rio_Branco', 'America/Rio_Branco'), ('America/Kralendijk', 'America/Kralendijk'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('America/Cayman', 'America/Cayman'), ('America/St_Kitts', 'America/St_Kitts'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('America/Regina', 'America/Regina'), ('Australia/Queensland', 'Australia/Queensland'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('PST8PDT', 'PST8PDT'), ('Asia/Saigon', 'Asia/Saigon'), ('Europe/Chisinau', 'Europe/Chisinau'), ('America/New_York', 'America/New_York'), ('America/Cordoba', 'America/Cordoba'), ('Africa/Malabo', 'Africa/Malabo'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('Etc/GMT-1', 'Etc/GMT-1'), ('America/Montreal', 'America/Montreal'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('America/Boa_Vista', 'America/Boa_Vista'), ('Africa/Asmara', 'Africa/Asmara'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('Cuba', 'Cuba'), ('Africa/Juba', 'Africa/Juba'), ('America/Guadeloupe', 'America/Guadeloupe'), ('Indian/Mahe', 'Indian/Mahe'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Pacific/Truk', 'Pacific/Truk'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Africa/Asmera', 'Africa/Asmera'), ('Canada/Central', 'Canada/Central'), ('Japan', 'Japan'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('America/Santarem', 'America/Santarem'), ('America/Toronto', 'America/Toronto'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('Europe/Skopje', 'Europe/Skopje'), ('EST5EDT', 'EST5EDT'), ('America/Guayaquil', 'America/Guayaquil'), ('Asia/Omsk', 'Asia/Omsk'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('America/Inuvik', 'America/Inuvik'), ('Asia/Taipei', 'Asia/Taipei'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('Europe/Stockholm', 'Europe/Stockholm'), ('America/Noronha', 'America/Noronha'), ('Europe/Budapest', 'Europe/Budapest'), ('Australia/North', 'Australia/North'), ('America/Manaus', 'America/Manaus'), ('US/Alaska', 'US/Alaska'), ('America/Atikokan', 'America/Atikokan'), ('America/Edmonton', 'America/Edmonton'), ('America/Nipigon', 'America/Nipigon'), ('Asia/Colombo', 'Asia/Colombo'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('America/Indianapolis', 'America/Indianapolis'), ('US/Samoa', 'US/Samoa'), ('America/Caracas', 'America/Caracas'), ('America/Whitehorse', 'America/Whitehorse'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('America/Barbados', 'America/Barbados'), ('Indian/Maldives', 'Indian/Maldives'), ('Asia/Chungking', 'Asia/Chungking'), ('Etc/GMT-11', 'Etc/GMT-11'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('Factory', 'Factory'), ('Asia/Muscat', 'Asia/Muscat'), ('Europe/London', 'Europe/London'), ('America/Adak', 'America/Adak'), ('America/La_Paz', 'America/La_Paz'), ('America/Winnipeg', 'America/Winnipeg'), ('Africa/Kigali', 'Africa/Kigali'), ('Pacific/Easter', 'Pacific/Easter'), ('W-SU', 'W-SU'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('Asia/Dili', 'Asia/Dili'), ('Hongkong', 'Hongkong'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Etc/GMT', 'Etc/GMT'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('Asia/Kuching', 'Asia/Kuching'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('Etc/GMT-4', 'Etc/GMT-4'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Pacific/Samoa', 'Pacific/Samoa'), ('America/Asuncion', 'America/Asuncion'), ('America/Grenada', 'America/Grenada'), ('Asia/Beirut', 'Asia/Beirut'), ('Europe/Oslo', 'Europe/Oslo'), ('Europe/Sofia', 'Europe/Sofia'), ('Africa/Luanda', 'Africa/Luanda'), ('build/etc/localtime', 'build/etc/localtime'), ('US/East-Indiana', 'US/East-Indiana'), ('Etc/GMT+5', 'Etc/GMT+5'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('Pacific/Yap', 'Pacific/Yap'), ('Pacific/Majuro', 'Pacific/Majuro'), ('Etc/UCT', 'Etc/UCT'), ('Africa/Kampala', 'Africa/Kampala'), ('Australia/Hobart', 'Australia/Hobart'), ('Etc/GMT-3', 'Etc/GMT-3'), ('Asia/Yangon', 'Asia/Yangon'), ('Etc/GMT+10', 'Etc/GMT+10'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('Etc/GMT0', 'Etc/GMT0'), ('Europe/Zagreb', 'Europe/Zagreb'), ('Africa/Bissau', 'Africa/Bissau'), ('Pacific/Apia', 'Pacific/Apia'), ('Europe/Andorra', 'Europe/Andorra'), ('Eire', 'Eire'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('Asia/Chita', 'Asia/Chita'), ('America/Dawson', 'America/Dawson'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('Europe/Jersey', 'Europe/Jersey'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Europe/Kiev', 'Europe/Kiev'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Turkey', 'Turkey'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('Asia/Famagusta', 'Asia/Famagusta'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Europe/Tirane', 'Europe/Tirane'), ('Asia/Hebron', 'Asia/Hebron'), ('Asia/Macau', 'Asia/Macau'), ('Pacific/Wake', 'Pacific/Wake'), ('America/Moncton', 'America/Moncton'), ('Europe/San_Marino', 'Europe/San_Marino'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('America/Knox_IN', 'America/Knox_IN'), ('Asia/Jakarta', 'Asia/Jakarta'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('Asia/Rangoon', 'Asia/Rangoon'), ('EET', 'EET'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Indian/Cocos', 'Indian/Cocos'), ('US/Hawaii', 'US/Hawaii'), ('Brazil/Acre', 'Brazil/Acre'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Asia/Kashgar', 'Asia/Kashgar'), ('Africa/Libreville', 'Africa/Libreville'), ('America/Creston', 'America/Creston'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Portugal', 'Portugal'), ('Africa/Tripoli', 'Africa/Tripoli'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('Libya', 'Libya'), ('CST6CDT', 'CST6CDT'), ('Pacific/Ponape', 'Pacific/Ponape'), ('Africa/Lagos', 'Africa/Lagos'), ('Europe/Bratislava', 'Europe/Bratislava'), ('America/Iqaluit', 'America/Iqaluit'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('America/St_Thomas', 'America/St_Thomas'), ('Etc/GMT-6', 'Etc/GMT-6'), ('America/Panama', 'America/Panama'), ('Asia/Baghdad', 'Asia/Baghdad'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('Australia/Currie', 'Australia/Currie'), ('Greenwich', 'Greenwich'), ('Europe/Vienna', 'Europe/Vienna'), ('Europe/Zurich', 'Europe/Zurich'), ('Indian/Chagos', 'Indian/Chagos'), ('Pacific/Guam', 'Pacific/Guam'), ('Asia/Bahrain', 'Asia/Bahrain'), ('America/Swift_Current', 'America/Swift_Current'), ('Europe/Rome', 'Europe/Rome'), ('Brazil/West', 'Brazil/West'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Etc/GMT-9', 'Etc/GMT-9'), ('Europe/Brussels', 'Europe/Brussels'), ('America/St_Vincent', 'America/St_Vincent'), ('Indian/Reunion', 'Indian/Reunion'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('US/Mountain', 'US/Mountain'), ('America/Lower_Princes', 'America/Lower_Princes'), ('Iran', 'Iran'), ('America/Chihuahua', 'America/Chihuahua'), ('America/Montevideo', 'America/Montevideo'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('Australia/ACT', 'Australia/ACT'), ('Africa/Casablanca', 'Africa/Casablanca'), ('Poland', 'Poland'), ('Europe/Saratov', 'Europe/Saratov'), ('Asia/Tehran', 'Asia/Tehran'), ('Australia/Sydney', 'Australia/Sydney'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('Pacific/Wallis', 'Pacific/Wallis'), ('Asia/Thimphu', 'Asia/Thimphu'), ('UTC', 'UTC'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('Egypt', 'Egypt'), ('Pacific/Johnston', 'Pacific/Johnston'), ('America/Managua', 'America/Managua'), ('MST', 'MST'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Africa/Nairobi', 'Africa/Nairobi'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('America/Guatemala', 'America/Guatemala'), ('America/Eirunepe', 'America/Eirunepe'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('Pacific/Midway', 'Pacific/Midway'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Etc/GMT+0', 'Etc/GMT+0'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('Asia/Yerevan', 'Asia/Yerevan'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('Indian/Comoro', 'Indian/Comoro'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('America/Lima', 'America/Lima'), ('Europe/Busingen', 'Europe/Busingen'), ('America/Curacao', 'America/Curacao'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('Africa/Khartoum', 'Africa/Khartoum'), ('Etc/GMT-13', 'Etc/GMT-13'), ('America/Dominica', 'America/Dominica'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Asia/Damascus', 'Asia/Damascus'), ('Africa/Banjul', 'Africa/Banjul'), ('Brazil/East', 'Brazil/East'), ('Europe/Kirov', 'Europe/Kirov'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Asia/Gaza', 'Asia/Gaza'), ('Africa/Maseru', 'Africa/Maseru')], default='Europe/London', max_length=35),
        ),
    ]
