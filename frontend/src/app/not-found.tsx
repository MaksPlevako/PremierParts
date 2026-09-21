/* eslint-disable @next/next/no-html-link-for-pages -- rendered outside the app layout */
// Requests that never reach the [locale] segment (e.g. unknown file-like paths).
export default function RootNotFound() {
  return (
    <html lang="uk">
      <body style={{ fontFamily: "system-ui, sans-serif", display: "grid", placeItems: "center", minHeight: "100vh", margin: 0 }}>
        <div style={{ textAlign: "center" }}>
          <p style={{ fontSize: 56, margin: 0, color: "#B98E3A" }}>404</p>
          <p>Сторінку не знайдено</p>
          <a href="/" style={{ color: "#9C7424", fontWeight: 600 }}>
            На головну
          </a>
        </div>
      </body>
    </html>
  );
}
