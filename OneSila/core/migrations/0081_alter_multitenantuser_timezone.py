# Generated by Django 5.0.2 on 2024-06-04 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0080_alter_multitenantuser_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('Eire', 'Eire'), ('W-SU', 'W-SU'), ('America/Toronto', 'America/Toronto'), ('America/Noronha', 'America/Noronha'), ('Australia/Canberra', 'Australia/Canberra'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('America/Tijuana', 'America/Tijuana'), ('Asia/Oral', 'Asia/Oral'), ('Asia/Kuwait', 'Asia/Kuwait'), ('America/Jujuy', 'America/Jujuy'), ('Etc/GMT+7', 'Etc/GMT+7'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('Europe/Bucharest', 'Europe/Bucharest'), ('America/Sitka', 'America/Sitka'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Australia/LHI', 'Australia/LHI'), ('Asia/Colombo', 'Asia/Colombo'), ('Canada/Mountain', 'Canada/Mountain'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('Australia/Queensland', 'Australia/Queensland'), ('Europe/Dublin', 'Europe/Dublin'), ('America/Guayaquil', 'America/Guayaquil'), ('America/Antigua', 'America/Antigua'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('America/Atikokan', 'America/Atikokan'), ('EST5EDT', 'EST5EDT'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Asia/Muscat', 'Asia/Muscat'), ('Europe/Belfast', 'Europe/Belfast'), ('America/Resolute', 'America/Resolute'), ('Etc/GMT-14', 'Etc/GMT-14'), ('Europe/Belgrade', 'Europe/Belgrade'), ('America/Thule', 'America/Thule'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('America/Santiago', 'America/Santiago'), ('CST6CDT', 'CST6CDT'), ('America/Vancouver', 'America/Vancouver'), ('America/Indianapolis', 'America/Indianapolis'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Asia/Dacca', 'Asia/Dacca'), ('Asia/Chungking', 'Asia/Chungking'), ('America/Knox_IN', 'America/Knox_IN'), ('Europe/Madrid', 'Europe/Madrid'), ('America/Caracas', 'America/Caracas'), ('Israel', 'Israel'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('America/Moncton', 'America/Moncton'), ('Asia/Hovd', 'Asia/Hovd'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Indian/Mahe', 'Indian/Mahe'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('America/Catamarca', 'America/Catamarca'), ('America/Mendoza', 'America/Mendoza'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('Asia/Anadyr', 'Asia/Anadyr'), ('Europe/Vatican', 'Europe/Vatican'), ('Africa/Bissau', 'Africa/Bissau'), ('Africa/Banjul', 'Africa/Banjul'), ('Africa/Tripoli', 'Africa/Tripoli'), ('Pacific/Fiji', 'Pacific/Fiji'), ('America/Montreal', 'America/Montreal'), ('Australia/Currie', 'Australia/Currie'), ('America/Cayenne', 'America/Cayenne'), ('US/Aleutian', 'US/Aleutian'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Etc/GMT+5', 'Etc/GMT+5'), ('America/Adak', 'America/Adak'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Pacific/Palau', 'Pacific/Palau'), ('Europe/Tirane', 'Europe/Tirane'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('GMT+0', 'GMT+0'), ('Africa/Accra', 'Africa/Accra'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('Asia/Singapore', 'Asia/Singapore'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('America/Lower_Princes', 'America/Lower_Princes'), ('America/Cancun', 'America/Cancun'), ('Asia/Brunei', 'Asia/Brunei'), ('Africa/Dakar', 'Africa/Dakar'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('Asia/Jakarta', 'Asia/Jakarta'), ('Asia/Macau', 'Asia/Macau'), ('America/Araguaina', 'America/Araguaina'), ('America/St_Thomas', 'America/St_Thomas'), ('Etc/GMT-13', 'Etc/GMT-13'), ('America/Anguilla', 'America/Anguilla'), ('Antarctica/Casey', 'Antarctica/Casey'), ('America/Regina', 'America/Regina'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('America/Porto_Acre', 'America/Porto_Acre'), ('America/Anchorage', 'America/Anchorage'), ('Indian/Chagos', 'Indian/Chagos'), ('Africa/Mbabane', 'Africa/Mbabane'), ('Canada/Atlantic', 'Canada/Atlantic'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('Etc/Universal', 'Etc/Universal'), ('America/St_Vincent', 'America/St_Vincent'), ('Asia/Harbin', 'Asia/Harbin'), ('Etc/GMT+0', 'Etc/GMT+0'), ('Pacific/Guam', 'Pacific/Guam'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('Asia/Kashgar', 'Asia/Kashgar'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('Europe/Riga', 'Europe/Riga'), ('Etc/GMT0', 'Etc/GMT0'), ('America/Juneau', 'America/Juneau'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('America/Marigot', 'America/Marigot'), ('Africa/Tunis', 'Africa/Tunis'), ('Asia/Seoul', 'Asia/Seoul'), ('Asia/Almaty', 'Asia/Almaty'), ('America/Maceio', 'America/Maceio'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('America/Los_Angeles', 'America/Los_Angeles'), ('Europe/Kyiv', 'Europe/Kyiv'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('America/Monterrey', 'America/Monterrey'), ('EET', 'EET'), ('Africa/Douala', 'Africa/Douala'), ('Asia/Famagusta', 'Asia/Famagusta'), ('Pacific/Yap', 'Pacific/Yap'), ('Etc/UCT', 'Etc/UCT'), ('Mexico/General', 'Mexico/General'), ('Pacific/Majuro', 'Pacific/Majuro'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('Asia/Baghdad', 'Asia/Baghdad'), ('America/Metlakatla', 'America/Metlakatla'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('Africa/Kigali', 'Africa/Kigali'), ('Europe/Nicosia', 'Europe/Nicosia'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('Etc/GMT-2', 'Etc/GMT-2'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Libya', 'Libya'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('Canada/Yukon', 'Canada/Yukon'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('Pacific/Auckland', 'Pacific/Auckland'), ('America/Cordoba', 'America/Cordoba'), ('America/St_Lucia', 'America/St_Lucia'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('Etc/GMT-4', 'Etc/GMT-4'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('Asia/Samarkand', 'Asia/Samarkand'), ('Asia/Vientiane', 'Asia/Vientiane'), ('America/Phoenix', 'America/Phoenix'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Asia/Dubai', 'Asia/Dubai'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('America/Fortaleza', 'America/Fortaleza'), ('America/Creston', 'America/Creston'), ('Africa/Lome', 'Africa/Lome'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('Asia/Magadan', 'Asia/Magadan'), ('Pacific/Chatham', 'Pacific/Chatham'), ('Africa/Maseru', 'Africa/Maseru'), ('Africa/Lusaka', 'Africa/Lusaka'), ('Australia/Sydney', 'Australia/Sydney'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Europe/Monaco', 'Europe/Monaco'), ('America/Whitehorse', 'America/Whitehorse'), ('Pacific/Apia', 'Pacific/Apia'), ('Africa/Gaborone', 'Africa/Gaborone'), ('Asia/Jayapura', 'Asia/Jayapura'), ('Etc/GMT-6', 'Etc/GMT-6'), ('ROC', 'ROC'), ('CET', 'CET'), ('America/Halifax', 'America/Halifax'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('Europe/Zagreb', 'Europe/Zagreb'), ('America/La_Paz', 'America/La_Paz'), ('America/Aruba', 'America/Aruba'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('America/Lima', 'America/Lima'), ('Etc/GMT-10', 'Etc/GMT-10'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('Africa/Monrovia', 'Africa/Monrovia'), ('Europe/Malta', 'Europe/Malta'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Brazil/East', 'Brazil/East'), ('America/Guatemala', 'America/Guatemala'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Pacific/Midway', 'Pacific/Midway'), ('Africa/Algiers', 'Africa/Algiers'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Iceland', 'Iceland'), ('Africa/Lagos', 'Africa/Lagos'), ('Asia/Thimbu', 'Asia/Thimbu'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('Japan', 'Japan'), ('Asia/Gaza', 'Asia/Gaza'), ('America/Asuncion', 'America/Asuncion'), ('Europe/Kirov', 'Europe/Kirov'), ('Zulu', 'Zulu'), ('GMT-0', 'GMT-0'), ('America/Havana', 'America/Havana'), ('Pacific/Wake', 'Pacific/Wake'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('Etc/GMT+10', 'Etc/GMT+10'), ('Africa/Freetown', 'Africa/Freetown'), ('America/Swift_Current', 'America/Swift_Current'), ('Singapore', 'Singapore'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('America/Ensenada', 'America/Ensenada'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('America/Paramaribo', 'America/Paramaribo'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Etc/GMT+2', 'Etc/GMT+2'), ('GMT', 'GMT'), ('Africa/Conakry', 'Africa/Conakry'), ('America/Detroit', 'America/Detroit'), ('GMT0', 'GMT0'), ('America/Bahia', 'America/Bahia'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Europe/Podgorica', 'Europe/Podgorica'), ('America/Edmonton', 'America/Edmonton'), ('Asia/Aden', 'Asia/Aden'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('Indian/Cocos', 'Indian/Cocos'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('Asia/Thimphu', 'Asia/Thimphu'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Asia/Taipei', 'Asia/Taipei'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('Poland', 'Poland'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('Africa/Khartoum', 'Africa/Khartoum'), ('America/Rio_Branco', 'America/Rio_Branco'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('America/Hermosillo', 'America/Hermosillo'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('Pacific/Efate', 'Pacific/Efate'), ('Africa/Bangui', 'Africa/Bangui'), ('Asia/Bangkok', 'Asia/Bangkok'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Pacific/Kanton', 'Pacific/Kanton'), ('America/Menominee', 'America/Menominee'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('America/Dawson', 'America/Dawson'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('Europe/Minsk', 'Europe/Minsk'), ('Europe/Chisinau', 'Europe/Chisinau'), ('Europe/Zurich', 'Europe/Zurich'), ('Etc/GMT+11', 'Etc/GMT+11'), ('America/Nassau', 'America/Nassau'), ('NZ', 'NZ'), ('Indian/Comoro', 'Indian/Comoro'), ('America/Panama', 'America/Panama'), ('America/Chihuahua', 'America/Chihuahua'), ('Turkey', 'Turkey'), ('Africa/Niamey', 'Africa/Niamey'), ('America/Guyana', 'America/Guyana'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('Europe/Budapest', 'Europe/Budapest'), ('Canada/Pacific', 'Canada/Pacific'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Navajo', 'Navajo'), ('America/Mazatlan', 'America/Mazatlan'), ('Etc/GMT+8', 'Etc/GMT+8'), ('Europe/Simferopol', 'Europe/Simferopol'), ('Asia/Rangoon', 'Asia/Rangoon'), ('America/Costa_Rica', 'America/Costa_Rica'), ('UTC', 'UTC'), ('America/Recife', 'America/Recife'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('GB-Eire', 'GB-Eire'), ('Africa/Bamako', 'Africa/Bamako'), ('America/St_Johns', 'America/St_Johns'), ('Europe/Skopje', 'Europe/Skopje'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('Asia/Qatar', 'Asia/Qatar'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('America/Belem', 'America/Belem'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Australia/Eucla', 'Australia/Eucla'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('America/Merida', 'America/Merida'), ('Brazil/West', 'Brazil/West'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('America/Atka', 'America/Atka'), ('US/Alaska', 'US/Alaska'), ('America/Belize', 'America/Belize'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('Greenwich', 'Greenwich'), ('Pacific/Gambier', 'Pacific/Gambier'), ('Etc/GMT-12', 'Etc/GMT-12'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('PST8PDT', 'PST8PDT'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('Asia/Beirut', 'Asia/Beirut'), ('Canada/Central', 'Canada/Central'), ('America/Denver', 'America/Denver'), ('US/Hawaii', 'US/Hawaii'), ('America/Kralendijk', 'America/Kralendijk'), ('Asia/Chita', 'Asia/Chita'), ('Asia/Kuching', 'Asia/Kuching'), ('US/Pacific', 'US/Pacific'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Europe/London', 'Europe/London'), ('Africa/Casablanca', 'Africa/Casablanca'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Asia/Omsk', 'Asia/Omsk'), ('Asia/Istanbul', 'Asia/Istanbul'), ('PRC', 'PRC'), ('Etc/GMT+4', 'Etc/GMT+4'), ('America/Nipigon', 'America/Nipigon'), ('US/East-Indiana', 'US/East-Indiana'), ('America/Virgin', 'America/Virgin'), ('Atlantic/Azores', 'Atlantic/Azores'), ('America/Inuvik', 'America/Inuvik'), ('Pacific/Ponape', 'Pacific/Ponape'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('Pacific/Easter', 'Pacific/Easter'), ('EST', 'EST'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('America/Martinique', 'America/Martinique'), ('Iran', 'Iran'), ('Indian/Christmas', 'Indian/Christmas'), ('Europe/Helsinki', 'Europe/Helsinki'), ('America/Grand_Turk', 'America/Grand_Turk'), ('Europe/Vilnius', 'Europe/Vilnius'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('Asia/Kabul', 'Asia/Kabul'), ('America/Cayman', 'America/Cayman'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('Etc/GMT-8', 'Etc/GMT-8'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Etc/GMT-3', 'Etc/GMT-3'), ('Australia/Victoria', 'Australia/Victoria'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('US/Central', 'US/Central'), ('America/Boise', 'America/Boise'), ('Asia/Yangon', 'Asia/Yangon'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Portugal', 'Portugal'), ('Africa/Abidjan', 'Africa/Abidjan'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Europe/Saratov', 'Europe/Saratov'), ('Australia/Hobart', 'Australia/Hobart'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Pacific/Niue', 'Pacific/Niue'), ('Asia/Kolkata', 'Asia/Kolkata'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('America/Winnipeg', 'America/Winnipeg'), ('Europe/Oslo', 'Europe/Oslo'), ('Africa/Ceuta', 'Africa/Ceuta'), ('Africa/Luanda', 'Africa/Luanda'), ('America/Eirunepe', 'America/Eirunepe'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('Europe/Vaduz', 'Europe/Vaduz'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('Canada/Eastern', 'Canada/Eastern'), ('Europe/Kiev', 'Europe/Kiev'), ('Etc/GMT-9', 'Etc/GMT-9'), ('America/Miquelon', 'America/Miquelon'), ('Europe/Moscow', 'Europe/Moscow'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('Africa/Malabo', 'Africa/Malabo'), ('Europe/Paris', 'Europe/Paris'), ('Pacific/Truk', 'Pacific/Truk'), ('Indian/Mayotte', 'Indian/Mayotte'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Africa/Harare', 'Africa/Harare'), ('HST', 'HST'), ('America/Jamaica', 'America/Jamaica'), ('America/Boa_Vista', 'America/Boa_Vista'), ('Africa/Juba', 'Africa/Juba'), ('Hongkong', 'Hongkong'), ('Pacific/Johnston', 'Pacific/Johnston'), ('Egypt', 'Egypt'), ('Indian/Maldives', 'Indian/Maldives'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('Asia/Amman', 'Asia/Amman'), ('Australia/Perth', 'Australia/Perth'), ('Etc/GMT+1', 'Etc/GMT+1'), ('Asia/Karachi', 'Asia/Karachi'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('MST7MDT', 'MST7MDT'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('Australia/Tasmania', 'Australia/Tasmania'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('America/Rainy_River', 'America/Rainy_River'), ('Europe/Athens', 'Europe/Athens'), ('Jamaica', 'Jamaica'), ('America/Louisville', 'America/Louisville'), ('Australia/NSW', 'Australia/NSW'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Kwajalein', 'Kwajalein'), ('Asia/Saigon', 'Asia/Saigon'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('Indian/Reunion', 'Indian/Reunion'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('Europe/Prague', 'Europe/Prague'), ('Europe/San_Marino', 'Europe/San_Marino'), ('America/Yakutat', 'America/Yakutat'), ('Asia/Makassar', 'Asia/Makassar'), ('America/Guadeloupe', 'America/Guadeloupe'), ('NZ-CHAT', 'NZ-CHAT'), ('Asia/Dili', 'Asia/Dili'), ('Africa/Asmara', 'Africa/Asmara'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('Europe/Volgograd', 'Europe/Volgograd'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('Etc/Greenwich', 'Etc/Greenwich'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('Europe/Andorra', 'Europe/Andorra'), ('Asia/Tomsk', 'Asia/Tomsk'), ('America/Godthab', 'America/Godthab'), ('Australia/Adelaide', 'Australia/Adelaide'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Africa/Cairo', 'Africa/Cairo'), ('America/Matamoros', 'America/Matamoros'), ('Asia/Macao', 'Asia/Macao'), ('Etc/GMT-0', 'Etc/GMT-0'), ('Etc/GMT+6', 'Etc/GMT+6'), ('Atlantic/Canary', 'Atlantic/Canary'), ('America/Bogota', 'America/Bogota'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('Asia/Manila', 'Asia/Manila'), ('Pacific/Wallis', 'Pacific/Wallis'), ('Australia/Darwin', 'Australia/Darwin'), ('Africa/Maputo', 'Africa/Maputo'), ('Europe/Berlin', 'Europe/Berlin'), ('America/Grenada', 'America/Grenada'), ('Africa/Kampala', 'Africa/Kampala'), ('Brazil/Acre', 'Brazil/Acre'), ('Etc/GMT', 'Etc/GMT'), ('Europe/Rome', 'Europe/Rome'), ('America/Santarem', 'America/Santarem'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('America/Scoresbysund', 'America/Scoresbysund'), ('Africa/Nairobi', 'Africa/Nairobi'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Asia/Baku', 'Asia/Baku'), ('Asia/Hebron', 'Asia/Hebron'), ('America/St_Kitts', 'America/St_Kitts'), ('Asia/Tehran', 'Asia/Tehran'), ('Etc/GMT-1', 'Etc/GMT-1'), ('America/Nuuk', 'America/Nuuk'), ('America/Curacao', 'America/Curacao'), ('Indian/Mauritius', 'Indian/Mauritius'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('Europe/Brussels', 'Europe/Brussels'), ('America/Barbados', 'America/Barbados'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('America/El_Salvador', 'America/El_Salvador'), ('Asia/Atyrau', 'Asia/Atyrau'), ('US/Mountain', 'US/Mountain'), ('America/Cuiaba', 'America/Cuiaba'), ('America/Rosario', 'America/Rosario'), ('Europe/Sofia', 'Europe/Sofia'), ('Cuba', 'Cuba'), ('US/Michigan', 'US/Michigan'), ('Asia/Urumqi', 'Asia/Urumqi'), ('Universal', 'Universal'), ('UCT', 'UCT'), ('America/Chicago', 'America/Chicago'), ('Asia/Damascus', 'Asia/Damascus'), ('America/Mexico_City', 'America/Mexico_City'), ('Etc/GMT-11', 'Etc/GMT-11'), ('Europe/Warsaw', 'Europe/Warsaw'), ('ROK', 'ROK'), ('America/Nome', 'America/Nome'), ('Africa/Libreville', 'Africa/Libreville'), ('Asia/Qostanay', 'Asia/Qostanay'), ('America/Managua', 'America/Managua'), ('Europe/Tallinn', 'Europe/Tallinn'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('Etc/GMT+9', 'Etc/GMT+9'), ('America/Porto_Velho', 'America/Porto_Velho'), ('Europe/Busingen', 'Europe/Busingen'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Europe/Jersey', 'Europe/Jersey'), ('Africa/Asmera', 'Africa/Asmera'), ('America/Goose_Bay', 'America/Goose_Bay'), ('Etc/Zulu', 'Etc/Zulu'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('WET', 'WET'), ('America/Iqaluit', 'America/Iqaluit'), ('Etc/UTC', 'Etc/UTC'), ('Europe/Samara', 'Europe/Samara'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Europe/Vienna', 'Europe/Vienna'), ('America/Montserrat', 'America/Montserrat'), ('America/Pangnirtung', 'America/Pangnirtung'), ('America/Dominica', 'America/Dominica'), ('GB', 'GB'), ('America/Yellowknife', 'America/Yellowknife'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('Australia/West', 'Australia/West'), ('Chile/Continental', 'Chile/Continental'), ('America/Ojinaga', 'America/Ojinaga'), ('US/Arizona', 'US/Arizona'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('America/Shiprock', 'America/Shiprock'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('America/Tortola', 'America/Tortola'), ('America/New_York', 'America/New_York'), ('America/Montevideo', 'America/Montevideo'), ('US/Eastern', 'US/Eastern'), ('MST', 'MST'), ('US/Samoa', 'US/Samoa'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('America/Manaus', 'America/Manaus'), ('Asia/Barnaul', 'Asia/Barnaul'), ('America/Campo_Grande', 'America/Campo_Grande'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Australia/North', 'Australia/North'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('Australia/South', 'Australia/South'), ('Factory', 'Factory'), ('Australia/ACT', 'Australia/ACT'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Asia/Riyadh', 'Asia/Riyadh'), ('Asia/Nicosia', 'Asia/Nicosia'), ('build/etc/localtime', 'build/etc/localtime'), ('Etc/GMT+3', 'Etc/GMT+3'), ('MET', 'MET')], default='Europe/London', max_length=35),
        ),
    ]
