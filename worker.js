export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    const cors = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }

    if (url.pathname === "/scoreboard") {
      const leagueKey = (url.searchParams.get("league") || "").trim().toLowerCase();
      const paths = {
        soccer: "soccer/eng.1",
        basketball: "basketball/nba",
        wnba: "basketball/wnba",
        f1: "racing/f1",
        baseball: "baseball/mlb",
        hockey: "hockey/nhl",
        football: "football/nfl",
      };
      const path = paths[leagueKey];
      if (!path) return jsonResponse({ events: [], error: "Unsupported scoreboard league" }, cors, 30);

      try {
        const response = await fetch(`https://site.api.espn.com/apis/site/v2/sports/${path}/scoreboard`, {
          cf: { cacheTtl: 5, cacheEverything: true },
        });
        const body = await response.text();
        return new Response(body, {
          status: response.status,
          headers: {
            ...cors,
            "Content-Type": "application/json; charset=utf-8",
            "Cache-Control": "public, max-age=2",
          },
        });
      } catch (_) {
        return jsonResponse({ events: [], error: "Fallback scoreboard unavailable" }, cors, 5);
      }
    }

    if (url.pathname === "/games") {
      const upstream = new URL("https://api.balldontlie.io/v1/games");
      for (const key of [
        "start_date",
        "end_date",
        "dates[]",
        "seasons[]",
        "team_ids[]",
        "per_page",
        "cursor",
      ]) {
        for (const value of url.searchParams.getAll(key)) {
          upstream.searchParams.append(key, value);
        }
      }

      const response = await fetch(upstream.toString(), {
        headers: { Authorization: env.BALLDONTLIE_API_KEY },
      });

      const body = await response.text();
      return new Response(body, {
        status: response.status,
        headers: {
          ...cors,
          "Content-Type": "application/json; charset=utf-8",
          "Cache-Control": "public, max-age=20",
        },
      });
    }

    if (url.pathname === "/events") {
      const limit = Math.min(Math.max(Number(url.searchParams.get("limit") || 6), 1), 12);
      const days = Math.min(Math.max(Number(url.searchParams.get("days") || 7), 1), 14);
      const start = new Date();
      const end = new Date(start.getTime() + days * 86400000);
      const startKey = espnDate(start);
      const endKey = espnDate(end);

      const calendars = [
        { sport: "Basketball", league: "NBA", path: "basketball/nba" },
        { sport: "Basketball", league: "WNBA", path: "basketball/wnba" },
        { sport: "Football", league: "NFL", path: "football/nfl" },
        { sport: "Baseball", league: "MLB", path: "baseball/mlb" },
        { sport: "Hockey", league: "NHL", path: "hockey/nhl" },
        { sport: "Football", league: "Premier League", path: "soccer/eng.1" },
        { sport: "Football", league: "LaLiga", path: "soccer/esp.1" },
        { sport: "Football", league: "UEFA Champions League", path: "soccer/uefa.champions" },
        { sport: "Motorsport", league: "Formula 1", path: "racing/f1" },
        { sport: "Tennis", league: "ATP", path: "tennis/atp" },
        { sport: "Tennis", league: "WTA", path: "tennis/wta" },
        { sport: "Golf", league: "PGA Tour", path: "golf/pga" },
        { sport: "Golf", league: "LPGA", path: "golf/lpga" },
        { sport: "MMA", league: "UFC", path: "mma/ufc" },
      ];

      const results = await Promise.allSettled(calendars.map(async (cal) => {
        const endpoint = `https://site.api.espn.com/apis/site/v2/sports/${cal.path}/scoreboard?dates=${startKey}-${endKey}`;
        // ESPN can reject custom browser-style User-Agent headers. Use a plain
        // server-side GET from the Cloudflare Worker instead.
        const response = await fetch(endpoint, {
          cf: { cacheTtl: 300, cacheEverything: true },
        });
        if (!response.ok) throw new Error(`${cal.league}: HTTP ${response.status}`);
        const data = await response.json();
        return (data.events || []).map((event) => normalizeEvent(event, cal));
      }));

      const failed = results.filter(r => r.status === "rejected").length;
      const events = results
        .filter(r => r.status === "fulfilled")
        .flatMap(r => r.value)
        .filter(e => e.date && e.title)
        .filter(e => Date.parse(e.date) >= Date.now() - 30 * 60000)
        .sort((a, b) => Date.parse(a.date) - Date.parse(b.date))
        .filter((event, index, all) => index === all.findIndex(x => x.id === event.id))
        .slice(0, limit);

      return jsonResponse({
        updated_at: new Date().toISOString(),
        refresh_seconds: 900,
        window_days: days,
        source: "ESPN public scoreboard feeds",
        sources_checked: calendars.length,
        sources_failed: failed,
        items: events,
      }, cors, 300);
    }


    if (url.pathname === "/boxing/meta") {
      const base = { configured: Boolean(env.BOXING_DATA_API_KEY), divisions: boxingDivisions(), sources: boxingOfficialSources() };
      if (!env.BOXING_DATA_API_KEY) return jsonResponse(base, cors, 3600);
      const [divisionsResult, organizationsResult] = await Promise.allSettled([
        boxingApiFetch(env, "/v2/divisions/"),
        boxingApiFetch(env, "/v2/organizations/"),
      ]);
      return jsonResponse({
        ...base,
        api_divisions: divisionsResult.status === "fulfilled" ? (divisionsResult.value?.data || []) : [],
        organizations: organizationsResult.status === "fulfilled" ? (organizationsResult.value?.data || []) : [],
      }, cors, 3600);
    }

    if (url.pathname === "/boxing/rankings") {
      const page = Math.min(Math.max(Number(url.searchParams.get("page_num") || 1), 1), 17);
      if (!env.BOXING_DATA_API_KEY) return jsonResponse({ configured: false, data: [], page_num: page, sources: boxingOfficialSources() }, cors, 300);
      try {
        const data = await boxingApiFetch(env, "/v2/rankings/", { page_num: String(page) });
        return jsonResponse({ configured: true, ...data, sources: boxingOfficialSources() }, cors, 1800);
      } catch (_) {
        return jsonResponse({ configured: true, data: [], error: "Boxing rankings feed unavailable", sources: boxingOfficialSources() }, cors, 120);
      }
    }

    if (url.pathname === "/boxing/fighters") {
      if (!env.BOXING_DATA_API_KEY) return jsonResponse({ configured: false, data: [], sources: boxingOfficialSources() }, cors, 300);
      const params = {};
      for (const key of ["name", "division_id", "title_id", "page_num", "page_size"]) {
        const value = url.searchParams.get(key);
        if (value) params[key] = value;
      }
      params.page_size = String(Math.min(Math.max(Number(params.page_size || 24), 1), 50));
      params.page_num = String(Math.max(Number(params.page_num || 1), 1));
      try {
        const data = await boxingApiFetch(env, "/v2/fighters/", params);
        return jsonResponse({ configured: true, ...data }, cors, 900);
      } catch (_) {
        return jsonResponse({ configured: true, data: [], error: "Boxer directory unavailable" }, cors, 120);
      }
    }

    if (url.pathname === "/boxing/fighter") {
      const id = (url.searchParams.get("id") || "").replace(/[^a-zA-Z0-9_-]/g, "");
      if (!id || !env.BOXING_DATA_API_KEY) return jsonResponse({ configured: Boolean(env.BOXING_DATA_API_KEY), data: null }, cors, 300);
      try {
        const data = await boxingApiFetch(env, `/v2/fighters/${id}`);
        return jsonResponse({ configured: true, ...data }, cors, 1800);
      } catch (_) {
        return jsonResponse({ configured: true, data: null, error: "Boxer profile unavailable" }, cors, 120);
      }
    }

    if (url.pathname === "/boxing/fights") {
      if (!env.BOXING_DATA_API_KEY) return jsonResponse({ configured: false, data: [], sources: boxingOfficialSources() }, cors, 300);
      const params = {};
      for (const key of ["date", "data_from", "date_to", "date_sort", "division_id", "event_id", "fighter_id", "page_num", "page_size"]) {
        const value = url.searchParams.get(key);
        if (value) params[key] = value;
      }
      params.page_size = String(Math.min(Math.max(Number(params.page_size || 24), 1), 50));
      params.page_num = String(Math.max(Number(params.page_num || 1), 1));
      if (!params.date_sort) params.date_sort = "DESC";
      try {
        const data = await boxingApiFetch(env, "/v2/fights/", params);
        return jsonResponse({ configured: true, ...data }, cors, 600);
      } catch (_) {
        return jsonResponse({ configured: true, data: [], error: "Boxing fight feed unavailable" }, cors, 120);
      }
    }

    if (url.pathname === "/regional-scores") {
      const leagueKey = (url.searchParams.get("league") || "").trim().toLowerCase();
      const config = regionalLeagueConfig(leagueKey);
      if (!config) {
        return jsonResponse({ events: [], error: "Unsupported regional league" }, cors, 60);
      }
      if (!env.SPORTSAPI_KEY) {
        return jsonResponse({
          events: [],
          league: config.label,
          source: "SportsAPI not configured",
        }, cors, 30);
      }

      try {
        const response = await fetch("https://api.sportsapi.app/v2/livescores?sport=basketball", {
          headers: { Authorization: `Bearer ${env.SPORTSAPI_KEY}` },
          cf: { cacheTtl: 20, cacheEverything: true },
        });
        if (!response.ok) {
          return jsonResponse({ events: [], league: config.label, source: "SportsAPI", upstream_status: response.status }, cors, 20);
        }
        const payload = await response.json();
        const raw = Array.isArray(payload?.data) ? payload.data : [];
        const matched = raw.filter((game) => regionalGameMatches(game, config));
        const events = matched.map((game) => normalizeRegionalGame(game, config));
        return jsonResponse({
          events,
          league: config.label,
          source: "SportsAPI",
          live_only: true,
        }, cors, 20);
      } catch (_) {
        return jsonResponse({ events: [], league: config.label, source: "SportsAPI" }, cors, 20);
      }
    }

    if (url.pathname === "/streams") {
      const home = (url.searchParams.get("home") || "").trim();
      const away = (url.searchParams.get("away") || "").trim();
      const sport = (url.searchParams.get("sport") || "").trim().toLowerCase();
      const eventId = (url.searchParams.get("event") || "").trim();
      const league = streamLeagueForSport(sport);
      const query = [away, home, league?.label || "", "live"].filter(Boolean).join(" ");

      const tasks = [
        findYouTubeLive(env, { query, sport, home, away }),
        findFacebookLive(env, { home, away, sport }),
        findConfiguredStreams(env, { home, away, sport }),
      ];

      const settled = await Promise.allSettled(tasks);
      const items = settled
        .filter((r) => r.status === "fulfilled")
        .flatMap((r) => r.value || [])
        .filter(Boolean)
        .filter((item, index, all) => index === all.findIndex((x) => (x.embedUrl || x.watchUrl) === (item.embedUrl || item.watchUrl)))
        .slice(0, 8);

      return jsonResponse({
        event: eventId,
        matchup: { away, home },
        providers_checked: ["YouTube", "Facebook", "Configured official sources"],
        items,
      }, cors, 120);
    }

    if (url.pathname === "/news") {
      const feeds = [
        { region: "International", sport: "All Sports", name: "BBC Sport", url: "https://feeds.bbci.co.uk/sport/rss.xml" },
        { region: "International", sport: "All Sports", name: "ESPN", url: "https://www.espn.com/espn/rss/news" },
        { region: "International", sport: "All Sports", name: "Sky Sports", url: "https://www.skysports.com/rss/12040" },
        { region: "International", sport: "All Sports", name: "The Guardian Sport", url: "https://www.theguardian.com/uk/sport/rss" },
        { region: "International", sport: "Tennis", name: "The Guardian Tennis", url: "https://www.theguardian.com/sport/tennis/rss" },
        { region: "International", sport: "Football", name: "The Guardian Football", url: "https://www.theguardian.com/football/rss" },
        { region: "International", sport: "Rugby", name: "The Guardian Rugby", url: "https://www.theguardian.com/sport/rugby-union/rss" },
        { region: "International", sport: "Formula 1", name: "The Guardian F1", url: "https://www.theguardian.com/sport/formulaone/rss" },
        {
          region: "Philippines",
          sport: "Sports",
          name: "Inquirer Sports",
          url: "https://sports.inquirer.net/feed",
        },
        {
          region: "Philippines",
          sport: "Sports",
          name: "Philstar Sports",
          url: "https://www.philstar.com/rss/sports",
        },
        {
          region: "Philippines",
          sport: "Sports",
          name: "GMA News Sports",
          url: "https://data.gmanetwork.com/gno/rss/sports/feed.xml",
        },
        {
          region: "Philippines",
          sport: "Sports",
          name: "Tiebreaker Times",
          url: "https://tiebreakertimes.com.ph/feed",
        },
        {
          region: "International",
          sport: "Basketball",
          name: "OurSports Central",
          url: "https://www.oursportscentral.com/feeds/Basketball.xml",
        },
        {
          region: "International",
          sport: "Baseball",
          name: "OurSports Central",
          url: "https://www.oursportscentral.com/feeds/Baseball.xml",
        },
        {
          region: "International",
          sport: "Football",
          name: "OurSports Central",
          url: "https://www.oursportscentral.com/feeds/Football.xml",
        },
        {
          region: "International",
          sport: "Hockey",
          name: "OurSports Central",
          url: "https://www.oursportscentral.com/feeds/Hockey.xml",
        },
        {
          region: "International",
          sport: "Soccer",
          name: "OurSports Central",
          url: "https://www.oursportscentral.com/feeds/Soccer.xml",
        },
        {
          region: "International",
          sport: "Other Sports",
          name: "OurSports Central",
          url: "https://www.oursportscentral.com/feeds/Other.xml",
        },
      ];

      const requestedRegion = (url.searchParams.get("region") || "").toLowerCase();
      const requestedSport = (url.searchParams.get("sport") || "").toLowerCase();
      const limit = Math.min(Math.max(Number(url.searchParams.get("limit") || 12), 1), 30);

      const selected = feeds.filter((feed) => {
        const regionOK = !requestedRegion || feed.region.toLowerCase() === requestedRegion;
        const sportOK = !requestedSport || feed.sport.toLowerCase() === requestedSport;
        return regionOK && sportOK;
      });

      const results = await Promise.allSettled(
        selected.map((feed) => fetchFeed(feed))
      );

      const items = results
        .filter((result) => result.status === "fulfilled")
        .flatMap((result) => result.value)
        .filter((item) => item.title && item.link)
        .sort((a, b) => dateValue(b.published) - dateValue(a.published))
        .filter((item, index, all) => index === all.findIndex((x) => normalizeLink(x.link) === normalizeLink(item.link)));

      // Use a fresh pool, then randomize the mix so the homepage is not
      // dominated by Philippines stories or a single sport/source.
      const pool = items.slice(0, Math.min(items.length, Math.max(limit * 4, 24)));
      for (let i = pool.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [pool[i], pool[j]] = [pool[j], pool[i]];
      }
      const mixedItems = pool.slice(0, limit);

      // Only fetch article metadata for the stories that actually need an image.
      // This avoids unnecessary requests to publishers.
      const withImages = await mapWithConcurrency(mixedItems, 4, async (item) => {
        if (item.image) return item;
        const image = await articleImage(item.link);
        return image ? { ...item, image } : item;
      });

      const philippinesCount = withImages.filter((item) => item.region === "Philippines").length;
      const internationalCount = withImages.filter((item) => item.region === "International").length;

      return jsonResponse(
        {
          updated_at: new Date().toISOString(),
          refresh_seconds: 900,
          sources: selected.map(({ name, region, sport, url: feedUrl }) => ({
            name,
            region,
            sport,
            feed: feedUrl,
          })),
          counts: {
            total: withImages.length,
            philippines: philippinesCount,
            international: internationalCount,
          },
          items: withImages,
        },
        cors,
        300
      );
    }

    return new Response("IMG sports API proxy", {
      status: 200,
      headers: cors,
    });
  },
};



function boxingDivisions() {
  return [
    { page: 1, name: "Heavyweight" }, { page: 2, name: "Cruiserweight" },
    { page: 3, name: "Light Heavyweight" }, { page: 4, name: "Super Middleweight" },
    { page: 5, name: "Middleweight" }, { page: 6, name: "Super Welterweight" },
    { page: 7, name: "Welterweight" }, { page: 8, name: "Super Lightweight" },
    { page: 9, name: "Lightweight" }, { page: 10, name: "Super Featherweight" },
    { page: 11, name: "Featherweight" }, { page: 12, name: "Super Bantamweight" },
    { page: 13, name: "Bantamweight" }, { page: 14, name: "Super Flyweight" },
    { page: 15, name: "Flyweight" }, { page: 16, name: "Light Flyweight" },
    { page: 17, name: "Minimumweight" },
  ];
}

function boxingOfficialSources() {
  return [
    { body: "WBC", label: "World Boxing Council", url: "https://wbcboxing.com/en/champion-ratings/" },
    { body: "WBA", label: "World Boxing Association", url: "https://www.wbaboxing.com/wba-ranking" },
    { body: "IBF", label: "International Boxing Federation", url: "https://www.ibf-usba-boxing.com/ratings/" },
    { body: "WBO", label: "World Boxing Organization", url: "https://wboboxing.com/rankings/" },
  ];
}

async function boxingApiFetch(env, path, params = {}) {
  if (!env.BOXING_DATA_API_KEY) throw new Error("Boxing API not configured");
  const endpoint = new URL("https://boxing-data-api.p.rapidapi.com" + path);
  for (const [key, value] of Object.entries(params)) if (value != null && value !== "") endpoint.searchParams.set(key, String(value));
  const response = await fetch(endpoint.toString(), {
    headers: {
      "X-RapidAPI-Key": env.BOXING_DATA_API_KEY,
      "X-RapidAPI-Host": "boxing-data-api.p.rapidapi.com",
      Accept: "application/json",
    },
    cf: { cacheTtl: 300, cacheEverything: true },
  });
  if (!response.ok) throw new Error(`Boxing API HTTP ${response.status}`);
  return response.json();
}

function regionalLeagueConfig(key) {
  const configs = {
    pba: {
      label: "PBA",
      country: "philippines",
      aliases: ["philippine basketball association", "pba"],
      teamAliases: ["barangay ginebra", "ginebra", "blackwater", "converge fiberxers", "magnolia hotshots", "meralco bolts", "nlex road warriors", "phoenix fuel masters", "rain or shine", "san miguel beermen", "tnt tropang", "terrafirma dyip", "titan ultra", "macau black"],
    },
    mpbl: {
      label: "MPBL",
      country: "philippines",
      aliases: ["maharlika pilipinas basketball league", "mpbl"],
      teamAliases: ["imus", "sarangani marlins", "quezon huskers", "rizal golden coolers", "gensan warriors", "general santos", "bulacan kuyas", "zamboanga sikat", "batang kankaloo", "batangas city", "marikina shoemasters", "san juan knights", "pasay voyagers", "pasig city"],
    },
    nbl: {
      label: "NBL-Pilipinas",
      country: "philippines",
      aliases: ["nbl pilipinas", "nbl-pilipinas", "national basketball league philippines"],
      teamAliases: ["pampanga", "batangas", "nueva ecija", "cam sur", "camsur", "zamboanga", "quezon city", "manila", "taguig city", "pangasinan"],
    },
    nblaus: {
      label: "NBL Australia",
      country: "australia",
      aliases: ["nbl australia", "national basketball league", "nbl"],
      teamAliases: ["melbourne united", "adelaide 36ers", "perth wildcats", "south east melbourne phoenix", "new zealand breakers", "illawarra hawks", "sydney kings", "cairns taipans", "tasmania jackjumpers", "brisbane bullets"],
    },
    vba: {
      label: "VBA",
      country: "vietnam",
      aliases: ["vietnam basketball association", "vietnam professional basketball league", "vba"],
      teamAliases: ["saigon heat", "hanoi buffaloes", "nha trang dolphins", "nhatrang dolphins", "ho chi minh city wings", "danang dragons", "da nang dragons", "cantho catfish", "can tho catfish"],
    },
  };
  return configs[key] || null;
}

function lowerText(value) {
  return String(value || "").trim().toLowerCase();
}

function regionalGameMatches(game, config) {
  const leagueName = lowerText(
    game?.league?.name ||
    game?.tournament?.name ||
    game?.competition?.name ||
    game?.season?.league?.name
  );
  const countryName = lowerText(
    game?.league?.country?.name ||
    game?.league?.country ||
    game?.tournament?.country?.name ||
    game?.tournament?.country ||
    game?.country?.name ||
    game?.country
  );
  const aliasMatch = config.aliases.some((alias) => {
    const a = lowerText(alias);
    if (/^[a-z0-9]{2,5}$/.test(a)) return leagueName === a || leagueName.startsWith(a + " ") || leagueName.endsWith(" " + a) || leagueName.includes(" " + a + " ");
    return leagueName.includes(a);
  });

  // SportsAPI /v2/livescores can omit league metadata. Fall back to current
  // league team names so live games are not discarded just because league
  // details are absent from the lightweight livescore payload.
  const homeName = lowerText(game?.home?.name || game?.homeTeam?.name || game?.home?.displayName || game?.homeTeam?.displayName);
  const awayName = lowerText(game?.away?.name || game?.awayTeam?.name || game?.away?.displayName || game?.awayTeam?.displayName);
  const teamMatch = (config.teamAliases || []).some((alias) => {
    const a = lowerText(alias);
    return homeName.includes(a) || awayName.includes(a);
  });

  if (!aliasMatch && !teamMatch) return false;
  if (teamMatch) return true;
  if (!config.country) return true;
  return countryName ? countryName.includes(config.country) : leagueName.includes(config.country);
}

function regionalScoreValue(value) {
  if (value == null) return "—";
  if (typeof value === "number" || typeof value === "string") return String(value);
  if (value.current != null) return String(value.current);
  if (value.display != null) return String(value.display);
  if (value.total != null) return String(value.total);
  return "—";
}

function normalizeRegionalState(type) {
  const value = lowerText(type);
  if (/live|inprogress|in_progress|running|period|quarter|half/.test(value)) return "in";
  if (/final|finished|complete|completed|ended/.test(value)) return "post";
  return "pre";
}

function normalizeRegionalGame(game, config) {
  const home = game?.home || game?.homeTeam || {};
  const away = game?.away || game?.awayTeam || {};
  const statusType = game?.status?.type || game?.status?.name || game?.status || "";
  const shortDetail = game?.status?.description || game?.status?.detail || game?.status?.short || statusType || "Live";
  const start = game?.startTime || game?.date || game?.start || new Date().toISOString();

  return {
    id: String(game?.id || game?.fixtureId || `${config.label}-${start}-${home?.name || "home"}-${away?.name || "away"}`),
    date: start,
    status: {
      type: {
        state: normalizeRegionalState(statusType),
        shortDetail: String(shortDetail),
        description: String(shortDetail),
      },
    },
    competitions: [{
      competitors: [
        {
          homeAway: "home",
          score: regionalScoreValue(game?.homeScore),
          team: {
            displayName: home?.name || home?.displayName || "Home",
            logo: home?.logo || home?.image || "",
          },
        },
        {
          homeAway: "away",
          score: regionalScoreValue(game?.awayScore),
          team: {
            displayName: away?.name || away?.displayName || "Away",
            logo: away?.logo || away?.image || "",
          },
        },
      ],
      odds: [],
    }],
  };
}

function streamLeagueForSport(sport) {
  const map = {
    soccer: { label: "Premier League", youtube: ["UCG5qGWdu8nIRZqJ_GgDwQ-w"] },
    basketball: { label: "NBA", youtube: ["UCWJ2lWNubArHWmf3FIHbfcQ"] },
    pba: { label: "PBA Philippines", youtube: [], youtubeHandles: [] },
    mpbl: { label: "MPBL Philippines", youtube: ["UCbxiLsJzOnnpDOZSwB5HWUQ"], youtubeHandles: ["MPBLOfficial"] },
    nbl: { label: "NBL Pilipinas", youtube: [], youtubeHandles: ["nblpilipinas"] },
    nblaus: { label: "NBL Australia", youtube: [], youtubeHandles: [], youtubeSeedVideos: ["iHbZ0ocIE8E"] },
    vba: { label: "VBA Vietnam", youtube: [], youtubeHandles: ["VBAofficial"] },
    baseball: { label: "MLB", youtube: ["UCoLrcjPV5PbUrUyXq5mjc_A"] },
    hockey: { label: "NHL", youtube: ["UCqFMzb-4AUf6WAIbl132QKA"] },
    football: { label: "NFL", youtube: ["UCDVYQ4Zhbm3S2dlz7P1GBDg"] },
    f1: { label: "Formula 1", youtube: ["UCB_qr75-ydFVKSF9Dmo6izg"], youtubeHandles: ["Formula1"] },
  };
  return map[sport] || null;
}

function splitCsv(value) {
  return String(value || "").split(",").map((x) => x.trim()).filter(Boolean);
}

function safeJson(value, fallback) {
  try { return JSON.parse(value); } catch (_) { return fallback; }
}

function matchText(value, home, away) {
  const text = String(value || "").toLowerCase();
  const h = String(home || "").toLowerCase();
  const a = String(away || "").toLowerCase();
  const tokens = [h, a].filter(Boolean);
  return tokens.length ? tokens.some((t) => text.includes(t)) : true;
}

async function youtubeChannelIdsForSeedVideos(env, videoIds) {
  if (!env.YOUTUBE_API_KEY || !Array.isArray(videoIds) || !videoIds.length) return [];
  try {
    const api = new URL("https://www.googleapis.com/youtube/v3/videos");
    api.searchParams.set("part", "snippet");
    api.searchParams.set("id", videoIds.join(","));
    api.searchParams.set("key", env.YOUTUBE_API_KEY);
    const response = await fetch(api.toString(), { cf: { cacheTtl: 86400, cacheEverything: true } });
    if (!response.ok) return [];
    const data = await response.json();
    return [...new Set((data.items || []).map((item) => item?.snippet?.channelId).filter(Boolean))];
  } catch (_) {
    return [];
  }
}

async function youtubeChannelIdsForHandles(env, handles) {
  if (!env.YOUTUBE_API_KEY || !Array.isArray(handles) || !handles.length) return [];
  const results = await Promise.allSettled(handles.map(async (handle) => {
    const api = new URL("https://www.googleapis.com/youtube/v3/channels");
    api.searchParams.set("part", "id");
    api.searchParams.set("forHandle", handle.startsWith("@") ? handle : "@" + handle);
    api.searchParams.set("key", env.YOUTUBE_API_KEY);
    const response = await fetch(api.toString(), { cf: { cacheTtl: 86400, cacheEverything: true } });
    if (!response.ok) return "";
    const data = await response.json();
    return data?.items?.[0]?.id || "";
  }));
  return results.filter((r) => r.status === "fulfilled" && r.value).map((r) => r.value);
}

async function findYouTubeLive(env, game) {
  if (!env.YOUTUBE_API_KEY || !game.query) return [];
  const league = streamLeagueForSport(game.sport);
  const [handleIds, seedIds] = await Promise.all([
    youtubeChannelIdsForHandles(env, league?.youtubeHandles || []),
    youtubeChannelIdsForSeedVideos(env, league?.youtubeSeedVideos || []),
  ]);
  const builtIn = [
    ...(league?.youtube || []),
    ...handleIds,
    ...seedIds,
    "UCiWLfSweyRNmLpgEHekhoAg",
  ];
  const allowed = new Set([...builtIn, ...splitCsv(env.YOUTUBE_ALLOWED_CHANNEL_IDS)]);
  if (!allowed.size) return [];

  const api = new URL("https://www.googleapis.com/youtube/v3/search");
  api.searchParams.set("part", "snippet");
  api.searchParams.set("type", "video");
  api.searchParams.set("eventType", "live");
  api.searchParams.set("videoEmbeddable", "true");
  api.searchParams.set("safeSearch", "strict");
  api.searchParams.set("maxResults", "25");
  api.searchParams.set("q", game.query);
  api.searchParams.set("key", env.YOUTUBE_API_KEY);

  try {
    const response = await fetch(api.toString(), { cf: { cacheTtl: 120, cacheEverything: true } });
    if (!response.ok) return [];
    const data = await response.json();
    return (data.items || [])
      .filter((item) => item?.id?.videoId && allowed.has(item?.snippet?.channelId))
      .filter((item) => matchText(item?.snippet?.title, game.home, game.away))
      .map((item) => {
        const videoId = item.id.videoId;
        return {
          provider: "YouTube",
          title: item.snippet?.title || "Live stream",
          channel: item.snippet?.channelTitle || "",
          thumbnail: item.snippet?.thumbnails?.high?.url || item.snippet?.thumbnails?.medium?.url || item.snippet?.thumbnails?.default?.url || "",
          embedUrl: `https://www.youtube.com/embed/${encodeURIComponent(videoId)}?autoplay=1&mute=1&playsinline=1&rel=0`,
          watchUrl: `https://www.youtube.com/watch?v=${encodeURIComponent(videoId)}`,
          kind: "iframe",
        };
      });
  } catch (_) {
    return [];
  }
}

async function findFacebookLive(env, game) {
  const token = env.FACEBOOK_ACCESS_TOKEN;
  const builtInPages = {
    pba: ["PBAOfficial"],
    mpbl: [],
    nbl: ["nblpilipinas"],
    nblaus: [],
    vba: ["VBA.vn"],
  };
  const pages = [...(builtInPages[game.sport] || []), ...splitCsv(env.FACEBOOK_PAGE_IDS)];
  if (!token || !pages.length) return [];
  const version = env.FACEBOOK_GRAPH_VERSION || "v24.0";
  const results = await Promise.allSettled(pages.map(async (pageId) => {
    const endpoint = new URL(`https://graph.facebook.com/${version}/${encodeURIComponent(pageId)}/live_videos`);
    endpoint.searchParams.set("broadcast_status", "LIVE_NOW");
    endpoint.searchParams.set("fields", "id,title,status,permalink_url,from");
    endpoint.searchParams.set("access_token", token);
    const response = await fetch(endpoint.toString(), { cf: { cacheTtl: 120, cacheEverything: true } });
    if (!response.ok) return [];
    const data = await response.json();
    return (data.data || [])
      .filter((v) => v?.permalink_url && matchText(v.title, game.home, game.away))
      .map((v) => ({
        provider: "Facebook",
        title: v.title || "Live stream",
        channel: v.from?.name || "",
        thumbnail: "",
        embedUrl: `https://www.facebook.com/plugins/video.php?href=${encodeURIComponent(v.permalink_url)}&show_text=false&autoplay=true&mute=true`,
        watchUrl: v.permalink_url,
        kind: "iframe",
      }));
  }));
  return results.filter((r) => r.status === "fulfilled").flatMap((r) => r.value || []);
}

function findConfiguredStreams(env, game) {
  const entries = safeJson(env.STREAM_SOURCES_JSON || "[]", []);
  if (!Array.isArray(entries)) return [];
  const now = Date.now();
  return entries
    .filter((x) => !x.expiresAt || Date.parse(x.expiresAt) > now)
    .filter((x) => !x.sport || String(x.sport).toLowerCase() === game.sport)
    .filter((x) => matchText([x.title, x.home, x.away].filter(Boolean).join(" "), game.home, game.away))
    .filter((x) => x.embedUrl && /^https:\/\//i.test(x.embedUrl))
    .map((x) => ({
      provider: x.provider || "Official stream",
      title: x.title || `${game.away} vs ${game.home}`,
      channel: x.channel || "",
      thumbnail: x.thumbnail || "",
      embedUrl: x.embedUrl,
      watchUrl: x.watchUrl || x.embedUrl,
      kind: x.kind || "iframe",
    }));
}

function espnDate(date) {
  const y = date.getUTCFullYear();
  const m = String(date.getUTCMonth() + 1).padStart(2, "0");
  const d = String(date.getUTCDate()).padStart(2, "0");
  return `${y}${m}${d}`;
}

function normalizeEvent(event, calendar) {
  const competition = event.competitions?.[0] || {};
  const competitors = competition.competitors || [];
  const names = competitors.map(c => c.team?.displayName || c.team?.name || c.athlete?.displayName).filter(Boolean);
  const title = names.length >= 2 ? `${names[0]} vs ${names[1]}` : (event.name || competition.name || calendar.league);
  return {
    id: String(event.id || `${calendar.league}-${event.date}-${title}`),
    date: event.date || competition.date || "",
    title,
    league: calendar.league,
    sport: calendar.sport,
    venue: competition.venue?.fullName || "",
    status: event.status?.type?.shortDetail || event.status?.type?.detail || "Scheduled",
    link: event.links?.[0]?.href || "",
  };
}

async function fetchFeed(feed) {
  const response = await fetch(feed.url, {
    headers: {
      "User-Agent": "IMG-Sports-Website/1.0 (+https://imgofficial.com)",
      Accept: "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.1",
    },
    cf: { cacheTtl: 300, cacheEverything: true },
  });

  if (!response.ok) {
    throw new Error(`${feed.name}: HTTP ${response.status}`);
  }

  const xml = await response.text();
  return parseFeed(xml, feed);
}

function parseFeed(xml, feed) {
  const items = [];
  const blocks = [
    ...(xml.match(/<item\b[\s\S]*?<\/item>/gi) || []),
    ...(xml.match(/<entry\b[\s\S]*?<\/entry>/gi) || []),
  ];

  for (const block of blocks) {
    const title = cleanXml(firstTag(block, ["title"]));
    const link = extractLink(block);
    const description = cleanXml(firstTag(block, ["description", "summary", "content:encoded"]));
    const published = cleanXml(
      firstTag(block, ["pubDate", "published", "updated", "dc:date"])
    );

    if (!title || !link) continue;

    items.push({
      title: title.replace(/\s+/g, " ").trim(),
      description: stripHtml(description).replace(/\s+/g, " ").trim().slice(0, 220),
      link,
      published,
      image: extractImage(block, description),
      sport: feed.sport,
      source: feed.name,
      region: feed.region,
    });
  }

  return items;
}

function extractLink(block) {
  const atom = block.match(/<link\b[^>]*\bhref\s*=\s*["']([^"']+)["'][^>]*>/i);
  if (atom?.[1]) return cleanXml(atom[1]);

  const rss = firstTag(block, ["link"]);
  return cleanXml(rss);
}

function extractImage(block, description) {
  const candidates = [
    tagAttr(block, "media:content", "url"),
    tagAttr(block, "media:thumbnail", "url"),
    tagAttr(block, "media:content", "href"),
    tagAttr(block, "enclosure", "url"),
    tagAttr(block, "enclosure", "href"),
    tagAttr(block, "image", "url"),
    tagAttr(block, "media:group", "url"),
    firstImageUrl(description),
  ];

  for (const value of candidates) {
    const cleaned = cleanXml(value);
    if (isHttpsUrl(cleaned)) return cleaned;
  }
  return "";
}

async function articleImage(link) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 4000);

    const response = await fetch(link, {
      headers: {
        "User-Agent": "IMG-Sports-Website/1.0 (+https://imgofficial.com)",
        Accept: "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
      },
      signal: controller.signal,
      cf: { cacheTtl: 900, cacheEverything: true },
    });

    clearTimeout(timeout);
    if (!response.ok) return "";

    const html = (await response.text()).slice(0, 350000);
    return extractMetaImage(html);
  } catch (_) {
    return "";
  }
}

function extractMetaImage(html) {
  const patterns = [
    /<meta[^>]+(?:property|name)\s*=\s*["']og:image(?::secure_url)?["'][^>]+content\s*=\s*["']([^"']+)["']/i,
    /<meta[^>]+content\s*=\s*["']([^"']+)["'][^>]+(?:property|name)\s*=\s*["']og:image(?::secure_url)?["']/i,
    /<meta[^>]+(?:property|name)\s*=\s*["']twitter:image(?::src)?["'][^>]+content\s*=\s*["']([^"']+)["']/i,
    /<meta[^>]+content\s*=\s*["']([^"']+)["'][^>]+(?:property|name)\s*=\s*["']twitter:image(?::src)?["']/i,
  ];

  for (const pattern of patterns) {
    const match = html.match(pattern);
    const value = match ? cleanXml(match[1]) : "";
    if (isHttpsUrl(value)) return value;
  }

  return "";
}

function tagAttr(block, name, attr) {
  const escapedName = name.replace(/:/g, "\\:");
  const regex = new RegExp(
    "<" + escapedName + "\\b[^>]*\\b" + attr + "\\s*=\\s*[\\\"']([^\\\"']+)[\\\"']",
    "i"
  );
  const match = block.match(regex);
  return match ? match[1] : "";
}

function firstImageUrl(value) {
  const match = String(value || "").match(/<img\b[^>]*\bsrc\s*=\s*["'](https:\/\/[^"']+)["']/i);
  return match ? match[1] : "";
}

function firstTag(block, names) {
  for (const name of names) {
    const escapedName = name.replace(/:/g, "\\:");
    const regex = new RegExp(`<${escapedName}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${escapedName}>`, "i");
    const match = block.match(regex);
    if (match) return match[1];
  }
  return "";
}

function cleanXml(value) {
  return String(value || "")
    .replace(/^<!\[CDATA\[/i, "")
    .replace(/\]\]>$/i, "")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&#(\d+);/g, (_, n) => {
      try { return String.fromCodePoint(Number(n)); } catch (_) { return ""; }
    })
    .trim();
}

function stripHtml(value) {
  return String(value || "").replace(/<[^>]*>/g, " ");
}

function isHttpsUrl(value) {
  return /^https:\/\//i.test(String(value || ""));
}

function normalizeLink(value) {
  try {
    const u = new URL(value);
    u.hash = "";
    return u.toString().replace(/\/$/, "");
  } catch (_) {
    return String(value || "").trim();
  }
}

function dateValue(value) {
  const time = Date.parse(value || "");
  return Number.isFinite(time) ? time : 0;
}

async function mapWithConcurrency(items, concurrency, mapper) {
  const output = new Array(items.length);
  let cursor = 0;

  async function worker() {
    while (true) {
      const index = cursor++;
      if (index >= items.length) return;
      output[index] = await mapper(items[index], index);
    }
  }

  const workers = Array.from(
    { length: Math.min(concurrency, items.length) },
    () => worker()
  );
  await Promise.all(workers);
  return output;
}

function jsonResponse(data, cors, cacheSeconds) {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: {
      ...cors,
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": `public, max-age=${cacheSeconds}, s-maxage=${cacheSeconds}`,
    },
  });
}
