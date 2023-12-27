# Generated by Django 4.2.6 on 2023-12-09 06:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_alter_multitenantuser_timezone_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='multitenantuserlogintoken',
            name='token',
            field=models.CharField(default='fake', max_length=20, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('Africa/Douala', 'Africa/Douala'), ('Indian/Cocos', 'Indian/Cocos'), ('Indian/Comoro', 'Indian/Comoro'), ('Canada/Atlantic', 'Canada/Atlantic'), ('Pacific/Midway', 'Pacific/Midway'), ('America/Cayman', 'America/Cayman'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('Israel', 'Israel'), ('Europe/Belfast', 'Europe/Belfast'), ('Asia/Qatar', 'Asia/Qatar'), ('Australia/Canberra', 'Australia/Canberra'), ('Europe/Tallinn', 'Europe/Tallinn'), ('America/Nassau', 'America/Nassau'), ('Africa/Mbabane', 'Africa/Mbabane'), ('America/Grenada', 'America/Grenada'), ('America/Nome', 'America/Nome'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('Australia/Adelaide', 'Australia/Adelaide'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('Africa/Casablanca', 'Africa/Casablanca'), ('Antarctica/Davis', 'Antarctica/Davis'), ('US/Alaska', 'US/Alaska'), ('Etc/GMT-9', 'Etc/GMT-9'), ('GB-Eire', 'GB-Eire'), ('Pacific/Efate', 'Pacific/Efate'), ('Europe/Oslo', 'Europe/Oslo'), ('Japan', 'Japan'), ('CET', 'CET'), ('America/Knox_IN', 'America/Knox_IN'), ('Europe/Chisinau', 'Europe/Chisinau'), ('Africa/Conakry', 'Africa/Conakry'), ('America/La_Paz', 'America/La_Paz'), ('Asia/Dili', 'Asia/Dili'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('Etc/GMT+8', 'Etc/GMT+8'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('America/Atikokan', 'America/Atikokan'), ('Europe/Samara', 'Europe/Samara'), ('Africa/Banjul', 'Africa/Banjul'), ('Europe/Helsinki', 'Europe/Helsinki'), ('America/Nuuk', 'America/Nuuk'), ('Pacific/Apia', 'Pacific/Apia'), ('Africa/Harare', 'Africa/Harare'), ('America/Guayaquil', 'America/Guayaquil'), ('America/Aruba', 'America/Aruba'), ('America/Toronto', 'America/Toronto'), ('Asia/Tomsk', 'Asia/Tomsk'), ('America/Manaus', 'America/Manaus'), ('Europe/Kyiv', 'Europe/Kyiv'), ('Etc/GMT+1', 'Etc/GMT+1'), ('America/Adak', 'America/Adak'), ('Canada/Central', 'Canada/Central'), ('Europe/Podgorica', 'Europe/Podgorica'), ('Africa/Lusaka', 'Africa/Lusaka'), ('Europe/Zagreb', 'Europe/Zagreb'), ('Asia/Aden', 'Asia/Aden'), ('America/Denver', 'America/Denver'), ('Africa/Asmara', 'Africa/Asmara'), ('US/Arizona', 'US/Arizona'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('America/Indianapolis', 'America/Indianapolis'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Etc/GMT+0', 'Etc/GMT+0'), ('America/Marigot', 'America/Marigot'), ('Africa/Algiers', 'Africa/Algiers'), ('America/Atka', 'America/Atka'), ('Pacific/Palau', 'Pacific/Palau'), ('Asia/Jakarta', 'Asia/Jakarta'), ('Europe/Malta', 'Europe/Malta'), ('America/Regina', 'America/Regina'), ('NZ-CHAT', 'NZ-CHAT'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('America/Swift_Current', 'America/Swift_Current'), ('Mexico/General', 'Mexico/General'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('America/Belize', 'America/Belize'), ('Europe/Skopje', 'Europe/Skopje'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('America/Vancouver', 'America/Vancouver'), ('Europe/Zurich', 'Europe/Zurich'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('Asia/Karachi', 'Asia/Karachi'), ('Europe/Warsaw', 'Europe/Warsaw'), ('Africa/Monrovia', 'Africa/Monrovia'), ('America/Virgin', 'America/Virgin'), ('Africa/Luanda', 'Africa/Luanda'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Etc/GMT-3', 'Etc/GMT-3'), ('Asia/Makassar', 'Asia/Makassar'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('America/Chihuahua', 'America/Chihuahua'), ('Asia/Colombo', 'Asia/Colombo'), ('UCT', 'UCT'), ('Europe/Vienna', 'Europe/Vienna'), ('Europe/Brussels', 'Europe/Brussels'), ('Chile/Continental', 'Chile/Continental'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('Asia/Kolkata', 'Asia/Kolkata'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Asia/Beirut', 'Asia/Beirut'), ('Africa/Bissau', 'Africa/Bissau'), ('EST', 'EST'), ('Canada/Mountain', 'Canada/Mountain'), ('Europe/Vaduz', 'Europe/Vaduz'), ('Etc/GMT', 'Etc/GMT'), ('ROC', 'ROC'), ('America/Rio_Branco', 'America/Rio_Branco'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('America/Yakutat', 'America/Yakutat'), ('America/Guyana', 'America/Guyana'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('US/Hawaii', 'US/Hawaii'), ('America/Costa_Rica', 'America/Costa_Rica'), ('America/Menominee', 'America/Menominee'), ('Libya', 'Libya'), ('Etc/GMT+9', 'Etc/GMT+9'), ('Africa/Kampala', 'Africa/Kampala'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('Asia/Pontianak', 'Asia/Pontianak'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('Etc/GMT-12', 'Etc/GMT-12'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Asia/Damascus', 'Asia/Damascus'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('Asia/Macao', 'Asia/Macao'), ('Europe/Budapest', 'Europe/Budapest'), ('Europe/Bucharest', 'Europe/Bucharest'), ('Europe/Dublin', 'Europe/Dublin'), ('Etc/GMT-0', 'Etc/GMT-0'), ('America/Miquelon', 'America/Miquelon'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('Australia/ACT', 'Australia/ACT'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('Canada/Yukon', 'Canada/Yukon'), ('Asia/Anadyr', 'Asia/Anadyr'), ('America/Montreal', 'America/Montreal'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('Africa/Libreville', 'Africa/Libreville'), ('Asia/Kashgar', 'Asia/Kashgar'), ('Asia/Amman', 'Asia/Amman'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Africa/Lagos', 'Africa/Lagos'), ('Australia/Sydney', 'Australia/Sydney'), ('Africa/Malabo', 'Africa/Malabo'), ('Greenwich', 'Greenwich'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Etc/UTC', 'Etc/UTC'), ('US/Michigan', 'US/Michigan'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('America/St_Thomas', 'America/St_Thomas'), ('Europe/Belgrade', 'Europe/Belgrade'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('GB', 'GB'), ('Asia/Vientiane', 'Asia/Vientiane'), ('Africa/Bangui', 'Africa/Bangui'), ('Indian/Mayotte', 'Indian/Mayotte'), ('PST8PDT', 'PST8PDT'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('America/Bogota', 'America/Bogota'), ('America/Matamoros', 'America/Matamoros'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('US/Samoa', 'US/Samoa'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('America/Eirunepe', 'America/Eirunepe'), ('Indian/Mauritius', 'Indian/Mauritius'), ('America/Grand_Turk', 'America/Grand_Turk'), ('NZ', 'NZ'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Eire', 'Eire'), ('Turkey', 'Turkey'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('Singapore', 'Singapore'), ('America/Campo_Grande', 'America/Campo_Grande'), ('Pacific/Easter', 'Pacific/Easter'), ('Etc/GMT-1', 'Etc/GMT-1'), ('America/Merida', 'America/Merida'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('America/St_Vincent', 'America/St_Vincent'), ('Etc/GMT-4', 'Etc/GMT-4'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Europe/Jersey', 'Europe/Jersey'), ('Asia/Harbin', 'Asia/Harbin'), ('Africa/Accra', 'Africa/Accra'), ('America/Guadeloupe', 'America/Guadeloupe'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Etc/Universal', 'Etc/Universal'), ('Asia/Chita', 'Asia/Chita'), ('Pacific/Guam', 'Pacific/Guam'), ('Etc/GMT-14', 'Etc/GMT-14'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Europe/Saratov', 'Europe/Saratov'), ('America/Paramaribo', 'America/Paramaribo'), ('America/Montserrat', 'America/Montserrat'), ('Etc/GMT+3', 'Etc/GMT+3'), ('America/Martinique', 'America/Martinique'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('America/Cancun', 'America/Cancun'), ('Australia/Currie', 'Australia/Currie'), ('Asia/Riyadh', 'Asia/Riyadh'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('Navajo', 'Navajo'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('Australia/West', 'Australia/West'), ('Egypt', 'Egypt'), ('Asia/Yangon', 'Asia/Yangon'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('Asia/Baku', 'Asia/Baku'), ('America/Havana', 'America/Havana'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Canada/Pacific', 'Canada/Pacific'), ('America/Cordoba', 'America/Cordoba'), ('America/Yellowknife', 'America/Yellowknife'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('GMT-0', 'GMT-0'), ('Asia/Kabul', 'Asia/Kabul'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('Asia/Magadan', 'Asia/Magadan'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Indian/Christmas', 'Indian/Christmas'), ('America/Mexico_City', 'America/Mexico_City'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('Etc/GMT+12', 'Etc/GMT+12'), ('America/Chicago', 'America/Chicago'), ('Etc/Greenwich', 'Etc/Greenwich'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('America/Maceio', 'America/Maceio'), ('Europe/Volgograd', 'Europe/Volgograd'), ('America/Noronha', 'America/Noronha'), ('Europe/Simferopol', 'Europe/Simferopol'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('Etc/GMT-2', 'Etc/GMT-2'), ('Iran', 'Iran'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Kwajalein', 'Kwajalein'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('Europe/Vatican', 'Europe/Vatican'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('Etc/GMT+2', 'Etc/GMT+2'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('Africa/Lome', 'Africa/Lome'), ('America/Lower_Princes', 'America/Lower_Princes'), ('ROK', 'ROK'), ('US/Eastern', 'US/Eastern'), ('America/Inuvik', 'America/Inuvik'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Africa/Kigali', 'Africa/Kigali'), ('America/Juneau', 'America/Juneau'), ('US/Central', 'US/Central'), ('America/Anguilla', 'America/Anguilla'), ('Africa/Freetown', 'Africa/Freetown'), ('Asia/Seoul', 'Asia/Seoul'), ('America/Araguaina', 'America/Araguaina'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('America/New_York', 'America/New_York'), ('Iceland', 'Iceland'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Australia/Melbourne', 'Australia/Melbourne'), ('America/Barbados', 'America/Barbados'), ('Australia/Queensland', 'Australia/Queensland'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('Pacific/Gambier', 'Pacific/Gambier'), ('America/Curacao', 'America/Curacao'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Australia/South', 'Australia/South'), ('Asia/Ashgabat', 'Asia/Ashgabat'), (
                'Pacific/Johnston', 'Pacific/Johnston'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('Africa/Juba', 'Africa/Juba'), ('America/Winnipeg', 'America/Winnipeg'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Australia/Hobart', 'Australia/Hobart'), ('MST7MDT', 'MST7MDT'), ('Asia/Chungking', 'Asia/Chungking'), ('America/Mendoza', 'America/Mendoza'), ('Universal', 'Universal'), ('Asia/Atyrau', 'Asia/Atyrau'), ('Europe/Nicosia', 'Europe/Nicosia'), ('America/Dawson', 'America/Dawson'), ('Pacific/Truk', 'Pacific/Truk'), ('America/El_Salvador', 'America/El_Salvador'), ('America/Shiprock', 'America/Shiprock'), ('Australia/LHI', 'Australia/LHI'), ('Asia/Taipei', 'Asia/Taipei'), ('Africa/Tunis', 'Africa/Tunis'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('HST', 'HST'), ('Australia/North', 'Australia/North'), ('Africa/Dakar', 'Africa/Dakar'), ('America/St_Johns', 'America/St_Johns'), ('Africa/Asmera', 'Africa/Asmera'), ('Australia/Tasmania', 'Australia/Tasmania'), ('Asia/Dacca', 'Asia/Dacca'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('America/Kralendijk', 'America/Kralendijk'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('Etc/GMT+11', 'Etc/GMT+11'), ('Asia/Bangkok', 'Asia/Bangkok'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('America/Metlakatla', 'America/Metlakatla'), ('Etc/GMT-13', 'Etc/GMT-13'), ('America/Lima', 'America/Lima'), ('America/Nipigon', 'America/Nipigon'), ('Asia/Oral', 'Asia/Oral'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('Africa/Maputo', 'Africa/Maputo'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Factory', 'Factory'), ('Asia/Katmandu', 'Asia/Katmandu'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Africa/Abidjan', 'Africa/Abidjan'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('EET', 'EET'), ('Europe/Busingen', 'Europe/Busingen'), ('Asia/Thimphu', 'Asia/Thimphu'), ('Asia/Barnaul', 'Asia/Barnaul'), ('Asia/Manila', 'Asia/Manila'), ('Africa/Cairo', 'Africa/Cairo'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('America/Guatemala', 'America/Guatemala'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('America/Louisville', 'America/Louisville'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Hongkong', 'Hongkong'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Asia/Hebron', 'Asia/Hebron'), ('Asia/Nicosia', 'Asia/Nicosia'), ('Atlantic/Canary', 'Atlantic/Canary'), ('PRC', 'PRC'), ('Africa/Niamey', 'Africa/Niamey'), ('Europe/Vilnius', 'Europe/Vilnius'), ('America/St_Kitts', 'America/St_Kitts'), ('Europe/Kiev', 'Europe/Kiev'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('Asia/Jayapura', 'Asia/Jayapura'), ('Etc/GMT-11', 'Etc/GMT-11'), ('America/Catamarca', 'America/Catamarca'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('Europe/Berlin', 'Europe/Berlin'), ('Asia/Almaty', 'Asia/Almaty'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('America/Jamaica', 'America/Jamaica'), ('America/Caracas', 'America/Caracas'), ('America/Panama', 'America/Panama'), ('Europe/Sofia', 'Europe/Sofia'), ('Africa/Blantyre', 'Africa/Blantyre'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('MST', 'MST'), ('US/Pacific', 'US/Pacific'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('Europe/Moscow', 'Europe/Moscow'), ('Europe/Andorra', 'Europe/Andorra'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('America/Resolute', 'America/Resolute'), ('Antarctica/Casey', 'Antarctica/Casey'), ('America/Antigua', 'America/Antigua'), ('Australia/Darwin', 'Australia/Darwin'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('Pacific/Niue', 'Pacific/Niue'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('US/Aleutian', 'US/Aleutian'), ('Asia/Bahrain', 'Asia/Bahrain'), ('America/Boise', 'America/Boise'), ('America/Recife', 'America/Recife'), ('Asia/Aqtau', 'Asia/Aqtau'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('America/Cayenne', 'America/Cayenne'), ('America/Dominica', 'America/Dominica'), ('America/Tortola', 'America/Tortola'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('WET', 'WET'), ('America/Santarem', 'America/Santarem'), ('America/Thule', 'America/Thule'), ('MET', 'MET'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('GMT', 'GMT'), ('Jamaica', 'Jamaica'), ('Etc/GMT0', 'Etc/GMT0'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('America/Moncton', 'America/Moncton'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('America/Bahia', 'America/Bahia'), ('Europe/Kirov', 'Europe/Kirov'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('Europe/Monaco', 'Europe/Monaco'), ('Pacific/Wake', 'Pacific/Wake'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Africa/Nairobi', 'Africa/Nairobi'), ('Pacific/Nauru', 'Pacific/Nauru'), ('America/Boa_Vista', 'America/Boa_Vista'), ('Africa/Gaborone', 'Africa/Gaborone'), ('Asia/Omsk', 'Asia/Omsk'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('America/Belem', 'America/Belem'), ('Asia/Saigon', 'Asia/Saigon'), ('America/Halifax', 'America/Halifax'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('America/Rosario', 'America/Rosario'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('Asia/Thimbu', 'Asia/Thimbu'), ('Portugal', 'Portugal'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('America/Asuncion', 'America/Asuncion'), ('Brazil/East', 'Brazil/East'), ('Europe/San_Marino', 'Europe/San_Marino'), ('America/Porto_Velho', 'America/Porto_Velho'), ('America/Goose_Bay', 'America/Goose_Bay'), ('Asia/Kuwait', 'Asia/Kuwait'), ('America/Scoresbysund', 'America/Scoresbysund'), ('Europe/Prague', 'Europe/Prague'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('Asia/Tehran', 'Asia/Tehran'), ('America/Tijuana', 'America/Tijuana'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('Etc/GMT-6', 'Etc/GMT-6'), ('America/Porto_Acre', 'America/Porto_Acre'), ('America/Ojinaga', 'America/Ojinaga'), ('Europe/Minsk', 'Europe/Minsk'), ('Pacific/Wallis', 'Pacific/Wallis'), ('America/Godthab', 'America/Godthab'), ('Poland', 'Poland'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('America/Whitehorse', 'America/Whitehorse'), ('Asia/Baghdad', 'Asia/Baghdad'), ('Pacific/Fiji', 'Pacific/Fiji'), ('America/Montevideo', 'America/Montevideo'), ('Australia/Victoria', 'Australia/Victoria'), ('UTC', 'UTC'), ('Europe/Athens', 'Europe/Athens'), ('Australia/NSW', 'Australia/NSW'), ('Asia/Hovd', 'Asia/Hovd'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Etc/Zulu', 'Etc/Zulu'), ('America/Jujuy', 'America/Jujuy'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Etc/GMT+6', 'Etc/GMT+6'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Asia/Urumqi', 'Asia/Urumqi'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('Asia/Muscat', 'Asia/Muscat'), ('America/Fortaleza', 'America/Fortaleza'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Asia/Brunei', 'Asia/Brunei'), ('Africa/Tripoli', 'Africa/Tripoli'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Europe/Riga', 'Europe/Riga'), ('Etc/GMT+10', 'Etc/GMT+10'), ('Etc/UCT', 'Etc/UCT'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('America/Anchorage', 'America/Anchorage'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('Pacific/Auckland', 'Pacific/Auckland'), ('Africa/Khartoum', 'Africa/Khartoum'), ('Indian/Mahe', 'Indian/Mahe'), ('Africa/Maseru', 'Africa/Maseru'), ('Asia/Singapore', 'Asia/Singapore'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Europe/London', 'Europe/London'), ('Pacific/Majuro', 'Pacific/Majuro'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('America/Cuiaba', 'America/Cuiaba'), ('Indian/Maldives', 'Indian/Maldives'), ('America/Rainy_River', 'America/Rainy_River'), ('America/Edmonton', 'America/Edmonton'), ('CST6CDT', 'CST6CDT'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Europe/Rome', 'Europe/Rome'), ('W-SU', 'W-SU'), ('America/Detroit', 'America/Detroit'), ('America/Hermosillo', 'America/Hermosillo'), ('GMT0', 'GMT0'), ('Etc/GMT+5', 'Etc/GMT+5'), ('Etc/GMT-10', 'Etc/GMT-10'), ('Asia/Dubai', 'Asia/Dubai'), ('US/East-Indiana', 'US/East-Indiana'), ('US/Mountain', 'US/Mountain'), ('America/Creston', 'America/Creston'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('Europe/Paris', 'Europe/Paris'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Australia/Eucla', 'Australia/Eucla'), ('America/Santiago', 'America/Santiago'), ('Pacific/Ponape', 'Pacific/Ponape'), ('Asia/Gaza', 'Asia/Gaza'), ('GMT+0', 'GMT+0'), ('Asia/Istanbul', 'Asia/Istanbul'), ('America/Managua', 'America/Managua'), ('Africa/Bamako', 'Africa/Bamako'), ('America/St_Lucia', 'America/St_Lucia'), ('Brazil/Acre', 'Brazil/Acre'), ('Europe/Tirane', 'Europe/Tirane'), ('America/Sitka', 'America/Sitka'), ('Asia/Macau', 'Asia/Macau'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Zulu', 'Zulu'), ('Asia/Rangoon', 'Asia/Rangoon'), ('Pacific/Chatham', 'Pacific/Chatham'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('America/Pangnirtung', 'America/Pangnirtung'), ('Europe/Madrid', 'Europe/Madrid'), ('Brazil/West', 'Brazil/West'), ('Asia/Samarkand', 'Asia/Samarkand'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Canada/Eastern', 'Canada/Eastern'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Cuba', 'Cuba'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Australia/Perth', 'Australia/Perth'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Indian/Reunion', 'Indian/Reunion'), ('Pacific/Yap', 'Pacific/Yap'), ('Australia/Brisbane', 'Australia/Brisbane'), ('America/Ensenada', 'America/Ensenada'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('America/Mazatlan', 'America/Mazatlan'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Asia/Famagusta', 'Asia/Famagusta'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('Etc/GMT+7', 'Etc/GMT+7'), ('America/Monterrey', 'America/Monterrey'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('America/Los_Angeles', 'America/Los_Angeles'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Indian/Chagos', 'Indian/Chagos'), ('EST5EDT', 'EST5EDT'), ('Asia/Bishkek', 'Asia/Bishkek'), ('America/Iqaluit', 'America/Iqaluit'), ('Africa/Ceuta', 'Africa/Ceuta'), ('America/Phoenix', 'America/Phoenix'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('Asia/Kuching', 'Asia/Kuching'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur')], default='Europe/London', max_length=35),
        ),
    ]