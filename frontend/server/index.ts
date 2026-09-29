import express from "express";
import { createServer } from "http";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const server = createServer(app);

  // The compiled server bundle lives at dist/index.js.
  // The React SPA build always outputs alongside it at dist/public/.
  // We resolve relative to __dirname so it works regardless of NODE_ENV.
  const staticPath = path.resolve(__dirname, "public");

  // Startup guard — surface path issues immediately in logs
  const indexHtml = path.join(staticPath, "index.html");
  if (!fs.existsSync(indexHtml)) {
    console.error(
      `[CareerBridge/ShikshaSetu] FATAL: index.html not found at ${indexHtml}. ` +
        `Run 'npm run build' first and ensure staticPath is correct.`
    );
    process.exit(1);
  }

  // Serve static assets (JS chunks, CSS, images, fonts, icons, sw.js…)
  app.use(
    express.static(staticPath, {
      // Long cache for hashed assets, no-cache for index.html & sw.js
      setHeaders(res, filePath) {
        if (
          filePath.endsWith("index.html") ||
          filePath.endsWith("sw.js")
        ) {
          res.setHeader("Cache-Control", "no-store, no-cache, must-revalidate");
        }
      },
    })
  );

  // SPA fallback — serve index.html for every route that isn't a real file.
  // This is what makes React Router / wouter work on hard refresh.
  app.get("*", (_req, res) => {
    res.sendFile(indexHtml, (err) => {
      if (err) {
        console.error("[SPA fallback] sendFile error:", err);
        res
          .status(500)
          .send("Internal server error — could not serve application.");
      }
    });
  });

  const port = parseInt(String(process.env.PORT || "3000"), 10);

  server.listen(port, "0.0.0.0", () => {
    console.log(`[ShikshaSetu] Server running on http://0.0.0.0:${port}/`);
    console.log(`[ShikshaSetu] Serving SPA from: ${staticPath}`);
  });
}

startServer().catch((err) => {
  console.error("[ShikshaSetu] Server failed to start:", err);
  process.exit(1);
});
