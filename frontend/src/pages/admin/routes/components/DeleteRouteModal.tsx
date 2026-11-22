import { isAxiosError } from 'axios';

import { useRouteDeletionImpact } from '@/api/route-deletion';
import { useDeleteRouteGroup } from '@/api/route-groups';
import { useDeleteRoute } from '@/api/routes';
import { ConfirmModal } from '@/common/components';
import { parseDateOnly } from '@/common/utils';

interface DeleteRouteModalProps {
  onClose: () => void;
  kind: 'route' | 'route group';
  id: string;
  name: string;
}

function countLabel(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? '' : 's'}`;
}

export function DeleteRouteModal({
  onClose,
  kind,
  id,
  name,
}: DeleteRouteModalProps) {
  const preview = useRouteDeletionImpact(kind, id);
  const route = useDeleteRoute();
  const group = useDeleteRouteGroup();
  const mutation = kind === 'route' ? route : group;
  const impact = preview.data;
  const error = mutation.error;
  const conflict = isAxiosError(error) && error.response?.status === 409;
  const detail: unknown = conflict ? error.response?.data?.detail : undefined;

  const handleDelete = () => {
    const options = { onSuccess: onClose };
    if (kind === 'route') {
      route.mutate({ path: { route_id: id } }, options);
    } else {
      group.mutate({ path: { route_group_id: id } }, options);
    }
  };

  const driveDate = impact
    ? parseDateOnly(impact.drive_date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      })
    : '';

  let description;
  if (preview.isFetching) {
    description = 'Checking what will be deleted…';
  } else if (preview.isError || !impact) {
    description = (
      <>
        Could not check what will be deleted.{' '}
        <button
          className="underline"
          type="button"
          onClick={() => void preview.refetch()}
        >
          Try again
        </button>
      </>
    );
  } else if (impact.blocked_reason) {
    description = impact.blocked_reason;
  } else {
    description = (
      <>
        This permanently deletes{' '}
        <strong>{countLabel(impact.num_routes, 'route')}</strong> and{' '}
        <strong>{countLabel(impact.num_stops, 'stop')}</strong>.
        {impact.num_drivers > 0 && (
          <>
            {' '}
            <strong>
              {countLabel(impact.num_drivers, 'assigned driver')}
            </strong>{' '}
            will lose{' '}
            {kind === 'route' ? 'this route' : 'their routes in this group'}.
          </>
        )}
        {impact.num_unrouted_locations > 0 && (
          <strong className="mt-2 block">
            {countLabel(impact.num_unrouted_locations, 'location')} will have no
            route for {driveDate}.
          </strong>
        )}
      </>
    );
  }

  return (
    <ConfirmModal
      open
      onOpenChange={(open) => {
        if (!open && !mutation.isPending) onClose();
      }}
      title={`Delete “${impact?.name ?? name}”?`}
      description={description}
      confirmLabel="Delete"
      confirmVariant="destructive"
      confirmDisabled={
        preview.isFetching ||
        preview.isError ||
        !impact ||
        !!impact.blocked_reason ||
        conflict
      }
      isLoading={mutation.isPending}
      error={
        typeof detail === 'string'
          ? detail
          : mutation.isError
            ? `Could not delete this ${kind}. Please try again.`
            : null
      }
      onConfirm={handleDelete}
    />
  );
}
