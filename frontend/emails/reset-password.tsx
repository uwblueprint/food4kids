import { Text, Button, Heading, Img, Section } from "@react-email/components";
import * as React from "react";
import F4KEmailLayout from "./components/Layout";

export default function ResetPasswordEmail() {
  return (
    <F4KEmailLayout previewText="Reset Your F4K Account Password!">

      <Heading className="text-2xl font-nunito font-bold text-grey-500 mt-[32px] mb-[38px] text-center">
          Reset your password
      </Heading>
      
      <Text className="text-[16px] leading-[24px] text-grey-500 m-0 mb-[32px]">
          Hi {"{{Driver Name}}"},
      </Text>
      <Text className="text-[14px] text-grey-500 m-0 mb-[8px]">
          We received a request to reset the password for your Food4Kids account. Click the button below to set a new password.
      </Text>

      <Section className="text-center mt-[36px] mb-[36px]">
        <Button 
          // REPLACE THIS WITH ACTUAL URL (unless we want to Rick Roll recipients...)
          href="https://www.youtube.com/watch?v=dQw4w9WgXcQ" 
          className="rounded-md bg-blue-300 px-[32px] py-[14px] font-nunito font-bold text-grey-100 text-[16px] tracking-wide"
        >
          Reset Password
        </Button>
      </Section>

      <Text className="text-[14px] text-grey-500 m-0 mb-[16px]">
        This link will expire in 3 days. If you didn't request this, you can safely ignore this email.
      </Text>
      
    </F4KEmailLayout>
  );
}