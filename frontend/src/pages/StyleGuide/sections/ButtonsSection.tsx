import { type ReactNode } from 'react';

import ChevronRight from '@/assets/icons/chevron-right.svg?react';
import { Button } from '@/common/components/Button';

import { ComponentPreview } from '../components/ComponentPreview';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';
import { SectionLabel } from '../components/SectionLabel';
import { SpecNote } from '../components/SpecNote';

// ---------------------------------------------------------------------------
// Code snippets
// ---------------------------------------------------------------------------

const BUTTON_PRIMARY_CODE = `import { Button } from '@/common/components';

<Button variant="primary">Save</Button>`;

const BUTTON_SECONDARY_CODE = `import { Button } from '@/common/components';

<Button variant="secondary">Cancel</Button>`;

const BUTTON_TERTIARY_CODE = `import { Button } from '@/common/components';

<Button variant="tertiary">Back</Button>`;

const BUTTON_DESTRUCTIVE_CODE = `import { Button } from '@/common/components';

<Button variant="destructive">Delete</Button>`;

const BUTTON_GHOST_CODE = `import { Button } from '@/common/components';

<Button variant="ghost">Cancel</Button>`;

const BUTTON_TEXT_LINK_CODE = `import { Button } from '@/common/components';

<Button variant="textLink">View Details</Button>`;

const BUTTON_DISABLED_CODE = `import { Button } from '@/common/components';

<Button variant="primary" disabled>Post</Button>`;

const BUTTON_CIRCULAR_CODE = `import { Button } from '@/common/components';
import ChevronRight from '@/assets/icons/chevron-right.svg?react';

<Button variant="primary" shape="circular" aria-label="Next">
  <ChevronRight className="h-5 w-5" />
</Button>`;

// ---------------------------------------------------------------------------

export function ButtonsSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Call to Action Buttons</SectionHeader>
      <SectionDescription>
        Interactive controls for triggering actions. Six variants cover the full
        range of intent — primary for the main CTA, secondary and tertiary for
        supporting actions, text link for inline navigation, destructive for
        irreversible actions, and ghost for low-emphasis controls. Icon-only
        buttons use the{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">shape="circular"</code>{' '}
        prop.
      </SectionDescription>

      {/* Spec notes */}
      <div className="mb-10 space-y-6">
        <SpecNote title="Button Height">
          Button height is 44px across desktop, tablet, and mobile.
        </SpecNote>
        <SpecNote title="Button Width">
          Width is auto based on container size, with 24px horizontal padding
          (left and right).
          <br />
          <br />
          Minimum width is 104px.
        </SpecNote>
        <SpecNote title="Mobile Button">
          On mobile, buttons span the full width of their container.
        </SpecNote>
        <SpecNote title="Border Radius">
          Border radius defaults to 40px on all corners.
        </SpecNote>
        <SpecNote title="Circular Button">
          Circular icon buttons are 44px × 44px.
        </SpecNote>
      </div>

      {/* Usage */}
      <SectionLabel>Usage</SectionLabel>
      <div className="space-y-6">
        <ComponentPreview title="Primary" code={BUTTON_PRIMARY_CODE}>
          <Button variant="primary">Save</Button>
        </ComponentPreview>

        <ComponentPreview title="Secondary" code={BUTTON_SECONDARY_CODE}>
          <Button variant="secondary">Cancel</Button>
        </ComponentPreview>

        <ComponentPreview title="Tertiary" code={BUTTON_TERTIARY_CODE}>
          <Button variant="tertiary">Back</Button>
        </ComponentPreview>

        <ComponentPreview title="Destructive" code={BUTTON_DESTRUCTIVE_CODE}>
          <Button variant="destructive">Delete</Button>
        </ComponentPreview>

        <ComponentPreview title="Ghost" code={BUTTON_GHOST_CODE}>
          <Button variant="ghost">Cancel</Button>
        </ComponentPreview>

        <ComponentPreview title="Text Link" code={BUTTON_TEXT_LINK_CODE}>
          <Button variant="textLink">View Details</Button>
        </ComponentPreview>

        <ComponentPreview title="Disabled" code={BUTTON_DISABLED_CODE}>
          <Button variant="primary" disabled>Post</Button>
        </ComponentPreview>
      </div>

      {/* States (hover reference) */}
      <SectionLabel className="mt-8">States</SectionLabel>
      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-2 divide-y md:grid-cols-7 md:divide-x md:divide-y-0">
          <ButtonColumn title="Primary">
            <ButtonDemo label="Default"><Button variant="primary">Save</Button></ButtonDemo>
            <ButtonDemo label="Hover"><Button variant="primary" className="!bg-blue-400">Save</Button></ButtonDemo>
          </ButtonColumn>
          <ButtonColumn title="Secondary">
            <ButtonDemo label="Default"><Button variant="secondary">Cancel</Button></ButtonDemo>
            <ButtonDemo label="Hover"><Button variant="secondary" className="!bg-grey-300">Cancel</Button></ButtonDemo>
          </ButtonColumn>
          <ButtonColumn title="Tertiary">
            <ButtonDemo label="Default"><Button variant="tertiary">Cancel</Button></ButtonDemo>
            <ButtonDemo label="Hover"><Button variant="tertiary">Cancel</Button></ButtonDemo>
          </ButtonColumn>
          <ButtonColumn title="Text Link">
            <ButtonDemo label="Default"><Button variant="textLink">Text</Button></ButtonDemo>
            <ButtonDemo label="Hover"><Button variant="textLink" className="underline">Text</Button></ButtonDemo>
          </ButtonColumn>
          <ButtonColumn title="Destructive">
            <ButtonDemo label="Default"><Button variant="destructive">Delete</Button></ButtonDemo>
            <ButtonDemo label="Hover"><Button variant="destructive" className="!opacity-90">Delete</Button></ButtonDemo>
          </ButtonColumn>
          <ButtonColumn title="Ghost">
            <ButtonDemo label="Default"><Button variant="ghost">Cancel</Button></ButtonDemo>
            <ButtonDemo label="Hover"><Button variant="ghost" className="!bg-grey-200">Cancel</Button></ButtonDemo>
          </ButtonColumn>
          <ButtonColumn title="Disabled">
            <ButtonDemo label="Disabled"><Button variant="primary" disabled>Post</Button></ButtonDemo>
          </ButtonColumn>
        </div>
      </div>

      {/* Circular buttons */}
      <SectionHeader className="mt-10">Circular Buttons</SectionHeader>
      <SectionDescription>
        Icon-only circular buttons for compact action triggers. Sized at 44×44px,
        they share the same variant palette as rectangular buttons.
      </SectionDescription>

      <SectionLabel>Usage</SectionLabel>
      <ComponentPreview title="Circular Button" code={BUTTON_CIRCULAR_CODE}>
        <Button variant="primary" shape="circular" aria-label="Next">
          <ChevronRight className="h-5 w-5" />
        </Button>
      </ComponentPreview>

      <SectionLabel className="mt-8">States</SectionLabel>
      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-3 divide-x">
          <ButtonColumn title="Circular Primary">
            <ButtonDemo label="Default">
              <Button variant="primary" shape="circular" aria-label="Next"><ChevronRight className="h-5 w-5" /></Button>
            </ButtonDemo>
            <ButtonDemo label="Hover">
              <Button variant="primary" shape="circular" className="!bg-blue-400" aria-label="Next"><ChevronRight className="h-5 w-5" /></Button>
            </ButtonDemo>
          </ButtonColumn>
          <ButtonColumn title="Circular Secondary">
            <ButtonDemo label="Default">
              <Button variant="secondary" shape="circular" aria-label="Next"><ChevronRight className="text-grey-500 h-5 w-5" /></Button>
            </ButtonDemo>
            <ButtonDemo label="Hover">
              <Button variant="secondary" shape="circular" className="!bg-grey-300" aria-label="Next"><ChevronRight className="text-grey-500 h-5 w-5" /></Button>
            </ButtonDemo>
          </ButtonColumn>
          <ButtonColumn title="Circular Tertiary">
            <ButtonDemo label="Default">
              <Button variant="tertiary" shape="circular" aria-label="Next"><ChevronRight className="text-grey-500 h-5 w-5" /></Button>
            </ButtonDemo>
            <ButtonDemo label="Hover">
              <Button variant="tertiary" shape="circular" aria-label="Next"><ChevronRight className="text-grey-500 h-5 w-5" /></Button>
            </ButtonDemo>
          </ButtonColumn>
        </div>
      </div>
    </section>
  );
}

function ButtonColumn({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="p-6">
      <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">{title}</p>
      <div className="space-y-6">{children}</div>
    </div>
  );
}

function ButtonDemo({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col items-start gap-2">
      {children}
      <p className="text-p3 text-grey-400">{label}</p>
    </div>
  );
}
