import {
  Body,
  Button,
  Container,
  Head,
  Hr,
  Html,
  Img,
  Link,
  Preview,
  Section,
  Text,
} from '@react-email/components';
import { pixelBasedPreset, Tailwind } from '@react-email/tailwind';
import * as React from 'react';

import { emailTailwindConfig } from '../email-tailwind-config';

interface LayoutProps {
  previewText: string;
  children: React.ReactNode;
  buttonText?: string;
  buttonUrl?: string;
  buttonSubtext?: string;
}

export default function F4KEmailLayout({
  previewText,
  children,
  buttonText,
  buttonUrl,
  buttonSubtext,
}: LayoutProps) {
  return (
    <Html>
      <Head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link 
          href="https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700;800&family=Nunito:wght@400;500;600;700;800&display=swap" 
          rel="stylesheet" 
        />
      </Head>
      <Preview>{previewText}</Preview>
      <Tailwind
        config={{
          presets: [pixelBasedPreset],
          ...emailTailwindConfig,
        }}
      >
        <Body className="bg-grey-200 font-nunito text-grey-500 m-0 p-0">
          <Container className="mx-auto my-[100px] max-w-[540px]">
            {/* Main email structure */}
            <Section className="bg-grey-100 overflow-hidden rounded-lg mb-[38px]">
              {/* Top Card: Logo Header */}
              <Section className="bg-grey-100 py-[30px] text-center">
                <Img
                  src="https://food4kidswr.ca/wp-content/uploads/2022/08/food4kids-waterloo-region.png"
                  alt="Food4Kids Waterloo Region"
                  width="276"
                  className="mx-auto"
                />
              </Section>

              <Hr className="border-grey-200 m-0 w-full border-solid" />

              {/* Bottom Card: Main Content Area */}
              <Section>
                {children}

                {/* Dynamic button */}
                {buttonText && buttonUrl && (
                  <Section className="mt-[32px] text-center">
                    <Button
                      href={buttonUrl}
                      className="font-nunito text-grey-100 rounded-md bg-blue-300 px-[32px] py-[14px] text-[16px] font-bold tracking-wide"
                    >
                      {buttonText}
                    </Button>
                  </Section>
                )}

                {/* Dynamic Button subtext */}
                {buttonSubtext && (
                  <Text className="text-grey-500 m-0 mb-[16px] text-[14px]">
                    {buttonSubtext}
                  </Text>
                )}
              </Section>
            </Section>

            {/* Footer */}
            <Section className="mt-[32px] text-center">
              {/* Social Media Icons Row.

                  Every value below comes from Settings > Contact Information,
                  substituted by Jinja2 at send time. The `{% if %}` wrappers
                  are emitted as literal text so a social link the org has not
                  configured drops its icon entirely rather than rendering a
                  dead `href=""`.

                  Spacing is per-icon (11px each side = the original 22px gap)
                  rather than on the middle one, so the row still spaces
                  correctly when any single link is unconfigured. */}
              <Section className="mb-[19px]">
                {"{% if Org_Facebook_URL %}"}
                <Link href="{{ Org_Facebook_URL }}" className="inline-block mx-[11px]">
                  <Img
                    src="/static/facebook.png"
                    width="30"
                    height="30"
                    alt="Facebook"
                  />
                </Link>
                {"{% endif %}"}
                {"{% if Org_Instagram_URL %}"}
                <Link
                  href="{{ Org_Instagram_URL }}"
                  className="inline-block mx-[11px]"
                >
                  <Img
                    src="/static/instagram.png"
                    width="30"
                    height="30"
                    alt="Instagram"
                  />
                </Link>
                {"{% endif %}"}
                {"{% if Org_Twitter_URL %}"}
                <Link href="{{ Org_Twitter_URL }}" className="inline-block mx-[11px]">
                  <Img
                    src="/static/x-logo.png"
                    width="30"
                    height="30"
                    alt="X"
                  />
                </Link>
                {"{% endif %}"}
              </Section>

              {/* Address and Website URL */}
              {"{% if Org_Website %}"}
              <Text className="font-nunito-sans text-grey-400 font-normal m-0 mb-[22px] text-[14px] leading-[18px]">
                {"{{ Org_Website }}"}
              </Text>
              {"{% endif %}"}
              {"{% if Org_Address %}"}
              <Text className="font-nunito-sans text-grey-400 font-normal m-0 mb-[30px] text-[14px] leading-[18px]">
                {"{{ Org_Address }}"}
              </Text>
              {"{% endif %}"}

              {/* Small Footer Logo */}
              <Section className="mt-[24px]">
                <Img
                  src="/static/f4k_full_logo_clear_bg.png"
                  alt="Food4Kids Waterloo Region"
                  width="125"
                  className="mx-auto"
                />
              </Section>
            </Section>
          </Container>
        </Body>
      </Tailwind>
    </Html>
  );
}
