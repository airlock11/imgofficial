IMG — Other Sports League Information Fix

Fixed a JavaScript scope bug that caused non-special-case league pages (football, baseball, tennis, hockey, cricket, volleyball, rugby, golf, boxing, motorsport, cycling, athletics, swimming and combat sports) to render blank.

The league directory data is now exposed safely to the league-detail renderer. Each league page remains isolated and uses its own league name/sport/location and source policy. No other league's teams or records are used as fallback.
