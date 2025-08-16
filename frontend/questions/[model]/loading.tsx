export default function Loading() {
  return (
    <div className="container mx-auto py-6">
      <div className="mb-8">
        <div className="h-8 bg-gray-200 rounded w-1/3 mb-3 animate-pulse"></div>
        <div className="h-6 bg-gray-200 rounded w-2/3 animate-pulse"></div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-2 py-4 px-1">
                <div className="h-4 bg-gray-200 rounded w-20 animate-pulse"></div>
                <div className="h-5 w-8 bg-gray-200 rounded-full animate-pulse"></div>
              </div>
            ))}
          </nav>
        </div>

        <div className="p-6">
          <div className="space-y-6">
            <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
              <div className="h-6 bg-gray-200 rounded w-1/4 mb-2 animate-pulse"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 animate-pulse"></div>
            </div>

            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-lg border border-gray-200 shadow-sm">
                <div className="px-6 py-4">
                  <div className="h-6 bg-gray-200 rounded w-3/4 mb-2 animate-pulse"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2 animate-pulse"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
