// src/app/(frontend)/questions/[model]/page.tsx
import { getPayload } from 'payload';
import config from '../../../../payload.config';
import { QuestionsClient } from '../QuestionsClient';
import { notFound } from 'next/navigation';

export async function generateStaticParams() {
  const payload = await getPayload({ config });
  const answersDoc = await payload.find({
    collection: 'answers',
    pagination: false,
    select: { model_name: true },
  });

  const modelNames = Array.from(
    new Set(answersDoc.docs.map((a) => a.model_name).filter((name): name is string => !!name))
  );

  return modelNames.map((model) => ({ model: encodeURIComponent(model) }));
}

// Accept both Next 14 (object) and Next 15 (Promise) shapes
export default async function Page({ params }) {
  const payload = await getPayload({ config });

  // Works whether params is a Promise or a plain object
  const { model } = await params;
  const modelName = decodeURIComponent(model);

  // Fetch all model names first (for validation + nav)
  const allAnswersDoc = await payload.find({
    collection: 'answers',
    pagination: false,
    select: { model_name: true },
  });

  if (allAnswersDoc.docs.length === 0) {
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
    new Set(allAnswersDoc.docs.map((a) => a.model_name).filter((name): name is string => !!name))
  );

  if (!availableModels.includes(modelName)) {
    notFound();
  }

  const modelAnswersDoc = await payload.find({
    collection: 'answers',
    where: { model_name: { equals: modelName } },
    sort: 'createdAt',
    pagination: false,
    depth: 1,
  });

  return (
    <>
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-8 mb-8">
        <div className="container mx-auto">
          <h1 className="text-4xl font-bold mb-2">Questions Collection</h1>
          <p className="text-blue-100 text-lg">Annotation tool for model training and evaluation</p>
        </div>
      </div>

      <QuestionsClient
        answers={modelAnswersDoc.docs as any}
        activeModel={modelName}
        availableModels={availableModels}
      />
    </>
  );
}
