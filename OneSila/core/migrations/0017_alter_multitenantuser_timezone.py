# Generated by Django 4.2.9 on 2024-02-20 15:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_alter_multitenantuser_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('Africa/Lagos', 'Africa/Lagos'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('Australia/NSW', 'Australia/NSW'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('Asia/Muscat', 'Asia/Muscat'), ('Europe/Busingen', 'Europe/Busingen'), ('Africa/Tunis', 'Africa/Tunis'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('America/Guatemala', 'America/Guatemala'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Europe/Monaco', 'Europe/Monaco'), ('Europe/Belfast', 'Europe/Belfast'), ('America/Boa_Vista', 'America/Boa_Vista'), ('Africa/Bangui', 'Africa/Bangui'), ('America/Rosario', 'America/Rosario'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('America/Cayenne', 'America/Cayenne'), ('Asia/Kuwait', 'Asia/Kuwait'), ('Asia/Colombo', 'Asia/Colombo'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('America/Boise', 'America/Boise'), ('America/Recife', 'America/Recife'), ('America/Atikokan', 'America/Atikokan'), ('Asia/Brunei', 'Asia/Brunei'), ('America/Guayaquil', 'America/Guayaquil'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('Asia/Taipei', 'Asia/Taipei'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('Asia/Samarkand', 'Asia/Samarkand'), ('Europe/Warsaw', 'Europe/Warsaw'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Asia/Macau', 'Asia/Macau'), ('Asia/Qatar', 'Asia/Qatar'), ('Africa/Nairobi', 'Africa/Nairobi'), ('Etc/GMT+5', 'Etc/GMT+5'), ('America/Jamaica', 'America/Jamaica'), ('Europe/Podgorica', 'Europe/Podgorica'), ('America/Nome', 'America/Nome'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('America/Lima', 'America/Lima'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Africa/Lusaka', 'Africa/Lusaka'), ('Asia/Istanbul', 'Asia/Istanbul'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('Australia/Melbourne', 'Australia/Melbourne'), ('MST7MDT', 'MST7MDT'), ('Africa/Tripoli', 'Africa/Tripoli'), ('America/Montreal', 'America/Montreal'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('Asia/Atyrau', 'Asia/Atyrau'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('America/Creston', 'America/Creston'), ('America/Indianapolis', 'America/Indianapolis'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('America/Managua', 'America/Managua'), ('America/Noronha', 'America/Noronha'), ('Australia/Hobart', 'Australia/Hobart'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Europe/Berlin', 'Europe/Berlin'), ('Europe/San_Marino', 'Europe/San_Marino'), ('America/Araguaina', 'America/Araguaina'), ('Antarctica/Davis', 'Antarctica/Davis'), ('America/Campo_Grande', 'America/Campo_Grande'), ('America/Monterrey', 'America/Monterrey'), ('Etc/GMT-3', 'Etc/GMT-3'), ('America/Eirunepe', 'America/Eirunepe'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('America/Yellowknife', 'America/Yellowknife'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Europe/London', 'Europe/London'), ('Pacific/Chatham', 'Pacific/Chatham'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Europe/Vienna', 'Europe/Vienna'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('Africa/Algiers', 'Africa/Algiers'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Australia/Victoria', 'Australia/Victoria'), ('Etc/GMT+3', 'Etc/GMT+3'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Indian/Reunion', 'Indian/Reunion'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Kwajalein', 'Kwajalein'), ('America/Montserrat', 'America/Montserrat'), ('Europe/Kyiv', 'Europe/Kyiv'), ('Africa/Kigali', 'Africa/Kigali'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('America/Bahia', 'America/Bahia'), ('Europe/Saratov', 'Europe/Saratov'), ('Pacific/Apia', 'Pacific/Apia'), ('Egypt', 'Egypt'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('America/St_Kitts', 'America/St_Kitts'), ('Pacific/Palau', 'Pacific/Palau'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('America/Aruba', 'America/Aruba'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('CET', 'CET'), ('Asia/Thimbu', 'Asia/Thimbu'), ('America/Martinique', 'America/Martinique'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('America/Tortola', 'America/Tortola'), ('America/Matamoros', 'America/Matamoros'), ('Europe/Kirov', 'Europe/Kirov'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('Europe/Istanbul', 'Europe/Istanbul'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('Europe/Prague', 'Europe/Prague'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Asia/Jayapura', 'Asia/Jayapura'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Etc/GMT-1', 'Etc/GMT-1'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('Pacific/Easter', 'Pacific/Easter'), ('America/Thule', 'America/Thule'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Europe/Zagreb', 'Europe/Zagreb'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('Europe/Paris', 'Europe/Paris'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('US/East-Indiana', 'US/East-Indiana'), ('America/Mexico_City', 'America/Mexico_City'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Etc/GMT-13', 'Etc/GMT-13'), ('Etc/GMT-12', 'Etc/GMT-12'), ('Africa/Conakry', 'Africa/Conakry'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('Africa/Gaborone', 'Africa/Gaborone'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Pacific/Yap', 'Pacific/Yap'), ('America/Juneau', 'America/Juneau'), ('Africa/Monrovia', 'Africa/Monrovia'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('Africa/Lome', 'Africa/Lome'), ('Canada/Pacific', 'Canada/Pacific'), ('Africa/Cairo', 'Africa/Cairo'), ('Canada/Yukon', 'Canada/Yukon'), ('America/Shiprock', 'America/Shiprock'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('America/Guyana', 'America/Guyana'), ('Europe/Athens', 'Europe/Athens'), ('America/New_York', 'America/New_York'), ('WET', 'WET'), ('Pacific/Kanton', 'Pacific/Kanton'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Indian/Mauritius', 'Indian/Mauritius'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Eire', 'Eire'), ('America/Nassau', 'America/Nassau'), ('Australia/Currie', 'Australia/Currie'), ('America/Havana', 'America/Havana'), ('America/Manaus', 'America/Manaus'), ('Asia/Riyadh', 'Asia/Riyadh'), ('Etc/GMT-14', 'Etc/GMT-14'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Pacific/Gambier', 'Pacific/Gambier'), ('Africa/Maseru', 'Africa/Maseru'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('Africa/Libreville', 'Africa/Libreville'), ('America/Nipigon', 'America/Nipigon'), ('Europe/Zurich', 'Europe/Zurich'), ('Jamaica', 'Jamaica'), ('Poland', 'Poland'), ('Asia/Chungking', 'Asia/Chungking'), ('Pacific/Noumea', 'Pacific/Noumea'), ('America/Grand_Turk', 'America/Grand_Turk'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Asia/Bangkok', 'Asia/Bangkok'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Asia/Kashgar', 'Asia/Kashgar'), ('America/Mazatlan', 'America/Mazatlan'), ('Asia/Makassar', 'Asia/Makassar'), ('America/Virgin', 'America/Virgin'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Portugal', 'Portugal'), ('Israel', 'Israel'), ('Asia/Kuching', 'Asia/Kuching'), ('America/Fortaleza', 'America/Fortaleza'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('America/Lower_Princes', 'America/Lower_Princes'), ('Asia/Harbin', 'Asia/Harbin'), ('Asia/Seoul', 'Asia/Seoul'), ('HST', 'HST'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('Etc/GMT+8', 'Etc/GMT+8'), ('America/Caracas', 'America/Caracas'), ('Africa/Khartoum', 'Africa/Khartoum'), ('Hongkong', 'Hongkong'), ('Libya', 'Libya'), ('America/Jujuy', 'America/Jujuy'), ('Europe/Kiev', 'Europe/Kiev'), ('Pacific/Auckland', 'Pacific/Auckland'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('UTC', 'UTC'), ('Etc/Universal', 'Etc/Universal'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Asia/Thimphu', 'Asia/Thimphu'), ('America/Menominee', 'America/Menominee'), ('Europe/Sofia', 'Europe/Sofia'), ('Etc/GMT-9', 'Etc/GMT-9'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('EST', 'EST'), ('America/Metlakatla', 'America/Metlakatla'), ('Etc/GMT+2', 'Etc/GMT+2'), ('Africa/Abidjan', 'Africa/Abidjan'), ('America/Catamarca', 'America/Catamarca'), ('America/Antigua', 'America/Antigua'), ('Europe/Minsk', 'Europe/Minsk'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Europe/Tirane', 'Europe/Tirane'), ('America/Maceio', 'America/Maceio'), ('Europe/Brussels', 'Europe/Brussels'), ('Australia/LHI', 'Australia/LHI'), ('Etc/Zulu', 'Etc/Zulu'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('Australia/Eucla', 'Australia/Eucla'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('America/Cordoba', 'America/Cordoba'), ('America/Scoresbysund', 'America/Scoresbysund'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('America/Barbados', 'America/Barbados'), ('America/Hermosillo', 'America/Hermosillo'), ('Etc/UCT', 'Etc/UCT'), ('Indian/Mahe', 'Indian/Mahe'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('America/St_Johns', 'America/St_Johns'), ('Africa/Harare', 'Africa/Harare'), ('Europe/Volgograd', 'Europe/Volgograd'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Asia/Saigon', 'Asia/Saigon'), ('Asia/Baghdad', 'Asia/Baghdad'), ('ROK', 'ROK'), ('Mexico/General', 'Mexico/General'), ('Brazil/West', 'Brazil/West'), ('Africa/Niamey', 'Africa/Niamey'), ('Europe/Moscow', 'Europe/Moscow'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Indian/Cocos', 'Indian/Cocos'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('America/Glace_Bay', 'America/Glace_Bay'), ('America/Rainy_River', 'America/Rainy_River'), ('Pacific/Johnston', 'Pacific/Johnston'), ('Australia/Perth', 'Australia/Perth'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('Europe/Andorra', 'Europe/Andorra'), ('America/Santiago', 'America/Santiago'), ('America/Guadeloupe', 'America/Guadeloupe'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('US/Pacific', 'US/Pacific'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Australia/South', 'Australia/South'), ('Etc/Greenwich', 'Etc/Greenwich'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Etc/GMT+7', 'Etc/GMT+7'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('America/Porto_Acre', 'America/Porto_Acre'), ('Indian/Mayotte', 'Indian/Mayotte'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('Africa/Maputo', 'Africa/Maputo'), ('America/Whitehorse', 'America/Whitehorse'), ('Etc/GMT-4', 'Etc/GMT-4'), ('America/Ensenada', 'America/Ensenada'), ('America/Dominica',
                                   'America/Dominica'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('Canada/Atlantic', 'Canada/Atlantic'), ('Asia/Baku', 'Asia/Baku'), ('Europe/Vaduz', 'Europe/Vaduz'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('America/Nuuk', 'America/Nuuk'), ('America/Porto_Velho', 'America/Porto_Velho'), ('America/Mendoza', 'America/Mendoza'), ('Africa/Bissau', 'Africa/Bissau'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Africa/Accra', 'Africa/Accra'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('Cuba', 'Cuba'), ('Asia/Jakarta', 'Asia/Jakarta'), ('Australia/Adelaide', 'Australia/Adelaide'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('US/Eastern', 'US/Eastern'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('MET', 'MET'), ('Europe/Samara', 'Europe/Samara'), ('Asia/Vientiane', 'Asia/Vientiane'), ('America/Belem', 'America/Belem'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('Africa/Casablanca', 'Africa/Casablanca'), ('America/Cayman', 'America/Cayman'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('America/Grenada', 'America/Grenada'), ('America/Goose_Bay', 'America/Goose_Bay'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('Europe/Vatican', 'Europe/Vatican'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('America/Chihuahua', 'America/Chihuahua'), ('America/Kralendijk', 'America/Kralendijk'), ('America/Moncton', 'America/Moncton'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('US/Arizona', 'US/Arizona'), ('Etc/GMT+11', 'Etc/GMT+11'), ('Asia/Dubai', 'Asia/Dubai'), ('PST8PDT', 'PST8PDT'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('America/Swift_Current', 'America/Swift_Current'), ('Australia/Tasmania', 'Australia/Tasmania'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('UCT', 'UCT'), ('America/Cancun', 'America/Cancun'), ('Africa/Freetown', 'Africa/Freetown'), ('US/Aleutian', 'US/Aleutian'), ('Asia/Damascus', 'Asia/Damascus'), ('NZ-CHAT', 'NZ-CHAT'), ('Australia/Brisbane', 'Australia/Brisbane'), ('PRC', 'PRC'), ('Australia/Canberra', 'Australia/Canberra'), ('Pacific/Midway', 'Pacific/Midway'), ('Pacific/Niue', 'Pacific/Niue'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('US/Mountain', 'US/Mountain'), ('Asia/Famagusta', 'Asia/Famagusta'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Europe/Madrid', 'Europe/Madrid'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('ROC', 'ROC'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('America/El_Salvador', 'America/El_Salvador'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('Africa/Banjul', 'Africa/Banjul'), ('Europe/Riga', 'Europe/Riga'), ('America/Panama', 'America/Panama'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('Etc/GMT+1', 'Etc/GMT+1'), ('Asia/Hovd', 'Asia/Hovd'), ('Asia/Beirut', 'Asia/Beirut'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('Asia/Hebron', 'Asia/Hebron'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('CST6CDT', 'CST6CDT'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('Australia/Queensland', 'Australia/Queensland'), ('Turkey', 'Turkey'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Asia/Manila', 'Asia/Manila'), ('America/Yakutat', 'America/Yakutat'), ('America/Miquelon', 'America/Miquelon'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('America/Marigot', 'America/Marigot'), ('Indian/Christmas', 'Indian/Christmas'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Canada/Eastern', 'Canada/Eastern'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('Australia/Darwin', 'Australia/Darwin'), ('US/Michigan', 'US/Michigan'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('Japan', 'Japan'), ('W-SU', 'W-SU'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('America/Dawson', 'America/Dawson'), ('Africa/Luanda', 'Africa/Luanda'), ('Pacific/Majuro', 'Pacific/Majuro'), ('America/Ojinaga', 'America/Ojinaga'), ('Europe/Jersey', 'Europe/Jersey'), ('Asia/Yangon', 'Asia/Yangon'), ('Asia/Anadyr', 'Asia/Anadyr'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('Africa/Dakar', 'Africa/Dakar'), ('GMT0', 'GMT0'), ('America/Montevideo', 'America/Montevideo'), ('US/Samoa', 'US/Samoa'), ('Africa/Ceuta', 'Africa/Ceuta'), ('Europe/Belgrade', 'Europe/Belgrade'), ('Asia/Omsk', 'Asia/Omsk'), ('Asia/Macao', 'Asia/Macao'), ('America/Anchorage', 'America/Anchorage'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('Asia/Oral', 'Asia/Oral'), ('America/Winnipeg', 'America/Winnipeg'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('Asia/Urumqi', 'Asia/Urumqi'), ('America/Belize', 'America/Belize'), ('America/Cuiaba', 'America/Cuiaba'), ('Australia/North', 'Australia/North'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('America/St_Lucia', 'America/St_Lucia'), ('Etc/GMT-11', 'Etc/GMT-11'), ('Brazil/East', 'Brazil/East'), ('Pacific/Ponape', 'Pacific/Ponape'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('America/Knox_IN', 'America/Knox_IN'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('Asia/Aden', 'Asia/Aden'), ('Europe/Dublin', 'Europe/Dublin'), ('America/Atka', 'America/Atka'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('Canada/Mountain', 'Canada/Mountain'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Asia/Pontianak', 'Asia/Pontianak'), ('America/Tijuana', 'America/Tijuana'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Brazil/Acre', 'Brazil/Acre'), ('Asia/Singapore', 'Asia/Singapore'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('EST5EDT', 'EST5EDT'), ('America/Godthab', 'America/Godthab'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('Factory', 'Factory'), ('Europe/Bucharest', 'Europe/Bucharest'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('Australia/Sydney', 'Australia/Sydney'), ('America/Denver', 'America/Denver'), ('Australia/West', 'Australia/West'), ('Chile/Continental', 'Chile/Continental'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Europe/Helsinki', 'Europe/Helsinki'), ('GB-Eire', 'GB-Eire'), ('GMT', 'GMT'), ('Africa/Juba', 'Africa/Juba'), ('America/Los_Angeles', 'America/Los_Angeles'), ('GMT-0', 'GMT-0'), ('America/Detroit', 'America/Detroit'), ('Asia/Barnaul', 'Asia/Barnaul'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('Asia/Magadan', 'Asia/Magadan'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Atlantic/Canary', 'Atlantic/Canary'), ('America/Edmonton', 'America/Edmonton'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('Europe/Chisinau', 'Europe/Chisinau'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Canada/Central', 'Canada/Central'), ('America/Pangnirtung', 'America/Pangnirtung'), ('Europe/Budapest', 'Europe/Budapest'), ('Singapore', 'Singapore'), ('Indian/Comoro', 'Indian/Comoro'), ('Pacific/Guam', 'Pacific/Guam'), ('Pacific/Efate', 'Pacific/Efate'), ('America/Toronto', 'America/Toronto'), ('Navajo', 'Navajo'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Etc/GMT-10', 'Etc/GMT-10'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('America/Adak', 'America/Adak'), ('America/Merida', 'America/Merida'), ('Africa/Kampala', 'Africa/Kampala'), ('America/Asuncion', 'America/Asuncion'), ('GMT+0', 'GMT+0'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('Antarctica/Casey', 'Antarctica/Casey'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('America/Anguilla', 'America/Anguilla'), ('Europe/Guernsey', 'Europe/Guernsey'), ('America/Vancouver', 'America/Vancouver'), ('Europe/Nicosia', 'Europe/Nicosia'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('MST', 'MST'), ('US/Alaska', 'US/Alaska'), ('Universal', 'Universal'), ('Pacific/Wake', 'Pacific/Wake'), ('Africa/Malabo', 'Africa/Malabo'), ('Australia/Lindeman', 'Australia/Lindeman'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('America/Rio_Branco', 'America/Rio_Branco'), ('America/Bogota', 'America/Bogota'), ('Etc/GMT-2', 'Etc/GMT-2'), ('America/Santarem', 'America/Santarem'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('America/St_Vincent', 'America/St_Vincent'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('America/Phoenix', 'America/Phoenix'), ('America/La_Paz', 'America/La_Paz'), ('NZ', 'NZ'), ('America/Inuvik', 'America/Inuvik'), ('Asia/Kabul', 'Asia/Kabul'), ('America/Louisville', 'America/Louisville'), ('Asia/Kolkata', 'Asia/Kolkata'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('America/St_Thomas', 'America/St_Thomas'), ('Europe/Skopje', 'Europe/Skopje'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Australia/ACT', 'Australia/ACT'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Etc/GMT-0', 'Etc/GMT-0'), ('America/Regina', 'America/Regina'), ('Europe/Simferopol', 'Europe/Simferopol'), ('Pacific/Truk', 'Pacific/Truk'), ('Asia/Gaza', 'Asia/Gaza'), ('Iceland', 'Iceland'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('Asia/Tehran', 'Asia/Tehran'), ('Europe/Tallinn', 'Europe/Tallinn'), ('Europe/Malta', 'Europe/Malta'), ('Etc/GMT+10', 'Etc/GMT+10'), ('America/Sitka', 'America/Sitka'), ('Asia/Almaty', 'Asia/Almaty'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Zulu', 'Zulu'), ('America/Resolute', 'America/Resolute'), ('Etc/GMT+9', 'Etc/GMT+9'), ('Asia/Amman', 'Asia/Amman'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Etc/GMT+0', 'Etc/GMT+0'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('Asia/Rangoon', 'Asia/Rangoon'), ('Africa/Douala', 'Africa/Douala'), ('America/Paramaribo', 'America/Paramaribo'), ('Etc/GMT0', 'Etc/GMT0'), ('EET', 'EET'), ('Iran', 'Iran'), ('US/Central', 'US/Central'), ('Pacific/Wallis', 'Pacific/Wallis'), ('America/Halifax', 'America/Halifax'), ('Etc/GMT', 'Etc/GMT'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Europe/Rome', 'Europe/Rome'), ('Asia/Chita', 'Asia/Chita'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Africa/Asmera', 'Africa/Asmera'), ('Asia/Nicosia', 'Asia/Nicosia'), ('Africa/Mbabane', 'Africa/Mbabane'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('Indian/Chagos', 'Indian/Chagos'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('America/Iqaluit', 'America/Iqaluit'), ('Greenwich', 'Greenwich'), ('Etc/GMT+6', 'Etc/GMT+6'), ('Indian/Maldives', 'Indian/Maldives'), ('Asia/Karachi', 'Asia/Karachi'), ('America/Curacao', 'America/Curacao'), ('US/Hawaii', 'US/Hawaii'), ('GB', 'GB'), ('Africa/Asmara', 'Africa/Asmara'), ('Africa/Bamako', 'Africa/Bamako'), ('America/Chicago', 'America/Chicago'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Asia/Dili', 'Asia/Dili'), ('Europe/Oslo', 'Europe/Oslo'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Etc/UTC', 'Etc/UTC'), ('Etc/GMT-6', 'Etc/GMT-6'), ('Asia/Dacca', 'Asia/Dacca')], default='Europe/London', max_length=35),
        ),
    ]