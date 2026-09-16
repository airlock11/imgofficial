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
        for (const value of url.searchParams.getAll(key)) {
          upstream.searchParams.append(key, value);
        }
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

    return new Response("IMG sports API proxy", { status: 200 });
  }
};
