"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export interface IntegrationItem {
  name: string;
  description: string;
  iconSrc: string;
  category?: string;
  status?: "connected" | "disconnected" | "configuring";
  href?: string;
  onClick?: () => void;
}

export interface IntegrationShowcaseProps extends React.HTMLAttributes<HTMLElement> {
  title?: string;
  subtitle?: string;
  illustrationSrc?: string;
  illustrationAlt?: string;
  integrations?: IntegrationItem[];
  onSelectIntegration?: (item: IntegrationItem) => void;
}

/**
 * HighlightedTitle: renders title with hand-drawn brush stroke under text surrounded by ~tilde~
 */
export const HighlightedTitle: React.FC<{ text: string; className?: string }> = ({
  text,
  className,
}) => {
  const parts = text.split(/~/);
  return (
    <h2 className={cn("text-3xl font-bold tracking-tight text-foreground sm:text-4xl", className)}>
      {parts.map((part, index) =>
        index === 1 ? (
          <span key={index} className="relative whitespace-nowrap text-primary">
            <span className="relative z-10">{part}</span>
            <svg
              aria-hidden="true"
              viewBox="0 0 418 42"
              className="absolute -bottom-1.5 left-0 h-auto w-full text-primary/70 fill-current pointer-events-none"
              preserveAspectRatio="none"
            >
              <path
                d="M203.371.916c-26.013-2.078-76.686 1.98-114.243 8.919-37.556 6.939-78.622 17.103-122.256 28.703-43.633 11.6-4.984 14.306 43.123 7.021 48.107-7.285 93.638-16.096 146.446-17.742 52.808-1.646 105.706 5.429 158.649 14.13 52.943 8.701 105.886 19.342 158.826 29.483 52.94 10.141 52.94 10.141-11.41-19.043C371.18 14.363 322.753 5.488 281.339 2.143 239.925-1.201 203.371.916 203.371.916z"
              />
            </svg>
          </span>
        ) : (
          <React.Fragment key={index}>{part}</React.Fragment>
        )
      )}
    </h2>
  );
};

/**
 * IntegrationShowcase: 21st.dev component by @ravikatiyar162
 * Displays title with highlight, hand-drawn illustration, and staggered animated integration cards.
 */
export const IntegrationShowcase = React.forwardRef<HTMLElement, IntegrationShowcaseProps>(
  (
    {
      title = "Connect your ~favorite~ tools",
      subtitle = "Save time using popular integrations to sync your form submissions.",
      illustrationSrc = "https://cdn.21st.dev/assets/mirror/91/913e6c36b2d27a75e0ee5fb3aa202dc67d1e48ef9e8d3f56da49ba4b3e6bddf5.png",
      illustrationAlt = "Hand-drawn illustration of characters reviewing integrations checklist",
      integrations = DEFAULT_INTEGRATIONS,
      onSelectIntegration,
      className,
      ...props
    },
    ref
  ) => {
    const containerVariants = {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: { staggerChildren: 0.06 },
      },
    };

    const itemVariants = {
      hidden: { opacity: 0, y: 18 },
      visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.45, ease: "easeOut" },
      },
    };

    return (
      <section
        ref={ref}
        className={cn("w-full py-12 sm:py-16 bg-background text-foreground", className)}
        {...props}
      >
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 items-center gap-x-12 gap-y-10 lg:grid-cols-2">
            <div className="max-w-xl">
              <HighlightedTitle text={title} />
              <p className="mt-4 text-base text-muted-foreground sm:text-lg">
                {subtitle}
              </p>
            </div>
            <div className="flex items-center justify-center lg:justify-end">
              <img
                src={illustrationSrc}
                alt={illustrationAlt}
                className="w-56 sm:w-64 h-auto object-contain drop-shadow-sm select-none pointer-events-none"
              />
            </div>
          </div>

          <motion.div
            className="mt-12 grid grid-cols-1 gap-x-8 gap-y-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            viewport={{ once: true, amount: 0.2 }}
          >
            {integrations.map((item) => (
              <motion.div
                key={item.name}
                variants={itemVariants}
                onClick={() => {
                  item.onClick?.();
                  onSelectIntegration?.(item);
                }}
                className={cn(
                  "flex items-start space-x-4 p-4 rounded-2xl border border-transparent transition-all duration-300",
                  "hover:bg-accent/40 hover:border-border/60 hover:shadow-sm cursor-pointer group"
                )}
              >
                <div className="flex-shrink-0 mt-0.5">
                  <img
                    src={item.iconSrc}
                    alt={`${item.name} logo`}
                    className="h-9 w-9 object-contain rounded-lg transition-transform duration-300 group-hover:scale-105"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors truncate">
                      {item.name}
                    </h3>
                    {item.status === "connected" && (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                        Connecté
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                    {item.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>
    );
  }
);

IntegrationShowcase.displayName = "IntegrationShowcase";

export const DEFAULT_INTEGRATIONS: IntegrationItem[] = [
  {
    name: "Notion",
    description: "Send submissions to Notion.",
    iconSrc: "https://cdn.21st.dev/assets/mirror/f0/f00e80e86e9962043ccc8e8b9ecbc4a69dae512c2718830f5ccae9abc0470cf1.svg",
  },
  {
    name: "Google Sheets",
    description: "Send submissions to a sheet.",
    iconSrc: "https://cdn.21st.dev/assets/mirror/d3/d3b9eaf85507404536f67500ec23361b96e4232fbcd128fa1ee035adcb48c269.svg",
  },
  {
    name: "Airtable",
    description: "Send submissions to Airtable.",
    iconSrc: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAMAAABF0y+mAAAAjVBMVEVHcEz+uwD9tQDtnB/9tQD9tAD8tAD/tAD+tQD+tQD+tgD9tQD9tAD9tgDfJ1a8IEi6EEv/uAD9tAD9tQAOwP8Xv/8YwP/5K2DnJ1m5H0e6IEe8HUnxJ2AXwP8Wv/8Yv/8Yv/8YwP/5K2DDIUv9tQANx/8OwP8YwP8Uwv8UwP/WJFK9IEnAIEj5LGD5K2Cg/8aNAAAAL3RSTlMAJmwOVdb/HoR9NKfqiK7GUke6t1XEueL//+yMLzOT9v/h//+5D1zdJpr/mkSwqkV2VRMAAADASURBVHgBvc5FFgJBEATRxN3G3d3ufzxacGqWENv/SvCHJtPphJbZfLFkLeazL1qtBQnerN5ou1u+tdveZTbdL7/aTyVul2QTqZPD/mtwvRJ0PJ2Bi/JK6gXQdIOhadmO62G2WdyfncEPwiiKOSZWattiPNvv2VBe6BGvFJgkTNn4DKyqZkNvmDQ2r0VeSnhDoacOfkRhYjEC/JDC3gNGcGBEoyACYwAeIxINiAgM6wojqBc5QGIY+CCrQkPDr7sCTOYgaxntCWQAAAAASUVORK5CYII=",
  },
  {
    name: "Webhooks",
    description: "Send events for new submissions to HTTP endpoints.",
    iconSrc: "https://cdn.21st.dev/assets/mirror/a3/a3200548fd9e7c24ee4214d4304dfdb8815b36e3fc2308bdae185353f4823adf.svg",
  },
  {
    name: "Slack",
    description: "Send Slack messages for new submissions.",
    iconSrc: "https://cdn.21st.dev/assets/mirror/c0/c0af31c6ff066af42be01942d97b843c037874f184e1c96f0a6bdf3946a4d1b9.svg",
  },
  {
    name: "Coda",
    description: "Send submissions to Coda.",
    iconSrc: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAAAiklEQVR4AWNwL/ChKx5YC79khSQC8X8q40SsFgIlOEAKaIQ5sFkoQ0MLZYa9hfyjFpKKDwNxIBBrQ3EdbVIpZj5DNo8f6pDDID61LKwjoZSh3EKQPnpa+HA4W4hIffS2cA6dLCScUqH58SEIU9FCRHxCM3sgFM8ZLUtpbuFIqfHp34iifzNx+Le8AdWFLhdVBCcKAAAAAElFTkSuQmCC",
  },
  {
    name: "Google Analytics",
    description: "Analyze traffic sources, visitor behavior and time spent.",
    iconSrc: "https://cdn.21st.dev/assets/mirror/a3/a30eb12f41044715f31314e9bf84ad984ae3b54b07125f5492b23cf151a0c461.svg",
  },
  {
    name: "Meta Pixel",
    description: "Measure and optimize your ad campaigns.",
    iconSrc: "https://cdn.21st.dev/assets/mirror/78/78e77f62b148c7e51c24d978f7f450deaa2adb84b7b716d113c0f2777b97e7e0.svg",
  },
  {
    name: "Zapier",
    description: "Send submissions to your favorite tools.",
    iconSrc: "https://cdn.21st.dev/assets/mirror/13/139a90853100a3a4afa575e33a8134a26d92cabbd26044c62f93ccc938dbb7c1.svg",
  },
  {
    name: "Make",
    description: "Send submissions to your favorite tools.",
    iconSrc: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAMAAABF0y+mAAAAwFBMVEX//////f/RY/LKYvDy4PvZwPF3ANGPTNeqhN/n3PVqAMuLS9X33/3GAO++GuyxAOnId/DFoOqEFtV+INLMteuDPdPhYPfNDvHEIu7UkvOsbOOJINeEJ9Tt4/jbAPXXF/SSGduTKdvxW/vnDvnbivT49PyQANuZW9v/2//yAPzpzPmHGNe6keb/Vf/mhvjNmu//AP+5ZumnJeWDANfzhPz/0//37f2jAOSnVeL/g//lxPfCjev/Sf+3TurZuPKIMda9K89qAAAAt0lEQVR4Ad3QAQfCYBDG8f9tu7e3WVRUBUCRCFDfH4gAAhkgCKWoNmZZTcy26QvswXF+nsPR3sifxRFJVfKAvAC8wgL5JfYj8Gvoi0R+jt2ouFUUrUXOxmBPaQPHSjaam++AXMtnl5KAaEpfoN5UyCahJnBs4NLtGI1xhtgp6yCtoAKDEIHrSWrNjQsdh62STYFZBT2gu8eDoQsP1mXcacAF7kafLvTsYVX97XYPgPfOWAy4hbQrHxHNJ3cZ8ThmAAAAAElFTkSuQmCC",
  },
  {
    name: "Pipedream",
    description: "Send submissions to your favorite tools.",
    iconSrc: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAcBAMAAACAI8KnAAAAMFBMVEUz0ow004s00os00osz0Ywr0Ygc0INC1ZJV2Zxw3qrN8+GJ5buw7dD////i+e+i6ccrH71KAAAABXRSTlMIiuv/iksBsyIAAACfSURBVHgBY2BUNoYDIwcGZ2MkYMgAkkRIMwAJ07Tg0IowMB/EjVy1ddeqNa0wbvTdV3fv3l2B4ILALSTuvXV3706Fc++1pa+9ewzOvW9suvfuMmTuvLvPULnX8HKf4TLqTmn4WSSL7p6cf/duK5Ij3yI7EgReIrh3/t5904zg3jevKDZG4gJJXFzLV6+RueYd7XCuMigo4QGLFuxokQIA5VCQSPPORxwAAAAASUVORK5CYII=",
  },
  {
    name: "And many more",
    description: "Integrate with thousands of tools using Zapier, Make or Pipedream.",
    iconSrc: "https://cdn.21st.dev/assets/mirror/51/5161cc75a34e63955dad792cabeccfe7c10d411fcd7b8e2a0c6b5d6b67d01ce9.png",
  },
];

export default IntegrationShowcase;
