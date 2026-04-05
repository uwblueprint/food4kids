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

// Great Job on working on the theme, However, I think it might be good to use a script to extract the design system like extract-tokens.ts instead
// You can now delete the below and use the import
const f4kTheme = {
  theme: {
    extend: {
      colors: {
        grey: {
          100: '#ffffff',
          150: '#f8f8f8',
          200: '#eff3f6',
          300: '#e0e7ed',
          400: '#707581',
          500: '#1c1b1f',
        },
        blue: { 50: '#e9f4ff', 100: '#bed3e9', 300: '#226ca7', 400: '#195586' },
        red: '#eb3131',
        'light-red': '#fef3f2',
        'dark-yellow': '#fdb022',
        'light-yellow': '#fffaeb',
        'success-stroke': '#039855',
        'success-fill': '#ecfdf3',
        brand: {
          green: '#27b28d',
          'light-blue': '#09a7df',
          orange: '#eb5531',
          pink: '#b33f93',
        },
      },
      fontFamily: {
        nunito: ['"Nunito"', 'sans-serif'],
        'nunito-sans': ['"Nunito Sans"', 'sans-serif'],
      },
    },
  },
};

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
      <Head />
      <Preview>{previewText}</Preview>
      <Tailwind
        config={{
          presets: [pixelBasedPreset],
          ...emailTailwindConfig,
        }}
      >
        <Body className="bg-grey-300 font-nunito-sans text-grey-500 m-0 p-0">
          <Container className="mx-[200px] my-[100px] max-w-[600px]">
            {/* Main email structure */}
            <Section className="bg-grey-100 overflow-hidden rounded-lg">
              {/* Top Card: Logo Header */}
              <Section className="bg-grey-100 py-[24px] text-center">
                <Img
                  src="/static/logo_mobile_one_line.png"
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
                    src="/static/instagram.png"
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
              <Text className="text-grey-400 m-0 text-[12px] leading-[18px]">
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
