import MegaphoneIcon from '@/assets/icons/megaphone.svg?react';
import SearchIcon from '@/assets/icons/search.svg?react';
import { Button, PageHeader } from '@/common/components';
import { formatDisplayDate } from '@/common/utils';

const today = formatDisplayDate(new Date());

export const AdminHomePage = () => {
  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Homepage"
        subtitle={today}
        actions={
          <div className="flex items-center justify-start gap-4">
            <Button variant="tertiary" shape="circular">
              <MegaphoneIcon className="size-5 text-blue-300" />
            </Button>
            <Button variant="tertiary" shape="circular">
              <SearchIcon className="size-5 text-blue-300" />
            </Button>
          </div>
        }
      />
      <div>TODO</div>
    </div>
  );
};
