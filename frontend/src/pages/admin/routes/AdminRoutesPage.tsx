import { useState } from 'react';
import { Link } from 'react-router-dom';

import ShareIcon from '@/assets/icons/share.svg?react';
import { Button } from '@/common/components';
import { cn } from '@/lib/utils';

type Tab = 'groups' | 'addresses';

export const AdminRoutesPage = () => {
  const [activeTab, setActiveTab] = useState<Tab>('groups');

  return (
    <div className="bg-grey-200 min-h-screen px-8 py-8">
      <div className="flex flex-col gap-8">
        {/* Header */}
        <h1 className="text-grey-500">Routes</h1>

        {/* Tabs */}
        <div className="flex flex-col gap-0">
          <div className="flex gap-12">
            {(['groups', 'addresses'] as Tab[]).map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                className={cn(
                  'font-nunito text-h2 pb-2 capitalize transition-colors',
                  activeTab === tab
                    ? 'text-grey-500 border-b-2 border-blue-300 font-bold'
                    : 'text-grey-400 font-normal'
                )}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
          <hr className="border-grey-300" />
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            TODO: Add search bar and filter button
          </div>
          <div className="flex items-center gap-4">
            <Button variant="primary" asChild>
              <Link to="/admin/routes/generation">Generate Routes</Link>
            </Button>
            <Button variant="primary" shape="circular">
              <ShareIcon className="size-5" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
