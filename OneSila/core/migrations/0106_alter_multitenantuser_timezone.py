# Generated by Django 5.0.2 on 2024-07-11 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0105_alter_multitenantuser_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('Mexico/BajaSur', 'Mexico/BajaSur'), ('Asia/Chungking', 'Asia/Chungking'), ('Etc/GMT-3', 'Etc/GMT-3'), ('Etc/Zulu', 'Etc/Zulu'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('Africa/Bamako', 'Africa/Bamako'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('GMT+0', 'GMT+0'), ('Asia/Kuwait', 'Asia/Kuwait'), ('America/Moncton', 'America/Moncton'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Europe/Athens', 'Europe/Athens'), ('Canada/Eastern', 'Canada/Eastern'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('America/Thule', 'America/Thule'), ('Brazil/West', 'Brazil/West'), ('Japan', 'Japan'), ('Australia/LHI', 'Australia/LHI'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('America/Mendoza', 'America/Mendoza'), ('Africa/Maseru', 'Africa/Maseru'), ('America/Atka', 'America/Atka'), ('Canada/Yukon', 'Canada/Yukon'), ('America/St_Kitts', 'America/St_Kitts'), ('Europe/Zurich', 'Europe/Zurich'), ('Indian/Mauritius', 'Indian/Mauritius'), ('America/Nome', 'America/Nome'), ('Canada/Central', 'Canada/Central'), ('Asia/Dubai', 'Asia/Dubai'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Asia/Tehran', 'Asia/Tehran'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('Etc/GMT-14', 'Etc/GMT-14'), ('America/Anchorage', 'America/Anchorage'), ('Europe/Lisbon', 'Europe/Lisbon'), ('America/Hermosillo', 'America/Hermosillo'), ('Asia/Baku', 'Asia/Baku'), ('Navajo', 'Navajo'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('Etc/GMT0', 'Etc/GMT0'), ('Etc/GMT+9', 'Etc/GMT+9'), ('America/Scoresbysund', 'America/Scoresbysund'), ('America/Recife', 'America/Recife'), ('Asia/Karachi', 'Asia/Karachi'), ('America/Guadeloupe', 'America/Guadeloupe'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('MST', 'MST'), ('Africa/Ceuta', 'Africa/Ceuta'), ('Asia/Oral', 'Asia/Oral'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('Chile/Continental', 'Chile/Continental'), ('America/Grenada', 'America/Grenada'), ('America/Cuiaba', 'America/Cuiaba'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('America/Iqaluit', 'America/Iqaluit'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('America/Boa_Vista', 'America/Boa_Vista'), ('America/Santarem', 'America/Santarem'), ('HST', 'HST'), ('Asia/Hebron', 'Asia/Hebron'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('America/Havana', 'America/Havana'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Etc/GMT+2', 'Etc/GMT+2'), ('Africa/Kigali', 'Africa/Kigali'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('Asia/Bangkok', 'Asia/Bangkok'), ('Europe/Samara', 'Europe/Samara'), ('Asia/Nicosia', 'Asia/Nicosia'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('Asia/Brunei', 'Asia/Brunei'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Asia/Macao', 'Asia/Macao'), ('Asia/Urumqi', 'Asia/Urumqi'), ('America/Indianapolis', 'America/Indianapolis'), ('America/Goose_Bay', 'America/Goose_Bay'), ('Africa/Niamey', 'Africa/Niamey'), ('Asia/Macau', 'Asia/Macau'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('Africa/Bangui', 'Africa/Bangui'), ('Europe/Kiev', 'Europe/Kiev'), ('EET', 'EET'), ('America/Martinique', 'America/Martinique'), ('Africa/Harare', 'Africa/Harare'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Asia/Aden', 'Asia/Aden'), ('Asia/Samarkand', 'Asia/Samarkand'), ('America/Bogota', 'America/Bogota'), ('America/Rosario', 'America/Rosario'), ('Australia/North', 'Australia/North'), ('Libya', 'Libya'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('America/Fortaleza', 'America/Fortaleza'), ('America/Regina', 'America/Regina'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Factory', 'Factory'), ('Africa/Asmera', 'Africa/Asmera'), ('America/Maceio', 'America/Maceio'), ('Greenwich', 'Greenwich'), ('Africa/Lome', 'Africa/Lome'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('Indian/Chagos', 'Indian/Chagos'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('America/Metlakatla', 'America/Metlakatla'), ('America/Barbados', 'America/Barbados'), ('America/Nassau', 'America/Nassau'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Europe/Dublin', 'Europe/Dublin'), ('Asia/Qatar', 'Asia/Qatar'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('US/Arizona', 'US/Arizona'), ('UTC', 'UTC'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('Asia/Tashkent', 'Asia/Tashkent'), ('America/Detroit', 'America/Detroit'), ('America/Denver', 'America/Denver'), ('Pacific/Efate', 'Pacific/Efate'), ('Asia/Kabul', 'Asia/Kabul'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('Europe/London', 'Europe/London'), ('Australia/West', 'Australia/West'), ('America/Manaus', 'America/Manaus'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('Etc/GMT+5', 'Etc/GMT+5'), ('Africa/Freetown', 'Africa/Freetown'), ('America/Montreal', 'America/Montreal'), ('US/Eastern', 'US/Eastern'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('Asia/Istanbul', 'Asia/Istanbul'), ('America/St_Johns', 'America/St_Johns'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('US/Samoa', 'US/Samoa'), ('America/Knox_IN', 'America/Knox_IN'), ('Pacific/Auckland', 'Pacific/Auckland'), ('Australia/Perth', 'Australia/Perth'), ('Australia/Eucla', 'Australia/Eucla'), ('Europe/Warsaw', 'Europe/Warsaw'), ('Etc/GMT-10', 'Etc/GMT-10'), ('Asia/Harbin', 'Asia/Harbin'), ('America/Bahia', 'America/Bahia'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Pacific/Chatham', 'Pacific/Chatham'), ('America/Chihuahua', 'America/Chihuahua'), ('Europe/Kirov', 'Europe/Kirov'), ('America/Dominica', 'America/Dominica'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Atlantic/Canary', 'Atlantic/Canary'), ('Etc/GMT+8', 'Etc/GMT+8'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Pacific/Midway', 'Pacific/Midway'), ('WET', 'WET'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Etc/Universal', 'Etc/Universal'), ('Europe/Berlin', 'Europe/Berlin'), ('Africa/Tunis', 'Africa/Tunis'), ('Eire', 'Eire'), ('Europe/Oslo', 'Europe/Oslo'), ('Etc/GMT+11', 'Etc/GMT+11'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('PST8PDT', 'PST8PDT'), ('America/Grand_Turk', 'America/Grand_Turk'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('America/Rio_Branco', 'America/Rio_Branco'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Africa/Maputo', 'Africa/Maputo'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('Asia/Muscat', 'Asia/Muscat'), ('Asia/Singapore', 'Asia/Singapore'), ('Etc/GMT-12', 'Etc/GMT-12'), ('Africa/Juba', 'Africa/Juba'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('Etc/GMT+10', 'Etc/GMT+10'), ('Etc/GMT+3', 'Etc/GMT+3'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Asia/Barnaul', 'Asia/Barnaul'), ('CET', 'CET'), ('America/Menominee', 'America/Menominee'), ('America/Monterrey', 'America/Monterrey'), ('Europe/Kyiv', 'Europe/Kyiv'), ('America/Jamaica', 'America/Jamaica'), ('Africa/Libreville', 'Africa/Libreville'), ('Australia/Adelaide', 'Australia/Adelaide'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('America/Miquelon', 'America/Miquelon'), ('Indian/Comoro', 'Indian/Comoro'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('America/Paramaribo', 'America/Paramaribo'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Pacific/Yap', 'Pacific/Yap'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('Australia/South', 'Australia/South'), ('Africa/Khartoum', 'Africa/Khartoum'), ('Asia/Rangoon', 'Asia/Rangoon'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Europe/Helsinki', 'Europe/Helsinki'), ('Etc/Greenwich', 'Etc/Greenwich'), ('America/Yellowknife', 'America/Yellowknife'), ('America/Lima', 'America/Lima'), ('America/Kralendijk', 'America/Kralendijk'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('America/Marigot', 'America/Marigot'), ('Iceland', 'Iceland'), ('America/Antigua', 'America/Antigua'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('America/Porto_Velho', 'America/Porto_Velho'), ('ROC', 'ROC'), ('Pacific/Easter', 'Pacific/Easter'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Australia/Queensland', 'Australia/Queensland'), ('America/Toronto', 'America/Toronto'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Asia/Thimphu', 'Asia/Thimphu'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Asia/Thimbu', 'Asia/Thimbu'), ('Universal', 'Universal'), ('America/Atikokan', 'America/Atikokan'), ('Asia/Almaty', 'Asia/Almaty'), ('Australia/Sydney', 'Australia/Sydney'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('America/Santiago', 'America/Santiago'), ('Europe/Monaco', 'Europe/Monaco'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('Asia/Saigon', 'Asia/Saigon'), ('CST6CDT', 'CST6CDT'), ('Etc/GMT-6', 'Etc/GMT-6'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Turkey', 'Turkey'), ('Europe/Malta', 'Europe/Malta'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Portugal', 'Portugal'), ('America/Tijuana', 'America/Tijuana'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('Australia/Darwin', 'Australia/Darwin'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('Canada/Pacific', 'Canada/Pacific'), ('Africa/Algiers', 'Africa/Algiers'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Etc/GMT+6', 'Etc/GMT+6'), ('Asia/Dacca', 'Asia/Dacca'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('Asia/Kashgar', 'Asia/Kashgar'), ('America/New_York', 'America/New_York'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Europe/San_Marino', 'Europe/San_Marino'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Europe/Belfast', 'Europe/Belfast'), ('America/Cayenne', 'America/Cayenne'), ('Etc/GMT-13', 'Etc/GMT-13'), ('Asia/Yangon', 'Asia/Yangon'), ('Asia/Damascus', 'Asia/Damascus'), ('Australia/Hobart', 'Australia/Hobart'), ('America/Whitehorse', 'America/Whitehorse'), ('America/Sitka', 'America/Sitka'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Asia/Manila', 'Asia/Manila'), ('Etc/GMT-11', 'Etc/GMT-11'), ('America/Los_Angeles', 'America/Los_Angeles'), ('W-SU', 'W-SU'), ('America/Curacao', 'America/Curacao'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Africa/Douala', 'Africa/Douala'), ('Australia/Currie', 'Australia/Currie'), ('America/Edmonton', 'America/Edmonton'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Asia/Makassar', 'Asia/Makassar'), ('Europe/Madrid', 'Europe/Madrid'), ('Europe/Vatican', 'Europe/Vatican'), ('GMT0', 'GMT0'), ('Poland', 'Poland'), ('Etc/GMT+7', 'Etc/GMT+7'), ('America/Aruba', 'America/Aruba'), ('Europe/Paris', 'Europe/Paris'), ('Indian/Christmas', 'Indian/Christmas'), ('America/Matamoros', 'America/Matamoros'), ('Pacific/Wake', 'Pacific/Wake'), ('Asia/Magadan', 'Asia/Magadan'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('America/Panama', 'America/Panama'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Indian/Mayotte', 'Indian/Mayotte'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('America/Phoenix', 'America/Phoenix'), ('Etc/GMT-0', 'Etc/GMT-0'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Asia/Anadyr', 'Asia/Anadyr'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('America/Halifax', 'America/Halifax'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Asia/Gaza', 'Asia/Gaza'), ('America/Godthab', 'America/Godthab'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('Europe/Vienna', 'Europe/Vienna'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('Europe/Moscow', 'Europe/Moscow'), ('Asia/Colombo', 'Asia/Colombo'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Europe/Tallinn', 'Europe/Tallinn'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Pacific/Palau', 'Pacific/Palau'), ('US/Hawaii', 'US/Hawaii'), ('NZ-CHAT', 'NZ-CHAT'), ('Africa/Mbabane', 'Africa/Mbabane'), ('Israel', 'Israel'), ('America/Eirunepe', 'America/Eirunepe'), ('Europe/Zagreb', 'Europe/Zagreb'), ('Africa/Tripoli', 'Africa/Tripoli'), ('America/Ensenada', 'America/Ensenada'), ('Asia/Vientiane', 'Asia/Vientiane'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('America/Cordoba', 'America/Cordoba'), ('America/Vancouver', 'America/Vancouver'), ('Asia/Yerevan', 'Asia/Yerevan'), ('America/Montserrat', 'America/Montserrat'), ('Canada/Mountain', 'Canada/Mountain'), ('Indian/Maldives', 'Indian/Maldives'), ('America/Noronha', 'America/Noronha'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Asia/Dili', 'Asia/Dili'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Europe/Jersey', 'Europe/Jersey'), ('Pacific/Ponape', 'Pacific/Ponape'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('Asia/Atyrau', 'Asia/Atyrau'), ('Africa/Lusaka', 'Africa/Lusaka'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('Asia/Jayapura', 'Asia/Jayapura'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('Africa/Accra', 'Africa/Accra'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Europe/Busingen', 'Europe/Busingen'), ('Africa/Nairobi', 'Africa/Nairobi'), ('MST7MDT', 'MST7MDT'), ('Brazil/Acre', 'Brazil/Acre'), ('America/Nipigon', 'America/Nipigon'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('America/Yakutat', 'America/Yakutat'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('Cuba', 'Cuba'), ('Pacific/Apia', 'Pacific/Apia'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('Europe/Tirane', 'Europe/Tirane'), ('Pacific/Niue', 'Pacific/Niue'), ('America/Cayman', 'America/Cayman'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Africa/Cairo', 'Africa/Cairo'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('ROK', 'ROK'), ('Asia/Beirut', 'Asia/Beirut'), ('America/Mazatlan', 'America/Mazatlan'), ('Africa/Gaborone', 'Africa/Gaborone'), ('Brazil/East', 'Brazil/East'), ('America/Lower_Princes', 'America/Lower_Princes'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('America/Creston', 'America/Creston'), ('Asia/Chita', 'Asia/Chita'), ('Europe/Volgograd', 'Europe/Volgograd'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('Europe/Andorra', 'Europe/Andorra'), ('Europe/Chisinau', 'Europe/Chisinau'), ('America/Swift_Current', 'America/Swift_Current'), ('Australia/Tasmania', 'Australia/Tasmania'), ('Asia/Seoul', 'Asia/Seoul'), ('Australia/Victoria', 'Australia/Victoria'), ('America/Belize', 'America/Belize'), ('Asia/Jakarta', 'Asia/Jakarta'), ('America/Anguilla', 'America/Anguilla'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('US/Alaska', 'US/Alaska'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('Europe/Podgorica', 'Europe/Podgorica'), ('America/Pangnirtung', 'America/Pangnirtung'), ('America/Tortola', 'America/Tortola'), ('Europe/Riga', 'Europe/Riga'), ('Europe/Bucharest', 'Europe/Bucharest'), ('America/Catamarca', 'America/Catamarca'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('Europe/Vaduz', 'Europe/Vaduz'), ('NZ', 'NZ'), ('America/Shiprock', 'America/Shiprock'), ('Indian/Cocos', 'Indian/Cocos'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('America/Boise', 'America/Boise'), ('Kwajalein', 'Kwajalein'), ('Pacific/Truk', 'Pacific/Truk'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('Europe/Sofia', 'Europe/Sofia'), ('Etc/UCT', 'Etc/UCT'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('MET', 'MET'), ('US/East-Indiana', 'US/East-Indiana'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('America/Virgin', 'America/Virgin'), ('Pacific/Majuro', 'Pacific/Majuro'), ('Europe/Saratov', 'Europe/Saratov'), ('Antarctica/Casey', 'Antarctica/Casey'), ('Europe/Skopje', 'Europe/Skopje'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('Etc/UTC', 'Etc/UTC'), ('Asia/Amman', 'Asia/Amman'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Africa/Lagos', 'Africa/Lagos'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('Asia/Kolkata', 'Asia/Kolkata'), ('Pacific/Guam', 'Pacific/Guam'), ('Africa/Asmara', 'Africa/Asmara'), ('Asia/Hovd', 'Asia/Hovd'), ('Pacific/Wallis', 'Pacific/Wallis'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('Asia/Taipei', 'Asia/Taipei'), ('Etc/GMT-4', 'Etc/GMT-4'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('America/Mexico_City', 'America/Mexico_City'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Africa/Bissau', 'Africa/Bissau'), ('Etc/GMT+1', 'Etc/GMT+1'), ('Europe/Rome', 'Europe/Rome'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('GB-Eire', 'GB-Eire'), ('Hongkong', 'Hongkong'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('America/Guayaquil', 'America/Guayaquil'), ('Africa/Abidjan', 'Africa/Abidjan'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('US/Aleutian', 'US/Aleutian'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('America/Montevideo', 'America/Montevideo'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Asia/Calcutta', 'Asia/Calcutta'), ('America/Asuncion', 'America/Asuncion'), ('Europe/Minsk', 'Europe/Minsk'), ('America/St_Vincent', 'America/St_Vincent'), ('US/Pacific', 'US/Pacific'), ('Asia/Kuching', 'Asia/Kuching'), ('Asia/Baghdad', 'Asia/Baghdad'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('Australia/NSW', 'Australia/NSW'), ('Africa/Banjul', 'Africa/Banjul'), ('America/Winnipeg', 'America/Winnipeg'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Singapore', 'Singapore'), ('Europe/Simferopol', 'Europe/Simferopol'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('America/Inuvik', 'America/Inuvik'), ('America/Araguaina', 'America/Araguaina'), ('Africa/Monrovia', 'Africa/Monrovia'), ('America/La_Paz', 'America/La_Paz'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('Pacific/Gambier', 'Pacific/Gambier'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Jamaica', 'Jamaica'), ('Etc/GMT-9', 'Etc/GMT-9'), ('EST', 'EST'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('Africa/Kampala', 'Africa/Kampala'), ('Australia/Melbourne', 'Australia/Melbourne'), ('EST5EDT', 'EST5EDT'), ('US/Mountain', 'US/Mountain'), ('Africa/Malabo', 'Africa/Malabo'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('GMT-0', 'GMT-0'), ('UCT', 'UCT'), ('Iran', 'Iran'), ('America/Louisville', 'America/Louisville'), ('Africa/Casablanca', 'Africa/Casablanca'), ('Canada/Atlantic', 'Canada/Atlantic'), ('GMT', 'GMT'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Asia/Omsk', 'Asia/Omsk'), ('Zulu', 'Zulu'), ('America/Managua', 'America/Managua'), ('Etc/GMT-2', 'Etc/GMT-2'), ('America/Rainy_River', 'America/Rainy_River'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('America/Dawson', 'America/Dawson'), ('America/Guyana', 'America/Guyana'), ('Australia/Canberra', 'Australia/Canberra'), ('Europe/Nicosia', 'Europe/Nicosia'), ('America/St_Thomas', 'America/St_Thomas'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('build/etc/localtime', 'build/etc/localtime'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('US/Central', 'US/Central'), ('PRC', 'PRC'), ('America/Merida', 'America/Merida'), ('America/Ojinaga', 'America/Ojinaga'), ('Egypt', 'Egypt'), ('Europe/Budapest', 'Europe/Budapest'), ('Europe/Brussels', 'Europe/Brussels'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('Indian/Reunion', 'Indian/Reunion'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Australia/ACT', 'Australia/ACT'), ('America/Jujuy', 'America/Jujuy'), ('Mexico/General', 'Mexico/General'), ('America/Nuuk', 'America/Nuuk'), ('America/El_Salvador', 'America/El_Salvador'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Indian/Mahe', 'Indian/Mahe'), ('Etc/GMT-1', 'Etc/GMT-1'), ('America/St_Lucia', 'America/St_Lucia'), ('Pacific/Johnston', 'Pacific/Johnston'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('Etc/GMT+0', 'Etc/GMT+0'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('America/Guatemala', 'America/Guatemala'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('America/Porto_Acre', 'America/Porto_Acre'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Africa/Dakar', 'Africa/Dakar'), ('Europe/Vilnius', 'Europe/Vilnius'), ('GB', 'GB'), ('America/Campo_Grande', 'America/Campo_Grande'), ('Etc/GMT', 'Etc/GMT'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Europe/Prague', 'Europe/Prague'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('America/Adak', 'America/Adak'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('America/Belem', 'America/Belem'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('America/Juneau', 'America/Juneau'), ('America/Cancun', 'America/Cancun'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('America/Chicago', 'America/Chicago'), ('Europe/Belgrade', 'Europe/Belgrade'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('Africa/Luanda', 'Africa/Luanda'), ('Asia/Famagusta', 'Asia/Famagusta'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('Africa/Conakry', 'Africa/Conakry'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('US/Michigan', 'US/Michigan'), ('America/Caracas', 'America/Caracas'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Africa/Windhoek', 'Africa/Windhoek'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('Asia/Riyadh', 'Asia/Riyadh'), ('America/Resolute', 'America/Resolute'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem')], default='Europe/London', max_length=35),
        ),
    ]