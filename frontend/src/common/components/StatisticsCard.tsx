import boyImg from '@/assets/illustrations/boy.png';
import boyPointingImg from '@/assets/illustrations/boy-pointing.png';
import girlSearchingImg from '@/assets/illustrations/girl-searching.png';
import grannyImg from '@/assets/illustrations/granny.png';
import { cn } from '@/lib/utils';

const CHARACTERS = {
  // Further reduce sizes and push illustrations more to bottom-right so they don't overlap the numbers
  granny: { src: grannyImg, size: 100, right: -22, bottom: -18 },
  boy: { src: boyImg, size: 90, right: -18, bottom: -14 },
  boyPointing: { src: boyPointingImg, size: 110, right: -20, bottom: -16 },
  girlSearching: { src: girlSearchingImg, size: 110, right: -20, bottom: -16 },
} as const;

const COLOR_MAP = {
  green: 'bg-brand-green',
  blue: 'bg-brand-light-blue',
  orange: 'bg-brand-orange',
  pink: 'bg-brand-pink',
} as const;

type Character = keyof typeof CHARACTERS;
type StatisticsCardColor = keyof typeof COLOR_MAP;

interface StatisticsCardProps {
  label: string;
  value: string | number;
  character: Character;
  color?: StatisticsCardColor;
  className?: string;
}

function StatisticsCard({
  label,
  value,
  character,
  color = 'green',
  className,
}: StatisticsCardProps) {
  return (
    <div
      className={cn('relative w-full overflow-hidden rounded-xl', className)}
    >
      <div
        className={cn(
          // reduced height and horizontal padding to tighten vertical spacing
          'shadow-card relative h-20 w-full overflow-hidden rounded-xl px-3',
          COLOR_MAP[color]
        )}
      >
        {/* Diagonal stripe decorations */}
        <div className="absolute -top-4 left-10 h-40 w-12 -skew-x-12 bg-white/10" />
        <div className="absolute -top-4 left-36 h-40 w-18 -skew-x-12 bg-white/10" />

        {/* Sparkle diamonds */}
        <div className="absolute top-3 right-20 size-1.5 rotate-45 bg-white" />
        <div className="absolute right-14 bottom-3 size-1.5 rotate-45 bg-white" />

        {/* Text */}
        <div className="relative flex h-full flex-col justify-center">
          <p className="text-h5 sm:text-h4 tablet:text-h3 text-grey-100 font-sans">
            {label}
          </p>
          <p className="text-h3 sm:text-h2 tablet:text-h1 text-grey-100 font-nunito font-bold">
            {value}
          </p>
        </div>
      </div>

      {/* Character — on the outer wrapper so the card's clip cuts it off */}
      <img
        src={CHARACTERS[character].src}
        alt=""
        aria-hidden
        className="absolute object-contain"
        style={{
          width: CHARACTERS[character].size,
          height: CHARACTERS[character].size,
          right: CHARACTERS[character].right,
          bottom: (CHARACTERS[character] as any).bottom,
        }}
      />
    </div>
  );
}

export { StatisticsCard };
export type { Character, StatisticsCardColor };
