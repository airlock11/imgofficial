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
        const response = await fetch(endpoint, {
          headers: { "User-Agent": "IMG-Sports-Website/1.0 (+https://imgofficial.com)" },
          cf: { cacheTtl: 300, cacheEverything: true },
        });
        if (!response.ok) throw new Error(`${cal.league}: HTTP ${response.status}`);
        const data = await response.json();
        return (data.events || []).map((event) => normalizeEvent(event, cal));
      }));

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
        items: events,
      }, cors, 300);
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
