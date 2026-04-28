import { type ReactNode } from 'react';

import ChevronRight from '@/assets/icons/chevron-right.svg?react';
import { Button } from '@/common/components/Button';

import { SectionHeader } from '../components/SectionHeader';
import { SpecNote } from '../components/SpecNote';
import { SubsectionHeader } from '../components/SubsectionHeader';

export function ButtonsSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Call to Action Buttons</SectionHeader>

      {/* ---- Spec notes ---- */}
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

      {/* ---- Rectangular button grid ---- */}
      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-2 divide-y md:grid-cols-7 md:divide-x md:divide-y-0">
          {/* Primary */}
          <ButtonColumn title="Primary">
            <ButtonDemo label="Default State">
              <Button variant="primary">Save</Button>
            </ButtonDemo>
            <ButtonDemo label="Hover State">
              <Button variant="primary" className="!bg-blue-400">
                Save
              </Button>
            </ButtonDemo>
          </ButtonColumn>

          {/* Secondary */}
          <ButtonColumn title="Secondary">
            <ButtonDemo label="Default State">
              <Button variant="secondary">Cancel</Button>
            </ButtonDemo>
            <ButtonDemo label="Hover State">
              <Button variant="secondary" className="!bg-grey-300">
                Cancel
              </Button>
            </ButtonDemo>
          </ButtonColumn>

          {/* Tertiary */}
          <ButtonColumn title="Tertiary">
            <ButtonDemo label="Default State">
              <Button variant="tertiary">Cancel</Button>
            </ButtonDemo>
            <ButtonDemo label="Hover State">
              <Button variant="tertiary">Cancel</Button>
            </ButtonDemo>
          </ButtonColumn>

          {/* Text Link */}
          <ButtonColumn title="Text Link">
            <ButtonDemo label="Default State">
              <Button variant="textLink">Text</Button>
            </ButtonDemo>
            <ButtonDemo label="Hover State">
              <Button variant="textLink" className="underline">
                Text
              </Button>
            </ButtonDemo>
          </ButtonColumn>

          {/* Destructive */}
          <ButtonColumn title="Destructive">
            <ButtonDemo label="Default State">
              <Button variant="destructive">Delete</Button>
            </ButtonDemo>
            <ButtonDemo label="Hover State">
              <Button variant="destructive" className="!opacity-90">
                Delete
              </Button>
            </ButtonDemo>
          </ButtonColumn>

          {/* Ghost */}
          <ButtonColumn title="Ghost">
            <ButtonDemo label="Default State">
              <Button variant="ghost">Cancel</Button>
            </ButtonDemo>
            <ButtonDemo label="Hover State">
              <Button variant="ghost" className="!bg-grey-200">
                Cancel
              </Button>
            </ButtonDemo>
          </ButtonColumn>

          {/* Disabled */}
          <ButtonColumn title="Disabled">
            <ButtonDemo label="Disabled State">
              <Button variant="primary" disabled>
                Post
              </Button>
            </ButtonDemo>
          </ButtonColumn>
        </div>
      </div>

      {/* ---- Circular buttons ---- */}
      <SubsectionHeader>Circular Buttons</SubsectionHeader>

      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-3 divide-x">
          {/* Circular Primary */}
          <ButtonColumn title="Circular Primary">
            <ButtonDemo label="Default State">
              <Button variant="primary" shape="circular" aria-label="Next">
                <ChevronRight className="h-5 w-5" />
              </Button>
            </ButtonDemo>
            <ButtonDemo label="Hover State">
              <Button
                variant="primary"
                shape="circular"
                className="!bg-blue-400"
                aria-label="Next"
              >
                <ChevronRight className="h-5 w-5" />
              </Button>
            </ButtonDemo>
          </ButtonColumn>

          {/* Circular Secondary */}
          <ButtonColumn title="Circular Secondary">
            <ButtonDemo label="Default State">
              <Button variant="secondary" shape="circular" aria-label="Next">
                <ChevronRight className="text-grey-500 h-5 w-5" />
              </Button>
            </ButtonDemo>
            <ButtonDemo label="Hover State">
              <Button
                variant="secondary"
                shape="circular"
                className="!bg-grey-300"
                aria-label="Next"
              >
                <ChevronRight className="text-grey-500 h-5 w-5" />
              </Button>
            </ButtonDemo>
          </ButtonColumn>

          {/* Circular Tertiary */}
          <ButtonColumn title="Circular Tertiary">
            <ButtonDemo label="Default State">
              <Button variant="tertiary" shape="circular" aria-label="Next">
                <ChevronRight className="text-grey-500 h-5 w-5" />
              </Button>
            </ButtonDemo>
            <ButtonDemo label="Hover State">
              <Button variant="tertiary" shape="circular" aria-label="Next">
                <ChevronRight className="text-grey-500 h-5 w-5" />
              </Button>
            </ButtonDemo>
          </ButtonColumn>
        </div>
      </div>
    </section>
  );
}

function ButtonColumn({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="p-6">
      <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
        {title}
      </p>
      <div className="space-y-6">{children}</div>
    </div>
  );
}

function ButtonDemo({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col items-start gap-2">
      {children}
      <p className="text-p3 text-grey-400">{label}</p>
    </div>
  );
}
