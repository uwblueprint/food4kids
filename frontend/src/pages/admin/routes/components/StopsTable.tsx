import {
  closestCenter,
  DndContext,
  type DragEndEvent,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { restrictToVerticalAxis } from '@dnd-kit/modifiers';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import type {
  RouteDetailRead,
  RouteStopDetailRead,
} from '@/api/generated/types.gen';
import { useUpdateRoute } from '@/api/routes';
import { Button } from '@/common/components';
import { formatPhone, orDash } from '@/common/utils';
import { cn } from '@/lib/utils';

import { AddStopModal } from './AddStopModal';
import { StopActionsCell } from './StopActionsCell';
import { StopNotesCell } from './StopNotesCell';

interface StopsTableProps {
  route: RouteDetailRead;
}

interface SortableStopRowProps {
  stop: RouteStopDetailRead;
  /** 1-based position shown in the numbered badge. */
  position: number;
  routeId: string;
  routeName: string;
  routeGroupId: string;
  locationIds: string[];
  disabled: boolean;
  /** Just-added row: tinted background + filled badge until dismissed. */
  highlighted: boolean;
}

function SortableStopRow({
  stop,
  position,
  routeId,
  routeName,
  routeGroupId,
  locationIds,
  disabled,
  highlighted,
}: SortableStopRowProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: stop.location_id, disabled });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const cell = 'text-p2 text-grey-500 px-4 py-3 align-middle font-semibold';

  return (
    <tr
      ref={setNodeRef}
      style={style}
      className={cn(
        'group bg-white transition-colors duration-500',
        highlighted && 'bg-blue-50',
        isDragging && 'relative z-10 shadow-md'
      )}
    >
      <td className={cn(cell, 'w-8 pr-0')}>
        <button
          type="button"
          aria-label="Drag to reorder"
          className={cn(
            'text-grey-400 flex size-6 items-center justify-center transition-opacity',
            // Reveal the handle only on row hover / keyboard focus (or while
            // dragging), so it isn't a permanent fixture on every row.
            'opacity-0 group-focus-within:opacity-100 group-hover:opacity-100',
            isDragging && 'opacity-100',
            disabled ? 'cursor-not-allowed opacity-40' : 'cursor-grab'
          )}
          {...attributes}
          {...listeners}
        >
          <GripVertical className="size-4" />
        </button>
      </td>
      <td className={cn(cell, 'w-10')}>
        <span
          className={cn(
            'text-p3 mx-auto flex size-6 items-center justify-center rounded-full font-bold transition-colors duration-500',
            highlighted ? 'bg-blue-300 text-white' : 'bg-grey-200 text-grey-500'
          )}
        >
          {position}
        </span>
      </td>
      <td className={cell}>{stop.address}</td>
      <td className={cell}>{stop.contact_name}</td>
      <td className={cell}>
        {orDash(stop.phone_primary && formatPhone(stop.phone_primary))}
      </td>
      <td className={cell}>{stop.boxes}</td>
      <td className={cell}>
        <StopNotesCell noteChainId={stop.note_chain_id} />
      </td>
      <td className={cn(cell, 'w-10 text-right')}>
        <StopActionsCell
          routeId={routeId}
          routeName={routeName}
          routeGroupId={routeGroupId}
          locationIds={locationIds}
          stopLocationId={stop.location_id}
          stopAddress={stop.address}
        />
      </td>
    </tr>
  );
}

/**
 * The route's stops as an editable, reorderable table. Drag a row to reorder
 * (PATCHes the new order, which re-runs routing); the kebab moves/removes a
 * stop; "Add stop" appends one. Boxes and driver notes are read-only.
 */
export function StopsTable({ route }: StopsTableProps) {
  const serverStops = route.stops ?? [];
  // Local ordering for a snappy drag; re-synced (during render, not in an
  // effect) whenever the server order changes — e.g. after a successful PATCH
  // invalidates the detail query.
  const [stops, setStops] = useState<RouteStopDetailRead[]>(serverStops);
  const [syncedStops, setSyncedStops] = useState(route.stops);
  const [addOpen, setAddOpen] = useState(false);
  // Location id of the most recently added stop; its row/badge flash
  // highlighted for 2s after the add, then fade back to normal.
  const [addedLocationId, setAddedLocationId] = useState<string | null>(null);
  const highlightTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  const handleStopAdded = (locationId: string) => {
    setAddedLocationId(locationId);
    clearTimeout(highlightTimer.current);
    highlightTimer.current = setTimeout(() => setAddedLocationId(null), 2000);
  };

  // Cancel a pending fade if the table unmounts first.
  useEffect(() => () => clearTimeout(highlightTimer.current), []);
  const { mutate: updateRoute, isPending, isError } = useUpdateRoute();

  if (route.stops !== syncedStops) {
    setSyncedStops(route.stops);
    setStops(serverStops);
  }

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const locationIds = stops.map((s) => s.location_id);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = stops.findIndex((s) => s.location_id === active.id);
    const newIndex = stops.findIndex((s) => s.location_id === over.id);
    if (oldIndex === -1 || newIndex === -1) return;

    const reordered = arrayMove(stops, oldIndex, newIndex);
    setStops(reordered); // optimistic
    updateRoute(
      {
        path: { route_id: route.route_id },
        body: { location_ids: reordered.map((s) => s.location_id) },
      },
      // Revert to the server order on failure.
      { onError: () => setStops(route.stops ?? []) }
    );
  };

  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-h2 font-nunito-sans text-grey-500 font-bold">
          Stops
        </h2>
        <Button
          variant="primary"
          className="w-[162.25px]"
          onClick={() => setAddOpen(true)}
        >
          Add stop
        </Button>
      </div>

      {isError && (
        <p className="text-p2 text-red">
          Couldn&apos;t update the stops. This can happen if routing isn&apos;t
          configured — please try again.
        </p>
      )}

      <div className="border-grey-300 overflow-hidden rounded-2xl border bg-white px-6 py-3">
        {/* Cap the body at ~5.5 rows once there are more than 5 stops: 5 full
            rows plus a sliver of the 6th, which cues that the list scrolls.
            (~48px row + 44px sticky header ⇒ 44 + 5.5×48 = 308px.) At 5 or
            fewer stops it stays auto-height with no scrollbar. The header is
            sticky so it holds while the rows scroll under it. */}
        <div
          className={cn(
            'overflow-x-auto',
            stops.length > 5 && 'max-h-[308px] overflow-y-auto'
          )}
        >
          <table className={cn('w-full', isPending && 'opacity-60')}>
            <thead className="sticky top-0 z-20 bg-white">
              <tr className="border-grey-300 text-p1 text-grey-500 border-b text-left font-bold">
                <th className="px-4 py-2.5" />
                <th className="px-4 py-2.5 text-center">#</th>
                <th className="px-4 py-2.5">Address</th>
                <th className="px-4 py-2.5">Contact</th>
                <th className="px-4 py-2.5">Phone</th>
                <th className="px-4 py-2.5">Boxes</th>
                <th className="px-4 py-2.5">Driver Notes</th>
                <th className="px-4 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {stops.length === 0 ? (
                <tr>
                  <td
                    colSpan={8}
                    className="text-p2 text-grey-500 px-4 py-6 text-center"
                  >
                    This route has no stops.
                  </td>
                </tr>
              ) : (
                <DndContext
                  sensors={sensors}
                  collisionDetection={closestCenter}
                  modifiers={[restrictToVerticalAxis]}
                  onDragEnd={handleDragEnd}
                >
                  <SortableContext
                    items={locationIds}
                    strategy={verticalListSortingStrategy}
                  >
                    {stops.map((stop, index) => (
                      <SortableStopRow
                        key={stop.location_id}
                        stop={stop}
                        position={index + 1}
                        routeId={route.route_id}
                        routeName={route.name || 'this route'}
                        routeGroupId={route.route_group_id}
                        locationIds={locationIds}
                        disabled={isPending}
                        highlighted={stop.location_id === addedLocationId}
                      />
                    ))}
                  </SortableContext>
                </DndContext>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <AddStopModal
        open={addOpen}
        onOpenChange={setAddOpen}
        routeId={route.route_id}
        locationIds={locationIds}
        deliveryType={route.delivery_type}
        onAdded={handleStopAdded}
      />
    </section>
  );
}
