// src/app/(frontend)/questions/page.tsx
import { getPayload } from 'payload';
import config from '../../../payload.config';
import { redirect } from 'next/navigation';

export default async function Page() {
  const payload = await getPayload({ config });

  const answersDoc = await payload.find({
    collection: 'answers',
    sort: 'model_name',
    pagination: false,
    depth: 1,
  });

  if (answersDoc.docs.length === 0) {
    return (
      <div className="container mx-auto py-8">
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="text-4xl text-gray-400 mb-4">📋</div>
              <h1 className="text-xl font-semibold text-gray-900 mb-2">No Answers Found</h1>
              <p className="text-gray-600">
                There are currently no answers available in the collection.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const availableModels = Array.from(
    new Set(
      answersDoc.docs.map((answer) => answer.model_name).filter((name): name is string => !!name)
    )
  );

  const firstModel = availableModels[0];

  if (firstModel) {
    redirect(`/questions/${encodeURIComponent(firstModel)}`);
  }

  // Fallback (shouldn't be reached)
  return (
    <div className="container mx-auto py-8">
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="text-4xl text-gray-400 mb-4">📋</div>
            <h1 className="text-xl font-semibold text-gray-900 mb-2">No Models Available</h1>
            <p className="text-gray-600">No model data found in the answers collection.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
