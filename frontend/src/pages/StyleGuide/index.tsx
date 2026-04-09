import { BannersSection } from './sections/BannersSection';
import { DropdownTableSection } from './sections/DropdownTableSection';
import { TagsSection } from './sections/TagsSection';
import { ButtonsSection } from './sections/ButtonsSection';
import { ColorsSection } from './sections/ColorsSection';
import { FormFieldsSection } from './sections/FormFieldsSection';
import { IconographySection } from './sections/IconographySection';
import { IllustrationsSection } from './sections/IllustrationsSection';
import { LogosSection } from './sections/LogosSection';
import { ShadowsSection } from './sections/ShadowsSection';
import { SpacingSection } from './sections/SpacingSection';
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
      <DropdownTableSection />
      <IllustrationsSection />
      <LogosSection />
      <IconographySection />
      <ButtonsSection />
      <FormFieldsSection />
    </div>
  );
};
