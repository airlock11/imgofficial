addEventListener("fetch", function(event) {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  var url = new URL(request.url);
  var cors = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type"
  };

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: cors });
  }

  if (url.pathname === "/") {
    return new Response("IMG sports API proxy", { status: 200, headers: cors });
  }

  if (url.pathname === "/scoreboard") {
    var leagueKey = (url.searchParams.get("league") || "").toLowerCase();
    var paths = {
      soccer: "soccer/eng.1",
      basketball: "basketball/nba",
      wnba: "basketball/wnba",
      baseball: "baseball/mlb",
      hockey: "hockey/nhl",
      football: "football/nfl"
    };
    var path = paths[leagueKey];

    if (!path) {
      return jsonResponse({ events: [], error: "Unsupported scoreboard league" }, cors);
    }

    try {
      var scoreboardResponse = await fetch("https://site.api.espn.com/apis/site/v2/sports/" + path + "/scoreboard", {
        cf: {
          cacheTtl: 5,
          cacheEverything: true
        }
      });
      var scoreboardBody = await scoreboardResponse.text();
      var scoreboardHeaders = {
        "Access-Control-Allow-Origin": cors["Access-Control-Allow-Origin"],
        "Access-Control-Allow-Methods": cors["Access-Control-Allow-Methods"],
        "Access-Control-Allow-Headers": cors["Access-Control-Allow-Headers"],
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "public, max-age=2"
      };
      return new Response(scoreboardBody, {
        status: scoreboardResponse.status,
        headers: scoreboardHeaders
      });
    } catch (e) {
      return jsonResponse({ events: [], error: "Fallback scoreboard unavailable" }, cors);
    }
  }

  if (url.pathname === "/boxing/meta") {
    return jsonResponse({
      configured: typeof BOXING_DATA_API_KEY !== "undefined" && !!BOXING_DATA_API_KEY,
      divisions: boxingDivisions()
    }, cors);
  }

  if (url.pathname === "/boxing/rankings") {
    if (typeof BOXING_DATA_API_KEY === "undefined" || !BOXING_DATA_API_KEY) {
      return jsonResponse({ configured: false, data: [] }, cors);
    }

    var page = url.searchParams.get("page_num") || "1";
    try {
      var rankings = await boxingFetch("/v2/rankings/", { page_num: page });
      rankings.configured = true;
      return jsonResponse(rankings, cors);
    } catch (e) {
      return jsonResponse({
        configured: true,
        data: [],
        error: String(e && e.message ? e.message : e)
      }, cors);
    }
  }

  if (url.pathname === "/boxing/fighters") {
    if (typeof BOXING_DATA_API_KEY === "undefined" || !BOXING_DATA_API_KEY) {
      return jsonResponse({ configured: false, data: [] }, cors);
    }

    var fighterParams = {};
    copyQuery(url, fighterParams, ["name", "division_id", "title_id", "page_num", "page_size"]);
    if (!fighterParams.page_num) fighterParams.page_num = "1";
    if (!fighterParams.page_size) fighterParams.page_size = "24";

    try {
      var fighters = await boxingFetch("/v2/fighters/", fighterParams);
      fighters.configured = true;
      return jsonResponse(fighters, cors);
    } catch (e) {
      return jsonResponse({
        configured: true,
        data: [],
        error: String(e && e.message ? e.message : e)
      }, cors);
    }
  }

  if (url.pathname === "/boxing/fighter") {
    if (typeof BOXING_DATA_API_KEY === "undefined" || !BOXING_DATA_API_KEY) {
      return jsonResponse({ configured: false, data: null }, cors);
    }

    var fighterId = (url.searchParams.get("id") || "").replace(/[^a-zA-Z0-9_-]/g, "");
    if (!fighterId) {
      return jsonResponse({ configured: true, data: null, error: "Missing fighter id" }, cors);
    }

    try {
      var fighter = await boxingFetch("/v2/fighters/" + fighterId, {});
      fighter.configured = true;
      return jsonResponse(fighter, cors);
    } catch (e) {
      return jsonResponse({
        configured: true,
        data: null,
        error: String(e && e.message ? e.message : e)
      }, cors);
    }
  }

  if (url.pathname === "/boxing/fights") {
    if (typeof BOXING_DATA_API_KEY === "undefined" || !BOXING_DATA_API_KEY) {
      return jsonResponse({ configured: false, data: [] }, cors);
    }

    var fightParams = {};
    copyQuery(url, fightParams, ["date", "data_from", "date_to", "date_sort", "division_id", "event_id", "fighter_id", "page_num", "page_size"]);
    if (!fightParams.page_num) fightParams.page_num = "1";
    if (!fightParams.page_size) fightParams.page_size = "24";
    if (!fightParams.date_sort) fightParams.date_sort = "DESC";

    try {
      var fights = await boxingFetch("/v2/fights/", fightParams);
      fights.configured = true;
      return jsonResponse(fights, cors);
    } catch (e) {
      return jsonResponse({
        configured: true,
        data: [],
        error: String(e && e.message ? e.message : e)
      }, cors);
    }
  }

  if (url.pathname === "/regional-scores") {
    var leagueKey = (url.searchParams.get("league") || "").toLowerCase();
    var config = regionalLeagueConfig(leagueKey);

    if (!config) {
      return jsonResponse({ events: [], error: "Unsupported regional league" }, cors);
    }

    if (typeof SPORTSAPI_KEY === "undefined" || !SPORTSAPI_KEY) {
      return jsonResponse({
        events: [],
        league: config.label,
        source: "SportsAPI not configured"
      }, cors);
    }

    try {
      var sportsResponse = await fetch("https://api.sportsapi.app/v2/livescores?sport=basketball", {
        headers: {
          "Authorization": "Bearer " + SPORTSAPI_KEY
        },
        cf: {
          cacheTtl: 20,
          cacheEverything: true
        }
      });

      if (!sportsResponse.ok) {
        return jsonResponse({
          events: [],
          league: config.label,
          source: "SportsAPI",
          upstream_status: sportsResponse.status
        }, cors);
      }

      var sportsPayload = await sportsResponse.json();
      var raw = Array.isArray(sportsPayload.data) ? sportsPayload.data : [];
      var matched = raw.filter(function(game) {
        return regionalGameMatches(game, config);
      });
      var events = matched.map(function(game) {
        return normalizeRegionalGame(game, config);
      });

      return jsonResponse({
        events: events,
        league: config.label,
        source: "SportsAPI",
        live_only: true
      }, cors);
    } catch (e) {
      return jsonResponse({
        events: [],
        league: config.label,
        source: "SportsAPI",
        error: String(e && e.message ? e.message : e)
      }, cors);
    }
  }

  return jsonResponse({ error: "Route not found", path: url.pathname }, cors);
}

function jsonResponse(data, cors) {
  var headers = {
    "Access-Control-Allow-Origin": cors["Access-Control-Allow-Origin"],
    "Access-Control-Allow-Methods": cors["Access-Control-Allow-Methods"],
    "Access-Control-Allow-Headers": cors["Access-Control-Allow-Headers"],
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store"
  };

  return new Response(JSON.stringify(data), {
    status: 200,
    headers: headers
  });
}

function boxingDivisions() {
  return [
    "Heavyweight",
    "Cruiserweight",
    "Light Heavyweight",
    "Super Middleweight",
    "Middleweight",
    "Super Welterweight",
    "Welterweight",
    "Super Lightweight",
    "Lightweight",
    "Super Featherweight",
    "Featherweight",
    "Super Bantamweight",
    "Bantamweight",
    "Super Flyweight",
    "Flyweight",
    "Light Flyweight",
    "Minimumweight"
  ];
}

async function boxingFetch(path, params) {
  var endpoint = new URL("https://boxing-data-api.p.rapidapi.com" + path);
  Object.keys(params || {}).forEach(function(key) {
    var value = params[key];
    if (value !== undefined && value !== null && value !== "") {
      endpoint.searchParams.set(key, String(value));
    }
  });

  var response = await fetch(endpoint.toString(), {
    headers: {
      "X-RapidAPI-Key": BOXING_DATA_API_KEY,
      "X-RapidAPI-Host": "boxing-data-api.p.rapidapi.com",
      "Accept": "application/json"
    }
  });

  if (!response.ok) {
    throw new Error("Boxing API HTTP " + response.status);
  }

  return await response.json();
}

function copyQuery(url, target, keys) {
  keys.forEach(function(key) {
    var value = url.searchParams.get(key);
    if (value) target[key] = value;
  });
}

function regionalLeagueConfig(key) {
  var configs = {
    pba: {
      label: "PBA",
      country: "philippines",
      aliases: ["philippine basketball association", "pba"],
      teamAliases: ["barangay ginebra", "ginebra", "blackwater", "converge fiberxers", "magnolia hotshots", "meralco bolts", "nlex road warriors", "phoenix fuel masters", "rain or shine", "san miguel beermen", "tnt tropang", "terrafirma dyip", "titan ultra", "macau black"]
    },
    mpbl: {
      label: "MPBL",
      country: "philippines",
      aliases: ["maharlika pilipinas basketball league", "mpbl"],
      teamAliases: ["imus", "sarangani marlins", "quezon huskers", "rizal golden coolers", "gensan warriors", "general santos", "bulacan kuyas", "zamboanga sikat", "batang kankaloo", "batangas city", "marikina shoemasters", "san juan knights", "pasay voyagers", "pasig city"]
    },
    nbl: {
      label: "NBL-Pilipinas",
      country: "philippines",
      aliases: ["nbl pilipinas", "nbl-pilipinas", "national basketball league philippines"],
      teamAliases: ["pampanga", "batangas", "nueva ecija", "cam sur", "camsur", "zamboanga", "quezon city", "manila", "taguig city", "pangasinan"]
    },
    nblaus: {
      label: "NBL Australia",
      country: "australia",
      aliases: ["nbl australia", "national basketball league", "nbl"],
      teamAliases: ["melbourne united", "adelaide 36ers", "perth wildcats", "south east melbourne phoenix", "new zealand breakers", "illawarra hawks", "sydney kings", "cairns taipans", "tasmania jackjumpers", "brisbane bullets"]
    },
    vba: {
      label: "VBA",
      country: "vietnam",
      aliases: ["vietnam basketball association", "vietnam professional basketball league", "vba"],
      teamAliases: ["saigon heat", "hanoi buffaloes", "nha trang dolphins", "nhatrang dolphins", "ho chi minh city wings", "danang dragons", "da nang dragons", "cantho catfish", "can tho catfish"]
    }
  };

  return configs[key] || null;
}

function textLower(value) {
  return String(value || "").trim().toLowerCase();
}

function getLeagueName(game) {
  if (game && game.league && game.league.name) return game.league.name;
  if (game && game.tournament && game.tournament.name) return game.tournament.name;
  if (game && game.competition && game.competition.name) return game.competition.name;
  return "";
}

function getCountryName(game) {
  if (game && game.league && game.league.country) {
    return game.league.country.name || game.league.country;
  }
  if (game && game.tournament && game.tournament.country) {
    return game.tournament.country.name || game.tournament.country;
  }
  if (game && game.country) {
    return game.country.name || game.country;
  }
  return "";
}

function regionalGameMatches(game, config) {
  var leagueName = textLower(getLeagueName(game));
  var countryName = textLower(getCountryName(game));
  var aliasMatch = config.aliases.some(function(alias) {
    var a = textLower(alias);
    if (/^[a-z0-9]{2,5}$/.test(a)) {
      return leagueName === a ||
        leagueName.indexOf(a + " ") === 0 ||
        leagueName.lastIndexOf(" " + a) === leagueName.length - a.length - 1 ||
        leagueName.indexOf(" " + a + " ") !== -1;
    }
    return leagueName.indexOf(a) !== -1;
  });

  var home = getTeam(game, "home");
  var away = getTeam(game, "away");
  var homeName = textLower(home.name || home.displayName);
  var awayName = textLower(away.name || away.displayName);
  var teamMatch = (config.teamAliases || []).some(function(alias) {
    var a = textLower(alias);
    return homeName.indexOf(a) !== -1 || awayName.indexOf(a) !== -1;
  });

  if (!aliasMatch && !teamMatch) return false;
  if (teamMatch) return true;
  if (!config.country) return true;
  if (countryName) return countryName.indexOf(config.country) !== -1;
  return leagueName.indexOf(config.country) !== -1;
}

function getTeam(game, side) {
  if (!game) return {};
  if (side === "home") return game.home || game.homeTeam || {};
  return game.away || game.awayTeam || {};
}

function getScore(game, side) {
  var value = side === "home" ? game.homeScore : game.awayScore;
  if (value === undefined || value === null) return "—";
  if (typeof value === "number" || typeof value === "string") return String(value);
  if (value.current !== undefined) return String(value.current);
  if (value.display !== undefined) return String(value.display);
  if (value.total !== undefined) return String(value.total);
  return "—";
}

function normalizeRegionalGame(game, config) {
  var home = getTeam(game, "home");
  var away = getTeam(game, "away");
  var status = game.status || {};
  var statusType = status.type || status.name || status;
  var statusText = status.description || status.detail || status.short || statusType || "Live";
  var stateText = textLower(statusType);
  var state = "pre";

  if (/live|inprogress|in_progress|running|period|quarter|half/.test(stateText)) state = "in";
  if (/final|finished|complete|completed|ended/.test(stateText)) state = "post";

  var start = game.startTime || game.date || game.start || new Date().toISOString();
  var homeName = home.name || home.displayName || "Home";
  var awayName = away.name || away.displayName || "Away";

  return {
    id: String(game.id || game.fixtureId || (config.label + "-" + start + "-" + homeName + "-" + awayName)),
    date: start,
    status: {
      type: {
        state: state,
        shortDetail: String(statusText),
        description: String(statusText)
      }
    },
    competitions: [{
      competitors: [{
        homeAway: "home",
        score: getScore(game, "home"),
        team: {
          displayName: homeName,
          logo: home.logo || home.image || ""
        }
      }, {
        homeAway: "away",
        score: getScore(game, "away"),
        team: {
          displayName: awayName,
          logo: away.logo || away.image || ""
        }
      }],
      odds: []
    }]
  };
}
