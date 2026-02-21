"""
NYC ZIP Code to Neighborhood mapping
Used to determine neighborhood for deal addresses
"""

# Comprehensive Manhattan ZIP → Neighborhood mapping
# Sources: USPS, NYC.gov, Realtor.com neighborhood definitions
ZIP_TO_NEIGHBORHOOD = {
    # Lower Manhattan / Financial District
    "10004": "Financial District",
    "10005": "Financial District",
    "10006": "Financial District",
    "10007": "Tribeca",
    "10038": "Financial District",
    "10280": "Battery Park City",
    "10281": "Battery Park City",
    "10282": "Battery Park City",

    # Downtown
    "10002": "Lower East Side",
    "10003": "East Village",
    "10009": "East Village",
    "10012": "SoHo",
    "10013": "Tribeca",
    "10014": "West Village",

    # Midtown South
    "10001": "Chelsea",
    "10010": "Kips Bay",  # 10010 covers Kips Bay, Gramercy, Flatiron — default to Kips Bay
    "10011": "Chelsea",
    "10016": "Murray Hill",
    "10017": "Murray Hill",
    "10018": "Midtown",
    "10036": "Midtown West",

    # Midtown
    "10019": "Midtown West",
    "10020": "Midtown",
    "10022": "Midtown East",
    "10055": "Midtown East",
    "10103": "Midtown",
    "10111": "Midtown",
    "10112": "Midtown",
    "10152": "Midtown East",
    "10153": "Midtown East",
    "10154": "Midtown East",
    "10105": "Midtown",

    # Upper East Side
    "10021": "Upper East Side",
    "10028": "Upper East Side",
    "10065": "Upper East Side",
    "10075": "Upper East Side",
    "10128": "Upper East Side",
    "10029": "East Harlem",

    # Upper West Side
    "10023": "Upper West Side",
    "10024": "Upper West Side",
    "10025": "Upper West Side",

    # Harlem / Upper Manhattan
    "10026": "Harlem",
    "10027": "Harlem",
    "10030": "Harlem",
    "10031": "Hamilton Heights",
    "10032": "Washington Heights",
    "10033": "Washington Heights",
    "10034": "Inwood",
    "10039": "Harlem",
    "10040": "Washington Heights",

    # Brooklyn
    "11201": "Brooklyn Heights",
    "11205": "Clinton Hill",
    "11206": "Williamsburg",
    "11207": "East New York",
    "11208": "East New York",
    "11209": "Bay Ridge",
    "11210": "Flatbush",
    "11211": "Williamsburg",
    "11212": "Brownsville",
    "11213": "Crown Heights",
    "11214": "Bensonhurst",
    "11215": "Park Slope",
    "11216": "Bedford-Stuyvesant",
    "11217": "Park Slope",
    "11218": "Kensington",
    "11219": "Borough Park",
    "11220": "Sunset Park",
    "11221": "Bushwick",
    "11222": "Greenpoint",
    "11223": "Gravesend",
    "11224": "Coney Island",
    "11225": "Crown Heights",
    "11226": "Flatbush",
    "11228": "Dyker Heights",
    "11229": "Sheepshead Bay",
    "11230": "Midwood",
    "11231": "Carroll Gardens",
    "11232": "Sunset Park",
    "11233": "Bedford-Stuyvesant",
    "11234": "Canarsie",
    "11235": "Brighton Beach",
    "11236": "Canarsie",
    "11237": "Bushwick",
    "11238": "Prospect Heights",
    "11239": "East New York",

    # Queens
    "11101": "Long Island City",
    "11102": "Astoria",
    "11103": "Astoria",
    "11104": "Sunnyside",
    "11105": "Astoria",
    "11106": "Astoria",
    "11109": "Long Island City",
    "11354": "Flushing",
    "11355": "Flushing",
    "11356": "College Point",
    "11357": "Whitestone",
    "11358": "Fresh Meadows",
    "11360": "Bayside",
    "11361": "Bayside",
    "11362": "Little Neck",
    "11363": "Douglaston",
    "11364": "Oakland Gardens",
    "11365": "Fresh Meadows",
    "11366": "Fresh Meadows",
    "11367": "Kew Gardens Hills",
    "11368": "Corona",
    "11369": "East Elmhurst",
    "11370": "Jackson Heights",
    "11372": "Jackson Heights",
    "11373": "Elmhurst",
    "11374": "Rego Park",
    "11375": "Forest Hills",
    "11377": "Woodside",
    "11378": "Maspeth",
    "11379": "Middle Village",
    "11385": "Ridgewood",

    # Bronx
    "10451": "South Bronx",
    "10452": "Highbridge",
    "10453": "Morris Heights",
    "10454": "Mott Haven",
    "10455": "South Bronx",
    "10456": "Morrisania",
    "10457": "Tremont",
    "10458": "Fordham",
    "10459": "Longwood",
    "10460": "West Farms",
    "10461": "Westchester Square",
    "10462": "Parkchester",
    "10463": "Kingsbridge",
    "10464": "City Island",
    "10465": "Throgs Neck",
    "10466": "Wakefield",
    "10467": "Norwood",
    "10468": "Fordham",
    "10469": "Eastchester",
    "10470": "Woodlawn",
    "10471": "Riverdale",
    "10472": "Soundview",
    "10473": "Clason Point",
    "10474": "Hunts Point",
    "10475": "Co-op City",

    # Staten Island
    "10301": "St. George",
    "10302": "Port Richmond",
    "10303": "Mariners Harbor",
    "10304": "Stapleton",
    "10305": "Rosebank",
    "10306": "New Dorp",
    "10307": "Tottenville",
    "10308": "Great Kills",
    "10309": "Charleston",
    "10310": "West Brighton",
    "10312": "Eltingville",
    "10314": "Bulls Head",

    # Additional Manhattan ZIPs
    "10069": "Upper West Side",  # Riverside Boulevard area
    "10035": "East Harlem",
    "10037": "Harlem",
    "10039": "Harlem",
    "10044": "Roosevelt Island",

    # New Jersey (common for NYC area)
    "07302": "Jersey City",
    "07030": "Hoboken",
    "07310": "Jersey City",
    "07311": "Jersey City",

    # Westchester
    "10530": "Hartsdale",
    "10538": "Larchmont",
    "10543": "Mamaroneck",
    "10580": "Rye",
    "10583": "Scarsdale",
    "10601": "White Plains",
    "10701": "Yonkers",
    "10801": "New Rochelle",

    # Long Island
    "11501": "Mineola",
    "11530": "Garden City",
    "11550": "Hempstead",
    "11570": "Rockville Centre",
    "11590": "Westbury",

    # Additional Long Island
    "11542": "Glen Cove",
    "11560": "Locust Valley",
    "11576": "Roslyn",
    "11577": "Roslyn Heights",

    # Additional Westchester
    "10502": "Ardsley",
    "10504": "Armonk",
    "10510": "Briarcliff Manor",
    "10514": "Chappaqua",
    "10520": "Croton-on-Hudson",
    "10522": "Dobbs Ferry",
    "10528": "Harrison",
    "10533": "Irvington",
    "10536": "Katonah",
    "10549": "Mount Kisco",
    "10550": "Mount Vernon",
    "10552": "Mount Vernon",
    "10562": "Ossining",
    "10570": "Pleasantville",
    "10573": "Port Chester",
    "10576": "Pound Ridge",
    "10577": "Purchase",
    "10591": "Tarrytown",
    "10594": "Thornwood",
    "10605": "White Plains",
    "10606": "White Plains",
    "10607": "White Plains",
    "10703": "Yonkers",
    "10704": "Yonkers",
    "10705": "Yonkers",
    "10706": "Hastings-on-Hudson",
    "10707": "Tuckahoe",
    "10708": "Bronxville",
    "10709": "Eastchester",
    "10710": "Yonkers",

    # Additional NJ
    "07002": "Bayonne",
    "07003": "Bloomfield",
    "07006": "Caldwell",
    "07010": "Cliffside Park",
    "07020": "Edgewater",
    "07024": "Fort Lee",
    "07026": "Garfield",
    "07031": "North Arlington",
    "07032": "Kearny",
    "07042": "Montclair",
    "07043": "Upper Montclair",
    "07044": "Verona",
    "07047": "North Bergen",
    "07052": "West Orange",
    "07060": "Plainfield",
    "07070": "Rutherford",
    "07071": "Lyndhurst",
    "07087": "Union City",
    "07086": "Weehawken",
    "07093": "West New York",
    "07094": "Secaucus",
    "07102": "Newark",
    "07103": "Newark",
    "07104": "Newark",
    "07105": "Newark",
    "07306": "Jersey City",
    "07307": "Jersey City",

    # Additional Miami/FL
    "33125": "Little Havana",
    "33126": "Westchester",
    "33127": "Wynwood",
    "33128": "Downtown Miami",
    "33129": "Brickell",
    "33130": "Brickell",
    "33133": "Coconut Grove",
    "33134": "Coral Gables",
    "33135": "Little Havana",
    "33136": "Overtown",
    "33138": "Upper East Side Miami",
    "33142": "Allapattah",
    "33143": "South Miami",
    "33144": "Westchester",
    "33145": "Shenandoah",
    "33146": "Coral Gables",
    "33149": "Key Biscayne",
    "33150": "Miami Shores",
    "33155": "Westchester",
    "33156": "Pinecrest",
    "33157": "Palmetto Bay",
    "33158": "Palmetto Bay",
    "33161": "North Miami",
    "33162": "North Miami Beach",
    "33165": "Westchester",
    "33166": "Medley",
    "33167": "North Miami",
    "33168": "North Miami",
    "33169": "Miami Gardens",
    "33170": "Homestead",
    "33172": "Doral",
    "33173": "Kendall",
    "33174": "Sweetwater",
    "33175": "Kendall",
    "33176": "Kendall",
    "33177": "Homestead",
    "33178": "Doral",
    "33179": "Aventura",
    "33181": "North Miami Beach",
    "33183": "Kendall",
    "33184": "Sweetwater",
    "33185": "Kendall",
    "33186": "Kendall",
    "33187": "Homestead",
    "33189": "Cutler Bay",
    "33190": "Cutler Bay",
    "33193": "Kendall",
    "33196": "Kendall",

    # Additional Long Island ZIPs
    "11703": "North Babylon",
    "11558": "Island Park",
    "11520": "Freeport",
    "11561": "Long Beach",
    "11572": "Oceanside",
    "11580": "Valley Stream",
    "11596": "Williston Park",
    "11598": "Woodmere",
    "11516": "Cedarhurst",
    "11557": "Hewlett",
    "11559": "Lawrence",
    "11563": "Lynbrook",
    "11510": "Baldwin",
    "11552": "West Hempstead",
    "11554": "East Meadow",

    # Additional Westchester ZIPs
    "10535": "Cortlandt Manor",
    "10541": "Mahopac",
    "10547": "Mohegan Lake",
    "10566": "Peekskill",
    "10578": "Purdys",
    "10588": "Shrub Oak",
    "10589": "Somers",
    "10590": "South Salem",
    "10598": "Yorktown Heights",

    # Additional FL ZIPs
    "33033": "Homestead",
    "33034": "Homestead",
    "33035": "Homestead",
    "33039": "Homestead",
    "33010": "Hialeah",
    "33012": "Hialeah",
    "33013": "Hialeah",
    "33014": "Hialeah",
    "33015": "Miami Lakes",
    "33016": "Hialeah",
    "33018": "Hialeah Gardens",
    "33054": "Opa-locka",
    "33055": "Miami Gardens",
    "33056": "Miami Gardens",

    # Connecticut
    "06830": "Greenwich",
    "06840": "New Canaan",
    "06851": "Norwalk",
    "06870": "Old Greenwich",
    "06880": "Westport",
    "06901": "Stamford",
    "06902": "Stamford",
    "06903": "Stamford",

    # Miami / Florida (some deals may be there)
    "33101": "Miami",
    "33109": "Miami Beach",
    "33131": "Brickell",
    "33132": "Downtown Miami",
    "33137": "Wynwood",
    "33139": "South Beach",
    "33140": "Miami Beach",
    "33141": "North Beach",
    "33154": "Bal Harbour",
    "33160": "Aventura",
    "33180": "Aventura",
}


# Manhattan numbered street → ZIP code mapping
# Based on street number ranges and East/West side
# This covers the majority of Manhattan addresses
MANHATTAN_STREET_TO_ZIP = {
    # Format: (min_street, max_street, side) → zip
    # East Side
    ("east", 1, 1): "10003",      # East 1st St → East Village
    ("east", 2, 8): "10003",      # East 2nd-8th → East Village
    ("east", 9, 13): "10003",     # East 9th-13th → East Village
    ("east", 14, 20): "10003",    # East 14th-20th → Gramercy area
    ("east", 14, 14): "10003",    # East 14th → Union Square area
    ("east", 15, 20): "10003",    # East 15th-20th → Gramercy
    ("east", 21, 30): "10010",    # East 21st-30th → Gramercy Park / Kips Bay
    ("east", 31, 39): "10016",    # East 31st-39th → Murray Hill
    ("east", 40, 49): "10017",    # East 40th-49th → Midtown East / Turtle Bay
    ("east", 50, 59): "10022",    # East 50th-59th → Midtown East / Sutton Place
    ("east", 60, 69): "10065",    # East 60th-69th → Upper East Side (Lenox Hill)
    ("east", 70, 79): "10021",    # East 70th-79th → Upper East Side
    ("east", 80, 89): "10028",    # East 80th-89th → Upper East Side
    ("east", 90, 99): "10128",    # East 90th-99th → Upper East Side (Carnegie Hill)
    ("east", 100, 110): "10029",  # East 100th-110th → East Harlem
    ("east", 111, 125): "10029",  # East 111th-125th → East Harlem

    # West Side
    ("west", 1, 8): "10014",      # West 1st-8th → West Village
    ("west", 9, 13): "10014",     # West 9th-13th → West Village
    ("west", 14, 20): "10011",    # West 14th-20th → Chelsea
    ("west", 21, 30): "10001",    # West 21st-30th → Chelsea
    ("west", 31, 39): "10001",    # West 31st-39th → Chelsea / Penn Station area
    ("west", 40, 49): "10036",    # West 40th-49th → Midtown West / Hell's Kitchen
    ("west", 50, 59): "10019",    # West 50th-59th → Midtown West
    ("west", 60, 69): "10023",    # West 60th-69th → Upper West Side (Lincoln Center)
    ("west", 70, 79): "10023",    # West 70th-79th → Upper West Side
    ("west", 80, 89): "10024",    # West 80th-89th → Upper West Side
    ("west", 90, 99): "10025",    # West 90th-99th → Upper West Side
    ("west", 100, 110): "10025",  # West 100th-110th → Upper West Side / Manhattan Valley
    ("west", 111, 125): "10027",  # West 111th-125th → Harlem
    ("west", 126, 145): "10027",  # West 126th-145th → Harlem
    ("west", 146, 165): "10031",  # West 146th-165th → Hamilton Heights
    ("west", 166, 190): "10032",  # West 166th-190th → Washington Heights
    ("west", 191, 220): "10040",  # West 191th-220th → Washington Heights / Inwood
}

# Named street → ZIP mapping for common NYC streets
NAMED_STREET_TO_ZIP = {
    "broadway": {
        (1, 100): "10006",       # Lower Broadway → Financial District
        (100, 400): "10013",     # Broadway SoHo/Tribeca
        (400, 800): "10012",     # Broadway → SoHo / NoHo
        (800, 1200): "10003",    # Broadway → Union Square area
        (1200, 1600): "10001",   # Broadway → Chelsea / Flatiron
        (1600, 2000): "10019",   # Broadway → Midtown
        (2000, 2500): "10023",   # Broadway → Upper West Side
    },
    "park avenue": {
        (1, 200): "10016",       # Park Ave South → Murray Hill
        (200, 500): "10017",     # Park Ave → Midtown
        (500, 700): "10022",     # Park Ave → Midtown East
        (700, 900): "10021",     # Park Ave → Upper East Side
        (900, 1200): "10028",    # Park Ave → Upper East Side
    },
    "5th avenue": {
        (1, 200): "10010",       # 5th Ave → Flatiron
        (200, 500): "10016",     # 5th Ave → Murray Hill / Midtown
        (500, 800): "10022",     # 5th Ave → Midtown
        (800, 1100): "10065",    # 5th Ave → Upper East Side
    },
    "lexington avenue": {
        (1, 200): "10010",       # Lex → Gramercy
        (200, 400): "10016",     # Lex → Murray Hill
        (400, 600): "10017",     # Lex → Midtown East
        (600, 800): "10065",     # Lex → Upper East Side
        (800, 1100): "10021",    # Lex → Upper East Side
    },
    "madison avenue": {
        (1, 200): "10010",       # Madison → Flatiron
        (200, 500): "10016",     # Madison → Murray Hill
        (500, 700): "10022",     # Madison → Midtown
        (700, 1000): "10065",    # Madison → Upper East Side
        (1000, 1400): "10028",   # Madison → Upper East Side
    },
    "west end avenue": {
        (1, 999): "10024",       # West End Ave → Upper West Side
    },
    "riverside drive": {
        (1, 999): "10024",       # Riverside Dr → Upper West Side
    },
    "central park west": {
        (1, 999): "10024",       # CPW → Upper West Side
    },
    "amsterdam avenue": {
        (1, 999): "10025",       # Amsterdam → Upper West Side
    },
    "columbus avenue": {
        (1, 999): "10024",       # Columbus → Upper West Side
    },
    "york avenue": {
        (1, 999): "10021",       # York Ave → Upper East Side
    },
    "1st avenue": {
        (1, 400): "10009",       # 1st Ave → East Village
        (400, 800): "10016",     # 1st Ave → Murray Hill / Kips Bay
        (800, 1200): "10021",    # 1st Ave → Upper East Side
    },
    "2nd avenue": {
        (1, 400): "10003",       # 2nd Ave → East Village
        (400, 800): "10016",     # 2nd Ave → Murray Hill
        (800, 1200): "10028",    # 2nd Ave → Upper East Side
    },
    "3rd avenue": {
        (1, 400): "10003",       # 3rd Ave → East Village
        (400, 800): "10016",     # 3rd Ave → Murray Hill
        (800, 1200): "10028",    # 3rd Ave → Upper East Side
    },
    # Brooklyn named streets
    "atlantic avenue": {
        (1, 999): "11217",       # Atlantic Ave → Park Slope / Boerum Hill
    },
    # Downtown Manhattan
    "wall street": {(1, 999): "10005"},
    "water street": {(1, 999): "10004"},
    "fulton street": {(1, 999): "10038"},
    "chambers street": {(1, 999): "10007"},
    "canal street": {(1, 999): "10013"},
    "houston street": {(1, 999): "10012"},
    "bleecker street": {(1, 999): "10012"},
    "spring street": {(1, 999): "10012"},
    "prince street": {(1, 999): "10012"},
    "greene street": {(1, 999): "10012"},
    "mercer street": {(1, 999): "10012"},
    "wooster street": {(1, 999): "10012"},
    "crosby street": {(1, 999): "10012"},
    "barrow street": {(1, 999): "10014"},
    "perry street": {(1, 999): "10014"},
    "charles street": {(1, 999): "10014"},
    "christopher street": {(1, 999): "10014"},
    "grove street": {(1, 999): "10014"},
    "bedford street": {(1, 999): "10014"},
    "morton street": {(1, 999): "10014"},
    "bank street": {(1, 999): "10014"},
    "jane street": {(1, 999): "10014"},
    "horatio street": {(1, 999): "10014"},
    "washington street": {(1, 999): "10014"},
    "greenwich street": {(1, 999): "10013"},
    "hudson street": {(1, 999): "10013"},
    "varick street": {(1, 999): "10013"},
    "laight street": {(1, 999): "10013"},
    "franklin street": {(1, 999): "10013"},
    "leonard street": {(1, 999): "10013"},
    "worth street": {(1, 999): "10013"},
    "duane street": {(1, 999): "10007"},
    "reade street": {(1, 999): "10007"},
    "warren street": {(1, 999): "10007"},
    "murray street": {(1, 999): "10007"},
    "barclay street": {(1, 999): "10007"},
    "vesey street": {(1, 999): "10007"},
    "john street": {(1, 999): "10038"},
    "maiden lane": {(1, 999): "10038"},
    "nassau street": {(1, 999): "10038"},
    "william street": {(1, 999): "10038"},
    "pearl street": {(1, 999): "10004"},
    "front street": {(1, 999): "10004"},
    "south street": {(1, 999): "10004"},
    "whitehall street": {(1, 999): "10004"},
    "state street": {(1, 999): "10004"},
    "confucius plaza": {(1, 999): "10002"},
    "east end avenue": {
        (1, 999): "10028",       # East End Ave → Upper East Side
    },
    # Additional Manhattan streets
    "irving place": {(1, 999): "10003"},
    "gramercy park south": {(1, 999): "10010"},
    "gramercy park north": {(1, 999): "10010"},
    "gramercy park east": {(1, 999): "10010"},
    "gramercy park west": {(1, 999): "10010"},
    "stuyvesant square": {(1, 999): "10003"},
    "sutton place": {(1, 999): "10022"},
    "beekman place": {(1, 999): "10022"},
    "tudor city place": {(1, 999): "10017"},
    "united nations plaza": {(1, 999): "10017"},
    "un plaza": {(1, 999): "10017"},
    "fdr drive": {(1, 999): "10002"},
    "fdr dr": {(1, 999): "10002"},
    "rector place": {(1, 999): "10280"},
    "south end avenue": {(1, 999): "10280"},
    "river terrace": {(1, 999): "10282"},
    "north end avenue": {(1, 999): "10282"},
    "albany street": {(1, 999): "10006"},
    "gold street": {(1, 999): "10038"},
    "bridge street": {(1, 999): "10004"},
    "broad street": {
        (1, 100): "10004",
        (100, 999): "10004",
    },
    "beaver street": {(1, 999): "10004"},
    "thomas street": {(1, 999): "10007"},
    "walker street": {(1, 999): "10013"},
    "lispenard street": {(1, 999): "10013"},
    "white street": {(1, 999): "10013"},
    "beach street": {(1, 999): "10013"},
    "north moore street": {(1, 999): "10013"},
    "harrison street": {(1, 999): "10013"},
    "jay street": {(1, 999): "10013"},
    "sullivan street": {(1, 999): "10012"},
    "thompson street": {(1, 999): "10012"},
    "macdougal street": {(1, 999): "10012"},
    "king street": {(1, 999): "10014"},
    "leroy street": {(1, 999): "10014"},
    "clarkson street": {(1, 999): "10014"},
    "carmine street": {(1, 999): "10014"},
    "cornelia street": {(1, 999): "10014"},
    "minetta lane": {(1, 999): "10012"},
    "sheridan square": {(1, 999): "10014"},
    "7th avenue": {
        (1, 200): "10014",       # 7th Ave → West Village
        (200, 500): "10001",     # 7th Ave → Chelsea
        (500, 999): "10019",     # 7th Ave → Midtown
    },
    "seventh avenue": {
        (1, 200): "10014",
        (200, 500): "10001",
        (500, 999): "10019",
    },
    "6th avenue": {
        (1, 200): "10013",       # 6th Ave → SoHo
        (200, 500): "10011",     # 6th Ave → Chelsea
        (500, 999): "10019",     # 6th Ave → Midtown
    },
    "avenue of the americas": {
        (1, 200): "10013",
        (200, 500): "10011",
        (500, 999): "10019",
    },
    "8th avenue": {
        (1, 200): "10014",
        (200, 500): "10001",
        (500, 999): "10019",
    },
    "9th avenue": {
        (1, 200): "10014",
        (200, 500): "10001",
        (500, 999): "10019",
    },
    "10th avenue": {
        (1, 200): "10014",
        (200, 500): "10001",
        (500, 999): "10019",
    },
    "11th avenue": {
        (1, 200): "10014",
        (200, 500): "10001",
        (500, 999): "10019",
    },
    "west street": {(1, 999): "10013"},
    "greenwich avenue": {(1, 999): "10014"},
    "waverly place": {(1, 999): "10014"},
    "west end avenue": {
        (1, 300): "10023",
        (300, 600): "10024",
        (600, 999): "10025",
    },
    "riverside boulevard": {(1, 999): "10069"},
    "henry hudson parkway": {(1, 999): "10463"},
    "pinehurst avenue": {(1, 999): "10033"},
    "fort washington avenue": {(1, 999): "10032"},
    "haven avenue": {(1, 999): "10032"},
    "cabrini boulevard": {(1, 999): "10033"},
    "convent avenue": {(1, 999): "10027"},
    "hamilton terrace": {(1, 999): "10031"},
    "st nicholas avenue": {(1, 999): "10027"},
    "adam clayton powell boulevard": {(1, 999): "10027"},
    "adam clayton powell blvd": {(1, 999): "10027"},
    "adam clayton powell jr blvd": {(1, 999): "10027"},
    "adam clayton powell jr boulevard": {(1, 999): "10027"},
    "frederick douglass boulevard": {(1, 999): "10027"},
    "frederick douglass blvd": {(1, 999): "10027"},
    "malcolm x boulevard": {(1, 999): "10027"},
    "lenox avenue": {(1, 999): "10027"},
    "morningside drive": {(1, 999): "10027"},
    "morningside avenue": {(1, 999): "10027"},
    "edgecombe avenue": {(1, 999): "10030"},
    "bradhurst avenue": {(1, 999): "10039"},
    "pleasant avenue": {(1, 999): "10029"},
    "central park south": {(1, 999): "10019"},
    "central park west": {
        (1, 200): "10023",
        (200, 400): "10024",
        (400, 999): "10025",
    },
    "central park w": {
        (1, 200): "10023",
        (200, 400): "10024",
        (400, 999): "10025",
    },
    "park row": {(1, 999): "10038"},
    "division street": {(1, 999): "10002"},
    "grand concourse": {
        (1, 600): "10451",
        (600, 1200): "10452",
        (1200, 999): "10453",
    },
    "sedgwick avenue": {(1, 999): "10453"},
    "sheridan avenue": {(1, 999): "10456"},
    "hudson manor terrace": {(1, 999): "10463"},
    # More Brooklyn streets
    "livingston street": {(1, 999): "11201"},
    "schermerhorn street": {(1, 999): "11201"},
    "boerum place": {(1, 999): "11201"},
    "hoyt street": {(1, 999): "11201"},
    "bond street": {(1, 999): "11217"},
    "nevins street": {(1, 999): "11217"},
    "3rd avenue": {
        (1, 400): "10003",       # 3rd Ave → East Village
        (400, 800): "10016",     # 3rd Ave → Murray Hill
        (800, 1200): "10028",    # 3rd Ave → Upper East Side
    },
    "4th avenue": {
        (1, 100): "10003",       # 4th Ave → East Village (Manhattan)
        (100, 999): "11215",     # 4th Ave → Park Slope (Brooklyn)
    },
    "prospect park southwest": {(1, 999): "11215"},
    "prospect park west": {(1, 999): "11215"},
    "plaza street east": {(1, 999): "11238"},
    "plaza street": {(1, 999): "11238"},
    "ashland place": {(1, 999): "11217"},
    "carlton avenue": {(1, 999): "11205"},
    "adelphi street": {(1, 999): "11205"},
    "clermont avenue": {(1, 999): "11205"},
    "vanderbilt avenue": {(1, 999): "11205"},
    "clinton avenue": {(1, 999): "11205"},
    "waverly avenue": {(1, 999): "11205"},
    "washington avenue": {(1, 999): "11205"},
    "underhill avenue": {(1, 999): "11238"},
    "st james place": {(1, 999): "11238"},
    "cambridge place": {(1, 999): "11238"},
    "grand avenue": {(1, 999): "11205"},
    "downing street": {(1, 999): "11238"},
    "poplar street": {(1, 999): "11201"},
    "middagh street": {(1, 999): "11201"},
    "cranberry street": {(1, 999): "11201"},
    "orange street": {(1, 999): "11201"},
    "pineapple street": {(1, 999): "11201"},
    "willow street": {(1, 999): "11201"},
    "love lane": {(1, 999): "11201"},
    "grace court": {(1, 999): "11201"},
    "garden place": {(1, 999): "11201"},
    "sidney place": {(1, 999): "11201"},
    "state street": {(1, 999): "10004"},
    "pacific avenue": {(1, 999): "11217"},
    "macdonough street": {(1, 999): "11216"},
    "herkimer street": {(1, 999): "11216"},
    "cumberland street": {(1, 999): "11205"},
    "devoe street": {(1, 999): "11211"},
    "calyer street": {(1, 999): "11222"},
    "havemeyer street": {(1, 999): "11211"},
    "rogers avenue": {(1, 999): "11225"},
    "rugby road": {(1, 999): "11226"},
    "willoughby avenue": {(1, 999): "11205"},
    "dikeman street": {(1, 999): "11231"},
    "seeley street": {(1, 999): "11218"},
    "arion place": {(1, 999): "11211"},
    "moffat street": {(1, 999): "11207"},
    "chauncey street": {(1, 999): "11233"},
    "bainebridge": {(1, 999): "11233"},
    "bainbridge street": {(1, 999): "11233"},
    "jefferson avenue": {(1, 999): "11216"},
    "franklin avenue": {(1, 999): "11238"},
    # Queens
    "yellowstone boulevard": {(1, 999): "11375"},
    "yellowstone blvd": {(1, 999): "11375"},
    # Downtown Brooklyn
    "jay street": {(1, 999): "11201"},
    "bridge street": {(1, 999): "11201"},
    # Jersey City
    "palisade avenue": {(1, 999): "07302"},
    "palisade ave": {(1, 999): "07302"},
    # Hoboken
    "hudson street": {(1, 999): "07030"},
    # Miami / Brickell
    "brickell avenue": {(1, 999): "33131"},
    "brickell ave": {(1, 999): "33131"},
    "brickell bay drive": {(1, 999): "33131"},
    "brickell bay dr": {(1, 999): "33131"},
    "biscayne boulevard": {(1, 999): "33132"},
    "biscayne blvd": {(1, 999): "33132"},
    "collins avenue": {
        (1, 5000): "33140",
        (5000, 8000): "33140",
        (8000, 12000): "33154",
    },
    "collins ave": {
        (1, 5000): "33140",
        (5000, 8000): "33140",
        (8000, 12000): "33154",
    },
    "ocean drive": {(1, 999): "33139"},
    "lincoln road": {(1, 999): "33139"},
    "washington ave": {(1, 999): "33139"},
    "meridian avenue": {(1, 999): "33139"},
    "meridian ave": {(1, 999): "33139"},
    "euclid avenue": {(1, 999): "33139"},
    "euclid ave": {(1, 999): "33139"},
    "michigan avenue": {(1, 999): "33139"},
    "michigan ave": {(1, 999): "33139"},
    "sunset harbour drive": {(1, 999): "33139"},
    "sunset harbour dr": {(1, 999): "33139"},
    "purdy avenue": {(1, 999): "33139"},
    "purdy ave": {(1, 999): "33139"},
    "bay road": {(1, 999): "33139"},
    "west avenue": {(1, 999): "33139"},
    "west ave": {(1, 999): "33139"},
    "broome street": {(1, 999): "10013"},
    "broome st": {(1, 999): "10013"},
    "grand street": {
        (1, 300): "10002",       # Grand St → Lower East Side (Manhattan)
        (300, 600): "10002",     # Grand St → LES
    },
    "rivington street": {(1, 999): "10002"},
    "delancey street": {(1, 999): "10002"},
    "orchard street": {(1, 999): "10002"},
    "ludlow street": {(1, 999): "10002"},
    "essex street": {(1, 999): "10002"},
    "norfolk street": {(1, 999): "10002"},
    "stanton street": {(1, 999): "10002"},
    "clinton street": {(1, 999): "10002"},  # Manhattan Clinton St (LES)
    "division street": {(1, 999): "10002"},
    "market street": {(1, 999): "10002"},
    "pike street": {(1, 999): "10002"},
    "rutgers street": {(1, 999): "10002"},
    "henry street": {(1, 999): "10002"},  # Manhattan Henry St (LES)
    "madison street": {(1, 999): "10002"},
    "monroe street": {(1, 999): "10002"},
    "cherry street": {(1, 999): "10002"},
    "south street": {(1, 999): "10004"},
    "north bayshore drive": {(1, 999): "33132"},
    "bayshore drive": {(1, 999): "33131"},
}

# Brooklyn street number → ZIP mapping
BROOKLYN_STREET_TO_ZIP = {
    # Park Slope / Gowanus area (numbered streets)
    (1, 9): "11215",     # 1st-9th St → Park Slope
    (10, 16): "11215",   # 10th-16th St → Park Slope
    (17, 25): "11215",   # 17th-25th St → South Slope
    (26, 40): "11232",   # 26th-40th St → Sunset Park
    (41, 65): "11220",   # 41st-65th St → Sunset Park / Borough Park
    (66, 86): "11209",   # 66th-86th St → Bay Ridge
    (87, 101): "11209",  # 87th-101st St → Bay Ridge
}

# Brooklyn named streets → ZIP
BROOKLYN_NAMED_STREETS = {
    "park place": "11238",        # Prospect Heights
    "sterling place": "11238",    # Prospect Heights
    "st marks avenue": "11238",   # Prospect Heights
    "prospect place": "11238",    # Prospect Heights
    "dean street": "11217",       # Boerum Hill / Park Slope
    "bergen street": "11217",     # Boerum Hill / Park Slope
    "pacific street": "11217",    # Boerum Hill
    "baltic street": "11217",     # Boerum Hill
    "butler street": "11217",     # Boerum Hill
    "sackett street": "11217",    # Carroll Gardens
    "union street": "11217",      # Park Slope
    "president street": "11215",  # Park Slope
    "carroll street": "11215",    # Park Slope / Carroll Gardens
    "garfield place": "11215",    # Park Slope
    "1st street": "11215",        # Park Slope
    "2nd street": "11215",        # Park Slope
    "3rd street": "11215",        # Park Slope
    "4th street": "11215",        # Park Slope
    "st johns place": "11238",    # Crown Heights
    "lincoln place": "11238",     # Prospect Heights
    "eastern parkway": "11238",   # Prospect Heights / Crown Heights
    "flatbush avenue": "11225",   # Flatbush
    "nostrand avenue": "11216",   # Bed-Stuy
    "bedford avenue": "11211",    # Williamsburg
    "driggs avenue": "11211",     # Williamsburg
    "kent avenue": "11211",       # Williamsburg
    "wythe avenue": "11211",      # Williamsburg
    "berry street": "11211",      # Williamsburg
    "north 10th street": "11211", # Williamsburg
    "metropolitan avenue": "11211", # Williamsburg
    "grand street": "11211",      # Williamsburg
    "smith street": "11231",      # Carroll Gardens
    "court street": "11201",      # Brooklyn Heights / Cobble Hill
    "henry street": "11201",      # Brooklyn Heights
    "hicks street": "11201",      # Brooklyn Heights
    "columbia street": "11231",   # Columbia Waterfront
    "clinton street": "11201",    # Brooklyn Heights / Cobble Hill
    "montague street": "11201",   # Brooklyn Heights
    "remsen street": "11201",     # Brooklyn Heights
    "joralemon street": "11201",  # Brooklyn Heights
    "pierrepont street": "11201", # Brooklyn Heights
    "maple street": "11225",      # Flatbush / Prospect Lefferts
    "midwood street": "11225",    # Flatbush
    "fenimore street": "11225",   # Flatbush
    "hawthorne street": "11225",  # Flatbush
    "winthrop street": "11225",   # Flatbush
    "clarkson avenue": "11226",   # Flatbush
    "linden boulevard": "11226",  # Flatbush
    "church avenue": "11226",     # Flatbush
    "beverley road": "11218",     # Kensington
    "cortelyou road": "11218",    # Kensington / Ditmas Park
    "ditmas avenue": "11218",     # Kensington / Ditmas Park
    "ocean avenue": "11226",      # Flatbush
    "ocean parkway": "11218",     # Kensington
    "coney island avenue": "11218", # Kensington
    "myrtle avenue": "11205",     # Clinton Hill
    "dekalb avenue": "11205",     # Clinton Hill
    "lafayette avenue": "11205",  # Clinton Hill
    "greene avenue": "11238",     # Clinton Hill / Prospect Heights
    "gates avenue": "11238",      # Clinton Hill
    "putnam avenue": "11238",     # Clinton Hill
    "fulton street": "11217",     # Fort Greene (Brooklyn)
    "flatlands avenue": "11234",  # Canarsie / Flatlands
    "avenue u": "11229",          # Sheepshead Bay
    "avenue x": "11235",          # Brighton Beach
    "brighton beach avenue": "11235", # Brighton Beach
    "neptune avenue": "11224",    # Coney Island
    "surf avenue": "11224",       # Coney Island
    "emmons avenue": "11235",     # Sheepshead Bay
    "jersey avenue": "11207",     # East New York
    "chestnut street": "11208",   # Cypress Hills
    "park place": "11238",        # Prospect Heights (duplicate for safety)
    "prospect park sw": "11215",  # Prospect Park Southwest
    "plaza st east": "11238",     # Plaza Street East
    "plaza st": "11238",          # Plaza Street
    "avenue r": "11229",          # Sheepshead Bay
    "avenue t": "11229",          # Sheepshead Bay
    "avenue y": "11235",          # Brighton Beach
    "utica avenue": "11213",      # Crown Heights
    "utica ave": "11213",         # Crown Heights
}


import re
import json
import time
import logging
import urllib.request
import urllib.parse
from typing import Optional, Dict, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Direct street-range → neighborhood mapping for Manhattan areas where ZIP is too coarse
# This is checked BEFORE the ZIP-based lookup for more precise results
MANHATTAN_STREET_NEIGHBORHOOD = {
    # East Side numbered streets
    ("east", 1, 8): "East Village",
    ("east", 9, 13): "East Village",
    ("east", 14, 20): "Gramercy Park",
    ("east", 21, 27): "Kips Bay",       # Kips Bay starts around 23rd but 21-22 are borderline
    ("east", 28, 34): "Kips Bay",
    ("east", 35, 39): "Murray Hill",
    ("east", 40, 49): "Midtown East",
    ("east", 50, 59): "Midtown East",
    ("east", 60, 69): "Upper East Side",
    ("east", 70, 79): "Upper East Side",
    ("east", 80, 89): "Upper East Side",
    ("east", 90, 99): "Upper East Side",
    ("east", 100, 125): "East Harlem",

    # West Side numbered streets
    ("west", 1, 8): "West Village",
    ("west", 9, 13): "West Village",
    ("west", 14, 20): "Chelsea",
    ("west", 21, 30): "Chelsea",
    ("west", 31, 39): "Chelsea",
    ("west", 40, 49): "Midtown West",
    ("west", 50, 59): "Midtown West",
    ("west", 60, 69): "Upper West Side",
    ("west", 70, 79): "Upper West Side",
    ("west", 80, 89): "Upper West Side",
    ("west", 90, 99): "Upper West Side",
    ("west", 100, 110): "Upper West Side",
    ("west", 111, 125): "Harlem",
    ("west", 126, 145): "Harlem",
    ("west", 146, 165): "Hamilton Heights",
    ("west", 166, 190): "Washington Heights",
    ("west", 191, 220): "Inwood",
}

# Named street → neighborhood for avenues that cross multiple neighborhoods
NAMED_STREET_NEIGHBORHOOD = {
    "gramercy park south": "Gramercy Park",
    "gramercy park north": "Gramercy Park",
    "gramercy park east": "Gramercy Park",
    "gramercy park west": "Gramercy Park",
    "irving place": "Gramercy Park",
    "stuyvesant square": "Gramercy Park",
    "5th avenue": {
        (1, 100): "Greenwich Village",
        (100, 250): "Flatiron",
        (250, 500): "Midtown",
        (500, 800): "Midtown",
        (800, 1200): "Upper East Side",
    },
    "5th ave": {
        (1, 100): "Greenwich Village",
        (100, 250): "Flatiron",
        (250, 500): "Midtown",
        (500, 800): "Midtown",
        (800, 1200): "Upper East Side",
    },
    "park avenue": {
        (1, 200): "Murray Hill",
        (200, 500): "Midtown East",
        (500, 700): "Midtown East",
        (700, 1200): "Upper East Side",
    },
    "park ave": {
        (1, 200): "Murray Hill",
        (200, 500): "Midtown East",
        (500, 700): "Midtown East",
        (700, 1200): "Upper East Side",
    },
    "broadway": {
        (1, 100): "Financial District",
        (100, 400): "Tribeca",
        (400, 800): "SoHo",
        (800, 1200): "Union Square",
        (1200, 1600): "Flatiron",
        (1600, 2000): "Midtown",
        (2000, 2500): "Upper West Side",
    },
    "lexington avenue": {
        (1, 200): "Kips Bay",
        (200, 400): "Murray Hill",
        (400, 600): "Midtown East",
        (600, 1200): "Upper East Side",
    },
    "lexington ave": {
        (1, 200): "Kips Bay",
        (200, 400): "Murray Hill",
        (400, 600): "Midtown East",
        (600, 1200): "Upper East Side",
    },
}

# Cache file for geocoded results
_GEOCODE_CACHE_FILE = Path(__file__).parent.parent.parent / "data" / "cache" / "geocode_cache.json"
_geocode_cache: Dict[str, Optional[Dict]] = {}


def _load_geocode_cache() -> Dict[str, Optional[Dict]]:
    """Load geocode cache from disk"""
    global _geocode_cache
    if _geocode_cache:
        return _geocode_cache
    try:
        if _GEOCODE_CACHE_FILE.exists():
            with open(_GEOCODE_CACHE_FILE, 'r') as f:
                _geocode_cache = json.load(f)
    except Exception:
        _geocode_cache = {}
    return _geocode_cache


def _save_geocode_cache():
    """Save geocode cache to disk"""
    try:
        _GEOCODE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_GEOCODE_CACHE_FILE, 'w') as f:
            json.dump(_geocode_cache, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving geocode cache: {e}")


def _clean_address(address: str) -> str:
    """Clean address for lookup: remove unit/apt, normalize"""
    if not address:
        return ""
    addr = address.strip()
    # Remove unit/apt info - be careful not to match "United" or "Eastern"
    # Only match apt/unit/suite/floor when followed by a space and then the unit identifier
    addr = re.sub(r'\s*[,]?\s*[#]?\s*(?:apt\.?|apartment|suite|ste\.?)\s+[#]?\s*[a-zA-Z0-9/\-]+', '', addr, flags=re.IGNORECASE)
    # Match "unit" only as a standalone word followed by unit number (not "United")
    addr = re.sub(r'\s+unit\s+[a-zA-Z0-9/\-]+', '', addr, flags=re.IGNORECASE)
    # Match "Fl" or "Floor" followed by number
    addr = re.sub(r'\s+(?:fl\.?|floor)\s*\d+', '', addr, flags=re.IGNORECASE)
    # Remove # followed by unit number
    addr = re.sub(r'\s*[,]?\s*#[a-zA-Z0-9/\-]+', '', addr)
    addr = re.sub(r'\s*\(.*?\)', '', addr)  # Remove parenthetical like (EXT)
    addr = re.sub(r'\s+', ' ', addr).strip().rstrip(',').rstrip('.').strip()
    return addr.lower()


def get_zip_from_address(address: str) -> Optional[str]:
    """
    Determine ZIP code from a street address using our mapping tables.
    Returns ZIP code string or None if not determinable.
    """
    if not address:
        return None

    addr = address.lower().strip()
    addr_clean = _clean_address(addr)

    # 0. Check if address already contains a ZIP code
    zip_match = re.search(r'\b(\d{5})\b', address)
    if zip_match:
        z = zip_match.group(1)
        if z in ZIP_TO_NEIGHBORHOOD:
            return z

    # 0b. Normalize common variations in the cleaned address
    # "Fifth" → "5th", "Second" → "2nd", etc.
    ordinal_map = {
        'first': '1st', 'second': '2nd', 'third': '3rd', 'fourth': '4th',
        'fifth': '5th', 'sixth': '6th', 'seventh': '7th', 'eighth': '8th',
        'ninth': '9th', 'tenth': '10th', 'eleventh': '11th', 'twelfth': '12th',
    }
    addr_normalized = addr_clean
    for word, num in ordinal_map.items():
        addr_normalized = re.sub(r'\b' + word + r'\b', num, addr_normalized)
    
    # Also normalize "central park s" → "central park south"
    addr_normalized = re.sub(r'\bcentral park s\b', 'central park south', addr_normalized)
    # "park pl" → "park place"
    addr_normalized = re.sub(r'\bpark pl\b', 'park place', addr_normalized)
    # "west end" without "avenue" → "west end avenue"
    addr_normalized = re.sub(r'\bwest end\b(?!\s+ave)', 'west end avenue', addr_normalized)
    # Remove letter suffix from building numbers: "2570c" → "2570"
    addr_normalized = re.sub(r'^(\d+)[a-zA-Z]\b', r'\1', addr_normalized)
    # "N 7th" → "north 7th" for Williamsburg
    addr_normalized = re.sub(r'\b(\d+)\s*n\s+(\d+)', r'\1 north \2', addr_normalized)
    # "Ave R" / "Ave T" / "Ave Y" → "avenue r" etc.
    ave_letter = re.search(r'\bave(?:nue)?\s+([a-z])\b', addr_normalized)
    if ave_letter:
        letter = ave_letter.group(1)
        bk_ave_map = {'r': '11229', 't': '11229', 'u': '11229', 'y': '11235', 'x': '11235',
                       'n': '11230', 'j': '11230', 'k': '11230', 'h': '11230', 'i': '11230',
                       'm': '11230', 'p': '11223', 'z': '11235'}
        if letter in bk_ave_map:
            return bk_ave_map[letter]

    # 1. Check for numbered Manhattan streets: "305 East 24th Street"
    # Also handle "305 E. 24th St", "510 E. 86th St."
    # Only match if building number is plausible for Manhattan (< 800)
    m = re.search(r'(\d+)\s+(east|west|e\.?|w\.?)\s+(\d+)(?:st|nd|rd|th)?', addr_normalized, re.IGNORECASE)
    if m:
        building_num = int(m.group(1))
        street_num = int(m.group(3))
        direction = m.group(2).lower().rstrip('.')
        if direction in ('e',):
            direction = 'east'
        elif direction in ('w',):
            direction = 'west'

        if building_num < 800:
            for (side, lo, hi), zipcode in MANHATTAN_STREET_TO_ZIP.items():
                if side == direction and lo <= street_num <= hi:
                    return zipcode
            # If street number > 125, could be upper Manhattan
            if street_num > 125 and street_num <= 220:
                if direction == 'east':
                    return "10029"  # East Harlem / upper
                elif direction == 'west':
                    if street_num <= 145:
                        return "10027"  # Harlem
                    elif street_num <= 165:
                        return "10031"  # Hamilton Heights
                    elif street_num <= 190:
                        return "10032"  # Washington Heights
                    else:
                        return "10040"  # Washington Heights / Inwood

    # 2. Check Brooklyn named streets first (before generic named streets)
    for street_name, zipcode in BROOKLYN_NAMED_STREETS.items():
        if street_name in addr_normalized:
            return zipcode
        # Also try abbreviated form: "dean street" → "dean st"
        if street_name.endswith(' street'):
            short = street_name.replace(' street', ' st')
            if short in addr_normalized:
                return zipcode
        elif street_name.endswith(' avenue'):
            short = street_name.replace(' avenue', ' ave')
            if short in addr_normalized:
                return zipcode
        elif street_name.endswith(' place'):
            short = street_name.replace(' place', ' pl')
            if short in addr_normalized:
                return zipcode

    # 3. Check named streets (Manhattan avenues, etc.)
    for street_name, ranges in NAMED_STREET_TO_ZIP.items():
        # Match "123 Broadway" or "123 Park Avenue" etc.
        pattern = r'(\d+)\s+' + re.escape(street_name)
        m2 = re.search(pattern, addr_normalized, re.IGNORECASE)
        if m2:
            building_num = int(m2.group(1))
            for (lo, hi), zipcode in ranges.items():
                if lo <= building_num < hi:
                    return zipcode
            # If building number is beyond our ranges, use the last range
            if ranges:
                return list(ranges.values())[-1]

    # 3b. Try matching without building number for streets with single ZIP
    for street_name, ranges in NAMED_STREET_TO_ZIP.items():
        if len(ranges) == 1 and street_name in addr_normalized:
            return list(ranges.values())[0]

    # 4. Check for abbreviated named streets
    abbreviations = {
        "avenue": "ave", "street": "st", "boulevard": "blvd",
        "drive": "dr", "place": "pl", "road": "rd",
    }
    for full, abbr in abbreviations.items():
        for street_name, ranges in NAMED_STREET_TO_ZIP.items():
            if full in street_name:
                short_name = street_name.replace(full, abbr)
                pattern = r'(\d+)\s+' + re.escape(short_name)
                m3 = re.search(pattern, addr_normalized, re.IGNORECASE)
                if m3:
                    building_num = int(m3.group(1))
                    for (lo, hi), zipcode in ranges.items():
                        if lo <= building_num < hi:
                            return zipcode
                    if ranges:
                        return list(ranges.values())[-1]

    # 4b. Try abbreviated match without building number for single-ZIP streets
    for full, abbr in abbreviations.items():
        for street_name, ranges in NAMED_STREET_TO_ZIP.items():
            if full in street_name and len(ranges) == 1:
                short_name = street_name.replace(full, abbr)
                if short_name in addr_normalized:
                    return list(ranges.values())[0]

    # 5. Brooklyn numbered streets without direction: "394 15th Street"
    m4 = re.search(r'(\d+)\s+(\d+)(?:st|nd|rd|th)\s*(?:street|st)?', addr_normalized, re.IGNORECASE)
    if m4:
        street_num = int(m4.group(2))
        for (lo, hi), zipcode in BROOKLYN_STREET_TO_ZIP.items():
            if lo <= street_num <= hi:
                return zipcode

    # 6. Check for "North Xth Street" or "N Xth St" pattern (Williamsburg)
    m5 = re.search(r'(\d+)\s+(?:north|n\.?)\s+(\d+)(?:st|nd|rd|th)', addr_normalized, re.IGNORECASE)
    if m5:
        return "11211"  # Williamsburg

    # 7. Numbered streets without direction (could be Bronx: "301 174th St")
    m6 = re.search(r'(\d+)\s+(\d+)(?:st|nd|rd|th)\s*(?:street|st)?$', addr_normalized)
    if m6:
        street_num = int(m6.group(2))
        if 130 <= street_num <= 175:
            return "10451"  # South Bronx area
        elif 176 <= street_num <= 240:
            return "10453"  # Bronx

    # 8. East/West streets beyond our range
    m7 = re.search(r'(\d+)\s+(east|west|e\.?|w\.?)\s+(\d+)(?:st|nd|rd|th)?', addr_normalized)
    if m7:
        street_num = int(m7.group(3))
        direction = m7.group(2).lower().rstrip('.')
        if direction in ('e',):
            direction = 'east'
        elif direction in ('w',):
            direction = 'west'
        # Bronx numbered streets (above 200)
        if street_num > 220:
            return "10466" if direction == 'east' else "10471"  # Wakefield / Riverdale

    # 9. Fallback: try matching just the street name without building number
    # For addresses like "68 Bradhurst", "100 Jay", "61 Irving"
    for street_name, ranges in NAMED_STREET_TO_ZIP.items():
        # Strip common suffixes from street_name for matching
        base_name = street_name.replace(' street', '').replace(' avenue', '').replace(' place', '').replace(' boulevard', '').replace(' drive', '').replace(' road', '')
        if len(base_name) >= 4:  # Only match if base name is long enough to be unique
            # Check if the address contains this base name
            pattern = r'(\d+)\s+' + re.escape(base_name) + r'\b'
            m8 = re.search(pattern, addr_normalized)
            if m8:
                building_num = int(m8.group(1))
                for (lo, hi), zipcode in ranges.items():
                    if lo <= building_num < hi:
                        return zipcode
                if ranges:
                    return list(ranges.values())[-1]

    return None


def geocode_address(address: str) -> Optional[Dict]:
    """
    Geocode an address using Nominatim (OpenStreetMap).
    Returns dict with 'postcode', 'neighbourhood', 'suburb', 'city', 'state' or None.
    Results are cached to avoid repeated API calls.
    Rate limited to 1 request/second per Nominatim policy.
    """
    cache = _load_geocode_cache()
    cache_key = _clean_address(address)

    if cache_key in cache:
        return cache[cache_key]

    # Try multiple query strategies
    queries_to_try = []
    lower = address.lower()
    
    # Check if address already has city/state info
    has_location = any(c in lower for c in [
        'new york', ', ny', 'miami', 'florida', ', fl', ', nj', 'jersey',
        'connecticut', ', ct', 'westchester', 'brooklyn', 'queens', 'bronx',
        'staten island', 'hoboken'
    ])
    
    # Check if it looks like a Florida address (NW/SW/NE/SE + high numbers)
    is_florida_style = bool(re.search(r'\b(nw|sw|ne|se)\b', lower)) or \
                       any(s in lower for s in ['brickell', 'collins', 'biscayne', 'bayshore', 'ocean drive'])
    
    if has_location:
        queries_to_try.append(address)
    elif is_florida_style:
        queries_to_try.append(f"{address}, Miami, FL")
        queries_to_try.append(address)
    else:
        # Try NYC first (most deals are NYC), then without city
        queries_to_try.append(f"{address}, New York, NY")
        queries_to_try.append(f"{address}, Brooklyn, NY")
        queries_to_try.append(address)

    for query in queries_to_try:
        try:
            params = urllib.parse.urlencode({
                'q': query,
                'format': 'json',
                'addressdetails': 1,
                'limit': 1,
                'countrycodes': 'us'
            })
            url = f'https://nominatim.openstreetmap.org/search?{params}'
            req = urllib.request.Request(url, headers={'User-Agent': 'PreWalkthroughGenerator/1.0'})
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())

            if data and len(data) > 0:
                addr_info = data[0].get('address', {})
                state = addr_info.get('state', '')
                city = addr_info.get('city', '')
                postcode = addr_info.get('postcode', '')
                
                # Check if result is in a relevant area (NY, NJ, CT, FL)
                relevant_states = ['New York', 'New Jersey', 'Connecticut', 'Florida']
                if state in relevant_states or postcode in ZIP_TO_NEIGHBORHOOD:
                    result = {
                        'postcode': postcode,
                        'neighbourhood': addr_info.get('neighbourhood'),
                        'suburb': addr_info.get('suburb'),
                        'city': city,
                        'town': addr_info.get('town'),
                        'village': addr_info.get('village'),
                        'state': state,
                        'display_name': data[0].get('display_name', ''),
                    }
                    cache[cache_key] = result
                    _save_geocode_cache()
                    time.sleep(1.1)
                    return result

            time.sleep(1.1)  # Rate limit between queries

        except Exception as e:
            logger.warning(f"Geocoding failed for '{query}': {e}")
            time.sleep(1.1)

    # No relevant result found
    cache[cache_key] = None
    _save_geocode_cache()
    return None


def get_neighborhood_from_address(address: str, use_geocoding: bool = False) -> Optional[str]:
    """
    Determine neighborhood from a street address.
    
    Strategy:
    1. Try direct street-to-neighborhood mapping (most precise)
    2. Try local ZIP lookup → neighborhood mapping
    3. Check geocode cache for previously resolved addresses
    4. If use_geocoding=True and not cached, call Nominatim API
    """
    if not address:
        return None

    # Strategy 1: Direct street-to-neighborhood (bypasses ZIP for precision)
    hood = _neighborhood_from_street(address)
    if hood:
        return hood

    # Strategy 2: Local ZIP-based lookup
    zipcode = get_zip_from_address(address)
    if zipcode and zipcode in ZIP_TO_NEIGHBORHOOD:
        return ZIP_TO_NEIGHBORHOOD[zipcode]

    # Strategy 3: Check geocode cache
    cache = _load_geocode_cache()
    cache_key = _clean_address(address)
    if cache_key in cache:
        geo = cache[cache_key]
        if geo:
            return _neighborhood_from_geocode(geo)
        return None

    # Strategy 4: Live geocoding (only if explicitly requested)
    if use_geocoding:
        geo = geocode_address(address)
        if geo:
            return _neighborhood_from_geocode(geo)

    return None


def _neighborhood_from_street(address: str) -> Optional[str]:
    """Determine neighborhood directly from street address without going through ZIP."""
    if not address:
        return None
    
    addr = address.lower().strip()
    addr_clean = _clean_address(addr)
    
    # Check named streets first (Gramercy Park South, Irving Place, 5th Ave, etc.)
    for street_name, value in NAMED_STREET_NEIGHBORHOOD.items():
        if isinstance(value, str):
            # Simple string match
            if street_name in addr_clean:
                return value
        elif isinstance(value, dict):
            # Range-based match: need building number
            pattern = r'(\d+)\s+' + re.escape(street_name)
            m = re.search(pattern, addr_clean)
            if m:
                building_num = int(m.group(1))
                for (lo, hi), neighborhood in value.items():
                    if lo <= building_num < hi:
                        return neighborhood
                # Beyond our ranges, use last
                if value:
                    return list(value.values())[-1]
            # Also try abbreviated form
            for full, abbr in [('avenue', 'ave'), ('street', 'st')]:
                if full in street_name:
                    short = street_name.replace(full, abbr)
                    pattern = r'(\d+)\s+' + re.escape(short)
                    m = re.search(pattern, addr_clean)
                    if m:
                        building_num = int(m.group(1))
                        for (lo, hi), neighborhood in value.items():
                            if lo <= building_num < hi:
                                return neighborhood
                        if value:
                            return list(value.values())[-1]
    
    # Check numbered Manhattan streets: "305 East 24th Street"
    # Only match if building number is plausible for Manhattan (< 800)
    # Higher building numbers (e.g. 2260 East 29th) are Brooklyn/other boroughs
    m = re.search(r'(\d+)\s+(east|west|e\.?|w\.?)\s+(\d+)(?:st|nd|rd|th)?', addr_clean, re.IGNORECASE)
    if m:
        building_num = int(m.group(1))
        street_num = int(m.group(3))
        direction = m.group(2).lower().rstrip('.')
        if direction in ('e',):
            direction = 'east'
        elif direction in ('w',):
            direction = 'west'
        
        # Manhattan building numbers on numbered streets are typically < 800
        if building_num < 800:
            for (side, lo, hi), neighborhood in MANHATTAN_STREET_NEIGHBORHOOD.items():
                if side == direction and lo <= street_num <= hi:
                    return neighborhood
    
    return None


def _neighborhood_from_geocode(geo: Dict) -> Optional[str]:
    """Extract neighborhood from geocode result, with multiple fallbacks."""
    # Try postcode → neighborhood
    pc = geo.get('postcode')
    if pc and pc in ZIP_TO_NEIGHBORHOOD:
        return ZIP_TO_NEIGHBORHOOD[pc]
    # Use the neighbourhood field from geocoder
    hood = geo.get('neighbourhood')
    if hood:
        return hood
    # Use suburb as fallback
    suburb = geo.get('suburb')
    if suburb:
        return suburb
    # Use city as fallback
    city = geo.get('city')
    if city:
        return city
    # Use town as fallback (common for suburban NY/NJ/CT)
    town = geo.get('town')
    if town:
        # Clean up "Town of X" → "X"
        if town.lower().startswith('town of '):
            town = town[8:]
        if town.lower().startswith('village of '):
            town = town[11:]
        return town
    # Use village as final fallback
    village = geo.get('village')
    if village:
        return village
    return None


def enrich_deals_with_neighborhoods(deals: list, use_geocoding: bool = True) -> Tuple[int, int]:
    """
    Add 'Neighborhood' field to each deal based on Deal_Name (address).
    
    Args:
        deals: List of deal dicts (modified in place)
        use_geocoding: Whether to use Nominatim for unresolved addresses
        
    Returns:
        Tuple of (matched_count, total_count)
    """
    matched = 0
    total = len(deals)

    for i, deal in enumerate(deals):
        name = deal.get("Deal_Name", "")
        if not name:
            continue

        hood = get_neighborhood_from_address(name, use_geocoding=use_geocoding)
        if hood:
            deal["Neighborhood"] = hood
            matched += 1
        else:
            deal["Neighborhood"] = None

        if (i + 1) % 50 == 0:
            logger.info(f"Processed {i+1}/{total} deals ({matched} matched so far)")

    logger.info(f"Neighborhood enrichment complete: {matched}/{total} matched")
    return matched, total
