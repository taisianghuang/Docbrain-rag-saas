/**
 * Next.js config with rewrites to proxy `/api/py/*` to the FastAPI backend.
 */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/py/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },
};

export default nextConfig;
