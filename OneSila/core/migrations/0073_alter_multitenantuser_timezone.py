# Generated by Django 5.0.2 on 2024-05-30 18:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0072_alter_multitenantuser_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('Europe/Tallinn', 'Europe/Tallinn'), ('America/Rosario', 'America/Rosario'), ('Europe/San_Marino', 'Europe/San_Marino'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('America/Guyana', 'America/Guyana'), ('Africa/Bangui', 'Africa/Bangui'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('EET', 'EET'), ('US/Alaska', 'US/Alaska'), ('Asia/Hovd', 'Asia/Hovd'), ('Portugal', 'Portugal'), ('Europe/Busingen', 'Europe/Busingen'), ('America/Santiago', 'America/Santiago'), ('America/Belem', 'America/Belem'), ('Etc/GMT+5', 'Etc/GMT+5'), ('America/Mexico_City', 'America/Mexico_City'), ('Australia/Perth', 'Australia/Perth'), ('America/El_Salvador', 'America/El_Salvador'), ('Europe/Kirov', 'Europe/Kirov'), ('Asia/Anadyr', 'Asia/Anadyr'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('Etc/GMT+8', 'Etc/GMT+8'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('Egypt', 'Egypt'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('Europe/Belgrade', 'Europe/Belgrade'), ('Africa/Asmara', 'Africa/Asmara'), ('Europe/Dublin', 'Europe/Dublin'), ('Asia/Baghdad', 'Asia/Baghdad'), ('NZ-CHAT', 'NZ-CHAT'), ('Iceland', 'Iceland'), ('Indian/Mahe', 'Indian/Mahe'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('EST', 'EST'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('Europe/Zagreb', 'Europe/Zagreb'), ('Africa/Bamako', 'Africa/Bamako'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Asia/Jakarta', 'Asia/Jakarta'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('Canada/Yukon', 'Canada/Yukon'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('Singapore', 'Singapore'), ('GMT+0', 'GMT+0'), ('Europe/Simferopol', 'Europe/Simferopol'), ('Etc/GMT+0', 'Etc/GMT+0'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('America/Winnipeg', 'America/Winnipeg'), ('Greenwich', 'Greenwich'), ('Factory', 'Factory'), ('Africa/Gaborone', 'Africa/Gaborone'), ('Etc/GMT-13', 'Etc/GMT-13'), ('US/Pacific', 'US/Pacific'), ('America/Barbados', 'America/Barbados'), ('America/Campo_Grande', 'America/Campo_Grande'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('America/Cayman', 'America/Cayman'), ('Australia/North', 'Australia/North'), ('Etc/GMT+1', 'Etc/GMT+1'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('America/Boa_Vista', 'America/Boa_Vista'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('Etc/GMT-10', 'Etc/GMT-10'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('Asia/Almaty', 'Asia/Almaty'), ('Europe/Saratov', 'Europe/Saratov'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('America/Dominica', 'America/Dominica'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('Etc/GMT-4', 'Etc/GMT-4'), ('America/Iqaluit', 'America/Iqaluit'), ('America/New_York', 'America/New_York'), ('Brazil/East', 'Brazil/East'), ('Navajo', 'Navajo'), ('America/Cordoba', 'America/Cordoba'), ('America/Yakutat', 'America/Yakutat'), ('America/Grand_Turk', 'America/Grand_Turk'), ('Asia/Bangkok', 'Asia/Bangkok'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('Pacific/Guam', 'Pacific/Guam'), ('Indian/Reunion', 'Indian/Reunion'), ('America/Curacao', 'America/Curacao'), ('Pacific/Midway', 'Pacific/Midway'), ('Etc/GMT-1', 'Etc/GMT-1'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Europe/Warsaw', 'Europe/Warsaw'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('Africa/Bissau', 'Africa/Bissau'), ('Asia/Nicosia', 'Asia/Nicosia'), ('America/Juneau', 'America/Juneau'), ('Antarctica/Casey', 'Antarctica/Casey'), ('America/Anguilla', 'America/Anguilla'), ('build/etc/localtime', 'build/etc/localtime'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('CET', 'CET'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('US/Michigan', 'US/Michigan'), ('America/Lower_Princes', 'America/Lower_Princes'), ('Pacific/Wake', 'Pacific/Wake'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('America/Metlakatla', 'America/Metlakatla'), ('Asia/Bishkek', 'Asia/Bishkek'), ('America/Merida', 'America/Merida'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Asia/Urumqi', 'Asia/Urumqi'), ('America/Pangnirtung', 'America/Pangnirtung'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('America/St_Kitts', 'America/St_Kitts'), ('HST', 'HST'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('Pacific/Easter', 'Pacific/Easter'), ('America/Denver', 'America/Denver'), ('Australia/Adelaide', 'Australia/Adelaide'), ('America/Vancouver', 'America/Vancouver'), ('Africa/Cairo', 'Africa/Cairo'), ('Asia/Magadan', 'Asia/Magadan'), ('Asia/Dili', 'Asia/Dili'), ('Europe/Paris', 'Europe/Paris'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Indian/Mayotte', 'Indian/Mayotte'), ('Canada/Pacific', 'Canada/Pacific'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('America/Toronto', 'America/Toronto'), ('Universal', 'Universal'), ('Europe/Malta', 'Europe/Malta'), ('Japan', 'Japan'), ('America/Ojinaga', 'America/Ojinaga'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Australia/West', 'Australia/West'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Etc/GMT+10', 'Etc/GMT+10'), ('Asia/Omsk', 'Asia/Omsk'), ('America/Los_Angeles', 'America/Los_Angeles'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('Asia/Beirut', 'Asia/Beirut'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Africa/Kampala', 'Africa/Kampala'), ('America/Manaus', 'America/Manaus'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('Europe/Athens', 'Europe/Athens'), ('Europe/Kyiv', 'Europe/Kyiv'), ('America/Jujuy', 'America/Jujuy'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('Pacific/Efate', 'Pacific/Efate'), ('Asia/Aden', 'Asia/Aden'), ('Asia/Brunei', 'Asia/Brunei'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('Indian/Comoro', 'Indian/Comoro'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('Europe/Bucharest', 'Europe/Bucharest'), ('Asia/Qatar', 'Asia/Qatar'), ('Etc/GMT-12', 'Etc/GMT-12'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('Asia/Gaza', 'Asia/Gaza'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('America/Nuuk', 'America/Nuuk'), ('Asia/Harbin', 'Asia/Harbin'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('Asia/Dacca', 'Asia/Dacca'), ('Asia/Oral', 'Asia/Oral'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Etc/Zulu', 'Etc/Zulu'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Chile/Continental', 'Chile/Continental'), ('Australia/Eucla', 'Australia/Eucla'), ('Europe/Brussels', 'Europe/Brussels'), ('Africa/Banjul', 'Africa/Banjul'), ('America/Montevideo', 'America/Montevideo'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('Australia/Canberra', 'Australia/Canberra'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('Etc/GMT', 'Etc/GMT'), ('Asia/Barnaul', 'Asia/Barnaul'), ('Pacific/Auckland', 'Pacific/Auckland'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('America/Dawson', 'America/Dawson'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('Africa/Libreville', 'Africa/Libreville'), ('Europe/Vilnius', 'Europe/Vilnius'), ('America/Jamaica', 'America/Jamaica'), ('Asia/Famagusta', 'Asia/Famagusta'), ('America/Nipigon', 'America/Nipigon'), ('Indian/Cocos', 'Indian/Cocos'), ('America/Moncton', 'America/Moncton'), ('America/Guayaquil', 'America/Guayaquil'), ('America/Ensenada', 'America/Ensenada'), ('Africa/Maputo', 'Africa/Maputo'), ('America/Maceio', 'America/Maceio'), ('Asia/Katmandu', 'Asia/Katmandu'), ('America/Matamoros', 'America/Matamoros'), ('Australia/Lindeman', 'Australia/Lindeman'), ('America/Chicago', 'America/Chicago'), ('GMT-0', 'GMT-0'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('America/Monterrey', 'America/Monterrey'), ('Atlantic/Canary', 'Atlantic/Canary'), ('Europe/Kiev', 'Europe/Kiev'), ('Asia/Yangon', 'Asia/Yangon'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('America/Regina', 'America/Regina'), ('America/Montreal', 'America/Montreal'), ('Etc/GMT+3', 'Etc/GMT+3'), ('Europe/Volgograd', 'Europe/Volgograd'), ('Australia/Victoria', 'Australia/Victoria'), ('Pacific/Ponape', 'Pacific/Ponape'), ('America/Menominee', 'America/Menominee'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Europe/Vaduz', 'Europe/Vaduz'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Indian/Christmas', 'Indian/Christmas'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Etc/GMT+11', 'Etc/GMT+11'), ('PST8PDT', 'PST8PDT'), ('America/Araguaina', 'America/Araguaina'), ('Etc/UCT', 'Etc/UCT'), ('America/Antigua', 'America/Antigua'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('W-SU', 'W-SU'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Europe/Skopje', 'Europe/Skopje'), ('Etc/GMT-11', 'Etc/GMT-11'), ('Israel', 'Israel'), ('Turkey', 'Turkey'), ('Cuba', 'Cuba'), ('America/Indianapolis', 'America/Indianapolis'), ('Europe/Oslo', 'Europe/Oslo'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('Africa/Casablanca', 'Africa/Casablanca'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('America/Mazatlan', 'America/Mazatlan'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('America/Santarem', 'America/Santarem'), ('America/Boise', 'America/Boise'), ('Asia/Chita', 'Asia/Chita'), ('Indian/Chagos', 'Indian/Chagos'), ('PRC', 'PRC'), ('America/Catamarca', 'America/Catamarca'), ('Etc/GMT-3', 'Etc/GMT-3'), ('Asia/Yerevan', 'Asia/Yerevan'), ('America/Phoenix', 'America/Phoenix'), ('Etc/GMT-8', 'Etc/GMT-8'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Africa/Mbabane', 'Africa/Mbabane'), ('America/Nassau', 'America/Nassau'), ('America/Knox_IN', 'America/Knox_IN'), ('Pacific/Majuro', 'Pacific/Majuro'), ('Eire', 'Eire'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Asia/Chungking', 'Asia/Chungking'), ('America/Goose_Bay', 'America/Goose_Bay'), ('America/Tortola', 'America/Tortola'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('America/Thule', 'America/Thule'), ('America/Edmonton', 'America/Edmonton'), ('Pacific/Johnston', 'Pacific/Johnston'), ('Australia/NSW', 'Australia/NSW'), ('Asia/Muscat', 'Asia/Muscat'), ('Europe/Nicosia', 'Europe/Nicosia'), ('America/Nome', 'America/Nome'), ('America/Cuiaba', 'America/Cuiaba'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('Europe/Minsk', 'Europe/Minsk'), ('America/Shiprock', 'America/Shiprock'), ('America/Scoresbysund', 'America/Scoresbysund'), ('America/Yellowknife', 'America/Yellowknife'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('Asia/Macau', 'Asia/Macau'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('America/Hermosillo', 'America/Hermosillo'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Europe/Andorra', 'Europe/Andorra'), ('Asia/Saigon', 'Asia/Saigon'), ('America/Bogota', 'America/Bogota'), ('Australia/Queensland', 'Australia/Queensland'), ('Asia/Kuching', 'Asia/Kuching'), ('Asia/Atyrau', 'Asia/Atyrau'), ('America/Mendoza', 'America/Mendoza'), ('US/Hawaii', 'US/Hawaii'), ('Africa/Lusaka', 'Africa/Lusaka'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Asia/Istanbul', 'Asia/Istanbul'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Europe/Tirane', 'Europe/Tirane'), ('America/Tijuana', 'America/Tijuana'), ('Asia/Vientiane', 'Asia/Vientiane'), ('Europe/Sofia', 'Europe/Sofia'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('Pacific/Truk', 'Pacific/Truk'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('Pacific/Chatham', 'Pacific/Chatham'), ('Pacific/Apia', 'Pacific/Apia'), ('Libya', 'Libya'), ('America/Montserrat', 'America/Montserrat'), ('Canada/Mountain', 'Canada/Mountain'), ('America/Whitehorse', 'America/Whitehorse'), ('America/Sitka', 'America/Sitka'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Africa/Djibouti', 'Africa/Djibouti'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('Pacific/Yap', 'Pacific/Yap'), ('Iran', 'Iran'), ('Etc/GMT+9', 'Etc/GMT+9'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('Etc/UTC', 'Etc/UTC'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('America/Rainy_River', 'America/Rainy_River'), ('Africa/Dakar', 'Africa/Dakar'), ('Africa/Maseru', 'Africa/Maseru'), ('America/Rio_Branco', 'America/Rio_Branco'), ('America/St_Johns', 'America/St_Johns'), ('America/Swift_Current', 'America/Swift_Current'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('America/Adak', 'America/Adak'), ('Etc/GMT0', 'Etc/GMT0'), ('America/Cayenne', 'America/Cayenne'), ('CST6CDT', 'CST6CDT'), ('Africa/Freetown', 'Africa/Freetown'), ('America/Porto_Acre', 'America/Porto_Acre'), ('America/Fortaleza', 'America/Fortaleza'), ('Australia/Hobart', 'Australia/Hobart'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('ROK', 'ROK'), ('Africa/Lome', 'Africa/Lome'), ('Asia/Hebron', 'Asia/Hebron'), ('Europe/Vienna', 'Europe/Vienna'), ('America/La_Paz', 'America/La_Paz'), ('America/Kralendijk', 'America/Kralendijk'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Europe/Belfast', 'Europe/Belfast'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('America/Panama', 'America/Panama'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('Asia/Thimphu', 'Asia/Thimphu'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Asia/Macao', 'Asia/Macao'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Pacific/Palau', 'Pacific/Palau'), ('America/Anchorage', 'America/Anchorage'), ('Asia/Riyadh', 'Asia/Riyadh'), ('Asia/Qostanay', 'Asia/Qostanay'), ('America/Martinique', 'America/Martinique'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Africa/Ceuta', 'Africa/Ceuta'), ('Europe/Riga', 'Europe/Riga'), ('Indian/Maldives', 'Indian/Maldives'), ('Mexico/General', 'Mexico/General'), ('Asia/Baku', 'Asia/Baku'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('Europe/Budapest', 'Europe/Budapest'), ('Etc/GMT-14', 'Etc/GMT-14'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('Poland', 'Poland'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('Africa/Luanda', 'Africa/Luanda'), ('Asia/Kabul', 'Asia/Kabul'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('Europe/Helsinki', 'Europe/Helsinki'), ('America/Aruba', 'America/Aruba'), ('America/Managua', 'America/Managua'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('Etc/GMT-9', 'Etc/GMT-9'), ('Asia/Tokyo', 'Asia/Tokyo'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Asia/Makassar', 'Asia/Makassar'), ('America/Louisville', 'America/Louisville'), ('America/Paramaribo', 'America/Paramaribo'), ('America/Guatemala', 'America/Guatemala'), ('America/Porto_Velho', 'America/Porto_Velho'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Europe/Rome', 'Europe/Rome'), ('Pacific/Gambier', 'Pacific/Gambier'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('GMT0', 'GMT0'), ('America/Halifax', 'America/Halifax'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('Hongkong', 'Hongkong'), ('Africa/Tripoli', 'Africa/Tripoli'), ('UCT', 'UCT'), ('Asia/Amman', 'Asia/Amman'), ('Asia/Damascus', 'Asia/Damascus'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('US/Samoa', 'US/Samoa'), ('Canada/Central', 'Canada/Central'), ('Pacific/Wallis', 'Pacific/Wallis'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('America/Eirunepe', 'America/Eirunepe'), ('America/Havana', 'America/Havana'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('US/East-Indiana', 'US/East-Indiana'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Asia/Kashgar', 'Asia/Kashgar'), ('US/Central', 'US/Central'), ('America/Guadeloupe', 'America/Guadeloupe'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('GB-Eire', 'GB-Eire'), ('Kwajalein', 'Kwajalein'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('Canada/Eastern', 'Canada/Eastern'), ('Asia/Kuwait', 'Asia/Kuwait'), ('Etc/GMT+6', 'Etc/GMT+6'), ('Etc/Universal', 'Etc/Universal'), ('MST', 'MST'), ('America/Detroit', 'America/Detroit'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('Europe/Chisinau', 'Europe/Chisinau'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('Africa/Nairobi', 'Africa/Nairobi'), ('US/Aleutian', 'US/Aleutian'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Australia/ACT', 'Australia/ACT'), ('Asia/Pontianak', 'Asia/Pontianak'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Europe/Jersey', 'Europe/Jersey'), ('Asia/Jayapura', 'Asia/Jayapura'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('Africa/Douala', 'Africa/Douala'), ('Asia/Tehran', 'Asia/Tehran'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('America/Miquelon', 'America/Miquelon'), ('Africa/Juba', 'Africa/Juba'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('Africa/Accra', 'Africa/Accra'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('Asia/Samarkand', 'Asia/Samarkand'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('Africa/Conakry', 'Africa/Conakry'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Pacific/Noumea', 'Pacific/Noumea'), ('GMT', 'GMT'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('America/Belize', 'America/Belize'), ('Pacific/Fiji', 'Pacific/Fiji'), ('MST7MDT', 'MST7MDT'), ('America/St_Lucia', 'America/St_Lucia'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('America/Grenada', 'America/Grenada'), ('Etc/GMT+7', 'Etc/GMT+7'), ('Europe/Podgorica', 'Europe/Podgorica'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Australia/LHI', 'Australia/LHI'), ('America/Chihuahua', 'America/Chihuahua'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('Australia/South', 'Australia/South'), ('Africa/Harare', 'Africa/Harare'), ('UTC', 'UTC'), ('US/Mountain', 'US/Mountain'), ('Etc/GMT+2', 'Etc/GMT+2'), ('Africa/Asmera', 'Africa/Asmera'), ('Australia/Sydney', 'Australia/Sydney'), ('Africa/Niamey', 'Africa/Niamey'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('America/Resolute', 'America/Resolute'), ('Asia/Karachi', 'Asia/Karachi'), ('GB', 'GB'), ('America/Creston', 'America/Creston'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Africa/Algiers', 'Africa/Algiers'), ('Europe/Prague', 'Europe/Prague'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('Indian/Mauritius', 'Indian/Mauritius'), ('Asia/Singapore', 'Asia/Singapore'), ('Africa/Khartoum', 'Africa/Khartoum'), ('EST5EDT', 'EST5EDT'), ('ROC', 'ROC'), ('Australia/Darwin', 'Australia/Darwin'), ('Europe/Monaco', 'Europe/Monaco'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('NZ', 'NZ'), ('Asia/Colombo', 'Asia/Colombo'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('WET', 'WET'), ('Europe/London', 'Europe/London'), ('Asia/Thimbu', 'Asia/Thimbu'), ('America/St_Vincent', 'America/St_Vincent'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('America/Atka', 'America/Atka'), ('Europe/Vatican', 'Europe/Vatican'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('US/Arizona', 'US/Arizona'), ('Pacific/Niue', 'Pacific/Niue'), ('America/Godthab', 'America/Godthab'), ('Etc/GMT-2', 'Etc/GMT-2'), ('Asia/Manila', 'Asia/Manila'), ('America/Atikokan', 'America/Atikokan'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Australia/Tasmania', 'Australia/Tasmania'), ('America/St_Thomas', 'America/St_Thomas'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Africa/Tunis', 'Africa/Tunis'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Etc/GMT-0', 'Etc/GMT-0'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Zulu', 'Zulu'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('Europe/Zurich', 'Europe/Zurich'), ('Europe/Moscow', 'Europe/Moscow'), ('MET', 'MET'), ('Africa/Kigali', 'Africa/Kigali'), ('America/Lima', 'America/Lima'), ('Brazil/West', 'Brazil/West'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('America/Recife', 'America/Recife'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Africa/Abidjan', 'Africa/Abidjan'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('America/Bahia', 'America/Bahia'), ('Brazil/Acre', 'Brazil/Acre'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('US/Eastern', 'US/Eastern'), ('Asia/Dubai', 'Asia/Dubai'), ('Etc/Greenwich', 'Etc/Greenwich'), ('Canada/Atlantic', 'Canada/Atlantic'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('America/Virgin', 'America/Virgin'), ('Asia/Taipei', 'Asia/Taipei'), ('Europe/Madrid', 'Europe/Madrid'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('Europe/Samara', 'Europe/Samara'), ('Asia/Rangoon', 'Asia/Rangoon'), ('America/Cancun', 'America/Cancun'), ('Jamaica', 'Jamaica'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('America/Noronha', 'America/Noronha'), ('Asia/Kolkata', 'Asia/Kolkata'), ('America/Marigot', 'America/Marigot'), ('Australia/Currie', 'Australia/Currie'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('America/Asuncion', 'America/Asuncion'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Etc/GMT+12', 'Etc/GMT+12'), ('America/Caracas', 'America/Caracas'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Asia/Seoul', 'Asia/Seoul'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('Africa/Malabo', 'Africa/Malabo'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('America/Inuvik', 'America/Inuvik'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Africa/Monrovia', 'Africa/Monrovia'), ('Africa/Lagos', 'Africa/Lagos'), ('Europe/Berlin', 'Europe/Berlin'), ('Etc/GMT-6', 'Etc/GMT-6')], default='Europe/London', max_length=35),
        ),
    ]