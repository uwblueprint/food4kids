import { Button, Heading, Img, Section,Text } from "@react-email/components";
import * as React from "react";

import F4KEmailLayout from "./components/Layout";

export default function AccountCreationEmail() {
  return (
    <F4KEmailLayout previewText="Your Food4Kids Driver Account is Ready!">

      <Heading className="text-[32px] font-nunito font-bold text-grey-500 mt-[32px] mb-[38px] text-center">
          Create your driver account
      </Heading>
      
      <Section>
        <Text className="text-[16px] leading-[24px] text-grey-500 m-0 mb-[32px]">
          Hi {"{{Driver Name}}"},
        </Text>
        <Text className="text-[14px] text-grey-500 m-0 mb-[8px]">
            You've been invited to create your driver account.
        </Text>
        <Text className="text-[14px] text-grey-500 m-0 mb-[16px]">
            Click the button below to set your password and activate your account.
        </Text>
      </Section>

      <Section className="text-center mt-[36px] mb-[36px]">
        <Button 
          // REPLACE THIS WITH ACTUAL URL (unless we want to Rick Roll recipients...)
          href="https://www.youtube.com/watch?v=dQw4w9WgXcQ" 
          className="rounded-full border border-solid border-blue-400 bg-blue-300 px-[32px] py-[14px] font-nunito font-bold text-grey-100 text-[16px] tracking-wide"
        >
          Verify Account
        </Button>
      </Section>

      <Text className="text-[14px] text-grey-500 m-0 mb-[16px]">
        This link will expire in 2 hours. If you are not an F4K Waterloo driver, please disregard this message.
      </Text>
      
    </F4KEmailLayout>
  );
}