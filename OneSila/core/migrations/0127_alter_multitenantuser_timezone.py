from django.db import migrations, models
# Generated by Django 5.0.7 on 2024-07-21 10:22


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0126_alter_multitenantuser_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('Asia/Ashgabat', 'Asia/Ashgabat'), ('Etc/GMT+0', 'Etc/GMT+0'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('US/Arizona', 'US/Arizona'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('America/Marigot', 'America/Marigot'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('America/Detroit', 'America/Detroit'), ('Asia/Aqtau', 'Asia/Aqtau'), ('EET', 'EET'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('Israel', 'Israel'), ('America/Santarem', 'America/Santarem'), ('Africa/Luanda', 'Africa/Luanda'), ('GMT-0', 'GMT-0'), ('America/Juneau', 'America/Juneau'), ('Zulu', 'Zulu'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('America/St_Johns', 'America/St_Johns'), ('US/Samoa', 'US/Samoa'), ('Asia/Bahrain', 'Asia/Bahrain'), ('US/Aleutian', 'US/Aleutian'), ('GMT+0', 'GMT+0'), ('US/East-Indiana', 'US/East-Indiana'), ('Indian/Christmas', 'Indian/Christmas'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('Asia/Gaza', 'Asia/Gaza'), ('Africa/Libreville', 'Africa/Libreville'), ('Europe/Volgograd', 'Europe/Volgograd'), ('Africa/Gaborone', 'Africa/Gaborone'), ('Portugal', 'Portugal'), ('Eire', 'Eire'), ('US/Central', 'US/Central'), ('Africa/Asmara', 'Africa/Asmara'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Europe/Nicosia', 'Europe/Nicosia'), ('Australia/Adelaide', 'Australia/Adelaide'), ('Asia/Magadan', 'Asia/Magadan'), ('Europe/Kiev', 'Europe/Kiev'), ('America/Porto_Velho', 'America/Porto_Velho'), ('America/Phoenix', 'America/Phoenix'), ('Canada/Eastern', 'Canada/Eastern'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('America/Guadeloupe', 'America/Guadeloupe'), ('Libya', 'Libya'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Etc/GMT0', 'Etc/GMT0'), ('build/etc/localtime', 'build/etc/localtime'), ('Africa/Banjul', 'Africa/Banjul'), ('Africa/Harare', 'Africa/Harare'), ('America/Barbados', 'America/Barbados'), ('Etc/GMT-9', 'Etc/GMT-9'), ('Europe/Riga', 'Europe/Riga'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('US/Eastern', 'US/Eastern'), ('MET', 'MET'), ('Asia/Barnaul', 'Asia/Barnaul'), ('America/Anguilla', 'America/Anguilla'), ('Africa/Bissau', 'Africa/Bissau'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('Pacific/Auckland', 'Pacific/Auckland'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Europe/Tallinn', 'Europe/Tallinn'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('Turkey', 'Turkey'), ('America/Mazatlan', 'America/Mazatlan'), ('US/Alaska', 'US/Alaska'), ('America/Tijuana', 'America/Tijuana'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Pacific/Ponape', 'Pacific/Ponape'), ('Europe/Belgrade', 'Europe/Belgrade'), ('America/Eirunepe', 'America/Eirunepe'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('CET', 'CET'), ('Africa/Juba', 'Africa/Juba'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('Europe/Simferopol', 'Europe/Simferopol'), ('America/Rio_Branco', 'America/Rio_Branco'), ('America/Guyana', 'America/Guyana'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('Australia/North', 'Australia/North'), ('Africa/Tunis', 'Africa/Tunis'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('Europe/Vatican', 'Europe/Vatican'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('Asia/Muscat', 'Asia/Muscat'), ('Africa/Lagos', 'Africa/Lagos'), ('Chile/Continental', 'Chile/Continental'), ('Pacific/Wallis', 'Pacific/Wallis'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('America/Managua', 'America/Managua'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('Europe/Helsinki', 'Europe/Helsinki'), ('US/Hawaii', 'US/Hawaii'), ('Africa/Casablanca', 'Africa/Casablanca'), ('America/Curacao', 'America/Curacao'), ('EST', 'EST'), ('Asia/Urumqi', 'Asia/Urumqi'), ('Australia/Brisbane', 'Australia/Brisbane'), ('America/Rainy_River', 'America/Rainy_River'), ('Asia/Jakarta', 'Asia/Jakarta'), ('Asia/Baku', 'Asia/Baku'), ('Asia/Tehran', 'Asia/Tehran'), ('Europe/Berlin', 'Europe/Berlin'), ('Asia/Makassar', 'Asia/Makassar'), ('Asia/Tashkent', 'Asia/Tashkent'), ('America/Santiago', 'America/Santiago'), ('Asia/Almaty', 'Asia/Almaty'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('Factory', 'Factory'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('Greenwich', 'Greenwich'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('Pacific/Kanton', 'Pacific/Kanton'), ('America/Shiprock', 'America/Shiprock'), ('Australia/Queensland', 'Australia/Queensland'), ('Africa/Niamey', 'Africa/Niamey'), ('Europe/Vaduz', 'Europe/Vaduz'), ('America/Adak', 'America/Adak'), ('America/Louisville', 'America/Louisville'), ('Poland', 'Poland'), ('Hongkong', 'Hongkong'), ('Europe/Bucharest', 'Europe/Bucharest'), ('America/Merida', 'America/Merida'), ('Etc/GMT+2', 'Etc/GMT+2'), ('America/St_Kitts', 'America/St_Kitts'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Pacific/Easter', 'Pacific/Easter'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Asia/Kuwait', 'Asia/Kuwait'), ('Etc/Universal', 'Etc/Universal'), ('Asia/Katmandu', 'Asia/Katmandu'), ('America/Paramaribo', 'America/Paramaribo'), ('Europe/Malta', 'Europe/Malta'), ('Etc/GMT+9', 'Etc/GMT+9'), ('Etc/GMT-10', 'Etc/GMT-10'), ('Europe/Warsaw', 'Europe/Warsaw'), ('America/Grand_Turk', 'America/Grand_Turk'), ('Australia/ACT', 'Australia/ACT'), ('America/Vancouver', 'America/Vancouver'), ('America/Recife', 'America/Recife'), ('Africa/Maseru', 'Africa/Maseru'), ('America/Hermosillo', 'America/Hermosillo'), ('Asia/Qatar', 'Asia/Qatar'), ('America/Chihuahua', 'America/Chihuahua'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Europe/San_Marino', 'Europe/San_Marino'), ('Etc/GMT+6', 'Etc/GMT+6'), ('NZ-CHAT', 'NZ-CHAT'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Kwajalein', 'Kwajalein'), ('America/St_Thomas', 'America/St_Thomas'), ('W-SU', 'W-SU'), ('America/Belem', 'America/Belem'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('Iran', 'Iran'), ('Asia/Dili', 'Asia/Dili'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Australia/South', 'Australia/South'), ('Australia/Lindeman', 'Australia/Lindeman'), ('UCT', 'UCT'), ('Europe/Budapest', 'Europe/Budapest'), ('America/Chicago', 'America/Chicago'), ('America/Montreal', 'America/Montreal'), ('Etc/GMT+1', 'Etc/GMT+1'), ('America/Matamoros', 'America/Matamoros'), ('Etc/GMT-14', 'Etc/GMT-14'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('Jamaica', 'Jamaica'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('Australia/Tasmania', 'Australia/Tasmania'), ('America/Aruba', 'America/Aruba'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('Etc/GMT-2', 'Etc/GMT-2'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Asia/Yangon', 'Asia/Yangon'), ('Australia/Eucla', 'Australia/Eucla'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Egypt', 'Egypt'), ('America/Inuvik', 'America/Inuvik'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('America/Nuuk', 'America/Nuuk'), ('Indian/Cocos', 'Indian/Cocos'), ('America/Martinique', 'America/Martinique'), ('America/Maceio', 'America/Maceio'), ('Asia/Vientiane', 'Asia/Vientiane'), ('America/St_Lucia', 'America/St_Lucia'), ('Europe/Zagreb', 'Europe/Zagreb'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('America/Havana', 'America/Havana'), ('America/Swift_Current', 'America/Swift_Current'), ('America/Montevideo', 'America/Montevideo'), ('Europe/Saratov', 'Europe/Saratov'), ('Pacific/Johnston', 'Pacific/Johnston'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('MST7MDT', 'MST7MDT'), ('GMT', 'GMT'), ('CST6CDT', 'CST6CDT'), ('America/La_Paz', 'America/La_Paz'), ('Europe/Tirane', 'Europe/Tirane'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Australia/Hobart', 'Australia/Hobart'), ('Etc/GMT-13', 'Etc/GMT-13'), ('America/Cayenne', 'America/Cayenne'), ('Asia/Famagusta', 'Asia/Famagusta'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('ROC', 'ROC'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Asia/Macau', 'Asia/Macau'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('PST8PDT', 'PST8PDT'), ('Cuba', 'Cuba'), ('Asia/Taipei', 'Asia/Taipei'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Europe/Oslo', 'Europe/Oslo'), ('Asia/Bishkek', 'Asia/Bishkek'), ('America/Antigua', 'America/Antigua'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Africa/Abidjan', 'Africa/Abidjan'), ('Europe/Kirov', 'Europe/Kirov'), ('Africa/Tripoli', 'Africa/Tripoli'), ('ROK', 'ROK'), ('America/Nassau', 'America/Nassau'), ('Etc/GMT-5', 'Etc/GMT-5'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('Pacific/Yap', 'Pacific/Yap'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Africa/Freetown', 'Africa/Freetown'), ('Brazil/East', 'Brazil/East'), ('US/Mountain', 'US/Mountain'), ('America/Campo_Grande', 'America/Campo_Grande'), ('Asia/Harbin', 'Asia/Harbin'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Europe/Skopje', 'Europe/Skopje'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('Pacific/Apia', 'Pacific/Apia'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('Asia/Kabul', 'Asia/Kabul'), ('America/Iqaluit', 'America/Iqaluit'), ('Asia/Nicosia', 'Asia/Nicosia'), ('Etc/GMT+7', 'Etc/GMT+7'), ('America/Godthab', 'America/Godthab'), ('Asia/Chita', 'Asia/Chita'), ('Etc/GMT-6', 'Etc/GMT-6'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('America/Bogota', 'America/Bogota'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('UTC', 'UTC'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('Asia/Riyadh', 'Asia/Riyadh'), ('Brazil/Acre', 'Brazil/Acre'), ('Australia/LHI', 'Australia/LHI'), ('HST', 'HST'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('America/Indianapolis', 'America/Indianapolis'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('America/Fortaleza', 'America/Fortaleza'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('Europe/Andorra', 'Europe/Andorra'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('Indian/Chagos', 'Indian/Chagos'), ('America/Boa_Vista', 'America/Boa_Vista'), ('America/Winnipeg', 'America/Winnipeg'), ('America/Thule', 'America/Thule'), ('Africa/Douala', 'Africa/Douala'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('America/Goose_Bay', 'America/Goose_Bay'),
                                   ('Navajo', 'Navajo'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('America/Cancun', 'America/Cancun'), ('America/Cayman', 'America/Cayman'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Europe/Vilnius', 'Europe/Vilnius'), ('America/Denver', 'America/Denver'), ('Asia/Amman', 'Asia/Amman'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('Antarctica/Casey', 'Antarctica/Casey'), ('Etc/GMT-3', 'Etc/GMT-3'), ('America/Atikokan', 'America/Atikokan'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Asia/Macao', 'Asia/Macao'), ('Asia/Seoul', 'Asia/Seoul'), ('Etc/Greenwich', 'Etc/Greenwich'), ('Europe/Minsk', 'Europe/Minsk'), ('Australia/West', 'Australia/West'), ('America/Creston', 'America/Creston'), ('Australia/Sydney', 'Australia/Sydney'), ('Europe/Brussels', 'Europe/Brussels'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('America/Jujuy', 'America/Jujuy'), ('Indian/Mayotte', 'Indian/Mayotte'), ('Asia/Singapore', 'Asia/Singapore'), ('Africa/Asmera', 'Africa/Asmera'), ('America/Rosario', 'America/Rosario'), ('America/Metlakatla', 'America/Metlakatla'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Europe/London', 'Europe/London'), ('America/Halifax', 'America/Halifax'), ('America/Nome', 'America/Nome'), ('Asia/Karachi', 'Asia/Karachi'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('Asia/Bangkok', 'Asia/Bangkok'), ('Pacific/Efate', 'Pacific/Efate'), ('WET', 'WET'), ('America/Yellowknife', 'America/Yellowknife'), ('Australia/Perth', 'Australia/Perth'), ('America/Virgin', 'America/Virgin'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Europe/Belfast', 'Europe/Belfast'), ('America/Resolute', 'America/Resolute'), ('Europe/Athens', 'Europe/Athens'), ('EST5EDT', 'EST5EDT'), ('Japan', 'Japan'), ('America/Guatemala', 'America/Guatemala'), ('PRC', 'PRC'), ('Asia/Jayapura', 'Asia/Jayapura'), ('Europe/Moscow', 'Europe/Moscow'), ('Europe/Podgorica', 'Europe/Podgorica'), ('Asia/Shanghai', 'Asia/Shanghai'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('Australia/Victoria', 'Australia/Victoria'), ('Asia/Baghdad', 'Asia/Baghdad'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('Etc/GMT+8', 'Etc/GMT+8'), ('Canada/Mountain', 'Canada/Mountain'), ('Brazil/West', 'Brazil/West'), ('Africa/Monrovia', 'Africa/Monrovia'), ('America/Yakutat', 'America/Yakutat'), ('Asia/Oral', 'Asia/Oral'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('Asia/Kashgar', 'Asia/Kashgar'), ('Indian/Comoro', 'Indian/Comoro'), ('Africa/Lusaka', 'Africa/Lusaka'), ('Pacific/Midway', 'Pacific/Midway'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Australia/Darwin', 'Australia/Darwin'), ('Europe/Chisinau', 'Europe/Chisinau'), ('America/Dominica', 'America/Dominica'), ('America/Pangnirtung', 'America/Pangnirtung'), ('Pacific/Gambier', 'Pacific/Gambier'), ('America/Dawson', 'America/Dawson'), ('Pacific/Palau', 'Pacific/Palau'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('Europe/Prague', 'Europe/Prague'), ('Asia/Khandyga', 'Asia/Khandyga'), ('America/Atka', 'America/Atka'), ('Asia/Rangoon', 'Asia/Rangoon'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('Asia/Chungking', 'Asia/Chungking'), ('Asia/Hebron', 'Asia/Hebron'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('Etc/GMT+5', 'Etc/GMT+5'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('Pacific/Niue', 'Pacific/Niue'), ('Asia/Aden', 'Asia/Aden'), ('Canada/Yukon', 'Canada/Yukon'), ('Australia/Canberra', 'Australia/Canberra'), ('Asia/Dacca', 'Asia/Dacca'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('America/Whitehorse', 'America/Whitehorse'), ('Etc/GMT-11', 'Etc/GMT-11'), ('GB', 'GB'), ('America/St_Vincent', 'America/St_Vincent'), ('Asia/Manila', 'Asia/Manila'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('Asia/Anadyr', 'Asia/Anadyr'), ('America/Araguaina', 'America/Araguaina'), ('Africa/Bangui', 'Africa/Bangui'), ('Africa/Maputo', 'Africa/Maputo'), ('Europe/Madrid', 'Europe/Madrid'), ('GB-Eire', 'GB-Eire'), ('Pacific/Truk', 'Pacific/Truk'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Asia/Dubai', 'Asia/Dubai'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('America/Porto_Acre', 'America/Porto_Acre'), ('Asia/Omsk', 'Asia/Omsk'), ('America/El_Salvador', 'America/El_Salvador'), ('GMT0', 'GMT0'), ('America/Toronto', 'America/Toronto'), ('Asia/Colombo', 'Asia/Colombo'), ('Singapore', 'Singapore'), ('Asia/Samarkand', 'Asia/Samarkand'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('America/Kralendijk', 'America/Kralendijk'), ('America/Moncton', 'America/Moncton'), ('America/Los_Angeles', 'America/Los_Angeles'), ('America/Boise', 'America/Boise'), ('US/Michigan', 'US/Michigan'), ('America/Ojinaga', 'America/Ojinaga'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('Africa/Accra', 'Africa/Accra'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('Etc/Zulu', 'Etc/Zulu'), ('US/Pacific', 'US/Pacific'), ('America/Jamaica', 'America/Jamaica'), ('America/Noronha', 'America/Noronha'), ('Africa/Lome', 'Africa/Lome'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Indian/Maldives', 'Indian/Maldives'), ('America/Lima', 'America/Lima'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('America/Asuncion', 'America/Asuncion'), ('Etc/GMT-0', 'Etc/GMT-0'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('Pacific/Chatham', 'Pacific/Chatham'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('America/Mexico_City', 'America/Mexico_City'), ('Etc/GMT-4', 'Etc/GMT-4'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('America/Nipigon', 'America/Nipigon'), ('Africa/Khartoum', 'Africa/Khartoum'), ('Asia/Atyrau', 'Asia/Atyrau'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('Africa/Cairo', 'Africa/Cairo'), ('Europe/Jersey', 'Europe/Jersey'), ('Europe/Sofia', 'Europe/Sofia'), ('America/Catamarca', 'America/Catamarca'), ('Pacific/Wake', 'Pacific/Wake'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Asia/Calcutta', 'Asia/Calcutta'), ('America/Regina', 'America/Regina'), ('Asia/Hovd', 'Asia/Hovd'), ('Etc/GMT+3', 'Etc/GMT+3'), ('Canada/Pacific', 'Canada/Pacific'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Europe/Monaco', 'Europe/Monaco'), ('Europe/Busingen', 'Europe/Busingen'), ('America/Knox_IN', 'America/Knox_IN'), ('Asia/Brunei', 'Asia/Brunei'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('America/Menominee', 'America/Menominee'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('America/Grenada', 'America/Grenada'), ('Europe/Kyiv', 'Europe/Kyiv'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Europe/Rome', 'Europe/Rome'), ('America/New_York', 'America/New_York'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('America/Mendoza', 'America/Mendoza'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('NZ', 'NZ'), ('Africa/Nairobi', 'Africa/Nairobi'), ('Asia/Kolkata', 'Asia/Kolkata'), ('America/Cordoba', 'America/Cordoba'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('Pacific/Majuro', 'Pacific/Majuro'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('America/Guayaquil', 'America/Guayaquil'), ('Africa/Dakar', 'Africa/Dakar'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('Etc/UTC', 'Etc/UTC'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Asia/Thimphu', 'Asia/Thimphu'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Etc/GMT+10', 'Etc/GMT+10'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('Africa/Kigali', 'Africa/Kigali'), ('America/Sitka', 'America/Sitka'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Iceland', 'Iceland'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('America/Monterrey', 'America/Monterrey'), ('Pacific/Guam', 'Pacific/Guam'), ('Pacific/Fiji', 'Pacific/Fiji'), ('America/Anchorage', 'America/Anchorage'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('Europe/Dublin', 'Europe/Dublin'), ('Mexico/General', 'Mexico/General'), ('Asia/Damascus', 'Asia/Damascus'), ('Africa/Conakry', 'Africa/Conakry'), ('Indian/Mauritius', 'Indian/Mauritius'), ('Indian/Reunion', 'Indian/Reunion'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('Africa/Bamako', 'Africa/Bamako'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Etc/GMT-12', 'Etc/GMT-12'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('America/Lower_Princes', 'America/Lower_Princes'), ('Canada/Central', 'Canada/Central'), ('Etc/GMT-1', 'Etc/GMT-1'), ('Africa/Algiers', 'Africa/Algiers'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Asia/Thimbu', 'Asia/Thimbu'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('Universal', 'Universal'), ('Australia/NSW', 'Australia/NSW'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Asia/Kuching', 'Asia/Kuching'), ('Europe/Samara', 'Europe/Samara'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Australia/Currie', 'Australia/Currie'), ('Asia/Istanbul', 'Asia/Istanbul'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('Europe/Vienna', 'Europe/Vienna'), ('America/Manaus', 'America/Manaus'), ('America/Edmonton', 'America/Edmonton'), ('Indian/Mahe', 'Indian/Mahe'), ('Atlantic/Canary', 'Atlantic/Canary'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('America/Belize', 'America/Belize'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('America/Montserrat', 'America/Montserrat'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('Africa/Kampala', 'Africa/Kampala'), ('Etc/GMT', 'Etc/GMT'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('Canada/Atlantic', 'Canada/Atlantic'), ('America/Cuiaba', 'America/Cuiaba'), ('America/Ensenada', 'America/Ensenada'), ('Africa/Mbabane', 'Africa/Mbabane'), ('Asia/Saigon', 'Asia/Saigon'), ('Etc/GMT+11', 'Etc/GMT+11'), ('America/Caracas', 'America/Caracas'), ('Africa/Malabo', 'Africa/Malabo'), ('Asia/Beirut', 'Asia/Beirut'), ('America/Scoresbysund', 'America/Scoresbysund'), ('Europe/Paris', 'Europe/Paris'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('America/Tortola', 'America/Tortola'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('Etc/UCT', 'Etc/UCT'), ('Africa/Ceuta', 'Africa/Ceuta'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('MST', 'MST'), ('Europe/Zurich', 'Europe/Zurich'), ('America/Miquelon', 'America/Miquelon'), ('America/Bahia', 'America/Bahia'), ('America/Panama', 'America/Panama'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby')], default='Europe/London', max_length=35),
        ),
    ]