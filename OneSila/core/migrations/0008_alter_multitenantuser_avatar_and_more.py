# Generated by Django 4.2.6 on 2023-11-30 23:50

import core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_multitenantuser_telegram_number_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars', validators=[
                                    core.validators.validate_image_extension, core.validators.no_dots_in_filename]),
        ),
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('Africa/Accra', 'Africa/Accra'), ('America/Martinique', 'America/Martinique'), ('ROC', 'ROC'), ('America/Edmonton', 'America/Edmonton'), ('America/Moncton', 'America/Moncton'), ('Europe/Vaduz', 'Europe/Vaduz'), ('Etc/GMT-3', 'Etc/GMT-3'), ('Indian/Comoro', 'Indian/Comoro'), ('America/Matamoros', 'America/Matamoros'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Africa/Khartoum', 'Africa/Khartoum'), ('Asia/Yangon', 'Asia/Yangon'), ('Europe/Malta', 'Europe/Malta'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Africa/Lome', 'Africa/Lome'), ('Europe/Zagreb', 'Europe/Zagreb'), ('America/Jujuy', 'America/Jujuy'), ('Asia/Atyrau', 'Asia/Atyrau'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Canada/Yukon', 'Canada/Yukon'), ('Canada/Atlantic', 'Canada/Atlantic'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Asia/Muscat', 'Asia/Muscat'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('Asia/Bangkok', 'Asia/Bangkok'), ('Navajo', 'Navajo'), ('Europe/Belgrade', 'Europe/Belgrade'), ('Etc/GMT-10', 'Etc/GMT-10'), ('Pacific/Easter', 'Pacific/Easter'), ('Africa/Lagos', 'Africa/Lagos'), ('Greenwich', 'Greenwich'), ('Australia/South', 'Australia/South'), ('America/Nassau', 'America/Nassau'), ('Chile/Continental', 'Chile/Continental'), ('Canada/Mountain', 'Canada/Mountain'), ('Asia/Kolkata', 'Asia/Kolkata'), ('W-SU', 'W-SU'), ('Pacific/Ponape', 'Pacific/Ponape'), ('America/Louisville', 'America/Louisville'), ('PRC', 'PRC'), ('America/Montserrat', 'America/Montserrat'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('UTC', 'UTC'), ('Europe/Kyiv', 'Europe/Kyiv'), ('America/Cayenne', 'America/Cayenne'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('US/Eastern', 'US/Eastern'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Asia/Istanbul', 'Asia/Istanbul'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('US/Pacific', 'US/Pacific'), ('Asia/Thimphu', 'Asia/Thimphu'), ('America/Bahia', 'America/Bahia'), ('GMT0', 'GMT0'), ('America/Manaus', 'America/Manaus'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Asia/Beirut', 'Asia/Beirut'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('Atlantic/Canary', 'Atlantic/Canary'), ('America/Mendoza', 'America/Mendoza'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('Europe/Busingen', 'Europe/Busingen'), ('America/Merida', 'America/Merida'), ('Etc/GMT+5', 'Etc/GMT+5'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('Europe/Sofia', 'Europe/Sofia'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('GMT-0', 'GMT-0'), ('America/Jamaica', 'America/Jamaica'), ('Europe/Istanbul', 'Europe/Istanbul'), ('US/East-Indiana', 'US/East-Indiana'), ('Asia/Jakarta', 'Asia/Jakarta'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Europe/Riga', 'Europe/Riga'), ('Asia/Gaza', 'Asia/Gaza'), ('America/Metlakatla', 'America/Metlakatla'), ('Europe/Stockholm', 'Europe/Stockholm'), ('America/Maceio', 'America/Maceio'), ('Africa/Juba', 'Africa/Juba'), ('America/Godthab', 'America/Godthab'), ('Africa/Freetown', 'Africa/Freetown'), ('Asia/Baku', 'Asia/Baku'), ('Australia/Darwin', 'Australia/Darwin'), ('America/Detroit', 'America/Detroit'), ('GMT', 'GMT'), ('Europe/Athens', 'Europe/Athens'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('America/Sitka', 'America/Sitka'), ('Etc/GMT+6', 'Etc/GMT+6'), ('America/Denver', 'America/Denver'), ('America/Atka', 'America/Atka'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Pacific/Auckland', 'Pacific/Auckland'), ('Asia/Amman', 'Asia/Amman'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Etc/GMT+3', 'Etc/GMT+3'), ('Pacific/Truk', 'Pacific/Truk'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Asia/Damascus', 'Asia/Damascus'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('America/Belize', 'America/Belize'), ('America/Guadeloupe', 'America/Guadeloupe'), ('US/Alaska', 'US/Alaska'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('Europe/Skopje', 'Europe/Skopje'), ('Australia/West', 'Australia/West'), ('America/Fortaleza', 'America/Fortaleza'), ('America/Grand_Turk', 'America/Grand_Turk'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('Asia/Barnaul', 'Asia/Barnaul'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('Canada/Eastern', 'Canada/Eastern'), ('America/Porto_Velho', 'America/Porto_Velho'), ('CST6CDT', 'CST6CDT'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('US/Aleutian', 'US/Aleutian'), ('Europe/Saratov', 'Europe/Saratov'), ('America/Indianapolis', 'America/Indianapolis'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Pacific/Efate', 'Pacific/Efate'), ('Asia/Almaty', 'Asia/Almaty'), ('Etc/GMT+11', 'Etc/GMT+11'), ('America/Cordoba', 'America/Cordoba'), ('America/Panama', 'America/Panama'), ('America/Dominica', 'America/Dominica'), ('Iran', 'Iran'), ('Brazil/Acre', 'Brazil/Acre'), ('PST8PDT', 'PST8PDT'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('Iceland', 'Iceland'), ('Europe/Vatican', 'Europe/Vatican'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('Pacific/Samoa', 'Pacific/Samoa'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('America/Inuvik', 'America/Inuvik'), ('Europe/Dublin', 'Europe/Dublin'), ('America/Whitehorse', 'America/Whitehorse'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('Africa/Bissau', 'Africa/Bissau'), ('Etc/GMT+0', 'Etc/GMT+0'), ('Etc/GMT-4', 'Etc/GMT-4'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('America/La_Paz', 'America/La_Paz'), ('Asia/Colombo', 'Asia/Colombo'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('Australia/Eucla', 'Australia/Eucla'), ('America/Resolute', 'America/Resolute'), ('GB-Eire', 'GB-Eire'), ('Asia/Macao', 'Asia/Macao'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Etc/UCT', 'Etc/UCT'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('Asia/Anadyr', 'Asia/Anadyr'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('America/Yakutat', 'America/Yakutat'), ('America/Los_Angeles', 'America/Los_Angeles'), ('America/Adak', 'America/Adak'), ('America/Halifax', 'America/Halifax'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('America/Miquelon', 'America/Miquelon'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Indian/Mahe', 'Indian/Mahe'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('EST5EDT', 'EST5EDT'), ('GMT+0', 'GMT+0'), ('Australia/Victoria', 'Australia/Victoria'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('Etc/GMT-2', 'Etc/GMT-2'), ('Asia/Seoul', 'Asia/Seoul'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('America/Asuncion', 'America/Asuncion'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('Africa/Kampala', 'Africa/Kampala'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('America/Mexico_City', 'America/Mexico_City'), ('US/Samoa', 'US/Samoa'), ('America/Nuuk', 'America/Nuuk'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('America/Cancun', 'America/Cancun'), ('Eire', 'Eire'), ('Europe/Tirane', 'Europe/Tirane'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Europe/Simferopol', 'Europe/Simferopol'), ('Asia/Singapore', 'Asia/Singapore'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Indian/Maldives', 'Indian/Maldives'), ('Poland', 'Poland'), ('America/Swift_Current', 'America/Swift_Current'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('Africa/Maputo', 'Africa/Maputo'), ('America/New_York', 'America/New_York'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('Europe/Helsinki', 'Europe/Helsinki'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Australia/NSW', 'Australia/NSW'), ('America/Caracas', 'America/Caracas'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Africa/Lusaka', 'Africa/Lusaka'), ('America/Dawson', 'America/Dawson'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Etc/GMT-0', 'Etc/GMT-0'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Hongkong', 'Hongkong'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Etc/UTC', 'Etc/UTC'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Africa/Conakry', 'Africa/Conakry'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('America/Boa_Vista', 'America/Boa_Vista'), ('America/Porto_Acre', 'America/Porto_Acre'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('America/Nome', 'America/Nome'), ('America/Bogota', 'America/Bogota'), ('Indian/Chagos', 'Indian/Chagos'), ('Europe/Tallinn', 'Europe/Tallinn'), ('America/Ensenada', 'America/Ensenada'), ('Australia/Perth', 'Australia/Perth'), ('HST', 'HST'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Pacific/Gambier', 'Pacific/Gambier'), ('Africa/Asmara', 'Africa/Asmara'), ('America/Lima', 'America/Lima'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Asia/Tehran', 'Asia/Tehran'), ('Europe/Kirov', 'Europe/Kirov'), ('Africa/Dakar', 'Africa/Dakar'), ('Australia/Melbourne', 'Australia/Melbourne'), ('America/St_Johns', 'America/St_Johns'), ('Asia/Manila', 'Asia/Manila'), ('Australia/ACT', 'Australia/ACT'), ('Jamaica', 'Jamaica'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Europe/Jersey', 'Europe/Jersey'), ('Africa/Maseru', 'Africa/Maseru'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Cuba', 'Cuba'), ('MET', 'MET'), ('America/Scoresbysund', 'America/Scoresbysund'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('Pacific/Majuro', 'Pacific/Majuro'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('Indian/Mayotte', 'Indian/Mayotte'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('America/Monterrey', 'America/Monterrey'), ('US/Hawaii', 'US/Hawaii'), ('Europe/Berlin', 'Europe/Berlin'), ('Australia/LHI', 'Australia/LHI'), ('Australia/Hobart', 'Australia/Hobart'), ('Asia/Macau', 'Asia/Macau'), ('Indian/Reunion', 'Indian/Reunion'), ('Africa/Bamako', 'Africa/Bamako'), ('Asia/Taipei', 'Asia/Taipei'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('America/Montevideo', 'America/Montevideo'), ('Asia/Makassar', 'Asia/Makassar'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('Etc/GMT-14', 'Etc/GMT-14'), ('Africa/Mbabane', 'Africa/Mbabane'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('Indian/Christmas', 'Indian/Christmas'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('America/Catamarca', 'America/Catamarca'), ('WET', 'WET'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('America/Anguilla', 'America/Anguilla'), ('America/Iqaluit', 'America/Iqaluit'), ('Europe/San_Marino', 'Europe/San_Marino'), ('America/Recife', 'America/Recife'), ('America/Antigua', 'America/Antigua'), ('Europe/Bratislava',
                                   'Europe/Bratislava'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('Egypt', 'Egypt'), ('Etc/GMT+2', 'Etc/GMT+2'), ('Asia/Thimbu', 'Asia/Thimbu'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('Africa/Ceuta', 'Africa/Ceuta'), ('Asia/Qatar', 'Asia/Qatar'), ('Africa/Luanda', 'Africa/Luanda'), ('Mexico/General', 'Mexico/General'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Africa/Cairo', 'Africa/Cairo'), ('Africa/Tunis', 'Africa/Tunis'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('Asia/Rangoon', 'Asia/Rangoon'), ('Europe/Warsaw', 'Europe/Warsaw'), ('America/St_Kitts', 'America/St_Kitts'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('Canada/Central', 'Canada/Central'), ('Africa/Malabo', 'Africa/Malabo'), ('America/St_Vincent', 'America/St_Vincent'), ('America/Glace_Bay', 'America/Glace_Bay'), ('America/Yellowknife', 'America/Yellowknife'), ('Asia/Jayapura', 'Asia/Jayapura'), ('America/Knox_IN', 'America/Knox_IN'), ('America/Chihuahua', 'America/Chihuahua'), ('Europe/Andorra', 'Europe/Andorra'), ('Africa/Banjul', 'Africa/Banjul'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Asia/Vientiane', 'Asia/Vientiane'), ('Pacific/Midway', 'Pacific/Midway'), ('America/Tijuana', 'America/Tijuana'), ('Etc/Universal', 'Etc/Universal'), ('Zulu', 'Zulu'), ('Asia/Chungking', 'Asia/Chungking'), ('Asia/Chita', 'Asia/Chita'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Japan', 'Japan'), ('America/Kralendijk', 'America/Kralendijk'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('America/Curacao', 'America/Curacao'), ('Australia/Lindeman', 'Australia/Lindeman'), ('America/St_Thomas', 'America/St_Thomas'), ('America/Eirunepe', 'America/Eirunepe'), ('Pacific/Johnston', 'Pacific/Johnston'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Australia/Tasmania', 'Australia/Tasmania'), ('Pacific/Apia', 'Pacific/Apia'), ('Australia/North', 'Australia/North'), ('Europe/Volgograd', 'Europe/Volgograd'), ('Africa/Bangui', 'Africa/Bangui'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('America/Rio_Branco', 'America/Rio_Branco'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('America/St_Lucia', 'America/St_Lucia'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('NZ-CHAT', 'NZ-CHAT'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('Asia/Kuwait', 'Asia/Kuwait'), ('Africa/Kigali', 'Africa/Kigali'), ('America/Barbados', 'America/Barbados'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Europe/Chisinau', 'Europe/Chisinau'), ('America/Santiago', 'America/Santiago'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('Pacific/Yap', 'Pacific/Yap'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Africa/Libreville', 'Africa/Libreville'), ('Asia/Harbin', 'Asia/Harbin'), ('Europe/Brussels', 'Europe/Brussels'), ('Brazil/West', 'Brazil/West'), ('America/Winnipeg', 'America/Winnipeg'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('America/Chicago', 'America/Chicago'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('Australia/Canberra', 'Australia/Canberra'), ('Asia/Kabul', 'Asia/Kabul'), ('Etc/GMT+8', 'Etc/GMT+8'), ('Africa/Djibouti', 'Africa/Djibouti'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Antarctica/Casey', 'Antarctica/Casey'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Europe/Rome', 'Europe/Rome'), ('Etc/GMT', 'Etc/GMT'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Australia/Queensland', 'Australia/Queensland'), ('Etc/GMT-1', 'Etc/GMT-1'), ('Europe/Prague', 'Europe/Prague'), ('America/Goose_Bay', 'America/Goose_Bay'), ('Indian/Mauritius', 'Indian/Mauritius'), ('Asia/Hebron', 'Asia/Hebron'), ('Africa/Nairobi', 'Africa/Nairobi'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('Europe/Oslo', 'Europe/Oslo'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('US/Michigan', 'US/Michigan'), ('Africa/Casablanca', 'Africa/Casablanca'), ('Pacific/Wake', 'Pacific/Wake'), ('America/Vancouver', 'America/Vancouver'), ('America/Guatemala', 'America/Guatemala'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('Etc/GMT-13', 'Etc/GMT-13'), ('Europe/Paris', 'Europe/Paris'), ('Asia/Magadan', 'Asia/Magadan'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('Europe/Monaco', 'Europe/Monaco'), ('America/Cuiaba', 'America/Cuiaba'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('Europe/Bucharest', 'Europe/Bucharest'), ('ROK', 'ROK'), ('Indian/Cocos', 'Indian/Cocos'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('America/Guyana', 'America/Guyana'), ('America/Grenada', 'America/Grenada'), ('America/Juneau', 'America/Juneau'), ('Etc/GMT-6', 'Etc/GMT-6'), ('Europe/Moscow', 'Europe/Moscow'), ('America/Ojinaga', 'America/Ojinaga'), ('Europe/Budapest', 'Europe/Budapest'), ('Asia/Saigon', 'Asia/Saigon'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('Etc/GMT-12', 'Etc/GMT-12'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('Asia/Urumqi', 'Asia/Urumqi'), ('Etc/Zulu', 'Etc/Zulu'), ('Africa/Harare', 'Africa/Harare'), ('Europe/Zurich', 'Europe/Zurich'), ('Asia/Dacca', 'Asia/Dacca'), ('Etc/Greenwich', 'Etc/Greenwich'), ('Australia/Adelaide', 'Australia/Adelaide'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('America/Montreal', 'America/Montreal'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Asia/Famagusta', 'Asia/Famagusta'), ('Europe/Minsk', 'Europe/Minsk'), ('Africa/Algiers', 'Africa/Algiers'), ('Asia/Kuching', 'Asia/Kuching'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('America/Mazatlan', 'America/Mazatlan'), ('Africa/Asmera', 'Africa/Asmera'), ('Asia/Omsk', 'Asia/Omsk'), ('Asia/Dubai', 'Asia/Dubai'), ('America/Aruba', 'America/Aruba'), ('Europe/Kiev', 'Europe/Kiev'), ('Asia/Kashgar', 'Asia/Kashgar'), ('America/Atikokan', 'America/Atikokan'), ('Brazil/East', 'Brazil/East'), ('Etc/GMT-9', 'Etc/GMT-9'), ('Africa/Douala', 'Africa/Douala'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('America/Toronto', 'America/Toronto'), ('Africa/Tripoli', 'Africa/Tripoli'), ('Asia/Samarkand', 'Asia/Samarkand'), ('Asia/Oral', 'Asia/Oral'), ('Etc/GMT-11', 'Etc/GMT-11'), ('Asia/Hovd', 'Asia/Hovd'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('Turkey', 'Turkey'), ('Canada/Pacific', 'Canada/Pacific'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('GB', 'GB'), ('US/Mountain', 'US/Mountain'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('Africa/Monrovia', 'Africa/Monrovia'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Europe/Madrid', 'Europe/Madrid'), ('America/Creston', 'America/Creston'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Asia/Dili', 'Asia/Dili'), ('NZ', 'NZ'), ('Africa/Abidjan', 'Africa/Abidjan'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('MST7MDT', 'MST7MDT'), ('Australia/Sydney', 'Australia/Sydney'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('America/Campo_Grande', 'America/Campo_Grande'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Asia/Aden', 'Asia/Aden'), ('America/Thule', 'America/Thule'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('America/Paramaribo', 'America/Paramaribo'), ('Asia/Karachi', 'Asia/Karachi'), ('MST', 'MST'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('Factory', 'Factory'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('UCT', 'UCT'), ('America/Guayaquil', 'America/Guayaquil'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Pacific/Palau', 'Pacific/Palau'), ('America/Belem', 'America/Belem'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('America/Costa_Rica', 'America/Costa_Rica'), ('America/Regina', 'America/Regina'), ('Asia/Brunei', 'Asia/Brunei'), ('America/Araguaina', 'America/Araguaina'), ('America/Rosario', 'America/Rosario'), ('Etc/GMT+10', 'Etc/GMT+10'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('America/Hermosillo', 'America/Hermosillo'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('Pacific/Guam', 'Pacific/Guam'), ('US/Arizona', 'US/Arizona'), ('America/Virgin', 'America/Virgin'), ('Europe/Nicosia', 'Europe/Nicosia'), ('Pacific/Chatham', 'Pacific/Chatham'), ('Africa/Niamey', 'Africa/Niamey'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('America/Noronha', 'America/Noronha'), ('Kwajalein', 'Kwajalein'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('America/Shiprock', 'America/Shiprock'), ('Universal', 'Universal'), ('Libya', 'Libya'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('EET', 'EET'), ('Portugal', 'Portugal'), ('America/Santarem', 'America/Santarem'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('America/Anchorage', 'America/Anchorage'), ('Antarctica/Troll', 'Antarctica/Troll'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('US/Central', 'US/Central'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('Australia/Currie', 'Australia/Currie'), ('Etc/GMT+9', 'Etc/GMT+9'), ('America/Lower_Princes', 'America/Lower_Princes'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('Asia/Riyadh', 'Asia/Riyadh'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('Asia/Nicosia', 'Asia/Nicosia'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('America/Nipigon', 'America/Nipigon'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('Europe/Belfast', 'Europe/Belfast'), ('Pacific/Niue', 'Pacific/Niue'), ('America/Phoenix', 'America/Phoenix'), ('Europe/Vienna', 'Europe/Vienna'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Etc/GMT+7', 'Etc/GMT+7'), ('America/El_Salvador', 'America/El_Salvador'), ('America/Rainy_River', 'America/Rainy_River'), ('America/Managua', 'America/Managua'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('America/Pangnirtung', 'America/Pangnirtung'), ('Africa/Gaborone', 'Africa/Gaborone'), ('America/Havana', 'America/Havana'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('Pacific/Wallis', 'Pacific/Wallis'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Singapore', 'Singapore'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('Europe/Podgorica', 'Europe/Podgorica'), ('Israel', 'Israel'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('Etc/GMT0', 'Etc/GMT0'), ('America/Boise', 'America/Boise'), ('America/Cayman', 'America/Cayman'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('America/Marigot', 'America/Marigot'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('CET', 'CET'), ('Etc/GMT+1', 'Etc/GMT+1'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Asia/Baghdad', 'Asia/Baghdad'), ('America/Menominee', 'America/Menominee'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Europe/Samara', 'Europe/Samara'), ('America/Tortola', 'America/Tortola'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('EST', 'EST'), ('Europe/London', 'Europe/London')], default='Europe/London', max_length=35),
        ),
    ]