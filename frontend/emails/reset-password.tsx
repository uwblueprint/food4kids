import { Button, Heading, Img, Section,Text } from "@react-email/components";
import * as React from "react";

import F4KEmailLayout from "./components/Layout";

export default function ResetPasswordEmail() {
  return (
    <F4KEmailLayout previewText="Reset Your F4K Account Password!">
      
      <Section className="px-[34px] pt-[34px] pb-[20px]">
        <Heading className="text-[32px] font-nunito font-bold text-grey-500 m-0 mb-[24px]">
          Reset your password
        </Heading>
        
        <Text className="text-[16px] text-grey-500 m-0 mb-[24px]">
            Hi {"[Driver Name]"},
        </Text>
        <Text className="text-[16px] text-grey-500 leading-[24px]">
            We received a request to reset the password for your Food4Kids account. Click the button below to set a new password.
        </Text>

        <Section className="text-center mt-[33px] mb-[33px]">
          <Button 
            // REPLACE THIS WITH ACTUAL URL (unless we want to Rick Roll recipients...)
            href="https://www.youtube.com/watch?v=dQw4w9WgXcQ" 
            className="rounded-full border border-solid border-blue-400 bg-blue-300 px-[42px] py-[10px] font-nunito text-grey-100 text-[16px] tracking-wide"
          >
            Reset Password
          </Button>
        </Section>

        <Text className="text-[14px] text-grey-400 m-0 mb-[14px] leading-[18px]">
          This link will expire in 3 days. If you didn't request this, you can safely ignore this email.
        </Text>
      </Section>
      
    </F4KEmailLayout>
  );
}