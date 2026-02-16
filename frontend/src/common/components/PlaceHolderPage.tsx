interface PlaceholderPageProps {
  pageName: string;
}

export const PlaceholderPage = ({ pageName }: PlaceholderPageProps) => {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="mb-4 text-6xl">🚧</div>
        <h1 className="mb-2 text-3xl font-bold text-gray-900">{pageName}</h1>
        <p className="text-gray-600">
          Routing works! This page is not built yet.
        </p>
      </div>
    </div>
  );
};