import { useState } from 'react';
import { Link } from 'react-router-dom';

import FilterLinesIcon from '@/assets/icons/filter-lines.svg?react';
import ShareIcon from '@/assets/icons/share.svg?react';
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  FilterChip,
  FilterChipGroup,
  SearchBar,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/common/components';

import { RouteAddressesTab, RouteGroupsTab } from './components';

// ---------------------------------------------------------------------------
// TODO: FILTER CONFIGURATIONS
// ---------------------------------------------------------------------------

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
const DELIVERY_TYPES = ['School Year', 'Summer'];
const ROUTE_STATUSES = ['Upcoming', 'Completed', 'Archived'];
const DRIVER_STATUSES = ['Assigned', 'Unassigned'];

interface FilterState {
  weekdays: Set<string>;
  deliveryTypes: Set<string>;
  routeStatuses: Set<string>;
  driverStatuses: Set<string>;
}

const emptyFilters = (): FilterState => ({
  weekdays: new Set(),
  deliveryTypes: new Set(),
  routeStatuses: new Set(),
  driverStatuses: new Set(),
});

const copyFilters = (f: FilterState): FilterState => ({
  weekdays: new Set(f.weekdays),
  deliveryTypes: new Set(f.deliveryTypes),
  routeStatuses: new Set(f.routeStatuses),
  driverStatuses: new Set(f.driverStatuses),
});

export const AdminRoutesPage = () => {
  const [search, setSearch] = useState('');
  const [filterOpen, setFilterOpen] = useState(false);

  // Committed filters (applied to the data)
  const [appliedFilters, setAppliedFilters] =
    useState<FilterState>(emptyFilters());
  // Draft filters (edited inside the dialog, only committed on Apply)
  const [draftFilters, setDraftFilters] = useState<FilterState>(emptyFilters());

  const openFilters = () => {
    setDraftFilters(copyFilters(appliedFilters));
    setFilterOpen(true);
  };

  const toggleDraft = (key: keyof FilterState, value: string) => {
    setDraftFilters((prev) => {
      const next = new Set(prev[key]);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return { ...prev, [key]: next };
    });
  };

  const handleApply = () => {
    setAppliedFilters(copyFilters(draftFilters));
    setFilterOpen(false);
    // TODO: pass appliedFilters to data fetching logic
  };

  return (
    <>
      <Tabs defaultValue="groups" className="flex flex-col gap-8">
        <h1>Routes</h1>

        <TabsList>
          <TabsTrigger value="groups">Groups</TabsTrigger>
          <TabsTrigger value="addresses">Addresses</TabsTrigger>
        </TabsList>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-5">
            <SearchBar
              placeholder="Search anything"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              wrapperClassName="w-64"
            />
            <Button
              variant="tertiary"
              shape="circular"
              className="bg-white"
              onClick={openFilters}
            >
              <FilterLinesIcon className="size-4" />
            </Button>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="primary" asChild>
              <Link to="/admin/routes/generation">Generate Routes</Link>
            </Button>
            <Button variant="primary" shape="circular">
              <ShareIcon className="size-5" />
            </Button>
          </div>
        </div>

        <TabsContent value="groups">
          <RouteGroupsTab />
        </TabsContent>
        <TabsContent value="addresses">
          <RouteAddressesTab />
        </TabsContent>
      </Tabs>

      {/* Filter dialog */}
      <Dialog open={filterOpen} onOpenChange={setFilterOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Filters</DialogTitle>
            <DialogDescription>Routes</DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4">
            <FilterChipGroup label="Weekday">
              {WEEKDAYS.map((day) => (
                <FilterChip
                  key={day}
                  selected={draftFilters.weekdays.has(day)}
                  onClick={() => toggleDraft('weekdays', day)}
                >
                  {day}
                </FilterChip>
              ))}
            </FilterChipGroup>

            <FilterChipGroup label="Delivery Type" showDelimiter>
              {DELIVERY_TYPES.map((type) => (
                <FilterChip
                  key={type}
                  selected={draftFilters.deliveryTypes.has(type)}
                  onClick={() => toggleDraft('deliveryTypes', type)}
                >
                  {type}
                </FilterChip>
              ))}
            </FilterChipGroup>

            <FilterChipGroup label="Route Status" showDelimiter>
              {ROUTE_STATUSES.map((status) => (
                <FilterChip
                  key={status}
                  selected={draftFilters.routeStatuses.has(status)}
                  onClick={() => toggleDraft('routeStatuses', status)}
                >
                  {status}
                </FilterChip>
              ))}
            </FilterChipGroup>

            <FilterChipGroup label="Driver Status" showDelimiter>
              {DRIVER_STATUSES.map((status) => (
                <FilterChip
                  key={status}
                  selected={draftFilters.driverStatuses.has(status)}
                  onClick={() => toggleDraft('driverStatuses', status)}
                >
                  {status}
                </FilterChip>
              ))}
            </FilterChipGroup>
          </div>

          <DialogFooter>
            <Button variant="primary" onClick={handleApply}>
              Apply
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};
