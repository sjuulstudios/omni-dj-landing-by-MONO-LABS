/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  // distDir lives outside the mounted folder so cross-mount unlink is avoided in the sandbox.
  // On Sjuul's Mac (no sandbox) this just writes a /tmp/.next that npm gitignores naturally.
  distDir: process.env.OMNIDJ_DIST_DIR || '.next',
  images: {
    unoptimized: true
  },
  trailingSlash: true,
  reactStrictMode: true
};

export default nextConfig;
