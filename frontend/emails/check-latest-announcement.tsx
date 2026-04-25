import { Button, Heading, Img, Section,Text } from "@react-email/components";
import * as React from "react";

import F4KEmailLayout from "./components/Layout";

export default function CheckLatestAnnouncementsEmail() {
  return (
    // REPLACE LINK HERE WITH ACTUAL URL (unless we want to Rick Roll recipients...)
    <F4KEmailLayout previewText="New Announcement">

      <Section className="px-[35px] pt-[10px] pb-[17px]">
        <Heading className="text-[32px] font-nunito font-bold text-grey-500 mb-[22px]">
          Check the latest announcement
        </Heading>
        
        <Text className="text-[16px] leading-[24px] text-grey-500 m-0 mb-[24px]">
            Hi {"[Driver Name]"},
        </Text>
        <Text className="text-[16px] text-grey-500 m-0 mb-[24px]">
            There's a new announcement from the Food4Kids team:
        </Text>

        <Section className="border-l-[4px] border-solid border-grey-300 pl-[22px] mb-[48px]">
          <Text className="text-[16px] text-grey-500 m-0">
            <strong>[ANNOUNCEMENT NAME]</strong>
          </Text>
          <Text className="text-[16px] text-grey-500 m-0">
            [ANNOUNCEMENT BODY]
          </Text>
        </Section>
        <Text className="text-[16px] text-grey-500 m-0">
            Please check the driver board to read the full update.
        </Text>

        <Section className="text-center mt-[32px] mb-[32px]">
          <Button 
          // REPLACE THIS WITH ACTUAL URL (unless we want to Rick Roll recipients...)
          href="https://www.youtube.com/watch?v=dQw4w9WgXcQ" 
          className="rounded-full border border-solid border-blue-400 bg-blue-300 px-[24px] py-[11px] font-nunito text-grey-100 text-[16px] tracking-wide"
          >
              View Announcement
          </Button>
        </Section>
      </Section>
      
    </F4KEmailLayout>
  );
}