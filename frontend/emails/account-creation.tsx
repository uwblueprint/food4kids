import { Button, Heading, Img, Section,Text } from "@react-email/components";
import * as React from "react";

import F4KEmailLayout from "./components/Layout";

export default function AccountCreationEmail() {
  return (
    <F4KEmailLayout previewText="Your Food4Kids Driver Account is Ready!">
      
      <Section className="px-[32px] pt-[34px] pb-[30px]">
        <Heading className="text-[32px] font-nunito font-bold text-grey-500 m-0 mb-[24px]">
          Create your driver account
        </Heading>
        <Text className="text-[16px] leading-[24px] text-grey-500 m-0 mb-[24px]">
          Hi {"[Driver Name]"},
        </Text>
        <Text className="text-[16px] text-grey-500 m-0 mb-[24px]">
            Thank you for volunteering as a driver for Food4Kids!
        </Text>
        <Text className="text-[16px] text-grey-500">
            You've been invited to create your account. Click the button below to set your password.
        </Text>
        <Section className="text-center mt-[16px] mb-[32px]">
          <Button 
            // REPLACE THIS WITH ACTUAL URL (unless we want to Rick Roll recipients...)
            href="https://www.youtube.com/watch?v=dQw4w9WgXcQ" 
            className="rounded-full border border-solid border-blue-400 bg-blue-300 px-[44px] py-[12px] font-nunito text-grey-100 text-[16px] tracking-wide"
          >
            Verify Account
          </Button>
        </Section>

        <Text className="text-[14px] text-grey-400 m-0 mb-[14px] leading-[18px]">
          This link will expire in 2 hours. If you're not an F4K Waterloo driver, please disregard this message.
        </Text>
      </Section>
      
    </F4KEmailLayout>
  );
}