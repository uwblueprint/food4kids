import loginPageIllustration from '@/assets/illustrations/login-page-illustration.png';
import loginPageIllustrationMobile from '@/assets/illustrations/login-page-illustration-mobile.png';
import logoImg from '@/assets/logos/logo_desktop_two_lines.png';
import logoImgMobile from '@/assets/logos/logo_mobile_one_line.svg';
import { cn } from '@/lib/utils';

/**
 * Shared shell for every pre-sign-in screen. The designs use two layout
 * systems and this implements both, selected by `showMobileIllustration`:
 *
 *                       block top  illus→heading  heading→form
 *   A  Login screens           64             24            32
 *   B  Everything else        124             40            16
 *   Create Password       centred              —            32
 */
interface WrapperProps {
  children: React.ReactNode;
  headerTitle: string;
  subheaderTitle: string;
  className?: string;
  /**
   * Below `desktop`, an illustration sits between the logo and the heading.
   * The password-entry forms opt out — too tall for a phone with it.
   */
  showMobileIllustration?: boolean;
}

export const WrapperWithLogo = ({
  children,
  headerTitle,
  subheaderTitle,
  className,
  showMobileIllustration = true,
}: WrapperProps) => {
  return (
    <div className="desktop:overflow-hidden relative flex h-screen w-full flex-row overflow-auto">
      {/* Left Column: Form Section */}
      <div
        className={cn(
          'tablet:flex desktop:w-1/2 tablet:justify-center desktop:justify-start desktop:pl-[8.5vw] w-full',
          showMobileIllustration
            ? // Fixed top through tablet; only desktop centres.
              'tablet:items-start desktop:items-center'
            : // No illustration: centred vertically at every width.
              'flex items-center justify-center'
        )}
      >
        <div
          className={cn(
            // `pt-16` is the login screens' fixed top (other screens override
            // it via `className`); desktop zeroes it because it centres instead.
            // `gap-8` is the heading→form gap.
            'desktop:pt-0 tablet:px-0 tablet:max-w-126 desktop:max-w-100 flex w-full flex-col gap-8 px-5 pt-16',
            // Centred by the parent, so swap the one-sided offset for symmetric
            // padding. Mobile only — at tablet up it pushed the content high.
            !showMobileIllustration && 'tablet:py-0 py-8',
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
            {showMobileIllustration && (
              <div className="desktop:hidden mb-6 flex flex-row items-center justify-center">
                <img
                  src={loginPageIllustrationMobile}
                  alt="Food4Kids Waterloo Region Illustration"
                  className="h-[212px] w-[307px] object-contain"
                />
              </div>
            )}
            {/* Heading */}
            <h1>{headerTitle}</h1>
            <p className="text-m-p2 tablet:font-medium whitespace-pre-line">{subheaderTitle}</p>
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
