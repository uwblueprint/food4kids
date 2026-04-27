import MegaphoneIcon from '@/assets/icons/megaphone.svg?react';
import SearchIcon from '@/assets/icons/search.svg?react';
import { Button } from '@/common/components';
import { formatDisplayDate } from '@/common/utils';

const today = formatDisplayDate(new Date());

export const AdminHomePage = () => {
  return (
    <div className="flex flex-col gap-8">
      <div className="inline-flex items-start justify-between self-stretch">
        <div className="inline-flex flex-col items-start justify-start">
          <h1>Homepage</h1>
          <p className="text-p1 text-grey-400">{today}</p>
        </div>

        <div className="flex items-center justify-end gap-6">
          <div className="flex items-center justify-start gap-4">
            <Button variant="tertiary" shape="circular">
              <MegaphoneIcon className="size-5 text-blue-300" />
            </Button>
            <Button variant="tertiary" shape="circular">
              <SearchIcon className="size-5 text-blue-300" />
            </Button>
          </div>

          <div className="flex items-center justify-start gap-4">
            <div className="bg-brand-light-blue size-10 rounded-full" />
            <div className="inline-flex flex-col items-start justify-start">
              <h3>Admin Account</h3>
              <p className="text-p1 text-grey-400 font-light">
                emilyloro@gmail.com
              </p>
            </div>
          </div>
        </div>
      </div>
      <div>TODO</div>
    </div>
  );
};
