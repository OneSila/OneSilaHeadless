# Generated by Django 4.2.6 on 2023-12-04 05:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_multitenantuser_avatar_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuser',
            name='timezone',
            field=models.CharField(choices=[('Europe/Kiev', 'Europe/Kiev'), ('GMT0', 'GMT0'), ('Europe/Madrid', 'Europe/Madrid'), ('America/St_Thomas', 'America/St_Thomas'), ('America/Mazatlan', 'America/Mazatlan'), ('Europe/Kirov', 'Europe/Kirov'), ('America/Menominee', 'America/Menominee'), ('Africa/Kampala', 'Africa/Kampala'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('America/Yakutat', 'America/Yakutat'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Africa/Abidjan', 'Africa/Abidjan'), ('America/Bahia', 'America/Bahia'), ('America/Jujuy', 'America/Jujuy'), ('America/New_York', 'America/New_York'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Europe/Rome', 'Europe/Rome'), ('America/Juneau', 'America/Juneau'), ('CST6CDT', 'CST6CDT'), ('Indian/Cocos', 'Indian/Cocos'), ('America/Rio_Branco', 'America/Rio_Branco'), ('America/Virgin', 'America/Virgin'), ('America/Recife', 'America/Recife'), ('Africa/Harare', 'Africa/Harare'), ('Asia/Colombo', 'Asia/Colombo'), ('Asia/Saigon', 'Asia/Saigon'), ('Africa/Monrovia', 'Africa/Monrovia'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('Africa/Tripoli', 'Africa/Tripoli'), ('Europe/Bucharest', 'Europe/Bucharest'), ('ROK', 'ROK'), ('Africa/Asmera', 'Africa/Asmera'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Asia/Karachi', 'Asia/Karachi'), ('Europe/Chisinau', 'Europe/Chisinau'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('America/Atka', 'America/Atka'), ('Asia/Kuwait', 'Asia/Kuwait'), ('America/Guyana', 'America/Guyana'), ('Asia/Istanbul', 'Asia/Istanbul'), ('Asia/Chita', 'Asia/Chita'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('America/Porto_Velho', 'America/Porto_Velho'), ('Asia/Oral', 'Asia/Oral'), ('Africa/Maputo', 'Africa/Maputo'), ('Europe/Saratov', 'Europe/Saratov'), ('Europe/Paris', 'Europe/Paris'), ('Australia/Canberra', 'Australia/Canberra'), ('America/Nuuk', 'America/Nuuk'), ('Pacific/Majuro', 'Pacific/Majuro'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('Asia/Kuching', 'Asia/Kuching'), ('Asia/Riyadh', 'Asia/Riyadh'), ('Asia/Amman', 'Asia/Amman'), ('Etc/GMT-3', 'Etc/GMT-3'), ('America/Atikokan', 'America/Atikokan'), ('Asia/Dubai', 'Asia/Dubai'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Etc/GMT+9', 'Etc/GMT+9'), ('Indian/Mayotte', 'Indian/Mayotte'), ('Asia/Rangoon', 'Asia/Rangoon'), ('Europe/Tirane', 'Europe/Tirane'), ('America/Eirunepe', 'America/Eirunepe'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Cuba', 'Cuba'), ('Pacific/Auckland', 'Pacific/Auckland'), ('Factory', 'Factory'), ('America/St_Kitts', 'America/St_Kitts'), ('Europe/Vatican', 'Europe/Vatican'), ('America/Antigua', 'America/Antigua'), ('Asia/Damascus', 'Asia/Damascus'), ('Jamaica', 'Jamaica'), ('Europe/Lisbon', 'Europe/Lisbon'), ('America/Kralendijk', 'America/Kralendijk'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Europe/Nicosia', 'Europe/Nicosia'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('Etc/GMT+4', 'Etc/GMT+4'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('America/Chihuahua', 'America/Chihuahua'), ('Asia/Makassar', 'Asia/Makassar'), ('America/Thule', 'America/Thule'), ('Europe/Jersey', 'Europe/Jersey'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Asia/Famagusta', 'Asia/Famagusta'), ('America/Cancun', 'America/Cancun'), ('Asia/Omsk', 'Asia/Omsk'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('Etc/Universal', 'Etc/Universal'), ('America/Belize', 'America/Belize'), ('Africa/Mbabane', 'Africa/Mbabane'), ('America/Tortola', 'America/Tortola'), ('Indian/Comoro', 'Indian/Comoro'), ('Asia/Kashgar', 'Asia/Kashgar'), ('Kwajalein', 'Kwajalein'), ('America/Nome', 'America/Nome'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('Antarctica/Casey', 'Antarctica/Casey'), ('Africa/Dakar', 'Africa/Dakar'), ('America/Los_Angeles', 'America/Los_Angeles'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('Etc/GMT+1', 'Etc/GMT+1'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('Portugal', 'Portugal'), ('America/Jamaica', 'America/Jamaica'), ('Africa/Nairobi', 'Africa/Nairobi'), ('America/Detroit', 'America/Detroit'), ('Africa/Bamako', 'Africa/Bamako'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('America/Belem', 'America/Belem'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('Asia/Manila', 'Asia/Manila'), ('America/Creston', 'America/Creston'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Asia/Anadyr', 'Asia/Anadyr'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('Etc/GMT+8', 'Etc/GMT+8'), ('America/Cayenne', 'America/Cayenne'), ('Etc/GMT+11', 'Etc/GMT+11'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('Europe/Sofia', 'Europe/Sofia'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('Africa/Lome', 'Africa/Lome'), ('Etc/GMT-1', 'Etc/GMT-1'), ('America/Havana', 'America/Havana'), ('Asia/Bangkok', 'Asia/Bangkok'), ('Europe/Brussels', 'Europe/Brussels'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Europe/Kyiv', 'Europe/Kyiv'), ('Asia/Dili', 'Asia/Dili'), ('GMT+0', 'GMT+0'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Etc/GMT0', 'Etc/GMT0'), ('America/Dominica', 'America/Dominica'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('America/Bogota', 'America/Bogota'), ('America/Guayaquil', 'America/Guayaquil'), ('Africa/Luanda', 'Africa/Luanda'), ('Europe/Berlin', 'Europe/Berlin'), ('MET', 'MET'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('Asia/Jayapura', 'Asia/Jayapura'), ('Australia/South', 'Australia/South'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Asia/Kabul', 'Asia/Kabul'), ('ROC', 'ROC'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('Africa/Ceuta', 'Africa/Ceuta'), ('America/Goose_Bay', 'America/Goose_Bay'), ('America/Dawson', 'America/Dawson'), ('Asia/Brunei', 'Asia/Brunei'), ('US/Alaska', 'US/Alaska'), ('Zulu', 'Zulu'), ('Asia/Macau', 'Asia/Macau'), ('Europe/Simferopol', 'Europe/Simferopol'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('Asia/Urumqi', 'Asia/Urumqi'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('Etc/Zulu', 'Etc/Zulu'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('America/Santarem', 'America/Santarem'), ('Asia/Baku', 'Asia/Baku'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('America/Toronto', 'America/Toronto'), ('Libya', 'Libya'), ('HST', 'HST'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('Australia/Brisbane', 'Australia/Brisbane'), ('America/Denver', 'America/Denver'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('Australia/Tasmania', 'Australia/Tasmania'), ('Etc/GMT-11', 'Etc/GMT-11'), ('Europe/Prague', 'Europe/Prague'), ('America/El_Salvador', 'America/El_Salvador'), ('Europe/Zurich', 'Europe/Zurich'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('Asia/Gaza', 'Asia/Gaza'), ('America/Costa_Rica', 'America/Costa_Rica'), ('Africa/Banjul', 'Africa/Banjul'), ('Atlantic/Canary', 'Atlantic/Canary'), ('America/Shiprock', 'America/Shiprock'), ('America/Metlakatla', 'America/Metlakatla'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Etc/GMT-4', 'Etc/GMT-4'), ('Asia/Tehran', 'Asia/Tehran'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('Africa/Maseru', 'Africa/Maseru'), ('America/Montevideo', 'America/Montevideo'), ('Antarctica/Davis', 'Antarctica/Davis'), ('US/Hawaii', 'US/Hawaii'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Asia/Barnaul', 'Asia/Barnaul'), ('Europe/Oslo', 'Europe/Oslo'), ('America/Halifax', 'America/Halifax'), ('Brazil/East', 'Brazil/East'), ('US/Aleutian', 'US/Aleutian'), ('Canada/Pacific', 'Canada/Pacific'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('Etc/GMT-14', 'Etc/GMT-14'), ('Atlantic/Azores', 'Atlantic/Azores'), ('America/Whitehorse', 'America/Whitehorse'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Pacific/Easter', 'Pacific/Easter'), ('America/Moncton', 'America/Moncton'), ('Asia/Yangon', 'Asia/Yangon'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('Etc/GMT-10', 'Etc/GMT-10'), ('Australia/Queensland', 'Australia/Queensland'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('Africa/Cairo', 'Africa/Cairo'), ('America/Marigot', 'America/Marigot'), ('America/Sitka', 'America/Sitka'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('Europe/Budapest', 'Europe/Budapest'), ('America/Campo_Grande', 'America/Campo_Grande'), ('Asia/Macao', 'Asia/Macao'), ('Asia/Taipei', 'Asia/Taipei'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Europe/Samara', 'Europe/Samara'), ('Etc/GMT+3', 'Etc/GMT+3'), ('Japan', 'Japan'), ('Pacific/Samoa', 'Pacific/Samoa'), ('Europe/Belfast', 'Europe/Belfast'), ('Asia/Qatar', 'Asia/Qatar'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('Africa/Algiers', 'Africa/Algiers'), ('Asia/Kolkata', 'Asia/Kolkata'), ('America/Inuvik', 'America/Inuvik'), ('America/Cordoba', 'America/Cordoba'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('Asia/Thimbu', 'Asia/Thimbu'), ('America/Martinique', 'America/Martinique'), ('Indian/Christmas', 'Indian/Christmas'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('W-SU', 'W-SU'), ('Africa/Lusaka', 'Africa/Lusaka'), ('Asia/Magadan', 'Asia/Magadan'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('America/Ensenada', 'America/Ensenada'), ('America/Montreal', 'America/Montreal'), ('Etc/GMT+2', 'Etc/GMT+2'), ('America/Araguaina', 'America/Araguaina'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('NZ-CHAT', 'NZ-CHAT'), ('America/Resolute', 'America/Resolute'), ('America/Adak', 'America/Adak'), ('America/Louisville', 'America/Louisville'), ('US/Samoa', 'US/Samoa'), ('Canada/Central', 'Canada/Central'), ('Africa/Douala', 'Africa/Douala'), ('Etc/Greenwich', 'Etc/Greenwich'), ('Etc/GMT+6', 'Etc/GMT+6'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('Pacific/Wake', 'Pacific/Wake'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Indian/Mauritius', 'Indian/Mauritius'), ('US/Mountain', 'US/Mountain'), ('Europe/Monaco', 'Europe/Monaco'), ('PRC', 'PRC'), ('America/Nassau', 'America/Nassau'), ('Europe/Vilnius', 'Europe/Vilnius'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('Africa/Gaborone', 'Africa/Gaborone'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Asia/Aqtau', 'Asia/Aqtau'), ('America/St_Johns', 'America/St_Johns'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('America/Catamarca', 'America/Catamarca'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('America/Ojinaga', 'America/Ojinaga'), ('Pacific/Wallis', 'Pacific/Wallis'),
                                   ('Australia/Currie', 'Australia/Currie'), ('America/Iqaluit', 'America/Iqaluit'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Navajo', 'Navajo'), ('Europe/Athens', 'Europe/Athens'), ('Australia/Darwin', 'Australia/Darwin'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Europe/Warsaw', 'Europe/Warsaw'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('Europe/Zagreb', 'Europe/Zagreb'), ('Australia/LHI', 'Australia/LHI'), ('Pacific/Guam', 'Pacific/Guam'), ('Europe/Vienna', 'Europe/Vienna'), ('Mexico/General', 'Mexico/General'), ('Etc/GMT+0', 'Etc/GMT+0'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('America/Lima', 'America/Lima'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('America/Santiago', 'America/Santiago'), ('Etc/GMT+12', 'Etc/GMT+12'), ('America/Noronha', 'America/Noronha'), ('America/St_Lucia', 'America/St_Lucia'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('EST', 'EST'), ('Etc/GMT-0', 'Etc/GMT-0'), ('Europe/Riga', 'Europe/Riga'), ('PST8PDT', 'PST8PDT'), ('America/Winnipeg', 'America/Winnipeg'), ('Africa/Lagos', 'Africa/Lagos'), ('Indian/Mahe', 'Indian/Mahe'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('UCT', 'UCT'), ('Africa/Accra', 'Africa/Accra'), ('Pacific/Noumea', 'Pacific/Noumea'), ('America/Asuncion', 'America/Asuncion'), ('US/East-Indiana', 'US/East-Indiana'), ('America/Tijuana', 'America/Tijuana'), ('America/Nipigon', 'America/Nipigon'), ('Australia/ACT', 'Australia/ACT'), ('Asia/Vientiane', 'Asia/Vientiane'), ('Pacific/Chatham', 'Pacific/Chatham'), ('America/Knox_IN', 'America/Knox_IN'), ('Europe/Helsinki', 'Europe/Helsinki'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('Asia/Chungking', 'Asia/Chungking'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Europe/Dublin', 'Europe/Dublin'), ('America/Cuiaba', 'America/Cuiaba'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('America/Yellowknife', 'America/Yellowknife'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('Australia/West', 'Australia/West'), ('America/Guatemala', 'America/Guatemala'), ('Etc/GMT-13', 'Etc/GMT-13'), ('Europe/London', 'Europe/London'), ('Africa/Conakry', 'Africa/Conakry'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('America/Boa_Vista', 'America/Boa_Vista'), ('GB-Eire', 'GB-Eire'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('America/Rosario', 'America/Rosario'), ('Australia/Perth', 'Australia/Perth'), ('Indian/Chagos', 'Indian/Chagos'), ('Europe/Andorra', 'Europe/Andorra'), ('Africa/Casablanca', 'Africa/Casablanca'), ('America/Monterrey', 'America/Monterrey'), ('Africa/Khartoum', 'Africa/Khartoum'), ('America/Caracas', 'America/Caracas'), ('Pacific/Johnston', 'Pacific/Johnston'), ('UTC', 'UTC'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('Europe/Minsk', 'Europe/Minsk'), ('Australia/Hobart', 'Australia/Hobart'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('Iran', 'Iran'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Europe/San_Marino', 'Europe/San_Marino'), ('Etc/GMT+10', 'Etc/GMT+10'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('America/Boise', 'America/Boise'), ('US/Eastern', 'US/Eastern'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('America/Vancouver', 'America/Vancouver'), ('America/Anguilla', 'America/Anguilla'), ('GMT', 'GMT'), ('Pacific/Truk', 'Pacific/Truk'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('Pacific/Yap', 'Pacific/Yap'), ('Australia/NSW', 'Australia/NSW'), ('Australia/Lindeman', 'Australia/Lindeman'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('Etc/GMT-2', 'Etc/GMT-2'), ('US/Pacific', 'US/Pacific'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('EET', 'EET'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('Asia/Seoul', 'Asia/Seoul'), ('Europe/Vaduz', 'Europe/Vaduz'), ('Egypt', 'Egypt'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('America/Edmonton', 'America/Edmonton'), ('America/Matamoros', 'America/Matamoros'), ('US/Central', 'US/Central'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Australia/North', 'Australia/North'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Asia/Chongqing', 'Asia/Chongqing'), ('America/Manaus', 'America/Manaus'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('America/Paramaribo', 'America/Paramaribo'), ('America/Maceio', 'America/Maceio'), ('Asia/Baghdad', 'Asia/Baghdad'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('Asia/Jakarta', 'Asia/Jakarta'), ('Asia/Almaty', 'Asia/Almaty'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('Eire', 'Eire'), ('Asia/Atyrau', 'Asia/Atyrau'), ('Europe/Skopje', 'Europe/Skopje'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Asia/Aden', 'Asia/Aden'), ('MST7MDT', 'MST7MDT'), ('Israel', 'Israel'), ('Asia/Muscat', 'Asia/Muscat'), ('Asia/Qostanay', 'Asia/Qostanay'), ('Africa/Windhoek', 'Africa/Windhoek'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Etc/UTC', 'Etc/UTC'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Canada/Eastern', 'Canada/Eastern'), ('America/Anchorage', 'America/Anchorage'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('America/Godthab', 'America/Godthab'), ('Pacific/Gambier', 'Pacific/Gambier'), ('America/Mexico_City', 'America/Mexico_City'), ('America/Merida', 'America/Merida'), ('America/Lower_Princes', 'America/Lower_Princes'), ('Etc/GMT-12', 'Etc/GMT-12'), ('America/Swift_Current', 'America/Swift_Current'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('America/Scoresbysund', 'America/Scoresbysund'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('GMT-0', 'GMT-0'), ('Iceland', 'Iceland'), ('Universal', 'Universal'), ('Etc/GMT-9', 'Etc/GMT-9'), ('America/Panama', 'America/Panama'), ('Asia/Hovd', 'Asia/Hovd'), ('Africa/Libreville', 'Africa/Libreville'), ('CET', 'CET'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('Pacific/Ponape', 'Pacific/Ponape'), ('Asia/Beirut', 'Asia/Beirut'), ('Pacific/Palau', 'Pacific/Palau'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('America/Regina', 'America/Regina'), ('Turkey', 'Turkey'), ('Australia/Adelaide', 'Australia/Adelaide'), ('Asia/Dacca', 'Asia/Dacca'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Canada/Mountain', 'Canada/Mountain'), ('US/Arizona', 'US/Arizona'), ('America/Montserrat', 'America/Montserrat'), ('Brazil/Acre', 'Brazil/Acre'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('America/Porto_Acre', 'America/Porto_Acre'), ('Europe/Podgorica', 'Europe/Podgorica'), ('Canada/Yukon', 'Canada/Yukon'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Asia/Harbin', 'Asia/Harbin'), ('Poland', 'Poland'), ('America/Guadeloupe', 'America/Guadeloupe'), ('NZ', 'NZ'), ('MST', 'MST'), ('Asia/Thimphu', 'Asia/Thimphu'), ('Africa/Asmara', 'Africa/Asmara'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('Europe/Volgograd', 'Europe/Volgograd'), ('America/La_Paz', 'America/La_Paz'), ('America/Phoenix', 'America/Phoenix'), ('Europe/Malta', 'Europe/Malta'), ('Asia/Samarkand', 'Asia/Samarkand'), ('America/Barbados', 'America/Barbados'), ('Canada/Atlantic', 'Canada/Atlantic'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('Etc/GMT-6', 'Etc/GMT-6'), ('Etc/GMT+7', 'Etc/GMT+7'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('America/Glace_Bay', 'America/Glace_Bay'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('Singapore', 'Singapore'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('Australia/Victoria', 'Australia/Victoria'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('Asia/Hebron', 'Asia/Hebron'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Pacific/Apia', 'Pacific/Apia'), ('Brazil/West', 'Brazil/West'), ('Australia/Eucla', 'Australia/Eucla'), ('Asia/Nicosia', 'Asia/Nicosia'), ('GB', 'GB'), ('America/Indianapolis', 'America/Indianapolis'), ('America/Aruba', 'America/Aruba'), ('Indian/Maldives', 'Indian/Maldives'), ('Europe/Tallinn', 'Europe/Tallinn'), ('Hongkong', 'Hongkong'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Africa/Bangui', 'Africa/Bangui'), ('Indian/Reunion', 'Indian/Reunion'), ('Pacific/Niue', 'Pacific/Niue'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Chile/Continental', 'Chile/Continental'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('America/Hermosillo', 'America/Hermosillo'), ('Europe/Belgrade', 'Europe/Belgrade'), ('Africa/Freetown', 'Africa/Freetown'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('EST5EDT', 'EST5EDT'), ('America/Fortaleza', 'America/Fortaleza'), ('America/Managua', 'America/Managua'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('America/Grand_Turk', 'America/Grand_Turk'), ('America/Chicago', 'America/Chicago'), ('Etc/GMT+5', 'Etc/GMT+5'), ('Asia/Singapore', 'Asia/Singapore'), ('Africa/Malabo', 'Africa/Malabo'), ('America/Mendoza', 'America/Mendoza'), ('Pacific/Efate', 'Pacific/Efate'), ('Africa/Juba', 'Africa/Juba'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Greenwich', 'Greenwich'), ('America/Miquelon', 'America/Miquelon'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Etc/UCT', 'Etc/UCT'), ('Europe/Moscow', 'Europe/Moscow'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('Australia/Sydney', 'Australia/Sydney'), ('America/Cayman', 'America/Cayman'), ('US/Michigan', 'US/Michigan'), ('America/Rainy_River', 'America/Rainy_River'), ('Africa/Kigali', 'Africa/Kigali'), ('America/Grenada', 'America/Grenada'), ('Pacific/Midway', 'Pacific/Midway'), ('Etc/GMT', 'Etc/GMT'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('America/St_Vincent', 'America/St_Vincent'), ('America/Curacao', 'America/Curacao'), ('Africa/Bissau', 'Africa/Bissau'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Africa/Niamey', 'Africa/Niamey'), ('Europe/Busingen', 'Europe/Busingen'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Africa/Tunis', 'Africa/Tunis'), ('WET', 'WET'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('America/Pangnirtung', 'America/Pangnirtung'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes')], default='Europe/London', max_length=35),
        ),
        migrations.CreateModel(
            name='MultiTenantUserLoginToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(null=True)),
                ('multi_tenant_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]