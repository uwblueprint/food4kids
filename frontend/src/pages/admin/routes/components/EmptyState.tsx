import girlConfused from '@/assets/illustrations/girl-confused.png';

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      <img src={girlConfused} alt="" className="h-28 w-auto" />
      <div>
        <p className="text-p2 text-grey-500 font-medium">
          No new entries found in the spreadsheet
        </p>
        <p className="text-p3 text-grey-400">It's feeling quite empty here</p>
      </div>
    </div>
  );
}
