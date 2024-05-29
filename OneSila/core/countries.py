from operator import itemgetter

COUNTRY_CODE_MAX_LENGTH = 2
COUNTRY_CHOICES = [
    (u'AF', u'Afghanistan'),
    (u'AL', u'Albania'),
    (u'DZ', u'Algeria'),
    (u'AS', u'American Samoa'),
    (u'AD', u'Andorra'),
    (u'AO', u'Angola'),
    (u'AI', u'Anguilla'),
    (u'AQ', u'Antarctica'),
    (u'AG', u'Antigua and Barbuda'),
    (u'AR', u'Argentina'),
    (u'AM', u'Armenia'),
    (u'AW', u'Aruba'),
    (u'AU', u'Australia'),
    (u'AT', u'Austria'),
    (u'AZ', u'Azerbaijan'),
    (u'BS', u'Bahamas'),
    (u'BH', u'Bahrain'),
    (u'BD', u'Bangladesh'),
    (u'BB', u'Barbados'),
    (u'BY', u'Belarus'),
    (u'BE', u'Belgium'),
    (u'BZ', u'Belize'),
    (u'BJ', u'Benin'),
    (u'BM', u'Bermuda'),
    (u'BT', u'Bhutan'),
    (u'BO', u'Bolivia'),
    (u'BQ', u'Bonaire'),
    (u'BA', u'Bosnia and Herzegovina'),
    (u'BW', u'Botswana'),
    (u'BV', u'Bouvet Island'),
    (u'BR', u'Brazil'),
    (u'IO', u'British Indian Ocean Territory'),
    (u'VG', u'British Virgin Islands'),
    (u'BN', u'Brunei Darussalam'),
    (u'BG', u'Bulgaria'),
    (u'BF', u'Burkina Faso'),
    (u'BI', u'Burundi'),
    (u'KH', u'Cambodia'),
    (u'CM', u'Cameroon'),
    (u'CA', u'Canada'),
    (u'CV', u'Cape Verde'),
    (u'KY', u'Cayman Islands'),
    (u'CF', u'Central African Republic'),
    (u'TD', u'Chad'),
    (u'CL', u'Chile'),
    (u'CN', u'China'),
    (u'CX', u'Christmas Island'),
    (u'CC', u'Cocos (Keeling) Islands'),
    (u'CO', u'Colombia'),
    (u'KM', u'Comoros'),
    (u'CG', u'Congo'),
    (u'CK', u'Cook Islands'),
    (u'CR', u'Costa Rica'),
    (u'CI', u"Cote d'Ivoire"),
    (u'HR', u'Croatia'),
    (u'CU', u'Cuba'),
    (u'CW', u'Curacao'),
    (u'CY', u'Cyprus'),
    (u'CZ', u'Czech Republic'),
    (u'CD', u'Democratic Republic of the Congo'),
    (u'DK', u'Denmark'),
    (u'DJ', u'Djibouti'),
    (u'DM', u'Dominica'),
    (u'DO', u'Dominican Republic'),
    (u'EC', u'Ecuador'),
    (u'EG', u'Egypt'),
    (u'SV', u'El Salvador'),
    (u'GQ', u'Equatorial Guinea'),
    (u'ER', u'Eritrea'),
    (u'EE', u'Estonia'),
    (u'ET', u'Ethiopia'),
    (u'FK', u'Falkland Islands (Malvinas)'),
    (u'FO', u'Faroe Islands'),
    (u'FJ', u'Fiji'),
    (u'FI', u'Finland'),
    (u'FR', u'France'),
    (u'GF', u'French Guiana'),
    (u'PF', u'French Polynesia'),
    (u'TF', u'French Southern Territories'),
    (u'GA', u'Gabon'),
    (u'GM', u'Gambia'),
    (u'GE', u'Georgia'),
    (u'DE', u'Germany'),
    (u'GH', u'Ghana'),
    (u'GI', u'Gibraltar'),
    (u'GR', u'Greece'),
    (u'GL', u'Greenland'),
    (u'GD', u'Grenada'),
    (u'GP', u'Guadeloupe'),
    (u'GU', u'Guam'),
    (u'GT', u'Guatemala'),
    (u'GG', u'Guernsey'),
    (u'GN', u'Guinea'),
    (u'GW', u'Guinea-Bissau'),
    (u'GY', u'Guyana'),
    (u'HT', u'Haiti'),
    (u'HM', u'Heard Island and McDonald Mcdonald Islands'),
    (u'VA', u'Holy See (Vatican City State)'),
    (u'HN', u'Honduras'),
    (u'HK', u'Hong Kong'),
    (u'HU', u'Hungary'),
    (u'IS', u'Iceland'),
    (u'IN', u'India'),
    (u'ID', u'Indonesia'),
    (u'IR', u'Iran, Islamic Republic of'),
    (u'IQ', u'Iraq'),
    (u'IE', u'Ireland'),
    (u'IM', u'Isle of Man'),
    (u'IL', u'Israel'),
    (u'IT', u'Italy'),
    (u'JM', u'Jamaica'),
    (u'JP', u'Japan'),
    (u'JE', u'Jersey'),
    (u'JO', u'Jordan'),
    (u'KZ', u'Kazakhstan'),
    (u'KE', u'Kenya'),
    (u'KI', u'Kiribati'),
    (u'KP', u"Korea, Democratic People's Republic of"),
    (u'KR', u'Korea, Republic of'),
    (u'KW', u'Kuwait'),
    (u'KG', u'Kyrgyzstan'),
    (u'LA', u"Lao People's Democratic Republic"),
    (u'LV', u'Latvia'),
    (u'LB', u'Lebanon'),
    (u'LS', u'Lesotho'),
    (u'LR', u'Liberia'),
    (u'LY', u'Libya'),
    (u'LI', u'Liechtenstein'),
    (u'LT', u'Lithuania'),
    (u'LU', u'Luxembourg'),
    (u'MO', u'Macao'),
    (u'MK', u'Macedonia, the Former Yugoslav Republic of'),
    (u'MG', u'Madagascar'),
    (u'MW', u'Malawi'),
    (u'MY', u'Malaysia'),
    (u'MV', u'Maldives'),
    (u'ML', u'Mali'),
    (u'MT', u'Malta'),
    (u'MH', u'Marshall Islands'),
    (u'MQ', u'Martinique'),
    (u'MR', u'Mauritania'),
    (u'MU', u'Mauritius'),
    (u'YT', u'Mayotte'),
    (u'MX', u'Mexico'),
    (u'FM', u'Micronesia, Federated States of'),
    (u'MD', u'Moldova, Republic of'),
    (u'MC', u'Monaco'),
    (u'MN', u'Mongolia'),
    (u'ME', u'Montenegro'),
    (u'MS', u'Montserrat'),
    (u'MA', u'Morocco'),
    (u'MZ', u'Mozambique'),
    (u'MM', u'Myanmar'),
    (u'NA', u'Namibia'),
    (u'NR', u'Nauru'),
    (u'NP', u'Nepal'),
    (u'NL', u'Netherlands'),
    (u'NC', u'New Caledonia'),
    (u'NZ', u'New Zealand'),
    (u'NI', u'Nicaragua'),
    (u'NE', u'Niger'),
    (u'NG', u'Nigeria'),
    (u'NU', u'Niue'),
    (u'NF', u'Norfolk Island'),
    (u'MP', u'Northern Mariana Islands'),
    (u'NO', u'Norway'),
    (u'OM', u'Oman'),
    (u'PK', u'Pakistan'),
    (u'PW', u'Palau'),
    (u'PS', u'Palestine, State of'),
    (u'PA', u'Panama'),
    (u'PG', u'Papua New Guinea'),
    (u'PY', u'Paraguay'),
    (u'PE', u'Peru'),
    (u'PH', u'Philippines'),
    (u'PN', u'Pitcairn'),
    (u'PL', u'Poland'),
    (u'PT', u'Portugal'),
    (u'PR', u'Puerto Rico'),
    (u'QA', u'Qatar'),
    (u'RE', u'Reunion'),
    (u'RO', u'Romania'),
    (u'RU', u'Russian Federation'),
    (u'RW', u'Rwanda'),
    (u'BL', u'Saint Barthelemy'),
    (u'SH', u'Saint Helena'),
    (u'KN', u'Saint Kitts and Nevis'),
    (u'LC', u'Saint Lucia'),
    (u'MF', u'Saint Martin (French part)'),
    (u'PM', u'Saint Pierre and Miquelon'),
    (u'VC', u'Saint Vincent and the Grenadines'),
    (u'WS', u'Samoa'),
    (u'SM', u'San Marino'),
    (u'ST', u'Sao Tome and Principe'),
    (u'SA', u'Saudi Arabia'),
    (u'SN', u'Senegal'),
    (u'RS', u'Serbia'),
    (u'SC', u'Seychelles'),
    (u'SL', u'Sierra Leone'),
    (u'SG', u'Singapore'),
    (u'SX', u'Sint Maarten (Dutch part)'),
    (u'SK', u'Slovakia'),
    (u'SI', u'Slovenia'),
    (u'SB', u'Solomon Islands'),
    (u'SO', u'Somalia'),
    (u'ZA', u'South Africa'),
    (u'GS', u'South Georgia and the South Sandwich Islands'),
    (u'SS', u'South Sudan'),
    (u'ES', u'Spain'),
    (u'LK', u'Sri Lanka'),
    (u'SD', u'Sudan'),
    (u'SR', u'Suriname'),
    (u'SJ', u'Svalbard and Jan Mayen'),
    (u'SZ', u'Swaziland'),
    (u'SE', u'Sweden'),
    (u'CH', u'Switzerland'),
    (u'SY', u'Syrian Arab Republic'),
    (u'TW', u'Taiwan, Province of China'),
    (u'TJ', u'Tajikistan'),
    (u'TH', u'Thailand'),
    (u'TL', u'Timor-Leste'),
    (u'TG', u'Togo'),
    (u'TK', u'Tokelau'),
    (u'TO', u'Tonga'),
    (u'TT', u'Trinidad and Tobago'),
    (u'TN', u'Tunisia'),
    (u'TR', u'Turkey'),
    (u'TM', u'Turkmenistan'),
    (u'TC', u'Turks and Caicos Islands'),
    (u'TV', u'Tuvalu'),
    (u'VI', u'US Virgin Islands'),
    (u'UG', u'Uganda'),
    (u'UA', u'Ukraine'),
    (u'AE', u'United Arab Emirates'),
    (u'GB', u'United Kingdom'),
    (u'TZ', u'United Republic of Tanzania'),
    (u'US', u'United States'),
    (u'UM', u'United States Minor Outlying Islands'),
    (u'UY', u'Uruguay'),
    (u'UZ', u'Uzbekistan'),
    (u'VU', u'Vanuatu'),
    (u'VE', u'Venezuela'),
    (u'VN', u'Viet Nam'),
    (u'WF', u'Wallis and Futuna'),
    (u'EH', u'Western Sahara'),
    (u'YE', u'Yemen'),
    (u'ZM', u'Zambia'),
    (u'ZW', u'Zimbabwe')]
COUNTRY_CHOICES.sort(key=itemgetter(1, 0))


EU_COUNTRIES = [
    'AT',  # Austria
    'BE',  # Belgium (1958)
    'BG',  # Bulgaria (2007)
    'HR',  # Croatia (2013)
    'CY',  # Cyprus (2004)
    'CZ',  # Czech Republic (2004)
    'DK',  # Denmark (1973)
    'EE',  # Estonia (2004)
    'FI',  # Finland (1995)
    'FR',  # France (1958)
    'DE',  # Germany (1958)
    'GR',  # Greece (1981)
    'HU',  # Hungary (2004)
    'IR',  # Ireland (1973)
    'IT',  # Italy (1958)
    'LV',  # Latvia (2004)
    'LT',  # Lithuania (2004)
    'LU',  # Luxembourg (1958)
    'MT',  # Malta (2004)
    'NL',  # Netherlands (1958)
    'PL',  # Poland (2004)
    'PT',  # Portugal (1986)
    'RO',  # Romania (2007)
    'SK',  # Slovakia (2004)
    'SI',  # Slovenia (2004)
    'ES',  # Spain (1986)
    'SE',  # Sweden (1995)
    'GB',  # United Kingdom (1973)
]


num_countries = len(COUNTRY_CHOICES)

vat_rates = {
    'AT': 20,  # Austria
    'BE': 21,  # Belgium
    'BG': 20,  # Bulgaria
    'HR': 25,  # Croatia
    'CY': 19,  # Cyprus
    'CZ': 21,  # Czech Republic
    'DK': 25,  # Denmark
    'EE': 20,  # Estonia
    'FI': 24,  # Finland
    'FR': 20,  # France
    'DE': 19,  # Germany
    'GR': 24,  # Greece
    'HU': 27,  # Hungary
    'IE': 23,  # Ireland
    'IT': 22,  # Italy
    'LV': 21,  # Latvia
    'LT': 21,  # Lithuania
    'LU': 17,  # Luxembourg
    'MT': 18,  # Malta
    'NL': 21,  # Netherlands
    'PL': 23,  # Poland
    'PT': 23,  # Portugal
    'RO': 19,  # Romania
    'SK': 20,  # Slovakia
    'SI': 22,  # Slovenia
    'ES': 21,  # Spain
    'SE': 25,  # Sweden
    'GB': 20,  # United Kingdom
    'US': 0,   # United States (no federal VAT, state-based sales tax)
    'CA': 5,   # Canada (GST)
    'AU': 10,  # Australia (GST)
    'JP': 10,  # Japan
    'CN': 13,  # China
    'IN': 18,  # India (varies, standard is around)
    'BR': 17,  # Brazil (average, varies by state)
    'RU': 20,  # Russia
    'ZA': 15,  # South Africa
    'SA': 15,  # Saudi Arabia
    'AE': 5,   # United Arab Emirates
    'MX': 16   # Mexico
}