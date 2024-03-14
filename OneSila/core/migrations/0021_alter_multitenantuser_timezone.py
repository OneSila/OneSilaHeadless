# Generated by Django 5.0.2 on 2024-03-04 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_alter_multitenantuser_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('build/etc/localtime', 'build/etc/localtime'), ('Etc/GMT+9', 'Etc/GMT+9'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('Pacific/Gambier', 'Pacific/Gambier'), ('America/Grenada', 'America/Grenada'), ('Asia/Bangkok', 'Asia/Bangkok'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Egypt', 'Egypt'), ('Africa/Tunis', 'Africa/Tunis'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Indian/Mauritius', 'Indian/Mauritius'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('Asia/Kuching', 'Asia/Kuching'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('Asia/Damascus', 'Asia/Damascus'), ('Antarctica/Casey', 'Antarctica/Casey'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('Asia/Seoul', 'Asia/Seoul'), ('America/Belize', 'America/Belize'), ('America/La_Paz', 'America/La_Paz'), ('Universal', 'Universal'), ('Iceland', 'Iceland'), ('Asia/Urumqi', 'Asia/Urumqi'), ('Asia/Atyrau', 'Asia/Atyrau'), ('Asia/Macau', 'Asia/Macau'), ('Europe/Jersey', 'Europe/Jersey'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Etc/UTC', 'Etc/UTC'), ('Europe/Budapest', 'Europe/Budapest'), ('America/Santarem', 'America/Santarem'), ('Africa/Mbabane', 'Africa/Mbabane'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('EST', 'EST'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('Europe/Oslo', 'Europe/Oslo'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('Asia/Almaty', 'Asia/Almaty'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('Europe/Vaduz', 'Europe/Vaduz'), ('Pacific/Wallis', 'Pacific/Wallis'), ('Africa/Algiers', 'Africa/Algiers'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('America/Atikokan', 'America/Atikokan'), ('America/St_Johns', 'America/St_Johns'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('Europe/Monaco', 'Europe/Monaco'), ('America/St_Vincent', 'America/St_Vincent'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Israel', 'Israel'), ('Asia/Muscat', 'Asia/Muscat'), ('America/Rainy_River', 'America/Rainy_River'), ('Pacific/Guam', 'Pacific/Guam'), ('Etc/GMT+5', 'Etc/GMT+5'), ('Europe/Brussels', 'Europe/Brussels'), ('Canada/Central', 'Canada/Central'), ('UTC', 'UTC'), ('America/Guadeloupe', 'America/Guadeloupe'), ('Asia/Kabul', 'Asia/Kabul'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('Jamaica', 'Jamaica'), ('Africa/Kampala', 'Africa/Kampala'), ('Africa/Ceuta', 'Africa/Ceuta'), ('PRC', 'PRC'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('Asia/Aden', 'Asia/Aden'), ('America/Rosario', 'America/Rosario'), ('Africa/Casablanca', 'Africa/Casablanca'), ('Africa/Kigali', 'Africa/Kigali'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Africa/Abidjan', 'Africa/Abidjan'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Asia/Dacca', 'Asia/Dacca'), ('America/Catamarca', 'America/Catamarca'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('Chile/Continental', 'Chile/Continental'), ('Europe/Vienna', 'Europe/Vienna'), ('Canada/Yukon', 'Canada/Yukon'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('America/St_Lucia', 'America/St_Lucia'), ('America/Tortola', 'America/Tortola'), ('Pacific/Wake', 'Pacific/Wake'), ('Etc/Zulu', 'Etc/Zulu'), ('Europe/London', 'Europe/London'), ('America/Ensenada', 'America/Ensenada'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Africa/Bamako', 'Africa/Bamako'), ('US/Michigan', 'US/Michigan'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('America/Curacao', 'America/Curacao'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Singapore', 'Singapore'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('America/Ojinaga', 'America/Ojinaga'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('America/Resolute', 'America/Resolute'), ('Africa/Bissau', 'Africa/Bissau'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('Etc/Universal', 'Etc/Universal'), ('CST6CDT', 'CST6CDT'), ('Australia/LHI', 'Australia/LHI'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('US/Hawaii', 'US/Hawaii'), ('Pacific/Majuro', 'Pacific/Majuro'), ('America/Godthab', 'America/Godthab'), ('Africa/Lome', 'Africa/Lome'), ('Africa/Asmara', 'Africa/Asmara'), ('America/Anguilla', 'America/Anguilla'), ('Asia/Jayapura', 'Asia/Jayapura'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Asia/Omsk', 'Asia/Omsk'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('Asia/Nicosia', 'Asia/Nicosia'), ('America/Atka', 'America/Atka'), ('America/Porto_Velho', 'America/Porto_Velho'), ('Pacific/Kanton', 'Pacific/Kanton'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('GB', 'GB'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Europe/Samara', 'Europe/Samara'), ('Asia/Saigon', 'Asia/Saigon'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Australia/Queensland', 'Australia/Queensland'), ('America/Bahia', 'America/Bahia'), ('Africa/Maseru', 'Africa/Maseru'), ('Australia/Canberra', 'Australia/Canberra'), ('America/Tijuana', 'America/Tijuana'), ('Europe/Kirov', 'Europe/Kirov'), ('Africa/Nairobi', 'Africa/Nairobi'), ('America/Monterrey', 'America/Monterrey'), ('Etc/Greenwich', 'Etc/Greenwich'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('Africa/Malabo', 'Africa/Malabo'), ('America/Hermosillo', 'America/Hermosillo'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Asia/Manila', 'Asia/Manila'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('US/Samoa', 'US/Samoa'), ('Asia/Singapore', 'Asia/Singapore'), ('Mexico/General', 'Mexico/General'), ('Asia/Kuwait', 'Asia/Kuwait'), ('America/Cayenne', 'America/Cayenne'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Asia/Famagusta', 'Asia/Famagusta'), ('Asia/Beirut', 'Asia/Beirut'), ('Europe/Malta', 'Europe/Malta'), ('Europe/Kiev', 'Europe/Kiev'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('America/Nuuk', 'America/Nuuk'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('Australia/South', 'Australia/South'), ('Europe/Busingen', 'Europe/Busingen'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Pacific/Johnston', 'Pacific/Johnston'), ('Europe/Belgrade', 'Europe/Belgrade'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('US/Central', 'US/Central'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('America/Metlakatla', 'America/Metlakatla'), ('America/Dominica', 'America/Dominica'), ('America/Vancouver', 'America/Vancouver'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('America/Juneau', 'America/Juneau'), ('Asia/Gaza', 'Asia/Gaza'), ('Australia/Victoria', 'Australia/Victoria'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('America/Cordoba', 'America/Cordoba'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Asia/Qatar', 'Asia/Qatar'), ('Etc/GMT-12', 'Etc/GMT-12'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Hongkong', 'Hongkong'), ('US/Arizona', 'US/Arizona'), ('Europe/Riga', 'Europe/Riga'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('Greenwich', 'Greenwich'), ('Pacific/Palau', 'Pacific/Palau'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('Australia/Perth', 'Australia/Perth'), ('Africa/Blantyre', 'Africa/Blantyre'), ('America/Virgin', 'America/Virgin'), ('Etc/GMT', 'Etc/GMT'), ('Europe/Paris', 'Europe/Paris'), ('America/Nassau', 'America/Nassau'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('America/Lima', 'America/Lima'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('America/Montserrat', 'America/Montserrat'), ('America/Managua', 'America/Managua'), ('Asia/Hovd', 'Asia/Hovd'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Europe/Podgorica', 'Europe/Podgorica'), ('Africa/Khartoum', 'Africa/Khartoum'), ('America/Iqaluit', 'America/Iqaluit'), ('Asia/Chongqing', 'Asia/Chongqing'), ('HST', 'HST'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('Europe/Tallinn', 'Europe/Tallinn'), ('Africa/Maputo', 'Africa/Maputo'), ('Asia/Chungking', 'Asia/Chungking'), ('Europe/San_Marino', 'Europe/San_Marino'), ('EET', 'EET'), ('Libya', 'Libya'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('America/Creston', 'America/Creston'), ('Etc/GMT-0', 'Etc/GMT-0'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('America/Cayman', 'America/Cayman'), ('Europe/Madrid', 'Europe/Madrid'), ('Zulu', 'Zulu'), ('Pacific/Yap', 'Pacific/Yap'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('Brazil/Acre', 'Brazil/Acre'), ('America/El_Salvador', 'America/El_Salvador'), ('US/Pacific', 'US/Pacific'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Europe/Nicosia', 'Europe/Nicosia'), ('America/Yakutat', 'America/Yakutat'), ('Etc/GMT+12', 'Etc/GMT+12'), ('America/Montevideo', 'America/Montevideo'), ('Africa/Douala', 'Africa/Douala'), ('America/Swift_Current', 'America/Swift_Current'), ('America/Maceio', 'America/Maceio'), ('Europe/Zurich', 'Europe/Zurich'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Etc/GMT-9', 'Etc/GMT-9'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('Pacific/Chatham', 'Pacific/Chatham'), ('America/Inuvik', 'America/Inuvik'), ('Australia/West', 'Australia/West'), ('Indian/Comoro', 'Indian/Comoro'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('America/New_York', 'America/New_York'), ('Africa/Juba', 'Africa/Juba'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Portugal', 'Portugal'), ('Etc/GMT+8', 'Etc/GMT+8'), ('America/Pangnirtung', 'America/Pangnirtung'), ('America/Asuncion', 'America/Asuncion'), ('Africa/Djibouti', 'Africa/Djibouti'), ('America/Panama', 'America/Panama'), ('Africa/Cairo', 'Africa/Cairo'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Europe/Andorra', 'Europe/Andorra'), ('Asia/Thimphu', 'Asia/Thimphu'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('America/Havana', 'America/Havana'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('America/Matamoros', 'America/Matamoros'), ('Etc/GMT-4', 'Etc/GMT-4'), ('America/Halifax', 'America/Halifax'), ('America/Mazatlan', 'America/Mazatlan'), ('Pacific/Niue', 'Pacific/Niue'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Asia/Istanbul', 'Asia/Istanbul'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('Asia/Dili', 'Asia/Dili'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('Cuba', 'Cuba'), ('Australia/Tasmania', 'Australia/Tasmania'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Europe/Dublin', 'Europe/Dublin'), ('Europe/Moscow', 'Europe/Moscow'), ('Etc/GMT+0', 'Etc/GMT+0'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('US/Alaska', 'US/Alaska'), ('America/Los_Angeles', 'America/Los_Angeles'), ('Etc/GMT-11', 'Etc/GMT-11'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('Etc/GMT0', 'Etc/GMT0'), ('America/Guyana', 'America/Guyana'), ('Pacific/Easter', 'Pacific/Easter'), ('Europe/Minsk', 'Europe/Minsk'), ('America/St_Kitts', 'America/St_Kitts'), ('America/Martinique', 'America/Martinique'), ('America/Jujuy', 'America/Jujuy'), ('Africa/Bangui', 'Africa/Bangui'), ('Africa/Accra', 'Africa/Accra'), ('Etc/GMT+10', 'Etc/GMT+10'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Canada/Atlantic', 'Canada/Atlantic'), ('Asia/Baghdad', 'Asia/Baghdad'), ('Asia/Magadan', 'Asia/Magadan'), ('America/Mendoza', 'America/Mendoza'), ('Asia/Karachi', 'Asia/Karachi'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Brazil/West', 'Brazil/West'), ('Etc/GMT-6', 'Etc/GMT-6'), ('Australia/NSW', 'Australia/NSW'), ('America/Lower_Princes', 'America/Lower_Princes'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Europe/Warsaw', 'Europe/Warsaw'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Europe/Tirane', 'Europe/Tirane'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('Europe/Chisinau', 'Europe/Chisinau'), ('Pacific/Efate', 'Pacific/Efate'), ('Asia/Thimbu', 'Asia/Thimbu'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Iran', 'Iran'), ('America/Jamaica', 'America/Jamaica'), ('Europe/Berlin', 'Europe/Berlin'), ('Asia/Amman', 'Asia/Amman'), ('Etc/UCT', 'Etc/UCT'), ('America/Thule', 'America/Thule'), ('US/Mountain', 'US/Mountain'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('Pacific/Ponape', 'Pacific/Ponape'), ('Indian/Maldives', 'Indian/Maldives'), ('Canada/Pacific', 'Canada/Pacific'), ('Japan', 'Japan'), ('GB-Eire', 'GB-Eire'), ('America/Yellowknife', 'America/Yellowknife'), ('Africa/Libreville', 'Africa/Libreville'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('America/Indianapolis', 'America/Indianapolis'), ('Asia/Tehran', 'Asia/Tehran'), ('MST7MDT', 'MST7MDT'), ('America/Manaus', 'America/Manaus'), ('America/Winnipeg', 'America/Winnipeg'), ('America/Bogota', 'America/Bogota'), ('America/Guatemala', 'America/Guatemala'), ('Poland', 'Poland'), ('Africa/Asmera', 'Africa/Asmera'), ('America/Toronto', 'America/Toronto'), ('America/Aruba', 'America/Aruba'), ('America/Scoresbysund', 'America/Scoresbysund'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Australia/Adelaide', 'Australia/Adelaide'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Etc/GMT+3', 'Etc/GMT+3'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('Asia/Taipei', 'Asia/Taipei'), ('Australia/ACT', 'Australia/ACT'), ('America/Knox_IN', 'America/Knox_IN'), ('Africa/Conakry', 'Africa/Conakry'), ('America/Denver', 'America/Denver'), ('US/Aleutian', 'US/Aleutian'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('America/Rio_Branco', 'America/Rio_Branco'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('America/Kralendijk', 'America/Kralendijk'), ('America/Moncton', 'America/Moncton'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('GMT+0', 'GMT+0'), ('Europe/Vatican', 'Europe/Vatican'), ('ROK', 'ROK'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Asia/Rangoon', 'Asia/Rangoon'), ('Asia/Brunei', 'Asia/Brunei'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('America/Eirunepe', 'America/Eirunepe'), ('Indian/Cocos', 'Indian/Cocos'), ('Asia/Jakarta', 'Asia/Jakarta'), ('America/Detroit', 'America/Detroit'), ('America/Santiago', 'America/Santiago'), ('America/Shiprock', 'America/Shiprock'), ('America/Boise', 'America/Boise'), ('Asia/Samarkand', 'Asia/Samarkand'), ('America/Sitka', 'America/Sitka'), ('Europe/Prague', 'Europe/Prague'), ('Europe/Simferopol', 'Europe/Simferopol'), ('America/Campo_Grande', 'America/Campo_Grande'), ('Indian/Mayotte', 'Indian/Mayotte'), ('America/Boa_Vista', 'America/Boa_Vista'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Etc/GMT-3', 'Etc/GMT-3'), ('GMT', 'GMT'), ('GMT-0', 'GMT-0'), ('Africa/Tripoli', 'Africa/Tripoli'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Asia/Baku', 'Asia/Baku'), ('Africa/Gaborone', 'Africa/Gaborone'), ('Indian/Christmas', 'Indian/Christmas'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('NZ', 'NZ'), ('Australia/Sydney', 'Australia/Sydney'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Etc/GMT-13', 'Etc/GMT-13'), ('America/Mexico_City', 'America/Mexico_City'), ('Pacific/Apia', 'Pacific/Apia'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('America/Dawson', 'America/Dawson'), ('America/Fortaleza', 'America/Fortaleza'), ('Australia/Currie', 'Australia/Currie'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('Europe/Zagreb', 'Europe/Zagreb'), ('US/East-Indiana', 'US/East-Indiana'), ('Etc/GMT+11', 'Etc/GMT+11'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Atlantic/Canary', 'Atlantic/Canary'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Asia/Macao', 'Asia/Macao'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('Asia/Chita', 'Asia/Chita'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('Etc/GMT-10', 'Etc/GMT-10'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Asia/Kashgar', 'Asia/Kashgar'), ('Etc/GMT-1', 'Etc/GMT-1'), ('EST5EDT', 'EST5EDT'), ('America/Marigot', 'America/Marigot'), ('MET', 'MET'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('Asia/Barnaul', 'Asia/Barnaul'), ('Etc/GMT-14', 'Etc/GMT-14'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('America/Cuiaba', 'America/Cuiaba'), ('Asia/Oral', 'Asia/Oral'), ('America/Menominee', 'America/Menominee'), ('Asia/Makassar', 'Asia/Makassar'), ('Canada/Eastern', 'Canada/Eastern'), ('Africa/Luanda', 'Africa/Luanda'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Etc/GMT+1', 'Etc/GMT+1'), ('America/Regina', 'America/Regina'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('Pacific/Auckland', 'Pacific/Auckland'), ('Europe/Belfast', 'Europe/Belfast'), ('America/Cancun', 'America/Cancun'), ('Asia/Anadyr', 'Asia/Anadyr'), ('Europe/Helsinki', 'Europe/Helsinki'), ('Eire', 'Eire'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('Australia/Darwin', 'Australia/Darwin'), ('Canada/Mountain', 'Canada/Mountain'), ('Europe/Bucharest', 'Europe/Bucharest'), ('Europe/Kyiv', 'Europe/Kyiv'), ('W-SU', 'W-SU'), ('NZ-CHAT', 'NZ-CHAT'), ('America/St_Thomas', 'America/St_Thomas'), ('America/Barbados', 'America/Barbados'), ('America/Noronha', 'America/Noronha'), ('Indian/Reunion', 'Indian/Reunion'), ('Africa/Dakar', 'Africa/Dakar'), ('America/Goose_Bay', 'America/Goose_Bay'), ('Australia/Hobart', 'Australia/Hobart'), ('Etc/GMT+2', 'Etc/GMT+2'), ('Europe/Skopje', 'Europe/Skopje'), ('Australia/North', 'Australia/North'), ('America/Adak', 'America/Adak'), ('America/Montreal', 'America/Montreal'), ('America/Nipigon', 'America/Nipigon'), ('Pacific/Midway', 'Pacific/Midway'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('Indian/Mahe', 'Indian/Mahe'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('America/Caracas', 'America/Caracas'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('Etc/GMT-2', 'Etc/GMT-2'), ('US/Eastern', 'US/Eastern'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('America/Antigua', 'America/Antigua'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('Etc/GMT+7', 'Etc/GMT+7'), ('Europe/Rome', 'Europe/Rome'), ('Europe/Volgograd', 'Europe/Volgograd'), ('Africa/Freetown', 'Africa/Freetown'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('UCT', 'UCT'), ('Indian/Chagos', 'Indian/Chagos'), ('America/Recife', 'America/Recife'), ('Asia/Dubai', 'Asia/Dubai'), ('Navajo', 'Navajo'), ('Asia/Harbin', 'Asia/Harbin'), ('Africa/Lusaka', 'Africa/Lusaka'), ('America/Paramaribo', 'America/Paramaribo'), ('MST', 'MST'), ('America/Chicago', 'America/Chicago'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Asia/Colombo', 'Asia/Colombo'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('Asia/Hebron', 'Asia/Hebron'), ('America/Belem', 'America/Belem'), ('Europe/Saratov', 'Europe/Saratov'), ('WET', 'WET'), ('Pacific/Truk', 'Pacific/Truk'), ('Africa/Niamey', 'Africa/Niamey'), ('America/Whitehorse', 'America/Whitehorse'), ('Africa/Harare', 'Africa/Harare'), ('America/Chihuahua', 'America/Chihuahua'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Asia/Yangon', 'Asia/Yangon'), ('PST8PDT', 'PST8PDT'), ('Asia/Riyadh', 'Asia/Riyadh'), ('Turkey', 'Turkey'), ('America/Porto_Acre', 'America/Porto_Acre'), ('America/Miquelon', 'America/Miquelon'), ('CET', 'CET'), ('Etc/GMT+6', 'Etc/GMT+6'), ('America/Guayaquil', 'America/Guayaquil'), ('GMT0', 'GMT0'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('America/Nome', 'America/Nome'), ('Asia/Vientiane', 'Asia/Vientiane'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('America/Grand_Turk', 'America/Grand_Turk'), ('Europe/Sofia', 'Europe/Sofia'), ('Asia/Kolkata', 'Asia/Kolkata'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Factory', 'Factory'), ('Australia/Eucla', 'Australia/Eucla'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('America/Louisville', 'America/Louisville'), ('Europe/Stockholm', 'Europe/Stockholm'), ('ROC', 'ROC'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('America/Araguaina', 'America/Araguaina'), ('America/Phoenix', 'America/Phoenix'), ('Africa/Monrovia', 'Africa/Monrovia'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('Africa/Banjul', 'Africa/Banjul'), ('Europe/Athens', 'Europe/Athens'), ('Africa/Lagos', 'Africa/Lagos'), ('Brazil/East', 'Brazil/East'), ('Kwajalein', 'Kwajalein'), ('America/Anchorage', 'America/Anchorage'), ('America/Edmonton', 'America/Edmonton'), ('America/Merida', 'America/Merida')], default='Europe/London', max_length=35),
        ),
    ]