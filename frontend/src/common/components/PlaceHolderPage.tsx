interface PlaceholderPageProps {
  pageName: string;
}

export const PlaceholderPage = ({ pageName }: PlaceholderPageProps) => {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <div className="mb-4 text-6xl">🚧</div>
        <h1 className="text-grey-500 mb-2 text-3xl font-bold">{pageName}</h1>
        <p className="text-grey-400">
          Routing works! This page is not built yet.
        </p>
      </div>
    </div>
  );
};
