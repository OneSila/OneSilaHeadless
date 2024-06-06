# Generated by Django 5.0.2 on 2024-05-30 16:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0059_alter_multitenantuser_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('build/etc/localtime', 'build/etc/localtime'), ('America/Marigot', 'America/Marigot'), ('America/St_Lucia', 'America/St_Lucia'), ('Asia/Aden', 'Asia/Aden'), ('Indian/Cocos', 'Indian/Cocos'), ('Europe/Bucharest', 'Europe/Bucharest'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Africa/Douala', 'Africa/Douala'), ('Europe/Dublin', 'Europe/Dublin'), ('America/Chicago', 'America/Chicago'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('America/Indianapolis', 'America/Indianapolis'), ('Asia/Thimphu', 'Asia/Thimphu'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('America/Caracas', 'America/Caracas'), ('US/Aleutian', 'US/Aleutian'), ('Europe/Nicosia', 'Europe/Nicosia'), ('America/Rainy_River', 'America/Rainy_River'), ('Asia/Damascus', 'Asia/Damascus'), ('US/Central', 'US/Central'), ('America/Porto_Acre', 'America/Porto_Acre'), ('Iceland', 'Iceland'), ('Europe/Busingen', 'Europe/Busingen'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('America/Rosario', 'America/Rosario'), ('America/Managua', 'America/Managua'), ('Asia/Shanghai', 'Asia/Shanghai'), ('America/St_Johns', 'America/St_Johns'), ('Pacific/Efate', 'Pacific/Efate'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Europe/Kyiv', 'Europe/Kyiv'), ('Asia/Beirut', 'Asia/Beirut'), ('Japan', 'Japan'), ('America/Nipigon', 'America/Nipigon'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('US/Hawaii', 'US/Hawaii'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Asia/Bangkok', 'Asia/Bangkok'), ('America/Inuvik', 'America/Inuvik'), ('Africa/Lome', 'Africa/Lome'), ('Europe/Budapest', 'Europe/Budapest'), ('Africa/Abidjan', 'Africa/Abidjan'), ('Asia/Kabul', 'Asia/Kabul'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('Etc/GMT-12', 'Etc/GMT-12'), ('America/Atka', 'America/Atka'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('Europe/Kiev', 'Europe/Kiev'), ('Atlantic/Canary', 'Atlantic/Canary'), ('Asia/Jakarta', 'Asia/Jakarta'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('Pacific/Saipan', 'Pacific/Saipan'), ('America/Recife', 'America/Recife'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('America/Guatemala', 'America/Guatemala'), ('America/Ojinaga', 'America/Ojinaga'), ('Etc/GMT-2', 'Etc/GMT-2'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('CET', 'CET'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('Turkey', 'Turkey'), ('Africa/Maputo', 'Africa/Maputo'), ('America/Bogota', 'America/Bogota'), ('America/Tortola', 'America/Tortola'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('America/Rio_Branco', 'America/Rio_Branco'), ('America/Anchorage', 'America/Anchorage'), ('Australia/Tasmania', 'Australia/Tasmania'), ('America/Regina', 'America/Regina'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Australia/North', 'Australia/North'), ('Indian/Reunion', 'Indian/Reunion'), ('Europe/Madrid', 'Europe/Madrid'), ('Australia/Eucla', 'Australia/Eucla'), ('Asia/Makassar', 'Asia/Makassar'), ('Europe/Rome', 'Europe/Rome'), ('America/Metlakatla', 'America/Metlakatla'), ('America/Cordoba', 'America/Cordoba'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('America/Chihuahua', 'America/Chihuahua'), ('America/Louisville', 'America/Louisville'), ('America/Nassau', 'America/Nassau'), ('GMT+0', 'GMT+0'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('America/Los_Angeles', 'America/Los_Angeles'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('Asia/Atyrau', 'Asia/Atyrau'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('MET', 'MET'), ('Etc/GMT-0', 'Etc/GMT-0'), ('America/Scoresbysund', 'America/Scoresbysund'), ('Pacific/Wallis', 'Pacific/Wallis'), ('America/Belem', 'America/Belem'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('America/Phoenix', 'America/Phoenix'), ('Pacific/Wake', 'Pacific/Wake'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('America/Miquelon', 'America/Miquelon'), ('Europe/Skopje', 'Europe/Skopje'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Asia/Brunei', 'Asia/Brunei'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('America/Sitka', 'America/Sitka'), ('Europe/Moscow', 'Europe/Moscow'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('Egypt', 'Egypt'), ('Europe/Athens', 'Europe/Athens'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('Etc/GMT', 'Etc/GMT'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('Pacific/Ponape', 'Pacific/Ponape'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('Africa/Monrovia', 'Africa/Monrovia'), ('Asia/Rangoon', 'Asia/Rangoon'), ('GMT-0', 'GMT-0'), ('Asia/Dili', 'Asia/Dili'), ('Africa/Kigali', 'Africa/Kigali'), ('America/Boise', 'America/Boise'), ('America/Moncton', 'America/Moncton'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Libya', 'Libya'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('Universal', 'Universal'), ('Etc/GMT+9', 'Etc/GMT+9'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('Asia/Samarkand', 'Asia/Samarkand'), ('America/New_York', 'America/New_York'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('Africa/Harare', 'Africa/Harare'), ('Africa/Luanda', 'Africa/Luanda'), ('America/Montevideo', 'America/Montevideo'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('America/Juneau', 'America/Juneau'), ('Etc/GMT-14', 'Etc/GMT-14'), ('America/Fortaleza', 'America/Fortaleza'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('Chile/Continental', 'Chile/Continental'), ('America/Shiprock', 'America/Shiprock'), ('Asia/Saigon', 'Asia/Saigon'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('Australia/Victoria', 'Australia/Victoria'), ('America/St_Kitts', 'America/St_Kitts'), ('Africa/Asmera', 'Africa/Asmera'), ('Indian/Mayotte', 'Indian/Mayotte'), ('America/Creston', 'America/Creston'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('America/Goose_Bay', 'America/Goose_Bay'), ('Etc/GMT+2', 'Etc/GMT+2'), ('America/Thule', 'America/Thule'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('America/Virgin', 'America/Virgin'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('Canada/Central', 'Canada/Central'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Etc/GMT-11', 'Etc/GMT-11'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('Pacific/Palau', 'Pacific/Palau'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('America/Dominica', 'America/Dominica'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('America/Pangnirtung', 'America/Pangnirtung'), ('America/Manaus', 'America/Manaus'), ('Africa/Dakar', 'Africa/Dakar'), ('Etc/GMT-10', 'Etc/GMT-10'), ('Europe/Zurich', 'Europe/Zurich'), ('Indian/Maldives', 'Indian/Maldives'), ('America/Halifax', 'America/Halifax'), ('Asia/Bishkek', 'Asia/Bishkek'), ('GB', 'GB'), ('America/Lima', 'America/Lima'), ('Africa/Maseru', 'Africa/Maseru'), ('America/Martinique', 'America/Martinique'), ('Canada/Atlantic', 'Canada/Atlantic'), ('America/Dawson', 'America/Dawson'), ('PRC', 'PRC'), ('Portugal', 'Portugal'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('US/East-Indiana', 'US/East-Indiana'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('Mexico/General', 'Mexico/General'), ('Europe/London', 'Europe/London'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Brazil/Acre', 'Brazil/Acre'), ('America/Panama', 'America/Panama'), ('Africa/Bamako', 'Africa/Bamako'), ('Antarctica/Casey', 'Antarctica/Casey'), ('Etc/GMT-9', 'Etc/GMT-9'), ('America/Knox_IN', 'America/Knox_IN'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('America/Swift_Current', 'America/Swift_Current'), ('Africa/Bissau', 'Africa/Bissau'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('Africa/Malabo', 'Africa/Malabo'), ('Australia/Darwin', 'Australia/Darwin'), ('Africa/Bangui', 'Africa/Bangui'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Etc/GMT+8', 'Etc/GMT+8'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Asia/Seoul', 'Asia/Seoul'), ('Asia/Almaty', 'Asia/Almaty'), ('Asia/Vientiane', 'Asia/Vientiane'), ('PST8PDT', 'PST8PDT'), ('America/Cayman', 'America/Cayman'), ('Brazil/East', 'Brazil/East'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('America/Noronha', 'America/Noronha'), ('Etc/GMT-1', 'Etc/GMT-1'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('America/Adak', 'America/Adak'), ('Pacific/Apia', 'Pacific/Apia'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('Etc/GMT-6', 'Etc/GMT-6'), ('Africa/Juba', 'Africa/Juba'), ('Australia/LHI', 'Australia/LHI'), ('Indian/Mahe', 'Indian/Mahe'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Asia/Qatar', 'Asia/Qatar'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('Europe/Helsinki', 'Europe/Helsinki'), ('Etc/GMT+0', 'Etc/GMT+0'), ('Europe/Samara', 'Europe/Samara'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('Canada/Pacific', 'Canada/Pacific'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('Europe/Brussels', 'Europe/Brussels'), ('America/Guayaquil', 'America/Guayaquil'), ('Asia/Urumqi', 'Asia/Urumqi'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('Asia/Taipei', 'Asia/Taipei'), ('America/Aruba', 'America/Aruba'), ('Europe/Zagreb', 'Europe/Zagreb'), ('Europe/Sofia', 'Europe/Sofia'), ('America/Godthab', 'America/Godthab'), ('America/Boa_Vista', 'America/Boa_Vista'), ('Africa/Freetown', 'Africa/Freetown'), ('Africa/Khartoum', 'Africa/Khartoum'), ('UTC', 'UTC'), ('Asia/Baku', 'Asia/Baku'), ('Asia/Singapore', 'Asia/Singapore'), ('Europe/Simferopol', 'Europe/Simferopol'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Pacific/Gambier', 'Pacific/Gambier'), ('America/Edmonton', 'America/Edmonton'), ('Europe/Chisinau', 'Europe/Chisinau'), ('America/Lower_Princes', 'America/Lower_Princes'), ('Etc/Greenwich', 'Etc/Greenwich'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Asia/Barnaul', 'Asia/Barnaul'), ('America/St_Vincent', 'America/St_Vincent'), ('Asia/Dacca', 'Asia/Dacca'), ('Canada/Eastern', 'Canada/Eastern'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('W-SU', 'W-SU'), ('America/Porto_Velho', 'America/Porto_Velho'), ('America/Toronto', 'America/Toronto'), ('America/Cuiaba', 'America/Cuiaba'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('Singapore', 'Singapore'), ('America/Nuuk', 'America/Nuuk'), ('America/El_Salvador', 'America/El_Salvador'), ('America/Nome', 'America/Nome'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('America/Curacao', 'America/Curacao'), ('America/Santiago', 'America/Santiago'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Asia/Hovd', 'Asia/Hovd'), ('CST6CDT', 'CST6CDT'), ('Europe/Volgograd', 'Europe/Volgograd'), ('GMT0', 'GMT0'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Antarctica/Davis', 'Antarctica/Davis'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('US/Mountain', 'US/Mountain'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Hongkong', 'Hongkong'), ('Asia/Pontianak', 'Asia/Pontianak'), ('America/Matamoros', 'America/Matamoros'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('US/Samoa', 'US/Samoa'), ('Etc/GMT-4', 'Etc/GMT-4'), ('Pacific/Midway', 'Pacific/Midway'), ('Asia/Anadyr', 'Asia/Anadyr'), ('US/Arizona', 'US/Arizona'), ('EST5EDT', 'EST5EDT'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('Indian/Christmas', 'Indian/Christmas'), ('Europe/Saratov', 'Europe/Saratov'), ('Etc/Zulu', 'Etc/Zulu'), ('Poland', 'Poland'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('America/Antigua', 'America/Antigua'), ('Asia/Macau', 'Asia/Macau'), ('America/Araguaina', 'America/Araguaina'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('Africa/Casablanca', 'Africa/Casablanca'), ('America/Campo_Grande', 'America/Campo_Grande'), ('America/Ensenada', 'America/Ensenada'), ('Europe/Berlin', 'Europe/Berlin'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('GB-Eire', 'GB-Eire'), ('WET', 'WET'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Asia/Macao', 'Asia/Macao'), ('Etc/GMT+7', 'Etc/GMT+7'), ('America/St_Thomas', 'America/St_Thomas'), ('Africa/Algiers', 'Africa/Algiers'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('America/Asuncion', 'America/Asuncion'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('America/Anguilla', 'America/Anguilla'), ('Australia/West', 'Australia/West'), ('Africa/Asmara', 'Africa/Asmara'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('America/Mazatlan', 'America/Mazatlan'), ('Europe/Belfast', 'Europe/Belfast'), ('Asia/Manila', 'Asia/Manila'), ('Cuba', 'Cuba'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('Asia/Amman', 'Asia/Amman'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('Africa/Kampala', 'Africa/Kampala'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Asia/Istanbul', 'Asia/Istanbul'), ('Africa/Lusaka', 'Africa/Lusaka'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Africa/Libreville', 'Africa/Libreville'), ('Europe/Oslo', 'Europe/Oslo'), ('America/Belize', 'America/Belize'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('America/Resolute', 'America/Resolute'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('Europe/Kirov', 'Europe/Kirov'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Asia/Chita', 'Asia/Chita'), ('America/Menominee', 'America/Menominee'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('America/Iqaluit', 'America/Iqaluit'), ('US/Alaska', 'US/Alaska'), ('NZ-CHAT', 'NZ-CHAT'), ('America/Santarem', 'America/Santarem'), ('Africa/Mbabane', 'Africa/Mbabane'), ('EET', 'EET'), ('EST', 'EST'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('Asia/Chungking', 'Asia/Chungking'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('Asia/Colombo', 'Asia/Colombo'), ('Etc/GMT+10', 'Etc/GMT+10'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('America/Tijuana', 'America/Tijuana'), ('Israel', 'Israel'), ('ROC', 'ROC'), ('US/Michigan', 'US/Michigan'), ('America/Vancouver', 'America/Vancouver'), ('Australia/Hobart', 'Australia/Hobart'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('Jamaica', 'Jamaica'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('MST7MDT', 'MST7MDT'), ('America/Yakutat', 'America/Yakutat'), ('Indian/Chagos', 'Indian/Chagos'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('Asia/Omsk', 'Asia/Omsk'), ('Pacific/Truk', 'Pacific/Truk'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Australia/NSW', 'Australia/NSW'), ('Etc/GMT-13', 'Etc/GMT-13'), ('Pacific/Yap', 'Pacific/Yap'), ('Pacific/Easter', 'Pacific/Easter'), ('Greenwich', 'Greenwich'), ('America/Jamaica', 'America/Jamaica'), ('Asia/Muscat', 'Asia/Muscat'), ('Etc/UCT', 'Etc/UCT'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Australia/Perth', 'Australia/Perth'), ('America/Jujuy', 'America/Jujuy'), ('America/Denver', 'America/Denver'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('ROK', 'ROK'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('Australia/Queensland', 'Australia/Queensland'), ('Pacific/Guam', 'Pacific/Guam'), ('Asia/Gaza', 'Asia/Gaza'), ('America/Guadeloupe', 'America/Guadeloupe'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('America/La_Paz', 'America/La_Paz'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('Eire', 'Eire'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Europe/Minsk', 'Europe/Minsk'), ('Pacific/Niue', 'Pacific/Niue'), ('Asia/Baghdad', 'Asia/Baghdad'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('America/Bahia', 'America/Bahia'), ('America/Hermosillo', 'America/Hermosillo'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('Factory', 'Factory'), ('Australia/Sydney', 'Australia/Sydney'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Etc/GMT+3', 'Etc/GMT+3'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('Africa/Accra', 'Africa/Accra'), ('Asia/Yangon', 'Asia/Yangon'), ('Europe/Podgorica', 'Europe/Podgorica'), ('America/Grenada', 'America/Grenada'), ('America/Maceio', 'America/Maceio'), ('America/Guyana', 'America/Guyana'), ('Pacific/Auckland', 'Pacific/Auckland'), ('America/Mendoza', 'America/Mendoza'), ('Europe/Paris', 'Europe/Paris'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Europe/Jersey', 'Europe/Jersey'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Europe/Monaco', 'Europe/Monaco'), ('US/Pacific', 'US/Pacific'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('GMT', 'GMT'), ('America/Barbados', 'America/Barbados'), ('America/Winnipeg', 'America/Winnipeg'), ('Etc/GMT+1', 'Etc/GMT+1'), ('Asia/Nicosia', 'Asia/Nicosia'), ('Australia/ACT', 'Australia/ACT'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('Africa/Nairobi', 'Africa/Nairobi'), ('Asia/Harbin', 'Asia/Harbin'), ('Africa/Cairo', 'Africa/Cairo'), ('Asia/Tehran', 'Asia/Tehran'), ('Africa/Lagos', 'Africa/Lagos'), ('Europe/Tirane', 'Europe/Tirane'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('Indian/Mauritius', 'Indian/Mauritius'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('America/Eirunepe', 'America/Eirunepe'), ('Africa/Conakry', 'Africa/Conakry'), ('America/Havana', 'America/Havana'), ('Europe/Belgrade', 'Europe/Belgrade'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('America/Grand_Turk', 'America/Grand_Turk'), ('Australia/Adelaide', 'Australia/Adelaide'), ('Pacific/Majuro', 'Pacific/Majuro'), ('Canada/Yukon', 'Canada/Yukon'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Africa/Gaborone', 'Africa/Gaborone'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Africa/Tunis', 'Africa/Tunis'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Australia/South', 'Australia/South'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('Asia/Kashgar', 'Asia/Kashgar'), ('Zulu', 'Zulu'), ('America/Cayenne', 'America/Cayenne'), ('Etc/GMT+5', 'Etc/GMT+5'), ('UCT', 'UCT'), ('Australia/Canberra', 'Australia/Canberra'), ('America/Mexico_City', 'America/Mexico_City'), ('America/Paramaribo', 'America/Paramaribo'), ('Europe/Vatican', 'Europe/Vatican'), ('America/Atikokan', 'America/Atikokan'), ('Indian/Comoro', 'Indian/Comoro'), ('America/Catamarca', 'America/Catamarca'), ('Europe/Andorra', 'Europe/Andorra'), ('Europe/Tallinn', 'Europe/Tallinn'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Etc/GMT+6', 'Etc/GMT+6'), ('Africa/Banjul', 'Africa/Banjul'), ('Asia/Famagusta', 'Asia/Famagusta'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('Brazil/West', 'Brazil/West'), ('Asia/Riyadh', 'Asia/Riyadh'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Asia/Dubai', 'Asia/Dubai'), ('Asia/Jayapura', 'Asia/Jayapura'), ('Kwajalein', 'Kwajalein'), ('Etc/UTC', 'Etc/UTC'), ('Navajo', 'Navajo'), ('Asia/Oral', 'Asia/Oral'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('America/Detroit', 'America/Detroit'), ('America/Whitehorse', 'America/Whitehorse'), ('Europe/Malta', 'Europe/Malta'), ('Europe/Riga', 'Europe/Riga'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('America/Monterrey', 'America/Monterrey'), ('Africa/Niamey', 'Africa/Niamey'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Etc/GMT0', 'Etc/GMT0'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('Etc/GMT-3', 'Etc/GMT-3'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('US/Eastern', 'US/Eastern'), ('Europe/Vienna', 'Europe/Vienna'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Asia/Magadan', 'Asia/Magadan'), ('America/Montreal', 'America/Montreal'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Pacific/Johnston', 'Pacific/Johnston'), ('Asia/Kuching', 'Asia/Kuching'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('America/Montserrat', 'America/Montserrat'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Pacific/Chatham', 'Pacific/Chatham'), ('Etc/GMT+11', 'Etc/GMT+11'), ('Africa/Tripoli', 'Africa/Tripoli'), ('America/Kralendijk', 'America/Kralendijk'), ('Australia/Currie', 'Australia/Currie'), ('Africa/Ceuta', 'Africa/Ceuta'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('Asia/Kolkata', 'Asia/Kolkata'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('Europe/San_Marino', 'Europe/San_Marino'), ('Asia/Thimbu', 'Asia/Thimbu'), ('Europe/Prague', 'Europe/Prague'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('Etc/Universal', 'Etc/Universal'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('MST', 'MST'), ('Iran', 'Iran'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Asia/Kuwait', 'Asia/Kuwait'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('Europe/Vaduz', 'Europe/Vaduz'), ('America/Yellowknife', 'America/Yellowknife'), ('Pacific/Samoa', 'Pacific/Samoa'), ('America/Merida', 'America/Merida'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('HST', 'HST'), ('Europe/Warsaw', 'Europe/Warsaw'), ('Asia/Hebron', 'Asia/Hebron'), ('NZ', 'NZ'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('America/Cancun', 'America/Cancun'), ('Asia/Karachi', 'Asia/Karachi'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Canada/Mountain', 'Canada/Mountain'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh')], default='Europe/London', max_length=35),
        ),
    ]