import { lazy, Suspense } from 'react';

const BannersSection = lazy(() => import('./sections/BannersSection').then((m) => ({ default: m.BannersSection })));
const ButtonsSection = lazy(() => import('./sections/ButtonsSection').then((m) => ({ default: m.ButtonsSection })));
const CalendarSection = lazy(() => import('./sections/CalendarSection').then((m) => ({ default: m.CalendarSection })));
const CardSection = lazy(() => import('./sections/CardSection').then((m) => ({ default: m.CardSection })));
const ColorsSection = lazy(() => import('./sections/ColorsSection').then((m) => ({ default: m.ColorsSection })));
const DatePickerSection = lazy(() => import('./sections/DatePickerSection').then((m) => ({ default: m.DatePickerSection })));
const DropdownSection = lazy(() => import('./sections/DropdownSection').then((m) => ({ default: m.DropdownSection })));
const FormFieldsSection = lazy(() => import('./sections/FormFieldsSection').then((m) => ({ default: m.FormFieldsSection })));
const IconographySection = lazy(() => import('./sections/IconographySection').then((m) => ({ default: m.IconographySection })));
const IllustrationsSection = lazy(() => import('./sections/IllustrationsSection').then((m) => ({ default: m.IllustrationsSection })));
const LogosSection = lazy(() => import('./sections/LogosSection').then((m) => ({ default: m.LogosSection })));
const ModalSection = lazy(() => import('./sections/ModalSection').then((m) => ({ default: m.ModalSection })));
const ProgressSection = lazy(() => import('./sections/ProgressSection').then((m) => ({ default: m.ProgressSection })));
const ShadowsSection = lazy(() => import('./sections/ShadowsSection').then((m) => ({ default: m.ShadowsSection })));
const SpacingSection = lazy(() => import('./sections/SpacingSection').then((m) => ({ default: m.SpacingSection })));
const SpinnerSection = lazy(() => import('./sections/SpinnerSection').then((m) => ({ default: m.SpinnerSection })));
const StatisticsCardSection = lazy(() => import('./sections/StatisticsCardSection').then((m) => ({ default: m.StatisticsCardSection })));
const TableSection = lazy(() => import('./sections/TableSection').then((m) => ({ default: m.TableSection })));
const TabsSection = lazy(() => import('./sections/TabsSection').then((m) => ({ default: m.TabsSection })));
const TagsSection = lazy(() => import('./sections/TagsSection').then((m) => ({ default: m.TagsSection })));
const TimePickerSection = lazy(() => import('./sections/TimePickerSection').then((m) => ({ default: m.TimePickerSection })));
const TypekitSection = lazy(() => import('./sections/TypekitSection').then((m) => ({ default: m.TypekitSection })));

export const StyleGuidePage = () => {
  return (
    <div className="page-margins min-h-screen pb-16">
      <h1 className="mb-2 text-blue-300">F4K Design System</h1>
      <p className="text-p2 text-grey-400 mb-2">
        Tailwind CSS v4 theme — typography, colors, shadows, and spacing.
      </p>

      <hr className="border-grey-300 mb-12" />

      <Suspense>
        <TypekitSection />
        <ColorsSection />
        <ShadowsSection />
        <SpacingSection />
        <BannersSection />
        <TagsSection />
        <CardSection />
        <TableSection />
        <ButtonsSection />
        <FormFieldsSection />
        <DropdownSection />
        <CalendarSection />
        <DatePickerSection />
        <TimePickerSection />
        <ModalSection />
        <SpinnerSection />
        <ProgressSection />
        <StatisticsCardSection />
        <TabsSection />
        <IllustrationsSection />
        <LogosSection />
        <IconographySection />
      </Suspense>
    </div>
  );
};
