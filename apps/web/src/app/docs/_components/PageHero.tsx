import Image from "next/image";

interface PageHeroProps {
  title: string;
  highlight?: string;
  subtitle: string;
  illustration: string;
}

export function PageHero({ title, highlight, subtitle, illustration }: PageHeroProps) {
  return (
    <section className="relative overflow-hidden rounded-2xl mb-12">
      {/* Background illustration */}
      <div className="absolute inset-0">
        <Image
          src={illustration}
          alt=""
          fill
          className="object-cover opacity-30"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-r from-background via-background/95 to-background/60" />
      </div>

      {/* Content */}
      <div className="relative px-6 sm:px-10 py-10 sm:py-14">
        <h1 className="font-['Newsreader'] text-2xl sm:text-3xl font-bold tracking-tight mb-3 text-on-surface">
          {title}
          {highlight && (
            <>
              {" "}
              <span className="text-primary">{highlight}</span>
            </>
          )}
        </h1>
        <p className="text-sm sm:text-base text-on-surface/50 max-w-xl leading-relaxed">
          {subtitle}
        </p>
      </div>
    </section>
  );
}
