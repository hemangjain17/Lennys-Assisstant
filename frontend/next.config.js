/** @type {import('next').NextConfig} */
const apiUrl = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_ORIGIN || process.env.BACKEND_ORIGIN || 'http://localhost:8000';

// Ensure the apiUrl starts with http:// or https:// during compilation to pass Next.js validation
const normalizedApiUrl = apiUrl.startsWith('http') ? apiUrl : `https://${apiUrl}`;

const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // Required for optimal Docker build size
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: `${normalizedApiUrl}/api/v1/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
