import boyImg from '@/assets/illustrations/boy.png';
import girlConfusedImg from '@/assets/illustrations/girl-confused.png';
import boyPointingImg from '@/assets/illustrations/boy-pointing.png';
import girlSearchingImg from '@/assets/illustrations/girl-searching.png';
import grannyImg from '@/assets/illustrations/granny.png';
import { cn } from '@/lib/utils';

const CHARACTER_MAP = {
  boy: boyImg,
  boyPointing: boyPointingImg,
  girlConfused: girlConfusedImg,
  girlSearching: girlSearchingImg,
  granny: grannyImg,
} as const;

const COLOR_MAP = {
  green: 'bg-brand-green',
  blue: 'bg-brand-light-blue',
  orange: 'bg-brand-orange',
  pink: 'bg-brand-pink',
} as const;

type Character = keyof typeof CHARACTER_MAP;
type StatCardColor = keyof typeof COLOR_MAP;

interface StatCardProps {
  label: string;
  value: string | number;
  character: Character;
  color?: StatCardColor;
  className?: string;
}

function StatCard({
  label,
  value,
  character,
  color = 'green',
  className,
}: StatCardProps) {
  return (
    <div
      className={cn('relative w-full overflow-hidden rounded-2xl', className)}
    >
      <div
        className={cn(
          'relative h-24 w-full overflow-hidden rounded-2xl p-4 shadow-[0px_0px_10px_0px_rgba(0,0,0,0.04)]',
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
        <div className="relative flex flex-col justify-center gap-0.5">
          <p className="font-nunito-sans text-grey-100 text-base leading-5 font-bold">
            {label}
          </p>
          <p className="font-nunito text-grey-100 text-3xl leading-10 font-bold">
            {value}
          </p>
        </div>
      </div>

      {/* Character — sits on outer wrapper, pops out below card */}
      <img
        src={CHARACTER_MAP[character]}
        alt=""
        aria-hidden
        className="absolute top-3/5 -right-2 w-38 -translate-y-1/2 object-contain"
      />
    </div>
  );
}

export { StatCard };
export type { Character, StatCardColor };
