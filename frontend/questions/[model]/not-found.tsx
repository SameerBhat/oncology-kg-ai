import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="container mx-auto py-8">
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="text-4xl text-gray-400 mb-4">🔍</div>
            <h1 className="text-xl font-semibold text-gray-900 mb-2">Model Not Found</h1>
            <p className="text-gray-600 mb-4">
              The requested model does not exist or has no answers available.
            </p>
            <Link
              href="/questions"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              ← Back to Questions
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
