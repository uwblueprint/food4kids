import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { useDriver, useDriverSummary } from '@/api/drivers';
import type { DriverListRead } from '@/api/generated/types.gen';
import { useNotes } from '@/api/notes';
import { useRoutes } from '@/api/routes';
import EditIcon from '@/assets/icons/edit.svg?react';
import MailIcon from '@/assets/icons/mail.svg?react';
import ClosePanelIcon from '@/assets/icons/right-panel-close.svg?react';
import TrashIcon from '@/assets/icons/trash.svg?react';
import boyIllustration from '@/assets/illustrations/boy.png';
import girlIllustration from '@/assets/illustrations/girl-catching.png';
import { Button } from '@/common/components';
import { formatPhone } from '@/common/utils';

import { DeleteDriverModal } from './DeleteDriverModal';
import { DriverNotesModal } from './DriverNotesModal';
import { EditDriverModal } from './EditDriverModal';

const DAYS = ['M', 'Tu', 'W', 'Th', 'F'];

function isoDate(date: Date) {
  return date.toISOString().slice(0, 10);
}

function currentWeek() {
  const now = new Date();
  const monday = new Date(now);
  const day = now.getDay() || 7;
  monday.setDate(now.getDate() - day + 1);
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  return { start: isoDate(monday), end: isoDate(sunday) };
}

function formatDate(value: string | null | undefined) {
  if (!value) return '—';
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatTime(value: string | null | undefined) {
  if (!value) return '—';
  const [hours = 0, minutes = 0] = value.split(':').map(Number);
  return new Date(2000, 0, 1, hours, minutes)
    .toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    })
    .replace(' ', '');
}

function ordinal(day: number) {
  if (day >= 11 && day <= 13) return `${day}th`;
  return `${day}${day % 10 === 1 ? 'st' : day % 10 === 2 ? 'nd' : day % 10 === 3 ? 'rd' : 'th'}`;
}

function formatNoteDate(value: string | null | undefined) {
  if (!value) return '';
  const date = new Date(value);
  const month = date.toLocaleDateString('en-US', { month: 'short' });
  const time = date
    .toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
    .replace(' ', '');
  return `${month} ${ordinal(date.getDate())}, ${time}`;
}

interface DriverPanelProps {
  selected: DriverListRead;
  onClose: () => void;
}

export function DriverPanel({ selected, onClose }: DriverPanelProps) {
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [notesOpen, setNotesOpen] = useState(false);
  const { data: fetched } = useDriver(selected.driver_id);
  const driver = fetched ?? selected;
  const { data: summary } = useDriverSummary(selected.driver_id);
  const week = useMemo(() => currentWeek(), []);
  const { data: assigned } = useRoutes({
    driver_id: selected.driver_id,
    start_date: week.start,
    end_date: week.end,
    order: 'asc',
    page_size: 20,
  });
  const { data: past } = useRoutes({
    driver_id: selected.driver_id,
    route_status: ['Completed'],
    order: 'desc',
    page_size: 4,
  });
  const { data: notes = [] } = useNotes(driver.note_chain_id, true);
  return (
    <aside className="border-grey-300 bg-grey-100 shadow-harsh fixed top-0 right-0 z-40 h-screen w-[430px] overflow-y-auto border-l">
      <div className="flex flex-col gap-4 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-h2 text-grey-500 font-bold">
              {driver.full_name}
            </h2>
            <p className="text-p3 text-grey-400 mt-1">
              Last Driven: {formatDate(selected.last_delivery)}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              aria-label="Delete driver"
              onClick={() => setDeleteOpen(true)}
              className="border-grey-300 text-grey-400 hover:text-red flex size-9 items-center justify-center rounded-full border"
            >
              <TrashIcon className="size-4" />
            </button>
            <button
              type="button"
              aria-label="Close driver panel"
              onClick={onClose}
              className="border-grey-300 text-grey-400 flex size-9 items-center justify-center rounded-full border"
            >
              <ClosePanelIcon className="size-4" />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="relative min-h-[92px] overflow-hidden rounded-xl bg-blue-300 p-4 text-white">
            <p className="text-h2 font-bold">
              {Math.round(
                summary?.current_year_km ?? selected.current_year_km ?? 0
              )}{' '}
              km
            </p>
            <p className="text-p3 mt-1">This Year</p>
            <img
              src={boyIllustration}
              alt=""
              className="absolute -right-4 -bottom-8 w-28"
            />
          </div>
          <div className="relative min-h-[92px] overflow-hidden rounded-xl bg-purple-400 p-4 text-white">
            <p className="text-h2 font-bold">
              {Math.round(summary?.lifetime_km ?? 0).toLocaleString()} km
            </p>
            <p className="text-p3 mt-1">Lifetime</p>
            <img
              src={girlIllustration}
              alt=""
              className="absolute -right-4 -bottom-8 w-28"
            />
          </div>
        </div>

        <section className="border-grey-200 rounded-xl border bg-white p-4">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-h3 text-grey-500 font-bold">
              Driver Information
            </h3>
            <div className="flex gap-2">
              <Button
                variant="primary"
                shape="circular"
                aria-label="Edit driver"
                className="size-8"
                onClick={() => setEditOpen(true)}
              >
                <EditIcon className="size-4" />
              </Button>
              <Button
                variant="tertiary"
                shape="circular"
                asChild
                aria-label="Email driver"
                className="size-8"
              >
                <a href={`mailto:${driver.email}`}>
                  <MailIcon className="size-4" />
                </a>
              </Button>
            </div>
          </div>
          <dl className="text-p3 text-grey-500 flex flex-col gap-3">
            <div>
              <dt className="text-grey-400">Email</dt>
              <dd>{driver.email}</dd>
            </div>
            <div>
              <dt className="text-grey-400">Phone Number</dt>
              <dd>{driver.phone ? formatPhone(driver.phone) : '—'}</dd>
            </div>
            <div>
              <dt className="text-grey-400">Address</dt>
              <dd>{driver.address || '—'}</dd>
            </div>
            <div>
              <dt className="text-grey-400">Vehicle</dt>
              <dd className="flex flex-col">
                <span>{driver.car_make_model || '—'}</span>
                {driver.license_plate && (
                  <span className="text-grey-400">{driver.license_plate}</span>
                )}
              </dd>
            </div>
          </dl>
          <div className="mt-4">
            <p className="text-p3 text-grey-400 mb-2">Availability</p>
            <div className="border-grey-200 flex justify-between rounded-lg border px-2 py-1">
              {DAYS.map((day, index) => (
                <span
                  key={day}
                  className={`flex size-8 items-center justify-center rounded-full text-xs font-semibold ${driver.availability?.[index] ? 'bg-blue-50 text-blue-300' : 'text-grey-400'}`}
                >
                  {day}
                </span>
              ))}
            </div>
          </div>
          <div className="mt-4">
            <div className="mb-2 flex items-center justify-between">
              <p className="text-p3 text-grey-400">Driver Notes</p>
              {driver.note_chain_id && (
                <button
                  type="button"
                  aria-label="Edit driver notes"
                  onClick={() => setNotesOpen(true)}
                  className="text-blue-300"
                >
                  <EditIcon className="size-4" />
                </button>
              )}
            </div>
            {notes.length ? (
              notes.slice(-3).map((note) => (
                <div
                  key={note.note_id}
                  className="border-grey-200 mb-2 rounded-lg border px-3 py-2 last:mb-0"
                >
                  <p className="text-p3 text-grey-500">{note.message}</p>
                  <p className="text-grey-400 mt-1 text-[10px]">
                    {formatNoteDate(note.created_at)}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-p3 text-grey-400">No notes</p>
            )}
          </div>
        </section>

        <section className="border-grey-200 rounded-xl border bg-white p-4">
          <h3 className="text-h3 text-grey-500 mb-3 font-bold">
            Assigned Routes
          </h3>
          {assigned?.items.length ? (
            <div className="divide-grey-200 flex flex-col divide-y">
              {assigned.items.map((route) => (
                <Link
                  key={route.route_id}
                  to={`/driver/route/${route.route_id}`}
                  className="text-p3 grid grid-cols-[1fr_auto_auto] items-start gap-3 py-2 hover:text-blue-300"
                >
                  <span>{route.name}</span>
                  <span>{formatDate(route.drive_date)}</span>
                  <span className="text-grey-400">{route.num_stops} stops</span>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-p3 text-grey-400 py-3 text-center">
              No Assigned Routes
            </p>
          )}
          {assigned?.items.length ? (
            <div className="mt-3 grid grid-cols-2 gap-3">
              <Button variant="tertiary">Edit</Button>
              <Button variant="primary">Assign</Button>
            </div>
          ) : (
            <Button variant="primary" className="mt-3 w-full">
              Assign
            </Button>
          )}
        </section>

        <section className="border-grey-200 rounded-xl border bg-white p-4">
          <h3 className="text-h3 text-grey-500 mb-3 font-bold">Past Routes</h3>
          {past?.items.length ? (
            past.items.map((route) => (
              <Link
                key={route.route_id}
                to={`/driver/route/${route.route_id}`}
                className="text-p3 grid grid-cols-[1fr_auto] gap-x-2 py-2 hover:text-blue-300"
              >
                <span className="text-blue-300 underline">{route.name}</span>
                <span>{formatTime(route.start_time)}</span>
                <span className="text-grey-400">
                  {formatDate(route.drive_date)}
                </span>
                <span className="text-grey-400 text-right">
                  {route.length.toFixed(1)} km
                </span>
              </Link>
            ))
          ) : (
            <p className="text-p3 text-grey-400">No completed routes</p>
          )}
        </section>
      </div>

      <EditDriverModal
        driver={driver}
        open={editOpen}
        onOpenChange={setEditOpen}
      />
      <DeleteDriverModal
        driver={driver}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        onDeleted={onClose}
      />
      {driver.note_chain_id && (
        <DriverNotesModal
          driverName={driver.full_name}
          noteChainId={driver.note_chain_id}
          notes={notes}
          open={notesOpen}
          onOpenChange={setNotesOpen}
        />
      )}
    </aside>
  );
}
