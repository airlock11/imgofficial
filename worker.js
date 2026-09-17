export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    if (url.pathname === "/games") {
      const upstream = new URL("https://api.balldontlie.io/v1/games");
      for (const key of ["start_date", "end_date", "dates[]", "seasons[]", "team_ids[]", "per_page", "cursor"]) {
        for (const value of url.searchParams.getAll(key)) upstream.searchParams.append(key, value);
      }
      const response = await fetch(upstream.toString(), {
        headers: { Authorization: env.BALLDONTLIE_API_KEY }
      });
      const body = await response.text();
      return new Response(body, {
        status: response.status,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
          "Cache-Control": "public, max-age=20"
        }
      });
    }

    if (url.pathname === "/news") {
      const feeds = [
        ["Basketball", "https://www.oursportscentral.com/feeds/Basketball.xml"],
        ["Baseball", "https://www.oursportscentral.com/feeds/Baseball.xml"],
        ["Football", "https://www.oursportscentral.com/feeds/Football.xml"],
        ["Hockey", "https://www.oursportscentral.com/feeds/Hockey.xml"],
        ["Soccer", "https://www.oursportscentral.com/feeds/Soccer.xml"],
        ["Other Sports", "https://www.oursportscentral.com/feeds/Other.xml"]
      ];

      const requestedSport = (url.searchParams.get("sport") || "").toLowerCase();
      const selected = requestedSport
        ? feeds.filter(([sport]) => sport.toLowerCase() === requestedSport)
        : feeds;

      const results = await Promise.allSettled(selected.map(async ([sport, feedUrl]) => {
        const response = await fetch(feedUrl, {
          headers: { "User-Agent": "IMG-Sports-Website/1.0" },
          cf: { cacheTtl: 300, cacheEverything: true }
        });
        if (!response.ok) throw new Error(`${sport} feed returned ${response.status}`);
        const xml = await response.text();
        return parseFeed(xml, sport);
      }));

      const items = results
        .filter(r => r.status === "fulfilled")
        .flatMap(r => r.value)
        .sort((a, b) => new Date(b.published || 0) - new Date(a.published || 0))
        .filter((item, index, arr) => index === arr.findIndex(x => x.link === item.link))
        .slice(0, 12);

      return new Response(JSON.stringify({
        updated_at: new Date().toISOString(),
        source: "OurSports Central RSS",
        items
      }), {
        headers: {
          "Content-Type": "application/json; charset=utf-8",
          "Access-Control-Allow-Origin": "*",
          "Cache-Control": "public, max-age=300, s-maxage=300"
        }
      });
    }

    return new Response("IMG sports API proxy", { status: 200 });
  }
};

function parseFeed(xml, sport) {
  const items = [];
  const blocks = xml.match(/<item\b[\s\S]*?<\/item>/gi) || [];
  for (const block of blocks) {
    const title = cleanXml(tag(block, "title"));
    const link = cleanXml(tag(block, "link"));
    const description = cleanXml(tag(block, "description"));
    const published = cleanXml(tag(block, "pubDate")) || cleanXml(tag(block, "dc:date"));
    if (!title || !link) continue;
    const image = extractImage(block, description);
    items.push({
      title: title.replace(/\s+/g, " ").trim(),
      description: stripHtml(description).replace(/\s+/g, " ").trim().slice(0, 180),
      link,
      published,
      image,
      sport,
      source: "OurSports Central"
    });
  }
  return items;
}

function extractImage(block, description) {
  const candidates = [
    tagAttr(block, "media:content", "url"),
    tagAttr(block, "media:thumbnail", "url"),
    tagAttr(block, "enclosure", "url"),
    tagAttr(block, "image", "url"),
    tagAttr(block, "media:content", "href"),
    tagAttr(block, "enclosure", "href"),
    firstImageUrl(description)
  ];
  for (const value of candidates) {
    const cleaned = cleanXml(value);
    if (/^https:\/\//i.test(cleaned)) return cleaned;
  }
  return "";
}

function tagAttr(block, name, attr) {
  const escapedName = name.replace(/:/g, "\\:");
  const re = new RegExp("<" + escapedName + "\\b[^>]*\\b" + attr + "\\s*=\\s*[\"']([^\"']+)[\"']", "i");
  const match = block.match(re);
  return match ? match[1] : "";
}

function firstImageUrl(value) {
  const match = String(value || "").match(/<img\\b[^>]*\\bsrc\\s*=\\s*[\"'](https:\/\\/[^\"']+)[\"']/i);
  return match ? match[1] : "";
}

function tag(block, name) {
  const re = new RegExp(`<${name}[^>]*>([\\s\\S]*?)<\\/${name}>`, "i");
  const match = block.match(re);
  return match ? match[1] : "";
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
    .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
    .trim();
}

function stripHtml(value) {
  return String(value || "").replace(/<[^>]*>/g, " ");
}
