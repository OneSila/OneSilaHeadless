# Generated by Django 5.0.2 on 2024-06-10 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0093_alter_multitenantuser_onboarding_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='onboarding_status',
            field=models.CharField(choices=[('GENERATE_DEMO_DATA', 'Generate Demo Data'), ('ADD_COMPANY', 'Add Company'), ('ADD_CURRENCY', 'Add Currency'), ('CONFIRM_VAT_RATE', 'Confirm VAT Rate'), ('CREATE_INVENTORY_LOCATION', 'Create Inventory Location'), ('DASHBOARD_CARDS_PRESENTATION', 'Dashboard Cards Presentation'), ('COMPLETE_DASHBOARD_CARDS', 'Complete Dashboard Cards'), ('DONE', 'Done')], default='ADD_COMPANY', max_length=30),
        ),
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('Asia/Brunei', 'Asia/Brunei'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('Kwajalein', 'Kwajalein'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('Asia/Hovd', 'Asia/Hovd'), ('Pacific/Easter', 'Pacific/Easter'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Brazil/East', 'Brazil/East'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('Pacific/Palau', 'Pacific/Palau'), ('Asia/Vientiane', 'Asia/Vientiane'), ('Etc/GMT-13', 'Etc/GMT-13'), ('Africa/Dakar', 'Africa/Dakar'), ('Canada/Yukon', 'Canada/Yukon'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('US/Hawaii', 'US/Hawaii'), ('America/Chihuahua', 'America/Chihuahua'), ('America/Bahia', 'America/Bahia'), ('America/Tijuana', 'America/Tijuana'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('NZ', 'NZ'), ('America/Lima', 'America/Lima'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Etc/GMT+12', 'Etc/GMT+12'), ('America/Dominica', 'America/Dominica'), ('America/Regina', 'America/Regina'), ('America/Sitka', 'America/Sitka'), ('Australia/ACT', 'Australia/ACT'), ('Europe/Skopje', 'Europe/Skopje'), ('GB-Eire', 'GB-Eire'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('Etc/GMT+0', 'Etc/GMT+0'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('America/Nome', 'America/Nome'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('America/Montserrat', 'America/Montserrat'), ('America/Menominee', 'America/Menominee'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Jamaica', 'Jamaica'), ('America/Hermosillo', 'America/Hermosillo'), ('Brazil/Acre', 'Brazil/Acre'), ('Europe/Saratov', 'Europe/Saratov'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('America/Mexico_City', 'America/Mexico_City'), ('Pacific/Niue', 'Pacific/Niue'), ('Turkey', 'Turkey'), ('Asia/Kabul', 'Asia/Kabul'), ('Australia/NSW', 'Australia/NSW'), ('Asia/Makassar', 'Asia/Makassar'), ('Africa/Kigali', 'Africa/Kigali'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('Asia/Karachi', 'Asia/Karachi'), ('America/Rosario', 'America/Rosario'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Asia/Kolkata', 'Asia/Kolkata'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('America/Matamoros', 'America/Matamoros'), ('Australia/Eucla', 'Australia/Eucla'), ('Etc/GMT+1', 'Etc/GMT+1'), ('US/Michigan', 'US/Michigan'), ('CST6CDT', 'CST6CDT'), ('Africa/Khartoum', 'Africa/Khartoum'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Libya', 'Libya'), ('Indian/Christmas', 'Indian/Christmas'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Portugal', 'Portugal'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('Asia/Beirut', 'Asia/Beirut'), ('America/Antigua', 'America/Antigua'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Asia/Bangkok', 'Asia/Bangkok'), ('Europe/Andorra', 'Europe/Andorra'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('Australia/Queensland', 'Australia/Queensland'), ('Europe/Simferopol', 'Europe/Simferopol'), ('Zulu', 'Zulu'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('Europe/Riga', 'Europe/Riga'), ('America/Winnipeg', 'America/Winnipeg'), ('Europe/Vaduz', 'Europe/Vaduz'), ('America/Toronto', 'America/Toronto'), ('Etc/UTC', 'Etc/UTC'), ('Asia/Hebron', 'Asia/Hebron'), ('America/Guadeloupe', 'America/Guadeloupe'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('Africa/Asmara', 'Africa/Asmara'), ('America/Ensenada', 'America/Ensenada'), ('Pacific/Efate', 'Pacific/Efate'), ('Africa/Maseru', 'Africa/Maseru'), ('America/Rainy_River', 'America/Rainy_River'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('PST8PDT', 'PST8PDT'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Africa/Harare', 'Africa/Harare'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Europe/Budapest', 'Europe/Budapest'), ('PRC', 'PRC'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('America/St_Kitts', 'America/St_Kitts'), ('America/Maceio', 'America/Maceio'), ('America/Bogota', 'America/Bogota'), ('America/Rio_Branco', 'America/Rio_Branco'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('Europe/Minsk', 'Europe/Minsk'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Africa/Monrovia', 'Africa/Monrovia'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Asia/Manila', 'Asia/Manila'), ('Europe/Belfast', 'Europe/Belfast'), ('America/Atka', 'America/Atka'), ('Asia/Aden', 'Asia/Aden'), ('America/Mazatlan', 'America/Mazatlan'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Etc/GMT-0', 'Etc/GMT-0'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('Europe/Busingen', 'Europe/Busingen'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('America/Grenada', 'America/Grenada'), ('US/Samoa', 'US/Samoa'), ('America/Grand_Turk', 'America/Grand_Turk'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Asia/Dacca', 'Asia/Dacca'), ('America/Barbados', 'America/Barbados'), ('Europe/Moscow', 'Europe/Moscow'), ('America/Chicago', 'America/Chicago'), ('America/Metlakatla', 'America/Metlakatla'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('America/Boa_Vista', 'America/Boa_Vista'), ('Asia/Taipei', 'Asia/Taipei'), ('America/Vancouver', 'America/Vancouver'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('Etc/GMT', 'Etc/GMT'), ('Australia/North', 'Australia/North'), ('Japan', 'Japan'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Europe/Rome', 'Europe/Rome'), ('America/Boise', 'America/Boise'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Canada/Atlantic', 'Canada/Atlantic'), ('America/Belem', 'America/Belem'), ('Australia/Adelaide', 'Australia/Adelaide'), ('Australia/West', 'Australia/West'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('Indian/Mauritius', 'Indian/Mauritius'), ('Pacific/Gambier', 'Pacific/Gambier'), ('Europe/Brussels', 'Europe/Brussels'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('America/Juneau', 'America/Juneau'), ('Asia/Seoul', 'Asia/Seoul'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('America/Nassau', 'America/Nassau'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('America/Resolute', 'America/Resolute'), ('HST', 'HST'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('Africa/Accra', 'Africa/Accra'), ('WET', 'WET'), ('Australia/LHI', 'Australia/LHI'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('Africa/Lome', 'Africa/Lome'), ('Africa/Bissau', 'Africa/Bissau'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Asia/Kashgar', 'Asia/Kashgar'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Australia/Victoria', 'Australia/Victoria'), ('America/Porto_Acre', 'America/Porto_Acre'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Mexico/General', 'Mexico/General'), ('Europe/Warsaw', 'Europe/Warsaw'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('America/Nuuk', 'America/Nuuk'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Pacific/Wallis', 'Pacific/Wallis'), ('Africa/Malabo', 'Africa/Malabo'), ('Asia/Amman', 'Asia/Amman'), ('Asia/Dili', 'Asia/Dili'), ('MST7MDT', 'MST7MDT'), ('US/East-Indiana', 'US/East-Indiana'), ('America/Whitehorse', 'America/Whitehorse'), ('Africa/Lusaka', 'Africa/Lusaka'), ('Etc/Greenwich', 'Etc/Greenwich'), ('Europe/Lisbon', 'Europe/Lisbon'), ('GMT0', 'GMT0'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('America/Asuncion', 'America/Asuncion'), ('America/Curacao', 'America/Curacao'), ('Asia/Gaza', 'Asia/Gaza'), ('Canada/Eastern', 'Canada/Eastern'), ('America/Montevideo', 'America/Montevideo'), ('Eire', 'Eire'), ('Africa/Tunis', 'Africa/Tunis'), ('CET', 'CET'), ('Europe/Jersey', 'Europe/Jersey'), ('America/El_Salvador', 'America/El_Salvador'), ('Etc/GMT-2', 'Etc/GMT-2'), ('Europe/Samara', 'Europe/Samara'), ('Australia/Currie', 'Australia/Currie'), ('Africa/Casablanca', 'Africa/Casablanca'), ('UTC', 'UTC'), ('Etc/GMT+9', 'Etc/GMT+9'), ('Africa/Niamey', 'Africa/Niamey'), ('Asia/Chita', 'Asia/Chita'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Africa/Bangui', 'Africa/Bangui'), ('America/Monterrey', 'America/Monterrey'), ('Australia/Sydney', 'Australia/Sydney'), ('Indian/Cocos', 'Indian/Cocos'), ('UCT', 'UCT'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('America/Anchorage', 'America/Anchorage'), ('Africa/Ceuta', 'Africa/Ceuta'), ('America/Iqaluit', 'America/Iqaluit'), ('Canada/Mountain', 'Canada/Mountain'), ('Africa/Algiers', 'Africa/Algiers'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('America/Guatemala', 'America/Guatemala'), ('Asia/Dubai', 'Asia/Dubai'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('America/St_Johns', 'America/St_Johns'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Asia/Oral', 'Asia/Oral'), ('Australia/South', 'Australia/South'), ('build/etc/localtime', 'build/etc/localtime'), ('America/Eirunepe', 'America/Eirunepe'), ('Africa/Freetown', 'Africa/Freetown'), ('Asia/Magadan', 'Asia/Magadan'), ('Etc/GMT-12', 'Etc/GMT-12'), ('America/Inuvik', 'America/Inuvik'), ('Etc/GMT+2', 'Etc/GMT+2'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('America/Edmonton', 'America/Edmonton'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('Europe/Nicosia', 'Europe/Nicosia'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('Europe/Stockholm', 'Europe/Stockholm'), ('America/Campo_Grande', 'America/Campo_Grande'), ('Asia/Atyrau', 'Asia/Atyrau'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('Asia/Riyadh', 'Asia/Riyadh'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Poland', 'Poland'), ('Canada/Pacific', 'Canada/Pacific'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('America/Yellowknife', 'America/Yellowknife'), ('Greenwich', 'Greenwich'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('America/Dawson', 'America/Dawson'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('Asia/Jakarta', 'Asia/Jakarta'), ('Europe/Kirov', 'Europe/Kirov'), ('US/Central', 'US/Central'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('Europe/Madrid', 'Europe/Madrid'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('America/Louisville', 'America/Louisville'), ('Etc/GMT-11', 'Etc/GMT-11'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('US/Mountain', 'US/Mountain'), ('America/Indianapolis', 'America/Indianapolis'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('Pacific/Yap', 'Pacific/Yap'), ('Egypt', 'Egypt'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('Africa/Luanda', 'Africa/Luanda'), ('Indian/Mahe', 'Indian/Mahe'), ('Australia/Tasmania', 'Australia/Tasmania'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('Asia/Thimbu', 'Asia/Thimbu'), ('America/Knox_IN', 'America/Knox_IN'), ('Asia/Harbin', 'Asia/Harbin'), ('Indian/Mayotte', 'Indian/Mayotte'), ('Iran', 'Iran'), ('Pacific/Ponape', 'Pacific/Ponape'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('America/Detroit', 'America/Detroit'), ('America/Anguilla', 'America/Anguilla'), ('Etc/GMT-4', 'Etc/GMT-4'), ('Navajo', 'Navajo'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('US/Aleutian', 'US/Aleutian'), ('Africa/Mbabane', 'Africa/Mbabane'), ('Europe/Berlin', 'Europe/Berlin'), ('Europe/Sofia', 'Europe/Sofia'), ('MST', 'MST'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('America/Adak', 'America/Adak'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('America/Recife', 'America/Recife'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('Europe/Oslo', 'Europe/Oslo'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Africa/Libreville', 'Africa/Libreville'), ('America/Godthab', 'America/Godthab'), ('Asia/Omsk', 'Asia/Omsk'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('America/Virgin', 'America/Virgin'), ('Asia/Qatar', 'Asia/Qatar'), ('Canada/Central', 'Canada/Central'), ('America/St_Thomas', 'America/St_Thomas'), ('Asia/Singapore', 'Asia/Singapore'), ('Pacific/Wake', 'Pacific/Wake'), ('Asia/Samarkand', 'Asia/Samarkand'), ('Pacific/Majuro', 'Pacific/Majuro'), ('America/Havana', 'America/Havana'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('Indian/Comoro', 'Indian/Comoro'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Europe/Zurich', 'Europe/Zurich'), ('Europe/San_Marino', 'Europe/San_Marino'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Asia/Tomsk', 'Asia/Tomsk'), ('America/Panama', 'America/Panama'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('America/Araguaina', 'America/Araguaina'), ('Etc/GMT-5', 'Etc/GMT-5'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Australia/Canberra', 'Australia/Canberra'), ('Chile/Continental', 'Chile/Continental'), ('Africa/Kampala', 'Africa/Kampala'), ('Asia/Baku', 'Asia/Baku'), ('Asia/Yerevan', 'Asia/Yerevan'), ('America/Catamarca', 'America/Catamarca'), ('Etc/GMT-10', 'Etc/GMT-10'), ('Africa/Lagos', 'Africa/Lagos'), ('America/Denver', 'America/Denver'), ('America/Jamaica', 'America/Jamaica'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Africa/Douala', 'Africa/Douala'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Asia/Kuwait', 'Asia/Kuwait'), ('Pacific/Truk', 'Pacific/Truk'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('America/Fortaleza', 'America/Fortaleza'), ('Etc/GMT-14', 'Etc/GMT-14'), ('Pacific/Apia', 'Pacific/Apia'), ('America/Pangnirtung', 'America/Pangnirtung'), ('ROK', 'ROK'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('Africa/Bamako', 'Africa/Bamako'), ('EST5EDT', 'EST5EDT'), ('Asia/Damascus', 'Asia/Damascus'), ('Australia/Hobart', 'Australia/Hobart'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('America/Lower_Princes', 'America/Lower_Princes'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('Etc/GMT+5', 'Etc/GMT+5'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Europe/Vienna', 'Europe/Vienna'), ('Iceland', 'Iceland'), ('Europe/Zagreb', 'Europe/Zagreb'), ('America/Cancun', 'America/Cancun'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Israel', 'Israel'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Asia/Saigon', 'Asia/Saigon'), ('Asia/Almaty', 'Asia/Almaty'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Europe/Tirane', 'Europe/Tirane'), ('Europe/Bucharest', 'Europe/Bucharest'), ('Europe/Paris', 'Europe/Paris'), ('Europe/Dublin', 'Europe/Dublin'), ('Etc/GMT+3', 'Etc/GMT+3'), ('Africa/Juba', 'Africa/Juba'), ('NZ-CHAT', 'NZ-CHAT'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('America/Goose_Bay', 'America/Goose_Bay'), ('America/Manaus', 'America/Manaus'), ('America/Scoresbysund', 'America/Scoresbysund'), ('Etc/GMT+7', 'Etc/GMT+7'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('America/Ojinaga', 'America/Ojinaga'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('America/Cordoba', 'America/Cordoba'), ('Europe/Tallinn', 'Europe/Tallinn'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Etc/GMT-1', 'Etc/GMT-1'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('Asia/Urumqi', 'Asia/Urumqi'), ('EST', 'EST'), ('ROC', 'ROC'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('America/Guyana', 'America/Guyana'), ('Europe/London', 'Europe/London'), ('Cuba', 'Cuba'), ('America/Yakutat', 'America/Yakutat'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('Europe/Vatican', 'Europe/Vatican'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Pacific/Midway', 'Pacific/Midway'), ('America/Paramaribo', 'America/Paramaribo'), ('America/Phoenix', 'America/Phoenix'), ('America/Swift_Current', 'America/Swift_Current'), ('Asia/Tehran', 'Asia/Tehran'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Etc/GMT+10', 'Etc/GMT+10'), ('America/Creston', 'America/Creston'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('Hongkong', 'Hongkong'), ('Asia/Barnaul', 'Asia/Barnaul'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('Africa/Tripoli', 'Africa/Tripoli'), ('US/Eastern', 'US/Eastern'), ('Pacific/Guam', 'Pacific/Guam'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('Universal', 'Universal'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('US/Arizona', 'US/Arizona'), ('Asia/Yangon', 'Asia/Yangon'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('Etc/GMT+11', 'Etc/GMT+11'), ('America/Thule', 'America/Thule'), ('America/Aruba', 'America/Aruba'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('Atlantic/Canary', 'Atlantic/Canary'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('Etc/GMT-3', 'Etc/GMT-3'), ('GB', 'GB'), ('Africa/Nairobi', 'Africa/Nairobi'), ('Etc/GMT-6', 'Etc/GMT-6'), ('W-SU', 'W-SU'), ('Africa/Cairo', 'Africa/Cairo'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Antarctica/Casey', 'Antarctica/Casey'), ('Pacific/Auckland', 'Pacific/Auckland'), ('Pacific/Johnston', 'Pacific/Johnston'), ('America/Porto_Velho', 'America/Porto_Velho'), ('America/St_Lucia', 'America/St_Lucia'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Indian/Reunion', 'Indian/Reunion'), ('America/New_York', 'America/New_York'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Europe/Prague', 'Europe/Prague'), ('Factory', 'Factory'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Etc/Zulu', 'Etc/Zulu'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Etc/Universal', 'Etc/Universal'), ('Europe/Volgograd', 'Europe/Volgograd'), ('America/Halifax', 'America/Halifax'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('America/Atikokan', 'America/Atikokan'), ('Europe/Athens', 'Europe/Athens'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('America/Kralendijk', 'America/Kralendijk'), ('America/Managua', 'America/Managua'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Asia/Macao', 'Asia/Macao'), ('America/Merida', 'America/Merida'), ('America/Caracas', 'America/Caracas'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('America/Jujuy', 'America/Jujuy'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Africa/Gaborone', 'Africa/Gaborone'), ('GMT', 'GMT'), ('America/Nipigon', 'America/Nipigon'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('Europe/Kyiv', 'Europe/Kyiv'), ('America/Montreal', 'America/Montreal'), ('Europe/Belgrade', 'Europe/Belgrade'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('America/Belize', 'America/Belize'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Asia/Chungking', 'Asia/Chungking'), ('America/Santiago', 'America/Santiago'), ('America/Miquelon', 'America/Miquelon'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('America/Tortola', 'America/Tortola'), ('America/Guayaquil', 'America/Guayaquil'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('Asia/Muscat', 'Asia/Muscat'), ('Etc/UCT', 'Etc/UCT'), ('EET', 'EET'), ('Asia/Kuching', 'Asia/Kuching'), ('Europe/Kiev', 'Europe/Kiev'), ('America/Marigot', 'America/Marigot'), ('America/La_Paz', 'America/La_Paz'), ('US/Alaska', 'US/Alaska'), ('MET', 'MET'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Africa/Abidjan', 'Africa/Abidjan'), ('America/Santarem', 'America/Santarem'), ('Indian/Maldives', 'Indian/Maldives'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Asia/Anadyr', 'Asia/Anadyr'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('Europe/Malta', 'Europe/Malta'), ('America/Shiprock', 'America/Shiprock'), ('Etc/GMT+6', 'Etc/GMT+6'), ('America/Cuiaba', 'America/Cuiaba'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('Asia/Jayapura', 'Asia/Jayapura'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('Brazil/West', 'Brazil/West'), ('Europe/Podgorica', 'Europe/Podgorica'), ('Etc/GMT0', 'Etc/GMT0'), ('Africa/Asmera', 'Africa/Asmera'), ('America/Moncton', 'America/Moncton'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('GMT-0', 'GMT-0'), ('Etc/GMT+8', 'Etc/GMT+8'), ('Singapore', 'Singapore'), ('Europe/Chisinau', 'Europe/Chisinau'), ('Etc/GMT-9', 'Etc/GMT-9'), ('Pacific/Chatham', 'Pacific/Chatham'), ('Africa/Banjul', 'Africa/Banjul'), ('America/Cayenne', 'America/Cayenne'), ('America/Martinique', 'America/Martinique'), ('America/Los_Angeles', 'America/Los_Angeles'), ('Asia/Macau', 'Asia/Macau'), ('Europe/Helsinki', 'Europe/Helsinki'), ('Australia/Perth', 'Australia/Perth'), ('Australia/Darwin', 'Australia/Darwin'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('Asia/Nicosia', 'Asia/Nicosia'), ('GMT+0', 'GMT+0'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('Asia/Istanbul', 'Asia/Istanbul'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('America/Mendoza', 'America/Mendoza'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('America/Noronha', 'America/Noronha'), ('Africa/Conakry', 'Africa/Conakry'), ('Asia/Rangoon', 'Asia/Rangoon'), ('Asia/Baghdad', 'Asia/Baghdad'), ('Asia/Thimphu', 'Asia/Thimphu'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Europe/Monaco', 'Europe/Monaco'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Africa/Maputo', 'Africa/Maputo'), ('Asia/Famagusta', 'Asia/Famagusta'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('US/Pacific', 'US/Pacific'), ('America/St_Vincent', 'America/St_Vincent'), ('Asia/Colombo', 'Asia/Colombo'), ('Indian/Chagos', 'Indian/Chagos'), ('America/Cayman', 'America/Cayman')], default='Europe/London', max_length=35),
        ),
    ]