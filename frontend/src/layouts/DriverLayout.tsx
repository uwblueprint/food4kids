import { Outlet } from 'react-router-dom';

/**
 * Driver platform shell.
 *
 * Per the F4K "Margins and Padding" design system (driver app):
 *   - Content is capped at a max-width of 834px, centered, with whitespace
 *     beyond it on wider monitors ("a white background covers anything past 834px").
 *   - Uniform margins on all sides: 20px on mobile (0–499px), 32px on
 *     tablet/desktop (≥500px). The 834px cap is inclusive of the 32px margins.
 */
export const DriverLayout = () => {
  return (
    <div className="tablet:p-8 mx-auto w-full max-w-[834px] p-5">
      <Outlet />
    </div>
  );
};
