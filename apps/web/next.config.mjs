/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Produces a minimal, self-contained server bundle (only the files
  // actually needed at runtime) - what the Dockerfile below is built
  // around. Doesn't change local `next dev`/`next build && next start`.
  output: "standalone",
};

export default nextConfig;
