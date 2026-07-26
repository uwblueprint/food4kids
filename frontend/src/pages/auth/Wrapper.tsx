import loginPageIllustration from '@/assets/illustrations/login-page-illustration.png';
import loginPageIllustrationMobile from '@/assets/illustrations/login-page-illustration-mobile.png';
import logoImg from '@/assets/logos/logo_desktop_two_lines.png';
import logoImgMobile from '@/assets/logos/logo_mobile_one_line.svg';
import { cn } from '@/lib/utils';

/**
 * Shared shell for every pre-sign-in screen.
 *
 * The designs use two coherent layout systems, not one, and this component
 * implements both — a screen picks one via `showMobileIllustration`. Measured
 * against the finalized Figma frames at 375 / 834 / 1440:
 *
 *                          block top  illus→heading  heading→form  logo x
 *   A  Login, Login|Error         64             24            32      20
 *   B  Forgot Password,          124             40            16      20
 *      link-sent, Account
 *      Created
 *   Create Password           centred              —           32      20
 *
 * The heading→subtitle gap is 0 in every system. Both put the logo at x=20.
 *
 * The trap in system B is below: the block is pinned to a fixed top through
 * tablet and only centres at desktop. Centring at tablet lands within half a
 * pixel on the login screens, so it can look right while being 11px out on
 * every shorter screen.
 */
interface WrapperProps {
  children: React.ReactNode;
  headerTitle: string;
  subheaderTitle: string;
  className?: string;
  /**
   * Below `desktop`, an illustration sits between the logo and the heading.
   * The password-entry forms opt out: their field list plus the password
   * criteria already overflow a phone screen, and the designs drop the
   * graphic there. Every other auth screen keeps it.
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
            ? /*
               * With the illustration the designs pin the block to a fixed top
               * — 64 on the login screens, 124 on the rest — and they use the
               * same number at mobile and at tablet. Only desktop centres.
               * Centring at tablet happened to land within half a pixel on
               * login (692 tall in 821 centres at 64.5) which is why it looked
               * right, but on the shorter screens it was 11px out.
               */
              'tablet:items-start desktop:items-center'
            : /*
               * Without the illustration the designs centre vertically at every
               * width instead: the taller "filled" frames start higher by
               * exactly the height they gain (522 tall at y=150, 578 tall at
               * y=122, in an 821 frame). A fixed padding would only be right at
               * one viewport height.
               */
              'flex items-center justify-center'
        )}
      >
        <div
          className={cn(
            /*
             * `pt-16` is the login screens' fixed top and carries through
             * tablet; the other screens override it via `className`. Desktop
             * centres instead, so it zeroes the padding — an asymmetric offset
             * would bias the centring by half its size.
             *
             * `gap-8` is the heading→form gap. 32 on login and the password
             * screens at every width; the confirmation screens are 16 below
             * desktop, which they override for themselves.
             */
            'desktop:pt-0 tablet:px-0 tablet:max-w-126 desktop:max-w-100 flex w-full flex-col gap-8 px-5 pt-16',
            /*
             * Centred by the parent at every width (see above), so replace
             * `pt-16`'s one-sided offset with symmetric padding and keep the
             * content off the edges on short viewports. Mobile only: from
             * `tablet` up the design has room for neither, and leaving the
             * bottom half of `py-8` behind there pushed the content 16px high.
             */
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
