import { Button, Heading, Img, Section,Text } from "@react-email/components";
import * as React from "react";

import F4KEmailLayout from "./components/Layout";

export default function CheckLatestAnnouncementsEmail() {
  return (
    // REPLACE LINK HERE WITH ACTUAL URL (unless we want to Rick Roll recipients...)
    <F4KEmailLayout previewText="New Announcement" buttonUrl="https://www.youtube.com/watch?v=dQw4w9WgXcQ" buttonText="View Announcement">

      <Heading className="text-2xl font-nunito font-bold text-grey-500 mt-[32px] mb-[38px] text-center">
          Check the latest accouncement
      </Heading>
      
      <Text className="text-[16px] leading-[24px] text-grey-500 m-0 mb-[32px]">
          Hi {"{{Driver Name}}"},
      </Text>
      <Text className="text-[14px] text-grey-500 m-0 mb-[36px]">
          There's a new announcement posted on the driver board:
      </Text>

      <Text className="text-[14px] text-grey-500 m-0 mb-[36px]">
        <strong>[ANNOUNCEMENT NAME]</strong>
        <br/>
        [ANNOUNCEMENT BODY]
      </Text>
      <Text className="text-[14px] text-grey-500 m-0">
          Plese check the board below for more details.
      </Text>
      
    </F4KEmailLayout>
  );
}