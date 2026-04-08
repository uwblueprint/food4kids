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
          <Container className="mx-[200px] my-[100px] max-w-[600px]">
            {/* Main email structure */}
            <Section className="bg-grey-100 overflow-hidden rounded-lg">
              {/* Top Card: Logo Header */}
              <Section className="bg-grey-100 py-[24px] text-center">
                <Img
                  src="https://food4kidswr.ca/wp-content/uploads/2022/08/food4kids-waterloo-region.png"
                  alt="Food4Kids Waterloo Region"
                  width="180"
                  className="mx-auto"
                />
              </Section>

              <Hr className="border-grey-300 m-0 w-full border-solid" />

              {/* Bottom Card: Main Content Area */}
              <Section className="p-[40px]">
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
              {/* Social Media Icons Row */}
              <Section className="mb-[16px]">
                <Link
                  href="https://facebook.com/Food4KidsWR"
                  className="mx-[8px] inline-block"
                >
                  <Img
                    src="/static/facebook.png"
                    width="24"
                    height="24"
                    alt="Facebook"
                  />
                </Link>
                <Link
                  href="https://instagram.com/food4kidswr"
                  className="mx-[8px] inline-block"
                >
                  <Img
                    src="https://static.xx.fbcdn.net/rsrc.php/yr/r/e0S_nAdcU32.webp"
                    width="24"
                    height="24"
                    alt="Instagram"
                  />
                </Link>
                <Link
                  href="https://twitter.com/food4kidsWR"
                  className="mx-[8px] inline-block"
                >
                  <Img
                    src="/static/twitter.png"
                    width="24"
                    height="24"
                    alt="Twitter"
                  />
                </Link>
              </Section>

              {/* Address and Website URL */}
              <Text className="font-nunito-sans text-grey-400 font-normal m-0 text-[14px] leading-[18px]">
                food4kidswr.ca
                <br />
                <br />
                330 Trillium Dr., Unit B Kitchener ON N2E 3J2
              </Text>

              {/* Small Footer Logo */}
              <Section className="mt-[24px]">
                <Img
                  src="/static/f4k_logo_footer.png"
                  alt="Food4Kids Mark"
                  width="50"
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
