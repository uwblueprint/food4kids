import { Button, Heading, Section, Text } from "@react-email/components";
import * as React from "react";

import F4KEmailLayout from "./components/F4KEmailLayout";

export default function AccountCreationEmail() {
  return (
    <F4KEmailLayout previewText="Your Food4Kids {{ Role_To_Replace | capitalize }} Account is Ready!">
      
      <Section className="px-[32px] pt-[34px] pb-[30px]">
        <Heading className="text-[32px] font-nunito font-bold text-grey-500 m-0 mb-[24px]">
          Create your {"{{ Role_To_Replace }}"} account
        </Heading>
        <Text className="text-[16px] leading-[24px] text-grey-500 m-0 mb-[24px]">
          Hi {"{{ Name_To_Replace }}"},
        </Text>
        <Text className="text-[16px] text-grey-500 m-0 mb-[24px]">
            {"{% if Role_To_Replace is admin %}"}Welcome to the Food4Kids platform!{"{% else %}"}Thank you for volunteering as a driver for Food4Kids!{"{% endif %}"}
        </Text>
        <Text className="text-[16px] text-grey-500">
            You've been invited to create your account. Click the button below to set your password.
        </Text>
        <Section className="text-center mt-[30px] mb-[32px]">
          <Button
            href="{{ Sign_Up_URL }}"
            className="rounded-full border border-solid border-blue-400 bg-blue-300 px-[44px] py-[12px] font-nunito text-grey-100 text-[16px] tracking-wide"
          >
            Verify account
          </Button>
        </Section>

        <Text className="text-[14px] text-grey-400 m-0 mb-[4px] leading-[18px]">
          This link will expire in {"{{ Hours_Till_Expiry }}"} hours. If you're not an F4K Waterloo {"{{ Role_To_Replace }}"}, please disregard this message.
        </Text>
      </Section>
      
    </F4KEmailLayout>
  );
}
