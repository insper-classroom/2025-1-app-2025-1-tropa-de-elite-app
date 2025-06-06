/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    // Increase the body size limit for file uploads
    isrMemoryCacheSize: 0,
  },
  // Configure for large file uploads
  api: {
    bodyParser: {
      sizeLimit: '100mb',
    },
    responseLimit: false,
  },
  // Configure server request size
  serverRuntimeConfig: {
    maxRequestSize: '100mb',
  },
}

module.exports = nextConfig