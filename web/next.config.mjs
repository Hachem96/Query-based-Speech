const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
// Origin media (video/covers/PDFs) is served from in production -- the OSS/CDN
// custom domain, same value as the API's MEDIA_BASE_URL. Unset locally, where
// media comes from the API's /media proxy (covered by apiBase). Headers are
// computed at build time, so this is a build arg in web/Dockerfile.
const mediaBase = process.env.MEDIA_BASE_URL || "";
const mediaSources = [apiBase, mediaBase].filter(Boolean).join(" ");

// `next dev` evaluates its client bundles with eval() and hot-reloads over a
// websocket; without these the browser blocks the JS, React never hydrates,
// and no click handler (theme/language toggles included) ever runs.
const isDev = process.env.NODE_ENV !== "production";

const securityHeaders = [
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
      "font-src 'self' https://fonts.gstatic.com",
      `img-src 'self' data: https: ${mediaSources}`,
      `media-src 'self' https: ${mediaSources}`,
      // Book PDFs render in an <iframe> from the media origin; without this
      // frame-src falls back to default-src 'self' and the viewer is blocked.
      `frame-src 'self' ${mediaSources}`,
      `connect-src 'self' ${apiBase}${isDev ? " ws: wss:" : ""}`,
      "frame-ancestors 'none'",
      "base-uri 'self'",
    ].join("; "),
  },
];

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Smaller, self-contained runtime image for Docker (Dockerfile copies
  // .next/standalone instead of node_modules + full .next).
  output: "standalone",
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
