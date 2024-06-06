# Generated by Django 5.0.2 on 2024-05-31 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0076_alter_multitenantuser_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('Africa/Timbuktu', 'Africa/Timbuktu'), ('Europe/Helsinki', 'Europe/Helsinki'), ('Pacific/Easter', 'Pacific/Easter'), ('Africa/Kampala', 'Africa/Kampala'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('Pacific/Niue', 'Pacific/Niue'), ('Asia/Qatar', 'Asia/Qatar'), ('America/Lima', 'America/Lima'), ('Europe/Belgrade', 'Europe/Belgrade'), ('Hongkong', 'Hongkong'), ('Etc/GMT+10', 'Etc/GMT+10'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('America/Dominica', 'America/Dominica'), ('Africa/Asmera', 'Africa/Asmera'), ('Etc/GMT-6', 'Etc/GMT-6'), ('US/Eastern', 'US/Eastern'), ('Africa/Douala', 'Africa/Douala'), ('Pacific/Wallis', 'Pacific/Wallis'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('GMT+0', 'GMT+0'), ('Asia/Jakarta', 'Asia/Jakarta'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('Africa/Algiers', 'Africa/Algiers'), ('Eire', 'Eire'), ('Europe/Kiev', 'Europe/Kiev'), ('Europe/Busingen', 'Europe/Busingen'), ('America/Atka', 'America/Atka'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('America/Ojinaga', 'America/Ojinaga'), ('Asia/Dubai', 'Asia/Dubai'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('America/Nome', 'America/Nome'), ('Asia/Nicosia', 'Asia/Nicosia'), ('America/Adak', 'America/Adak'), ('Europe/Zurich', 'Europe/Zurich'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('Africa/Luanda', 'Africa/Luanda'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('Etc/GMT+11', 'Etc/GMT+11'), ('America/Indianapolis', 'America/Indianapolis'), ('Africa/Freetown', 'Africa/Freetown'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Europe/San_Marino', 'Europe/San_Marino'), ('America/Caracas', 'America/Caracas'), ('Europe/Skopje', 'Europe/Skopje'), ('America/Regina', 'America/Regina'), ('US/East-Indiana', 'US/East-Indiana'), ('America/Louisville', 'America/Louisville'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Europe/Warsaw', 'Europe/Warsaw'), ('Etc/GMT+8', 'Etc/GMT+8'), ('Kwajalein', 'Kwajalein'), ('America/Dawson', 'America/Dawson'), ('America/Inuvik', 'America/Inuvik'), ('Libya', 'Libya'), ('Asia/Colombo', 'Asia/Colombo'), ('Europe/Chisinau', 'Europe/Chisinau'), ('Africa/Juba', 'Africa/Juba'), ('Asia/Brunei', 'Asia/Brunei'), ('Canada/Yukon', 'Canada/Yukon'), ('America/Montevideo', 'America/Montevideo'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Canada/Mountain', 'Canada/Mountain'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('America/Denver', 'America/Denver'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Europe/Vienna', 'Europe/Vienna'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('Asia/Hebron', 'Asia/Hebron'), ('Asia/Tashkent', 'Asia/Tashkent'), ('America/Noronha', 'America/Noronha'), ('GB', 'GB'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('America/Recife', 'America/Recife'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Africa/Niamey', 'Africa/Niamey'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Pacific/Efate', 'Pacific/Efate'), ('Israel', 'Israel'), ('America/Mazatlan', 'America/Mazatlan'), ('America/Yakutat', 'America/Yakutat'), ('Etc/GMT', 'Etc/GMT'), ('America/Edmonton', 'America/Edmonton'), ('EST5EDT', 'EST5EDT'), ('Jamaica', 'Jamaica'), ('America/Santarem', 'America/Santarem'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('EST', 'EST'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Europe/Prague', 'Europe/Prague'), ('America/Catamarca', 'America/Catamarca'), ('America/Los_Angeles', 'America/Los_Angeles'), ('America/Halifax', 'America/Halifax'), ('Indian/Cocos', 'Indian/Cocos'), ('America/Araguaina', 'America/Araguaina'), ('Africa/Lagos', 'Africa/Lagos'), ('America/Tortola', 'America/Tortola'), ('Asia/Amman', 'Asia/Amman'), ('Europe/Stockholm', 'Europe/Stockholm'), ('America/Toronto', 'America/Toronto'), ('Iceland', 'Iceland'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Etc/GMT-11', 'Etc/GMT-11'), ('America/Swift_Current', 'America/Swift_Current'), ('America/Pangnirtung', 'America/Pangnirtung'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('America/Kralendijk', 'America/Kralendijk'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Africa/Nairobi', 'Africa/Nairobi'), ('America/Asuncion', 'America/Asuncion'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('Africa/Bissau', 'Africa/Bissau'), ('Europe/Nicosia', 'Europe/Nicosia'), ('Canada/Atlantic', 'Canada/Atlantic'), ('America/Nuuk', 'America/Nuuk'), ('MET', 'MET'), ('America/Havana', 'America/Havana'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('Africa/Dakar', 'Africa/Dakar'), ('Zulu', 'Zulu'), ('America/Mexico_City', 'America/Mexico_City'), ('Asia/Riyadh', 'Asia/Riyadh'), ('MST', 'MST'), ('Europe/Belfast', 'Europe/Belfast'), ('Australia/Tasmania', 'Australia/Tasmania'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Africa/Lome', 'Africa/Lome'), ('Cuba', 'Cuba'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Indian/Christmas', 'Indian/Christmas'), ('Asia/Macau', 'Asia/Macau'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('America/Chicago', 'America/Chicago'), ('America/El_Salvador', 'America/El_Salvador'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('Asia/Aqtau', 'Asia/Aqtau'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('Asia/Anadyr', 'Asia/Anadyr'), ('Africa/Malabo', 'Africa/Malabo'), ('Australia/Hobart', 'Australia/Hobart'), ('GB-Eire', 'GB-Eire'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Africa/Conakry', 'Africa/Conakry'), ('ROK', 'ROK'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Factory', 'Factory'), ('Asia/Gaza', 'Asia/Gaza'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Europe/Zagreb', 'Europe/Zagreb'), ('Asia/Kashgar', 'Asia/Kashgar'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('America/Fortaleza', 'America/Fortaleza'), ('America/Eirunepe', 'America/Eirunepe'), ('America/Resolute', 'America/Resolute'), ('Europe/Minsk', 'Europe/Minsk'), ('America/Cancun', 'America/Cancun'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('Asia/Tokyo', 'Asia/Tokyo'), ('America/Creston', 'America/Creston'), ('America/Belem', 'America/Belem'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('Antarctica/Casey', 'Antarctica/Casey'), ('Etc/GMT-0', 'Etc/GMT-0'), ('America/New_York', 'America/New_York'), ('Australia/Adelaide', 'Australia/Adelaide'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('Europe/Budapest', 'Europe/Budapest'), ('Asia/Vientiane', 'Asia/Vientiane'), ('Indian/Reunion', 'Indian/Reunion'), ('Europe/Saratov', 'Europe/Saratov'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Australia/South', 'Australia/South'), ('Australia/Melbourne', 'Australia/Melbourne'), ('CST6CDT', 'CST6CDT'), ('America/Jamaica', 'America/Jamaica'), ('Singapore', 'Singapore'), ('Asia/Seoul', 'Asia/Seoul'), ('Australia/NSW', 'Australia/NSW'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('America/Guadeloupe', 'America/Guadeloupe'), ('America/Nassau', 'America/Nassau'), ('Asia/Magadan', 'Asia/Magadan'), ('Africa/Cairo', 'Africa/Cairo'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('Asia/Dacca', 'Asia/Dacca'), ('Etc/GMT-2', 'Etc/GMT-2'), ('Asia/Hovd', 'Asia/Hovd'), ('Asia/Saigon', 'Asia/Saigon'), ('Asia/Thimphu', 'Asia/Thimphu'), ('Europe/Vaduz', 'Europe/Vaduz'), ('America/Miquelon', 'America/Miquelon'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Iran', 'Iran'), ('Europe/Moscow', 'Europe/Moscow'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('Canada/Eastern', 'Canada/Eastern'), ('America/Cuiaba', 'America/Cuiaba'), ('America/Porto_Velho', 'America/Porto_Velho'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('America/Mendoza', 'America/Mendoza'), ('WET', 'WET'), ('Australia/Queensland', 'Australia/Queensland'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('EET', 'EET'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('Etc/Universal', 'Etc/Universal'), ('build/etc/localtime', 'build/etc/localtime'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('Etc/Zulu', 'Etc/Zulu'), ('Europe/Kirov', 'Europe/Kirov'), ('America/Belize', 'America/Belize'), ('America/Aruba', 'America/Aruba'), ('Asia/Baku', 'Asia/Baku'), ('America/Nipigon', 'America/Nipigon'), ('Africa/Khartoum', 'Africa/Khartoum'), ('Europe/Oslo', 'Europe/Oslo'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('Chile/Continental', 'Chile/Continental'), ('Portugal', 'Portugal'), ('Canada/Pacific', 'Canada/Pacific'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Pacific/Palau', 'Pacific/Palau'), ('America/Juneau', 'America/Juneau'), ('America/Marigot', 'America/Marigot'), ('America/Moncton', 'America/Moncton'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('Australia/Sydney', 'Australia/Sydney'), ('America/Guyana', 'America/Guyana'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('US/Hawaii', 'US/Hawaii'), ('Pacific/Wake', 'Pacific/Wake'), ('America/St_Lucia', 'America/St_Lucia'), ('Asia/Chongqing', 'Asia/Chongqing'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('Europe/Berlin', 'Europe/Berlin'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('Asia/Oral', 'Asia/Oral'), ('Australia/Brisbane', 'Australia/Brisbane'), ('GMT', 'GMT'), ('America/Curacao', 'America/Curacao'), ('Asia/Muscat', 'Asia/Muscat'), ('Australia/Darwin', 'Australia/Darwin'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Etc/GMT+3', 'Etc/GMT+3'), ('America/Panama', 'America/Panama'), ('Europe/Bucharest', 'Europe/Bucharest'), ('Africa/Tunis', 'Africa/Tunis'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Pacific/Truk', 'Pacific/Truk'), ('Etc/GMT+6', 'Etc/GMT+6'), ('Asia/Beirut', 'Asia/Beirut'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Etc/UTC', 'Etc/UTC'), ('Etc/GMT+1', 'Etc/GMT+1'), ('Etc/GMT+7', 'Etc/GMT+7'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Asia/Urumqi', 'Asia/Urumqi'), ('America/Guatemala', 'America/Guatemala'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('UCT', 'UCT'), ('GMT0', 'GMT0'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Etc/GMT+5', 'Etc/GMT+5'), ('Brazil/West', 'Brazil/West'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('America/Sitka', 'America/Sitka'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('America/La_Paz', 'America/La_Paz'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('Europe/Malta', 'Europe/Malta'), ('Africa/Libreville', 'Africa/Libreville'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('America/Paramaribo', 'America/Paramaribo'), ('Atlantic/Canary', 'Atlantic/Canary'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('Australia/Currie', 'Australia/Currie'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('America/Manaus', 'America/Manaus'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('Africa/Monrovia', 'Africa/Monrovia'), ('Africa/Windhoek', 'Africa/Windhoek'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('America/Menominee', 'America/Menominee'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('America/Cordoba', 'America/Cordoba'), ('US/Arizona', 'US/Arizona'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('Asia/Karachi', 'Asia/Karachi'), ('Canada/Central', 'Canada/Central'), ('America/Detroit', 'America/Detroit'), ('Asia/Aden', 'Asia/Aden'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Asia/Omsk', 'Asia/Omsk'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('US/Alaska', 'US/Alaska'), ('America/St_Thomas', 'America/St_Thomas'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('America/Martinique', 'America/Martinique'), ('America/Boa_Vista', 'America/Boa_Vista'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Asia/Damascus', 'Asia/Damascus'), ('Asia/Thimbu', 'Asia/Thimbu'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('Africa/Gaborone', 'Africa/Gaborone'), ('US/Samoa', 'US/Samoa'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Etc/GMT+9', 'Etc/GMT+9'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Pacific/Yap', 'Pacific/Yap'), ('Universal', 'Universal'), ('Asia/Famagusta', 'Asia/Famagusta'), ('Africa/Maseru', 'Africa/Maseru'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('MST7MDT', 'MST7MDT'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('Africa/Mbabane', 'Africa/Mbabane'), ('Asia/Jayapura', 'Asia/Jayapura'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('Asia/Khandyga', 'Asia/Khandyga'), ('UTC', 'UTC'), ('Australia/Perth', 'Australia/Perth'), ('Asia/Dili', 'Asia/Dili'), ('Asia/Kolkata', 'Asia/Kolkata'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Pacific/Auckland', 'Pacific/Auckland'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('America/Lower_Princes', 'America/Lower_Princes'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('Asia/Calcutta', 'Asia/Calcutta'), ('America/Boise', 'America/Boise'), ('America/Matamoros', 'America/Matamoros'), ('America/Whitehorse', 'America/Whitehorse'), ('Asia/Atyrau', 'Asia/Atyrau'), ('Europe/Brussels', 'Europe/Brussels'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('Etc/GMT-12', 'Etc/GMT-12'), ('America/Atikokan', 'America/Atikokan'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('Asia/Macao', 'Asia/Macao'), ('Europe/Bratislava', 'Europe/Bratislava'), ('America/Yellowknife', 'America/Yellowknife'), ('ROC', 'ROC'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Asia/Taipei', 'Asia/Taipei'), ('Asia/Katmandu', 'Asia/Katmandu'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('Etc/GMT+2', 'Etc/GMT+2'), ('Asia/Barnaul', 'Asia/Barnaul'), ('Europe/Monaco', 'Europe/Monaco'), ('America/St_Johns', 'America/St_Johns'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Europe/Volgograd', 'Europe/Volgograd'), ('America/Rio_Branco', 'America/Rio_Branco'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('America/Merida', 'America/Merida'), ('Australia/ACT', 'Australia/ACT'), ('Japan', 'Japan'), ('America/Antigua', 'America/Antigua'), ('America/Anchorage', 'America/Anchorage'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Asia/Harbin', 'Asia/Harbin'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Asia/Kuwait', 'Asia/Kuwait'), ('Etc/GMT0', 'Etc/GMT0'), ('Australia/Canberra', 'Australia/Canberra'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('America/Thule', 'America/Thule'), ('America/Metlakatla', 'America/Metlakatla'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Europe/Athens', 'Europe/Athens'), ('America/Guayaquil', 'America/Guayaquil'), ('America/Barbados', 'America/Barbados'), ('America/Chihuahua', 'America/Chihuahua'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('America/Anguilla', 'America/Anguilla'), ('America/Grenada', 'America/Grenada'), ('America/Jujuy', 'America/Jujuy'), ('Australia/North', 'Australia/North'), ('Indian/Mahe', 'Indian/Mahe'), ('Africa/Casablanca', 'Africa/Casablanca'), ('Europe/Samara', 'Europe/Samara'), ('America/Monterrey', 'America/Monterrey'), ('Europe/Andorra', 'Europe/Andorra'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Africa/Accra', 'Africa/Accra'), ('US/Central', 'US/Central'), ('America/Cayman', 'America/Cayman'), ('Europe/Kyiv', 'Europe/Kyiv'), ('Africa/Tripoli', 'Africa/Tripoli'), ('America/Scoresbysund', 'America/Scoresbysund'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('Etc/GMT-4', 'Etc/GMT-4'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('America/Bogota', 'America/Bogota'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Europe/Jersey', 'Europe/Jersey'), ('Asia/Makassar', 'Asia/Makassar'), ('Australia/West', 'Australia/West'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('America/Rosario', 'America/Rosario'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Asia/Rangoon', 'Asia/Rangoon'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Mexico/General', 'Mexico/General'), ('PST8PDT', 'PST8PDT'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('Asia/Manila', 'Asia/Manila'), ('Indian/Maldives', 'Indian/Maldives'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('Pacific/Chatham', 'Pacific/Chatham'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('Turkey', 'Turkey'), ('US/Michigan', 'US/Michigan'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('Australia/Victoria', 'Australia/Victoria'), ('NZ-CHAT', 'NZ-CHAT'), ('Etc/GMT+0', 'Etc/GMT+0'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Asia/Samarkand', 'Asia/Samarkand'), ('Etc/GMT-14', 'Etc/GMT-14'), ('US/Pacific', 'US/Pacific'), ('America/Hermosillo', 'America/Hermosillo'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('America/St_Vincent', 'America/St_Vincent'), ('America/Porto_Acre', 'America/Porto_Acre'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('Navajo', 'Navajo'), ('Pacific/Midway', 'Pacific/Midway'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('Pacific/Guam', 'Pacific/Guam'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('America/Winnipeg', 'America/Winnipeg'), ('Asia/Kabul', 'Asia/Kabul'), ('America/Shiprock', 'America/Shiprock'), ('Asia/Bishkek', 'Asia/Bishkek'), ('America/Goose_Bay', 'America/Goose_Bay'), ('America/Phoenix', 'America/Phoenix'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Asia/Kuching', 'Asia/Kuching'), ('America/Managua', 'America/Managua'), ('Europe/Rome', 'Europe/Rome'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Pacific/Ponape', 'Pacific/Ponape'), ('W-SU', 'W-SU'), ('America/Montserrat', 'America/Montserrat'), ('Brazil/Acre', 'Brazil/Acre'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Africa/Banjul', 'Africa/Banjul'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('Australia/Eucla', 'Australia/Eucla'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('Indian/Mauritius', 'Indian/Mauritius'), ('Pacific/Apia', 'Pacific/Apia'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('America/Vancouver', 'America/Vancouver'), ('Pacific/Majuro', 'Pacific/Majuro'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('America/Montreal', 'America/Montreal'), ('Pacific/Gambier', 'Pacific/Gambier'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Europe/Sofia', 'Europe/Sofia'), ('Europe/Tirane', 'Europe/Tirane'), ('Asia/Chungking', 'Asia/Chungking'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('America/St_Kitts', 'America/St_Kitts'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Indian/Comoro', 'Indian/Comoro'), ('Africa/Ceuta', 'Africa/Ceuta'), ('Etc/GMT-10', 'Etc/GMT-10'), ('GMT-0', 'GMT-0'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('Africa/Bangui', 'Africa/Bangui'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('Asia/Singapore', 'Asia/Singapore'), ('Poland', 'Poland'), ('Etc/GMT-3', 'Etc/GMT-3'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Europe/Vatican', 'Europe/Vatican'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('Asia/Tehran', 'Asia/Tehran'), ('America/Maceio', 'America/Maceio'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('Europe/Madrid', 'Europe/Madrid'), ('CET', 'CET'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('America/Santiago', 'America/Santiago'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('Europe/Paris', 'Europe/Paris'), ('NZ', 'NZ'), ('HST', 'HST'), ('Europe/Dublin', 'Europe/Dublin'), ('America/Bahia', 'America/Bahia'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('PRC', 'PRC'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('Africa/Abidjan', 'Africa/Abidjan'), ('Brazil/East', 'Brazil/East'), ('Etc/Greenwich', 'Etc/Greenwich'), ('America/Campo_Grande', 'America/Campo_Grande'), ('Europe/Podgorica', 'Europe/Podgorica'), ('Indian/Mayotte', 'Indian/Mayotte'), ('Asia/Almaty', 'Asia/Almaty'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('Europe/Simferopol', 'Europe/Simferopol'), ('Australia/LHI', 'Australia/LHI'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('America/Grand_Turk', 'America/Grand_Turk'), ('Europe/Tallinn', 'Europe/Tallinn'), ('Indian/Chagos', 'Indian/Chagos'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('America/Tijuana', 'America/Tijuana'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('Asia/Bangkok', 'Asia/Bangkok'), ('Etc/GMT-1', 'Etc/GMT-1'), ('Europe/Riga', 'Europe/Riga'), ('Europe/London', 'Europe/London'), ('Greenwich', 'Greenwich'), ('America/Rainy_River', 'America/Rainy_River'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('Asia/Baghdad', 'Asia/Baghdad'), ('Pacific/Johnston', 'Pacific/Johnston'), ('Egypt', 'Egypt'), ('Etc/UCT', 'Etc/UCT'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Etc/GMT-9', 'Etc/GMT-9'), ('Africa/Harare', 'Africa/Harare'), ('America/Ensenada', 'America/Ensenada'), ('Africa/Bamako', 'Africa/Bamako'), ('Antarctica/Davis', 'Antarctica/Davis'), ('America/Virgin', 'America/Virgin'), ('America/Cayenne', 'America/Cayenne'), ('Africa/Kigali', 'Africa/Kigali'), ('Asia/Istanbul', 'Asia/Istanbul'), ('Africa/Asmara', 'Africa/Asmara'), ('America/Godthab', 'America/Godthab'), ('Africa/Maputo', 'Africa/Maputo'), ('America/Iqaluit', 'America/Iqaluit'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Etc/GMT-13', 'Etc/GMT-13'), ('Africa/Lusaka', 'Africa/Lusaka'), ('US/Mountain', 'US/Mountain'), ('America/Knox_IN', 'America/Knox_IN'), ('US/Aleutian', 'US/Aleutian'), ('Asia/Yangon', 'Asia/Yangon'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('Asia/Chita', 'Asia/Chita')], default='Europe/London', max_length=35),
        ),
    ]