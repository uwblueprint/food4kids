import { BannersSection } from './sections/BannersSection';
import { ButtonsSection } from './sections/ButtonsSection';
import { CalendarSection } from './sections/CalendarSection';
import { CardSection } from './sections/CardSection';
import { ColorsSection } from './sections/ColorsSection';
import { DatePickerSection } from './sections/DatePickerSection';
import { ModalSection } from './sections/ModalSection';
import { FormFieldsSection } from './sections/FormFieldsSection';
import { IconographySection } from './sections/IconographySection';
import { IllustrationsSection } from './sections/IllustrationsSection';
import { LogosSection } from './sections/LogosSection';
import { ProgressSection } from './sections/ProgressSection';
import { ShadowsSection } from './sections/ShadowsSection';
import { SpacingSection } from './sections/SpacingSection';
import { SpinnerSection } from './sections/SpinnerSection';
import { StatisticsCardSection } from './sections/StatisticsCardSection';
import { TableSection } from './sections/TableSection';
import { TabsSection } from './sections/TabsSection';
import { TagsSection } from './sections/TagsSection';
import { TimePickerSection } from './sections/TimePickerSection';
import { TypekitSection } from './sections/TypekitSection';

export const StyleGuidePage = () => {
  return (
    <div className="page-margins min-h-screen pb-16">
      <h1 className="mb-2 text-blue-300">F4K Design System</h1>
      <p className="text-p2 text-grey-400 mb-2">
        Tailwind CSS v4 theme — typography, colors, shadows, and spacing.
      </p>

      <hr className="border-grey-300 mb-12" />

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
    </div>
  );
};
