import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/common/components';

import { ComponentPreview } from '../components/ComponentPreview';
import { CompositionTree } from '../components/CompositionTree';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';
import { SectionLabel } from '../components/SectionLabel';
import { SpecNote } from '../components/SpecNote';

const COMPOSITION_TREE = `Card
├── CardHeader
│   ├── CardTitle
│   └── CardDescription
└── CardContent`;

const FULL_CODE = `import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/common/components';

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>A short description of the card's purpose.</CardDescription>
  </CardHeader>
  <CardContent>
    {/* main content */}
  </CardContent>
</Card>`;

const HEADER_ONLY_CODE = `<Card>
  <CardHeader>
    <CardTitle>Header Only</CardTitle>
    <CardDescription>Use when the card body is not yet needed.</CardDescription>
  </CardHeader>
</Card>`;

const CONTENT_ONLY_CODE = `<Card>
  <CardContent>
    {/* content without a header */}
  </CardContent>
</Card>`;

export function CardSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Card</SectionHeader>
      <SectionDescription>
        A surface container with rounded corners and a drop shadow for grouping
        related content. Compose sub-components to build structured card layouts
        — only include the pieces you need.
      </SectionDescription>

      <SectionLabel>Composition</SectionLabel>
      <div className="mb-10">
        <CompositionTree tree={COMPOSITION_TREE} />
      </div>

      <div className="mb-10 space-y-6">
        <SpecNote title="CardHeader">
          Stacks its children vertically with a small gap. Place{' '}
          <code>CardTitle</code> and <code>CardDescription</code> inside.
        </SpecNote>
        <SpecNote title="CardTitle">
          Renders as an <code>h2</code> with <code>text-grey-500</code>. Use for
          the primary label of the card.
        </SpecNote>
        <SpecNote title="CardDescription">
          Renders as a <code>p</code> with <code>text-p1 text-grey-500</code>.
          Use for supporting context below the title.
        </SpecNote>
        <SpecNote title="CardContent">
          Adds top spacing (<code>pt-4</code>) to separate it from the header.
          Takes <code>flex-1</code> to fill available height in a flex parent.
        </SpecNote>
      </div>

      <SectionLabel>Usage</SectionLabel>
      <div className="space-y-6">
        <ComponentPreview title="Full Composition" code={FULL_CODE}>
          <div className="w-full max-w-sm">
            <Card>
              <CardHeader>
                <CardTitle>Card Title</CardTitle>
                <CardDescription>
                  A short description of the card's purpose.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-grey-150 rounded-lg py-8 text-center">
                  <p className="text-p2 text-grey-400">Content area</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </ComponentPreview>

        <ComponentPreview title="Header Only" code={HEADER_ONLY_CODE}>
          <div className="w-full max-w-sm">
            <Card>
              <CardHeader>
                <CardTitle>Header Only</CardTitle>
                <CardDescription>
                  Use when the card body is not yet needed.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </ComponentPreview>

        <ComponentPreview title="Content Only" code={CONTENT_ONLY_CODE}>
          <div className="w-full max-w-sm">
            <Card>
              <CardContent>
                <div className="bg-grey-150 rounded-lg py-8 text-center">
                  <p className="text-p2 text-grey-400">Content without a header</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </ComponentPreview>
      </div>
    </section>
  );
}
