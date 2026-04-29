import { Card } from '@/common/components';

import { ComponentPreview } from '../components/ComponentPreview';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';
import { SectionLabel } from '../components/SectionLabel';

const CARD_CODE = `import { Card } from '@/common/components';

<Card>
  <h3 className="font-semibold">Card Title</h3>
  <p className="text-p2 text-grey-500">
    Card description or content goes here.
  </p>
</Card>`;

export function CardSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Card</SectionHeader>
      <SectionDescription>
        A surface container with rounded corners and a drop shadow for grouping
        related content. Cards accept any children and support a{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">className</code> override
        for custom sizing and layout.
      </SectionDescription>

      <SectionLabel>Usage</SectionLabel>
      <ComponentPreview title="Basic Card" code={CARD_CODE}>
        <div className="w-full max-w-sm">
          <Card>
            <h3 className="font-semibold">Card Title</h3>
            <p className="text-p2 text-grey-500">
              Card description or content goes here.
            </p>
          </Card>
        </div>
      </ComponentPreview>
    </section>
  );
}
