import loginPageIllustration from '@/assets/illustrations/login-page-illustration.png';
import loginPageIllustrationMobile from '@/assets/illustrations/login-page-illustration-mobile.png';
import logoImg from '@/assets/logos/logo_desktop_two_lines.png';
import logoImgMobile from '@/assets/logos/logo_mobile_one_line.svg';
import { cn } from '@/lib/utils';

interface WrapperProps {
  children: React.ReactNode;
  headerTitle: string;
  subheaderTitle: string;
  className?: string;
}

export const WrapperWithLogo = ({
  children,
  headerTitle,
  subheaderTitle,
  className,
}: WrapperProps) => {
  return (
    <div className="desktop:overflow-hidden relative flex h-screen w-full flex-row overflow-auto">
      {/* Left Column: Form Section */}
      <div className="tablet:flex desktop:w-1/2 tablet:items-center tablet:justify-center desktop:justify-start desktop:pl-[8.5vw] w-full">
        <div
          className={cn(
            'tablet:pt-0 tablet:px-0 tablet:max-w-126 tablet:gap-4 desktop:max-w-100 flex w-full flex-col gap-8 px-5 pt-16',
            className
          )}
        >
          {/* Logo and Heading */}
          <div className="flex-col">
            <div className="self-start">
              {/* Desktop Logo */}
              <img
                src={logoImg}
                alt="Food4Kids Waterloo Region Logo"
                className="desktop:block hidden h-26 w-auto object-contain"
              />
              {/* Mobile Logo */}
              <img
                src={logoImgMobile}
                alt="Food4Kids Waterloo Region Logo"
                className="desktop:hidden absolute top-5 left-5 h-7 w-auto"
              />
            </div>
            {/* Mobile Login Illustration */}
            <div className="desktop:hidden mb-6 flex flex-row items-center justify-center">
              <img
                src={loginPageIllustrationMobile}
                alt="Food4Kids Waterloo Region Illustration"
                className="h-[212px] w-[307px] object-contain"
              />
            </div>
            {/* Heading */}
            <h1>{headerTitle}</h1>
            <p className="text-m-p2 tablet:font-medium">{subheaderTitle}</p>
          </div>
          {children}
        </div>
      </div>
      {/* Right Column: Illustration Section */}
      <div className="desktop:block hidden h-full w-1/2 overflow-hidden">
        <img
          src={loginPageIllustration}
          alt="Food4Kids Illustration"
          className="h-full w-full object-cover"
        />
      </div>
    </div>
  );
};
