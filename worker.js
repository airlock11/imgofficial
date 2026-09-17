export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    const cors = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type"
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: cors });
    }

    if (url.pathname === "/games") {
      const upstream = new URL("https://api.balldontlie.io/v1/games");
      const keys = ["start_date", "end_date", "dates[]", "seasons[]", "team_ids[]", "per_page", "cursor"];

      for (const key of keys) {
        for (const value of url.searchParams.getAll(key)) {
          upstream.searchParams.append(key, value);
        }
      }

      const response = await fetch(upstream.toString(), {
        headers: {
          Authorization: env.BALLDONTLIE_API_KEY
        }
      });

      return new Response(await response.text(), {
        status: response.status,
        headers: {
          ...cors,
          "Content-Type": "application/json",
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
        ? feeds.filter(function (feed) {
            return feed[0].toLowerCase() === requestedSport;
          })
        : feeds;

      const results = await Promise.allSettled(
        selected.map(async function (feed) {
          const sport = feed[0];
          const feedUrl = feed[1];
          const response = await fetch(feedUrl, {
            headers: { "User-Agent": "IMG-Sports-Website/1.0" },
            cf: { cacheTtl: 300, cacheEverything: true }
          });

          if (!response.ok) {
            throw new Error(sport + " feed returned " + response.status);
          }

          return parseFeed(await response.text(), sport);
        })
      );

      const items = results
        .filter(function (result) {
          return result.status === "fulfilled";
        })
        .flatMap(function (result) {
          return result.value;
        })
        .sort(function (a, b) {
          return new Date(b.published || 0) - new Date(a.published || 0);
        })
        .filter(function (item, index, array) {
          return index === array.findIndex(function (other) {
            return other.link === item.link;
          });
        })
        .slice(0, 12);

      return new Response(
        JSON.stringify({
          updated_at: new Date().toISOString(),
          source: "OurSports Central RSS",
          items: items
        }),
        {
          headers: {
            ...cors,
            "Content-Type": "application/json; charset=utf-8",
            "Cache-Control": "public, max-age=300, s-maxage=300"
          }
        }
      );
    }

    return new Response("IMG sports API proxy", {
      status: 200,
      headers: cors
    });
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

    items.push({
      title: title.replace(/\s+/g, " ").trim(),
      description: stripHtml(description).replace(/\s+/g, " ").trim().slice(0, 180),
      link: link,
      published: published,
      image: extractImage(block, description),
      sport: sport,
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
  const pattern = "<" + escapedName + "\\b[^>]*\\b" + attr + "\\s*=\\s*[\\\"']([^\\\"']+)[\\\"']";
  const match = block.match(new RegExp(pattern, "i"));
  return match ? match[1] : "";
}

function firstImageUrl(value) {
  const match = String(value || "").match(/<img\b[^>]*\bsrc\s*=\s*[\"'](https:\/\/[^\"']+)[\"']/i);
  return match ? match[1] : "";
}

function tag(block, name) {
  const pattern = "<" + name + "[^>]*>([\\s\\S]*?)<\\/" + name + ">";
  const match = block.match(new RegExp(pattern, "i"));
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
    .replace(/&#(\d+);/g, function (_, n) {
      return String.fromCodePoint(Number(n));
    })
    .trim();
}

function stripHtml(value) {
  return String(value || "").replace(/<[^>]*>/g, " ");
}
