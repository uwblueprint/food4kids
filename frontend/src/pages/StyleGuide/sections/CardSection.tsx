import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/common/components';

import { ComponentPreview } from '../components/ComponentPreview';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';
import { SectionLabel } from '../components/SectionLabel';

const CARD_CODE = `import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/common/components';

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description or content goes here.</CardDescription>
  </CardHeader>
  <CardContent>
    {/* main content */}
  </CardContent>
</Card>`;

export function CardSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Card</SectionHeader>
      <SectionDescription>
        A surface container with rounded corners and a drop shadow for grouping
        related content. Compose with{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">CardHeader</code>,{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">CardTitle</code>,{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">CardDescription</code>
        , and{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">CardContent</code>{' '}
        for structured layouts.
      </SectionDescription>

      <SectionLabel>Usage</SectionLabel>
      <ComponentPreview title="Basic Card" code={CARD_CODE}>
        <div className="w-full max-w-sm">
          <Card>
            <CardHeader>
              <CardTitle>Card Title</CardTitle>
              <CardDescription>Card description or content goes here.</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-p2 text-grey-400">Main content goes here.</p>
            </CardContent>
          </Card>
        </div>
      </ComponentPreview>
    </section>
  );
}
