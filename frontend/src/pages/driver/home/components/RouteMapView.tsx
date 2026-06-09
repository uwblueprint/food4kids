import { RouteMap } from '@/common/components/RouteMap';
import { useRoute } from '@/common/hooks/useRoute';
import { cn } from '@/lib/utils';

export interface RouteMapViewProps {
  routeId: string;
  className?: string;
}

const statusWrapper =
  'flex w-full items-center justify-center rounded-2xl border border-grey-300 bg-grey-150';

export function RouteMapView({ routeId, className }: RouteMapViewProps) {
  const { data: route, isError, error } = useRoute(routeId);

  if (isError || !route) {
    return (
      <div className={cn(statusWrapper, 'text-p2 text-grey-500', className)}>
        {isError ? `Failed to load route: ${error.message}` : 'Route not found.'}
      </div>
    );
  }

  // TODO: Add loading state once design has drawn up the loading screen

  return <RouteMap encodedPolyline={route.encoded_polyline} className={className} />;
}