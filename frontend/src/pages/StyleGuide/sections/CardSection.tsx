import ShareIcon from '@/assets/icons/share.svg?react';
import { Button, Card } from '@/common/components';

import { SectionHeader } from '../components/SectionHeader';

export function CardSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Card</SectionHeader>

      <div className="max-w-[527px]">
        <Card className="h-[278px]">
          <div>
            <h3 className="font-semibold">Import Data</h3>
            <p className="text-p2 text-grey-500">
              Upload a new Excel file (.xlsx) to generate fresh routes.
            </p>
          </div>

          <div className="flex justify-center">
            <ShareIcon className="text-blue-300 h-10 w-10" />
          </div>

          <Button variant="primary">Import New File</Button>
        </Card>
      </div>
    </section>
  );
}
