"use client";

/**
 * Tailark integrations variants packed for 21st.
 * Named exports match demo slugs; default is the card grid.
 */

import * as React from "react";
import { useEffect, useState } from "react";
import Link from "next/link";
import { animate, motion, useMotionValue } from "framer-motion";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import {
  Bot,
  ChevronRight,
  CodeXml,
  Container,
  Database,
  GitMerge,
  PenTool,
  Shapes,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn as cnUtil } from "@/lib/utils";

const cn = cnUtil;

function useMeasure(): [
  (node: Element | null) => void,
  { width: number; height: number },
] {
  const [size, setSize] = useState({ width: 0, height: 0 });
  const ref = React.useCallback((node: Element | null) => {
    if (!node) return;
    const el = node as HTMLElement;
    const update = () => {
      setSize({ width: el.offsetWidth, height: el.offsetHeight });
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
  }, []);
  return [ref, size];
}

// --- IntegrationsSection (default) ---
const IntegrationsSection = (() => {
  function IntegrationsSection() {
    return (
      <section>
        <div className="py-32">
          <div className="mx-auto max-w-5xl px-6">
            <div className="text-center">
              <h2 className="text-balance text-3xl font-semibold md:text-4xl">
                Integrate with your favorite tools
              </h2>
              <p className="text-muted-foreground mt-6">
                Connect seamlessly with popular platforms and services to
                enhance your workflow.
              </p>
            </div>

            <div className="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <IntegrationCard
                title="GitHub"
                description="Version control and collaboration platform for developers."
              >
                <GitHubLogo />
              </IntegrationCard>

              <IntegrationCard
                title="Slack"
                description="Team communication and collaboration hub."
              >
                <SlackLogo />
              </IntegrationCard>

              <IntegrationCard
                title="Notion"
                description="All-in-one workspace for notes, tasks, and projects."
              >
                <NotionLogo />
              </IntegrationCard>

              <IntegrationCard
                title="Figma"
                description="Collaborative design and prototyping platform."
              >
                <FigmaLogo />
              </IntegrationCard>

              <IntegrationCard
                title="Discord"
                description="Voice, video, and text chat platform for communities."
              >
                <DiscordLogo />
              </IntegrationCard>

              <IntegrationCard
                title="VS Code"
                description="Lightweight but powerful source code editor."
              >
                <VSCodeLogo />
              </IntegrationCard>
            </div>
          </div>
        </div>
      </section>
    );
  }

  const IntegrationCard = ({
    title,
    description,
    children,
    link = "https://github.com/meschacirung/cnblocks",
  }: {
    title: string;
    description: string;
    children: React.ReactNode;
    link?: string;
  }) => {
    return (
      <Card className="p-6">
        <div className="relative">
          <div className="*:size-10">{children}</div>

          <div className="space-y-2 py-6">
            <h3 className="text-base font-medium">{title}</h3>
            <p className="text-muted-foreground line-clamp-2 text-sm">
              {description}
            </p>
          </div>

          <div className="flex gap-3 border-t border-dashed pt-6">
            <Button
              asChild
              variant="secondary"
              size="sm"
              className="gap-1 pr-2 shadow-none"
            >
              <Link href={link}>
                Learn More
                <ChevronRight className="ml-0 !size-3.5 opacity-50" />
              </Link>
            </Button>
          </div>
        </div>
      </Card>
    );
  };

  // --- Logos (inline SVG) ---
  const GitHubLogo = () => (
    <svg viewBox="0 0 24 24" fill="currentColor" className="text-black">
      <path
        d="M12 0C5.37 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.6.11.793-.26.793-.577 
      0-.285-.01-1.04-.016-2.04-3.338.726-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.757-1.333-1.757-1.09-.745.083-.73.083-.73 
      1.204.085 1.838 1.237 1.838 1.237 1.07 1.835 2.807 1.304 3.492.997.108-.775.42-1.304.763-1.604-2.665-.3-5.466-1.333-5.466-5.93 
      0-1.31.47-2.38 1.236-3.22-.124-.303-.536-1.52.117-3.167 0 0 1.008-.322 3.3 1.23a11.52 11.52 0 0 1 3-.404c1.02.004 2.045.137 
      3 .404 2.29-1.552 3.297-1.23 3.297-1.23.655 1.647.243 2.864.12 3.167.77.84 1.235 1.91 1.235 3.22 
      0 4.61-2.803 5.625-5.475 5.92.431.372.816 1.102.816 2.222 0 1.606-.015 2.9-.015 3.293 
      0 .32.19.694.8.576C20.565 21.796 24 17.3 24 12c0-6.627-5.373-12-12-12z"
      />
    </svg>
  );

  const SlackLogo = () => (
    <svg viewBox="0 0 24 24" fill="currentColor" className="text-purple-600">
      <path d="M5.2 15.7a2.6 2.6 0 1 1 0 5.2H2.6a2.6 2.6 0 1 1 0-5.2H5.2zm1.3-1.3a2.6 2.6 0 1 1 0-5.2h2.6v5.2H6.5zm6.5-6.5a2.6 2.6 0 1 1 5.2 0v2.6h-5.2V7.9zm-1.3 1.3a2.6 2.6 0 1 1 0 5.2H9.1V9.2h2.6zm8.4 0a2.6 2.6 0 1 1 0 5.2h-2.6V9.2h2.6zM15.7 5.2a2.6 2.6 0 1 1 0 5.2h-2.6V5.2h2.6zM9.2 2.6a2.6 2.6 0 1 1 0 5.2H6.6V2.6h2.6z" />
    </svg>
  );

  const NotionLogo = () => (
    <svg viewBox="0 0 24 24" fill="currentColor" className="text-gray-900">
      <path d="M4 3.5l16-1.5 0 19-16 1.5V3.5zm2 3.7v9.6l8 .6v-9.6l-8-.6z" />
    </svg>
  );

  const FigmaLogo = () => (
    <svg viewBox="0 0 24 24" fill="currentColor" className="text-pink-500">
      <path d="M12 4a4 4 0 100 8 4 4 0 000-8zM12 12a4 4 0 100 8 4 4 0 000-8zM4 4a4 4 0 100 8 4 4 0 000-8zM20 4a4 4 0 100 8 4 4 0 000-8zM12 20a4 4 0 100 8 4 4 0 000-8z" />
    </svg>
  );

  const DiscordLogo = () => (
    <svg viewBox="0 0 24 24" fill="currentColor" className="text-indigo-500">
      <path d="M20 0H4C1.79 0 0 1.79 0 4v16c0 2.21 1.79 4 4 4h12l-1-3h5l1 3c2.21 0 4-1.79 4-4V4c0-2.21-1.79-4-4-4z" />
    </svg>
  );

  const VSCodeLogo = () => (
    <svg viewBox="0 0 24 24" fill="currentColor" className="text-blue-600">
      <path d="M4 3l16 9-16 9V3zm4 5v8l6-4-6-4z" />
    </svg>
  );
  return IntegrationsSection;
})();

// --- IntegrationsDefault (integrations-1.tsx) ---
export const IntegrationsDefault = (() => {
  function IntegrationsSection() {
    return (
      <section>
        <div className="bg-muted dark:bg-background py-24 md:py-32">
          <div className="mx-auto max-w-5xl px-6">
            <div className="grid items-center sm:grid-cols-2">
              <div className="dark:bg-muted/50 relative mx-auto w-fit">
                <div className="bg-radial to-muted dark:to-background absolute inset-0 z-10 from-transparent to-75%"></div>

                {/* Première ligne */}
                <div className="mx-auto mb-2 flex w-fit justify-center gap-2">
                  <IntegrationCard>
                    {/* Gemini */}
                    <svg viewBox="0 0 48 48" className="size-8">
                      <circle cx="24" cy="24" r="24" fill="#00BCD4" />
                      <path
                        d="M14 24a10 10 0 0020 0 10 10 0 00-20 0z"
                        fill="#fff"
                      />
                    </svg>
                  </IntegrationCard>
                  <IntegrationCard>
                    {/* Replit */}
                    <svg viewBox="0 0 48 48" className="size-8">
                      <circle cx="24" cy="24" r="24" fill="#F26207" />
                      <path d="M18 14h12v20H18z" fill="#fff" />
                    </svg>
                  </IntegrationCard>
                </div>

                {/* Deuxième ligne */}
                <div className="mx-auto my-2 flex w-fit justify-center gap-2">
                  <IntegrationCard>
                    {/* Magic UI */}
                    <svg viewBox="0 0 48 48" className="size-8">
                      <circle cx="24" cy="24" r="24" fill="#7C4DFF" />
                      <path d="M14 20h20v8H14z" fill="#fff" />
                    </svg>
                  </IntegrationCard>
                  <IntegrationCard
                    borderClassName="shadow-black-950/10 shadow-xl border-black/25 dark:border-white/25"
                    className="dark:bg-white/10"
                  >
                    <img
                      src="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse1.mm.bing.net%2Fth%2Fid%2FOIP.0HN280BhxnzOHuacFJDipAAAAA%3Fpid%3DApi&f=1&ipt=cf7842e1050c9ec938a9b76c119ee693231d1c9bed95f13ccfee2cafb3ebd1c0&ipo=images"
                      alt="Custom Logo"
                      className="size-8 object-contain rounded"
                    />
                  </IntegrationCard>
                  <IntegrationCard>
                    {/* VSCodium */}
                    <svg viewBox="0 0 48 48" className="size-8">
                      <circle cx="24" cy="24" r="24" fill="#007ACC" />
                      <path d="M16 16l16 8-16 8z" fill="#fff" />
                    </svg>
                  </IntegrationCard>
                </div>

                {/* Troisième ligne */}
                <div className="mx-auto flex w-fit justify-center gap-2">
                  <IntegrationCard>
                    {/* MediaWiki */}
                    <svg viewBox="0 0 48 48" className="size-8">
                      <circle cx="24" cy="24" r="24" fill="#F8DB4D" />
                      <text
                        x="50%"
                        y="55%"
                        textAnchor="middle"
                        fontSize="12"
                        fill="#000"
                      >
                        MW
                      </text>
                    </svg>
                  </IntegrationCard>
                  <IntegrationCard>
                    {/* Google PaLM */}
                    <svg viewBox="0 0 48 48" className="size-8">
                      <circle cx="24" cy="24" r="24" fill="#34A853" />
                      <text
                        x="50%"
                        y="55%"
                        textAnchor="middle"
                        fontSize="12"
                        fill="#fff"
                      >
                        PaLM
                      </text>
                    </svg>
                  </IntegrationCard>
                </div>
              </div>

              {/* Bloc de texte */}
              <div className="mx-auto mt-6 max-w-lg space-y-6 text-center sm:mt-0 sm:text-left">
                <h2 className="text-balance text-3xl font-semibold md:text-4xl">
                  Integrate with your favorite tools
                </h2>
                <p className="text-muted-foreground">
                  Connect seamlessly with popular platforms and services to
                  enhance your workflow.
                </p>

                <Button variant="outline" size="sm" asChild>
                  <Link href="#">Get Started</Link>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  const IntegrationCard = ({
    children,
    className,
    borderClassName,
  }: {
    children: React.ReactNode;
    className?: string;
    borderClassName?: string;
  }) => {
    return (
      <div
        className={cn(
          "bg-background relative flex size-20 rounded-xl dark:bg-transparent",
          className,
        )}
      >
        <div
          role="presentation"
          className={cn(
            "absolute inset-0 rounded-xl border border-black/20 dark:border-white/25",
            borderClassName,
          )}
        />
        <div className="relative z-20 m-auto size-fit *:size-8">{children}</div>
      </div>
    );
  };
  return IntegrationsSection;
})();

// --- IntegrationsNetwork (integrations-4.tsx) ---
export const IntegrationsNetwork = (() => {
  const PlaceholderLogoIcon = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
    </svg>
  );

  const Gemini = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M12.0001 9.1716L14.8285 6.34313L17.6569 9.1716L14.8285 12.0001L12.0001 9.1716Z" />
      <path d="M9.17157 12.0001L6.34311 14.8285L9.17157 17.6569L12.0001 14.8285L9.17157 12.0001Z" />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22ZM12 20C16.4183 20 20 16.4183 20 12C20 7.58172 16.4183 4 12 4C7.58172 4 4 7.58172 4 12C4 16.4183 7.58172 20 12 20Z"
      />
    </svg>
  );

  const Replit = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M8.28,3.027,3.16,8.147v7.706l5.12,5.12h7.706l5.12-5.12V8.147L15.987,3.027ZM9.033,9.44h5.933v2.373H9.033Zm0,3.56h5.933v2.373H9.033Z" />
    </svg>
  );

  const MagicUI = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M12 3v6M6.343 6.343l4.243 4.243M3 12h6m-1.657 5.657l4.243-4.243M12 21v-6m5.657-4.343l-4.243 4.243M21 12h-6m1.657-5.657l-4.243 4.243" />
    </svg>
  );

  const VSCodium = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M22.5 1.5l-13 10.375v9.625l13 1.5V1.5zm-14.5.5L1.625 8.125 8 12l-6.375 3.875L8 22l6.5-4.5V5z" />
    </svg>
  );

  const MediaWiki = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M4.11 15.35c.42 0 .8-.14 1.09-.42l1.01-1.02a.84.84 0 00.25-.6c0-.23-.08-.44-.25-.6L4.25 10.7a1.44 1.44 0 00-1.09-.44c-.41 0-.8.15-1.1.44l-.8.8c-.3.3-.44.68-.44 1.1s.15.8.44 1.1l.8.8c.3.28.68.41 1.09.41zm15.78 0c.41 0 .8-.14 1.09-.42l.8-.8c.3-.3.44-.68.44-1.1s-.14-.8-.44-1.1l-.8-.8a1.44 1.44 0 00-1.09-.44c-.42 0-.8.15-1.09.44l-1.96 1.97c-.17.16-.25.37-.25.6s.08.44.25.6l1.01 1.02c.28.28.67.42 1.09.42zM12 2.01c.41 0 .8.15 1.1.44l.8.8c.3.3.44.68.44 1.1s-.14.8-.44 1.1l-1.95 1.96a.84.84 0 01-.6.25c-.24 0-.45-.08-.61-.25L9.72 6.46a1.44 1.44 0 01-.44-1.1c0-.41.15-.8.44-1.1l.8-.8c.3-.3.68-.44 1.09-.44zm0 11.28c.41 0 .8.14 1.09.42l1.01 1.01c.17.17.25.38.25.61s-.08.44-.25.6L12.09 18a1.44 1.44 0 01-1.09.44c-.41 0-.8-.14-1.09-.44l-1.01-1.01a.84.84 0 01-.25-.6c0-.24.08-.45.25-.61l2-1.96c.28-.28.67-.42 1.09-.42zm-2.65 6.36c.42 0 .8-.14 1.09-.42l1.96-1.96a.84.84 0 00.25-.6c0-.24-.08-.45-.25-.61L9.4 14.1c-.3-.3-.68-.44-1.09-.44-.41 0-.8.15-1.09.44l-.8.8c-.3.3-.44.68-.44 1.1s.15.8.44 1.1l.8.8c.3.28.68.41 1.09.41zm10.6-5.26c-.17-.17-.38-.25-.6-.25-.24 0-.45.08-.61.25l-2 1.96c-.3.3-.44.68-.44 1.09s.14.8.44 1.09l1.01 1.01c.28.28.67.42 1.09.42.41 0 .8-.14 1.09-.42l.8-.8c.3-.3.44-.68.44-1.1s-.14-.8-.44-1.1l-.8-.8a1.44 1.44 0 00-1.09-.44z" />
    </svg>
  );

  const GooglePaLM = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M12 2a10 10 0 0 0-4.32 19.14" />
      <path d="M12 2a10 10 0 0 1 4.32 19.14" />
      <path d="M12 2v8" />
      <path d="M17.68 6.86a6 6 0 0 1-11.36 0" />
      <path d="M4 12H2" />
      <path d="M22 12h-2" />
      <path d="M12 12v10" />
    </svg>
  );

  function IntegrationsSection() {
    return (
      <section>
        <div className="bg-muted dark:bg-background py-24 md:py-32">
          <div className="mx-auto max-w-5xl px-6">
            <div className="relative mx-auto flex max-w-sm items-center justify-between">
              <div className="space-y-6">
                <IntegrationCard position="left-top">
                  <Gemini />
                </IntegrationCard>
                <IntegrationCard position="left-middle">
                  <Replit />
                </IntegrationCard>
                <IntegrationCard position="left-bottom">
                  <MagicUI />
                </IntegrationCard>
              </div>
              <div className="mx-auto my-2 flex w-fit justify-center gap-2">
                <div className="bg-muted relative z-20 rounded-2xl border p-1">
                  <IntegrationCard
                    className="shadow-black-950/10 dark:bg-background size-16 border-black/25 shadow-xl dark:border-white/25 dark:shadow-white/10"
                    isCenter={true}
                  >
                    <PlaceholderLogoIcon />
                  </IntegrationCard>
                </div>
              </div>
              <div
                role="presentation"
                className="absolute inset-1/3 bg-[radial-gradient(var(--dots-color)_1px,transparent_1px)] opacity-50 [--dots-color:black] [background-size:16px_16px] [mask-image:radial-gradient(ellipse_50%_50%_at_50%_50%,#000_70%,transparent_100%)] dark:[--dots-color:white]"
              ></div>

              <div className="space-y-6">
                <IntegrationCard position="right-top">
                  <VSCodium />
                </IntegrationCard>
                <IntegrationCard position="right-middle">
                  <MediaWiki />
                </IntegrationCard>
                <IntegrationCard position="right-bottom">
                  <GooglePaLM />
                </IntegrationCard>
              </div>
            </div>
            <div className="mx-auto mt-12 max-w-lg space-y-6 text-center">
              <h2 className="text-balance text-3xl font-semibold md:text-4xl">
                Integrate with your favorite tools
              </h2>
              <p className="text-muted-foreground">
                Connect seamlessly with popular platforms and services to
                enhance your workflow.
              </p>

              <Button variant="outline" size="sm" asChild>
                <Link href="#">Get Started</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    );
  }

  const IntegrationCard = ({
    children,
    className,
    position,
    isCenter = false,
  }: {
    children: React.ReactNode;
    className?: string;
    position?:
      | "left-top"
      | "left-middle"
      | "left-bottom"
      | "right-top"
      | "right-middle"
      | "right-bottom";
    isCenter?: boolean;
  }) => {
    return (
      <div
        className={cn(
          "bg-background relative flex size-12 rounded-xl border dark:bg-transparent",
          className,
        )}
      >
        <div
          className={cn(
            "relative z-20 m-auto size-fit *:size-6",
            isCenter && "*:size-8",
          )}
        >
          {children}
        </div>
        {position && !isCenter && (
          <div
            className={cn(
              "bg-linear-to-r to-muted-foreground/25 absolute z-10 h-px",
              position === "left-top" &&
                "left-full top-1/2 w-[130px] origin-left rotate-[25deg]",
              position === "left-middle" &&
                "left-full top-1/2 w-[120px] origin-left",
              position === "left-bottom" &&
                "left-full top-1/2 w-[130px] origin-left rotate-[-25deg]",
              position === "right-top" &&
                "bg-linear-to-l right-full top-1/2 w-[130px] origin-right rotate-[-25deg]",
              position === "right-middle" &&
                "bg-linear-to-l right-full top-1/2 w-[120px] origin-right",
              position === "right-bottom" &&
                "bg-linear-to-l right-full top-1/2 w-[130px] origin-right rotate-[25deg]",
            )}
          />
        )}
      </div>
    );
  };
  return IntegrationsSection;
})();

// --- IntegrationsOrbit (integrations-5.tsx) ---
export const IntegrationsOrbit = (() => {
  const LogoIcon = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
    </svg>
  );

  const Gemini = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M12.0001 9.1716L14.8285 6.34313L17.6569 9.1716L14.8285 12.0001L12.0001 9.1716Z" />
      <path d="M9.17157 12.0001L6.34311 14.8285L9.17157 17.6569L12.0001 14.8285L9.17157 12.0001Z" />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22ZM12 20C16.4183 20 20 16.4183 20 12C20 7.58172 16.4183 4 12 4C7.58172 4 4 7.58172 4 12C4 16.4183 7.58172 20 12 20Z"
      />
    </svg>
  );

  const Replit = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M8.28,3.027,3.16,8.147v7.706l5.12,5.12h7.706l5.12-5.12V8.147L15.987,3.027ZM9.033,9.44h5.933v2.373H9.033Zm0,3.56h5.933v2.373H9.033Z" />
    </svg>
  );

  const MagicUI = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M12 3v6M6.343 6.343l4.243 4.243M3 12h6m-1.657 5.657l4.243-4.243M12 21v-6m5.657-4.343l-4.243 4.243M21 12h-6m1.657-5.657l-4.243 4.243" />
    </svg>
  );

  const VSCodium = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M22.5 1.5l-13 10.375v9.625l13 1.5V1.5zm-14.5.5L1.625 8.125 8 12l-6.375 3.875L8 22l6.5-4.5V5z" />
    </svg>
  );

  const MediaWiki = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M4.11 15.35c.42 0 .8-.14 1.09-.42l1.01-1.02a.84.84 0 00.25-.6c0-.23-.08-.44-.25-.6L4.25 10.7a1.44 1.44 0 00-1.09-.44c-.41 0-.8.15-1.1.44l-.8.8c-.3.3-.44.68-.44 1.1s.15.8.44 1.1l.8.8c.3.28.68.41 1.09.41zm15.78 0c.41 0 .8-.14 1.09-.42l.8-.8c.3-.3.44-.68.44-1.1s-.14-.8-.44-1.1l-.8-.8a1.44 1.44 0 00-1.09-.44c-.42 0-.8.15-1.09.44l-1.96 1.97c-.17.16-.25.37-.25.6s.08.44.25.6l1.01 1.02c.28.28.67.42 1.09.42zM12 2.01c.41 0 .8.15 1.1.44l.8.8c.3.3.44.68.44 1.1s-.14.8-.44 1.1l-1.95 1.96a.84.84 0 01-.6.25c-.24 0-.45-.08-.61-.25L9.72 6.46a1.44 1.44 0 01-.44-1.1c0-.41.15-.8.44-1.1l.8-.8c.3-.3.68-.44 1.09-.44zm0 11.28c.41 0 .8.14 1.09.42l1.01 1.01c.17.17.25.38.25.61s-.08.44-.25.6L12.09 18a1.44 1.44 0 01-1.09.44c-.41 0-.8-.14-1.09-.44l-1.01-1.01a.84.84 0 01-.25-.6c0-.24.08-.45.25-.61l2-1.96c.28-.28.67-.42 1.09-.42zm-2.65 6.36c.42 0 .8-.14 1.09-.42l1.96-1.96a.84.84 0 00.25-.6c0-.24-.08-.45-.25-.61L9.4 14.1c-.3-.3-.68-.44-1.09-.44-.41 0-.8.15-1.09.44l-.8.8c-.3.3-.44.68-.44 1.1s.15.8.44 1.1l.8.8c.3.28.68.41 1.09.41zm10.6-5.26c-.17-.17-.38-.25-.6-.25-.24 0-.45.08-.61.25l-2 1.96c-.3.3-.44.68-.44 1.09s.14.8.44 1.09l1.01 1.01c.28.28.67.42 1.09.42.41 0 .8-.14 1.09-.42l.8-.8c.3-.3.44-.68.44-1.1s-.14-.8-.44-1.1l-.8-.8a1.44 1.44 0 00-1.09-.44z" />
    </svg>
  );

  const GooglePaLM = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M12 2a10 10 0 0 0-4.32 19.14" />
      <path d="M12 2a10 10 0 0 1 4.32 19.14" />
      <path d="M12 2v8" />
      <path d="M17.68 6.86a6 6 0 0 1-11.36 0" />
      <path d="M4 12H2" />
      <path d="M22 12h-2" />
      <path d="M12 12v10" />
    </svg>
  );

  function IntegrationsSection() {
    return (
      <section>
        <div className="py-24 md:py-32">
          <div className="mx-auto max-w-5xl px-6">
            <div className="aspect-16/10 group relative mx-auto flex max-w-[22rem] items-center justify-between sm:max-w-sm">
              <div
                role="presentation"
                className="bg-linear-to-b border-foreground/5 absolute inset-0 z-10 aspect-square animate-spin items-center justify-center rounded-full border-t from-lime-500/15 to-transparent to-25% opacity-0 duration-[3.5s] group-hover:opacity-100 dark:from-white/5"
              ></div>
              <div
                role="presentation"
                className="bg-linear-to-b border-foreground/5 absolute inset-16 z-10 aspect-square scale-90 animate-spin items-center justify-center rounded-full border-t from-blue-500/15 to-transparent to-25% opacity-0 duration-[3.5s] group-hover:opacity-100"
              ></div>
              <div className="bg-linear-to-b from-muted-foreground/15 absolute inset-0 flex aspect-square items-center justify-center rounded-full border-t to-transparent to-25%">
                <IntegrationCard className="-translate-x-1/6 absolute left-0 top-1/4 -translate-y-1/4">
                  <Gemini />
                </IntegrationCard>
                <IntegrationCard className="absolute top-0 -translate-y-1/2">
                  <Replit />
                </IntegrationCard>
                <IntegrationCard className="translate-x-1/6 absolute right-0 top-1/4 -translate-y-1/4">
                  <MagicUI />
                </IntegrationCard>
              </div>
              <div className="bg-linear-to-b from-muted-foreground/15 absolute inset-16 flex aspect-square scale-90 items-center justify-center rounded-full border-t to-transparent to-25%">
                <IntegrationCard className="absolute top-0 -translate-y-1/2">
                  <VSCodium />
                </IntegrationCard>
                <IntegrationCard className="absolute left-0 top-1/4 -translate-x-1/4 -translate-y-1/4">
                  <MediaWiki />
                </IntegrationCard>
                <IntegrationCard className="absolute right-0 top-1/4 -translate-y-1/4 translate-x-1/4">
                  <GooglePaLM />
                </IntegrationCard>
              </div>
              <div className="absolute inset-x-0 bottom-0 mx-auto my-2 flex w-fit justify-center gap-2">
                <div className="bg-muted relative z-20 rounded-full border p-1">
                  <IntegrationCard
                    className="shadow-black-950/10 dark:bg-background size-16 border-black/20 shadow-xl dark:border-white/25 dark:shadow-white/15"
                    isCenter={true}
                  >
                    <LogoIcon className="text-blue-500" />
                  </IntegrationCard>
                </div>
              </div>
            </div>
            <div className="bg-linear-to-t from-background relative z-20 mx-auto mt-12 max-w-lg space-y-6 from-55% text-center">
              <h2 className="text-balance text-3xl font-semibold md:text-4xl">
                Integrate with your favorite tools
              </h2>
              <p className="text-muted-foreground">
                Connect seamlessly with popular platforms and services to
                enhance your workflow.
              </p>

              <Button variant="outline" size="sm" asChild>
                <Link href="#">Get Started</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    );
  }

  const IntegrationCard = ({
    children,
    className,
    isCenter = false,
  }: {
    children: React.ReactNode;
    className?: string;
    isCenter?: boolean;
  }) => {
    return (
      <div
        className={cn(
          "relative z-30 flex size-12 rounded-full border bg-white shadow-sm shadow-black/5 dark:bg-white/5 dark:backdrop-blur-md",
          className,
        )}
      >
        <div className={cn("m-auto size-fit *:size-5", isCenter && "*:size-8")}>
          {children}
        </div>
      </div>
    );
  };
  return IntegrationsSection;
})();

// --- IntegrationsList (integrations-6.tsx) ---
export const IntegrationsList = (() => {
  const Gemini = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M12.0001 9.1716L14.8285 6.34313L17.6569 9.1716L14.8285 12.0001L12.0001 9.1716Z" />
      <path d="M9.17157 12.0001L6.34311 14.8285L9.17157 17.6569L12.0001 14.8285L9.17157 12.0001Z" />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22ZM12 20C16.4183 20 20 16.4183 20 12C20 7.58172 16.4183 4 12 4C7.58172 4 4 7.58172 4 12C4 16.4183 7.58172 20 12 20Z"
      />
    </svg>
  );

  const Replit = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M8.28,3.027,3.16,8.147v7.706l5.12,5.12h7.706l5.12-5.12V8.147L15.987,3.027ZM9.033,9.44h5.933v2.373H9.033Zm0,3.56h5.933v2.373H9.033Z" />
    </svg>
  );

  const GooglePaLM = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M12 2a10 10 0 0 0-4.32 19.14" />
      <path d="M12 2a10 10 0 0 1 4.32 19.14" />
      <path d="M12 2v8" />
      <path d="M17.68 6.86a6 6 0 0 1-11.36 0" />
      <path d="M4 12H2" />
      <path d="M22 12h-2" />
      <path d="M12 12v10" />
    </svg>
  );

  const Plus = (props: React.SVGProps<SVGSVGElement>) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <line x1="12" y1="5" x2="12" y2="19"></line>
      <line x1="5" y1="12" x2="19" y2="12"></line>
    </svg>
  );

  function IntegrationsSection() {
    return (
      <section>
        <div className="bg-muted dark:bg-background py-24 md:py-32">
          <div className="mx-auto max-w-5xl px-6">
            <div className="mx-auto max-w-md px-6 [mask-image:radial-gradient(ellipse_100%_100%_at_50%_0%,#000_70%,transparent_100%)]">
              <div className="bg-background dark:bg-muted/50 rounded-xl border px-6 pb-12 pt-3 shadow-xl">
                <Integration
                  icon={<Gemini className="size-6" />}
                  name="Gemini"
                  description="The AI model that powers Google's search engine."
                />
                <Integration
                  icon={<Replit className="size-6" />}
                  name="Replit"
                  description="An online IDE for coding in your browser."
                />
                <Integration
                  icon={<GooglePaLM className="size-6" />}
                  name="Google PaLM"
                  description="Google's next-generation large language model."
                />
              </div>
            </div>
            <div className="mx-auto mt-6 max-w-lg space-y-6 text-center">
              <h2 className="text-balance text-3xl font-semibold md:text-4xl lg:text-5xl">
                Integrate with your favorite LLMs
              </h2>
              <p className="text-muted-foreground">
                Connect seamlessly with popular platforms and services to
                enhance your workflow.
              </p>

              <Button variant="outline" size="sm" asChild>
                <Link href="#">Get Started</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    );
  }

  const Integration = ({
    icon,
    name,
    description,
  }: {
    icon: React.ReactNode;
    name: string;
    description: string;
  }) => {
    return (
      <div className="grid grid-cols-[auto_1fr_auto] items-center gap-3 border-b border-dashed py-3 last:border-b-0">
        <div className="bg-muted border-foreground/5 flex size-12 items-center justify-center rounded-lg border">
          {icon}
        </div>
        <div className="space-y-0.5">
          <h3 className="text-sm font-medium">{name}</h3>
          <p className="text-muted-foreground line-clamp-1 text-sm">
            {description}
          </p>
        </div>
        <Button variant="outline" size="icon" aria-label="Add integration">
          <Plus className="size-4" />
        </Button>
      </div>
    );
  };
  return IntegrationsSection;
})();

// --- IntegrationsMarquee (integration-7.tsx) ---
export const IntegrationsMarquee = (() => {
  function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
  }

  const VscodeLogo = () => <CodeXml className="size-full" />;
  const GitLogo = () => <GitMerge className="size-full" />;
  const DockerLogo = () => <Container className="size-full" />;
  const PostgresLogo = () => <Database className="size-full" />;
  const NpmLogo = () => <Bot className="size-full" />;
  const PenpotLogo = () => <PenTool className="size-full" />;
  const MainLogoIcon = () => <Shapes className="size-full" />;

  const Link = ({ href, children, ...props }: React.ComponentProps<"a">) => (
    <a href={href} {...props}>
      {children}
    </a>
  );

  const Button = React.forwardRef<
    HTMLButtonElement,
    React.ButtonHTMLAttributes<HTMLButtonElement> & {
      asChild?: boolean;
      variant?: string;
      size?: string;
    }
  >(({ className, asChild = false, variant, size, ...props }, ref) => {
    const Comp = asChild ? motion.div : "button";
    const baseClasses =
      "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50";
    const variantClasses =
      "border border-input bg-transparent hover:bg-accent hover:text-accent-foreground";
    const sizeClasses = "h-9 px-3 py-2";
    return (
      <Comp
        className={cn(baseClasses, variantClasses, sizeClasses, className)}
        ref={ref}
        {...props}
      />
    );
  });
  Button.displayName = "Button";

  type InfiniteSliderProps = {
    children: React.ReactNode;
    gap?: number;
    speed?: number;
    speedOnHover?: number;
    direction?: "horizontal" | "vertical";
    reverse?: boolean;
    className?: string;
  };

  function InfiniteSlider({
    children,
    gap = 16,
    speed = 100,
    speedOnHover,
    direction = "horizontal",
    reverse = false,
    className,
  }: InfiniteSliderProps) {
    const [currentSpeed, setCurrentSpeed] = useState(speed);
    const [ref, { width, height }] = useMeasure();
    const translation = useMotionValue(0);
    const [isTransitioning, setIsTransitioning] = useState(false);
    const [key, setKey] = useState(0);

    useEffect(() => {
      let controls;
      const size = direction === "horizontal" ? width : height;
      if (size === 0) return;

      const contentSize = size + gap;
      const from = reverse ? -contentSize / 2 : 0;
      const to = reverse ? 0 : -contentSize / 2;

      const distanceToTravel = Math.abs(to - from);
      const duration = distanceToTravel / currentSpeed;

      if (isTransitioning) {
        const remainingDistance = Math.abs(translation.get() - to);
        const transitionDuration = remainingDistance / currentSpeed;

        controls = animate(translation, [translation.get(), to], {
          ease: "linear",
          duration: transitionDuration,
          onComplete: () => {
            setIsTransitioning(false);
            setKey((prevKey) => prevKey + 1);
          },
        });
      } else {
        translation.set(from);
        controls = animate(translation, [from, to], {
          ease: "linear",
          duration: duration,
          repeat: Infinity,
          repeatType: "loop",
          repeatDelay: 0,
        });
      }

      return () => controls?.stop();
    }, [
      key,
      translation,
      currentSpeed,
      width,
      height,
      gap,
      isTransitioning,
      direction,
      reverse,
    ]);

    const hoverProps = speedOnHover
      ? {
          onHoverStart: () => {
            setIsTransitioning(true);
            setCurrentSpeed(speedOnHover);
          },
          onHoverEnd: () => {
            setIsTransitioning(true);
            setCurrentSpeed(speed);
          },
        }
      : {};

    return (
      <div className={cn("overflow-hidden", className)}>
        <motion.div
          className="flex w-max"
          style={{
            ...(direction === "horizontal"
              ? { x: translation }
              : { y: translation }),
            gap: `${gap}px`,
            flexDirection: direction === "horizontal" ? "row" : "column",
          }}
          ref={ref}
          {...hoverProps}
        >
          {children}
          {children}
        </motion.div>
      </div>
    );
  }

  const IntegrationCard = ({
    children,
    className,
    isCenter = false,
  }: {
    children: React.ReactNode;
    className?: string;
    isCenter?: boolean;
  }) => {
    return (
      <div
        className={cn(
          "bg-background relative z-20 flex size-12 items-center justify-center rounded-full border",
          className,
        )}
      >
        <div
          className={cn(
            "m-auto size-fit text-muted-foreground *:size-5",
            isCenter && "*:size-8",
          )}
        >
          {children}
        </div>
      </div>
    );
  };

  function IntegrationsSection() {
    return (
      <section>
        <div className="bg-muted dark:bg-background py-24 md:py-32">
          <div className="mx-auto max-w-5xl px-6">
            <div className="bg-muted/25 group relative mx-auto max-w-[22rem] items-center justify-between space-y-6 [mask-image:radial-gradient(ellipse_50%_50%_at_50%_50%,#000_70%,transparent_100%)] sm:max-w-md">
              <div
                role="presentation"
                className="absolute inset-0 -z-10 bg-[linear-gradient(to_right,var(--color-border)_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:32px_32px] opacity-50 dark:bg-[linear-gradient(to_right,rgba(255,255,255,0.1)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.1)_1px,transparent_1px)]"
              ></div>

              <div>
                <InfiniteSlider gap={24} speed={20} speedOnHover={10}>
                  <IntegrationCard>
                    <VscodeLogo />
                  </IntegrationCard>
                  <IntegrationCard>
                    <GitLogo />
                  </IntegrationCard>
                  <IntegrationCard>
                    <DockerLogo />
                  </IntegrationCard>
                  <IntegrationCard>
                    <PostgresLogo />
                  </IntegrationCard>
                  <IntegrationCard>
                    <NpmLogo />
                  </IntegrationCard>
                  <IntegrationCard>
                    <PenpotLogo />
                  </IntegrationCard>
                </InfiniteSlider>
              </div>

              <div>
                <InfiniteSlider gap={24} speed={20} speedOnHover={10} reverse>
                  <IntegrationCard>
                    <PostgresLogo />
                  </IntegrationCard>
                  <IntegrationCard>
                    <DockerLogo />
                  </IntegrationCard>
                  <IntegrationCard>
                    <PenpotLogo />
                  </IntegrationCard>
                  <IntegrationCard>
                    <VscodeLogo />
                  </IntegrationCard>
                  <IntegrationCard>
                    <NpmLogo />
                  </IntegrationCard>
                  <IntegrationCard>
                    <GitLogo />
                  </IntegrationCard>
                </InfiniteSlider>
              </div>

              <div>
                <InfiniteSlider gap={24} speed={20} speedOnHover={10}>
                  <IntegrationCard>
                    <NpmLogo />
                  </IntegrationCard>
                  <IntegrationCard>
                    <PenpotLogo />
                  </IntegrationCard>
                  <IntegrationCard>
                    <GitLogo />
                  </IntegrationCard>
                  <IntegrationCard>
                    <DockerLogo />
                  </IntegrationCard>
                  <IntegrationCard>
                    <VscodeLogo />
                  </IntegrationCard>
                  <IntegrationCard>
                    <PostgresLogo />
                  </IntegrationCard>
                </InfiniteSlider>
              </div>

              <div className="absolute inset-0 m-auto flex size-fit justify-center gap-2">
                <IntegrationCard
                  className="shadow-black-950/10 size-16 bg-white/25 shadow-xl backdrop-blur-md backdrop-grayscale dark:border-white/10 dark:bg-black/25 dark:shadow-white/15"
                  isCenter={true}
                >
                  <MainLogoIcon />
                </IntegrationCard>
              </div>
            </div>

            <div className="mx-auto mt-12 max-w-lg space-y-6 text-center">
              <h2 className="text-balance text-3xl font-semibold md:text-4xl">
                Integrate with your favorite tools
              </h2>
              <p className="text-muted-foreground">
                Connect seamlessly with popular platforms and services to
                enhance your workflow.
              </p>

              <Button variant="outline" size="sm" asChild>
                <Link href="#">Get Started</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    );
  }
  return IntegrationsSection;
})();

// --- IntegrationsGridWithText (integrations-8.tsx) ---
export const IntegrationsGridWithText = (() => {
  function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
  }

  const VSCodiumLogo = () => <CodeXml className="size-9" />;
  const GitLogo = () => <GitMerge className="size-9" />;
  const DockerLogo = () => <Container className="size-9" />;
  const PostgresLogo = () => <Database className="size-9" />;
  const OllamaLogo = () => <Bot className="size-9" />;
  const PenpotLogo = () => <PenTool className="size-9" />;

  const Link = ({ href, children, ...props }: React.ComponentProps<"a">) => (
    <a href={href} {...props}>
      {children}
    </a>
  );

  const Button = React.forwardRef<
    HTMLButtonElement,
    React.ButtonHTMLAttributes<HTMLButtonElement> & {
      asChild?: boolean;
      variant?: string;
      size?: string;
    }
  >(({ className, asChild = false, variant, size, ...props }, ref) => {
    const Comp = asChild ? "div" : "button";
    const baseClasses =
      "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50";
    const variantClasses =
      "border border-input bg-transparent hover:bg-accent hover:text-accent-foreground";
    const sizeClasses = "h-9 px-3 py-2";
    return (
      <Comp
        className={cn(baseClasses, variantClasses, sizeClasses, className)}
        ref={ref as React.Ref<any>}
        {...props}
      />
    );
  });
  Button.displayName = "Button";

  const Integration = ({
    icon,
    name,
    description,
  }: {
    icon: React.ReactNode;
    name: string;
    description: string;
  }) => {
    return (
      <div className="hover:bg-muted dark:hover:bg-muted/50 space-y-4 rounded-lg border p-4 transition-colors">
        <div className="flex size-fit items-center justify-center">{icon}</div>
        <div className="space-y-1">
          <h3 className="text-sm font-medium">{name}</h3>
          <p className="text-muted-foreground line-clamp-2 text-sm">
            {description}
          </p>
        </div>
      </div>
    );
  };

  function IntegrationsSection() {
    return (
      <section>
        <div className="bg-muted dark:bg-background py-24 md:py-32">
          <div className="mx-auto flex flex-col px-6 md:grid md:max-w-5xl md:grid-cols-2 md:gap-12">
            <div className="order-last mt-12 flex flex-col gap-12 md:order-first md:mt-0">
              <div className="space-y-6">
                <h2 className="text-balance text-3xl font-semibold md:text-4xl lg:text-5xl">
                  Integrate with your favorite tools
                </h2>
                <p className="text-muted-foreground">
                  Connect seamlessly with popular open-source platforms and
                  services to enhance your workflow.
                </p>
                <Button variant="outline" size="sm" asChild>
                  <Link href="#">Get Started</Link>
                </Button>
              </div>

              <div className="mt-auto grid grid-cols-[auto_1fr] items-center gap-4">
                <div className="bg-background flex aspect-square size-16 items-center justify-center rounded-lg border">
                  <GitLogo />
                </div>
                <blockquote className="text-sm">
                  <p className="italic">
                    "A free and open source distributed version control system
                    designed to handle everything from small to very large
                    projects with speed and efficiency."
                  </p>
                  <div className="mt-2 flex gap-2">
                    <cite className="font-semibold not-italic">Git</cite>
                    <p className="text-muted-foreground">
                      The official website
                    </p>
                  </div>
                </blockquote>
              </div>
            </div>

            <div className="-mx-6 px-6 [mask-image:radial-gradient(ellipse_100%_100%_at_50%_0%,#000_70%,transparent_100%)] sm:mx-auto sm:max-w-md md:-mx-6 md:ml-auto md:mr-0">
              <div className="bg-background dark:bg-muted/50 rounded-2xl border p-3 shadow-lg md:pb-12">
                <div className="grid grid-cols-2 gap-2">
                  <Integration
                    icon={<OllamaLogo />}
                    name="Ollama"
                    description="Run large language models, like Llama 2, locally."
                  />
                  <Integration
                    icon={<DockerLogo />}
                    name="Docker"
                    description="An open platform for developing, shipping, and running applications."
                  />
                  <Integration
                    icon={<PostgresLogo />}
                    name="PostgreSQL"
                    description="A powerful, open source object-relational database system."
                  />
                  <Integration
                    icon={<PenpotLogo />}
                    name="Penpot"
                    description="The open-source design and prototyping platform for product teams."
                  />
                  <Integration
                    icon={<VSCodiumLogo />}
                    name="VSCodium"
                    description="A community-driven, freely-licensed binary distribution of VS Code."
                  />
                  <Integration
                    icon={<GitLogo />}
                    name="Git"
                    description="A free and open source distributed version control system."
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    );
  }
  return IntegrationsSection;
})();

// --- IntegrationsCloud (integrations-grid.tsx) ---
export const IntegrationsCloud = (() => {
  function IntegrationsSection() {
    return (
      <section>
        <div className="bg-muted dark:bg-background py-24 md:py-32">
          <div className="mx-auto max-w-5xl px-6">
            <div className="dark:bg-muted/50 relative mx-auto w-fit">
              <div
                role="presentation"
                className="bg-radial to-muted dark:to-background absolute inset-0 z-10 from-transparent to-75%"
              ></div>
              <div className="mx-auto mb-2 flex w-fit justify-center gap-2">
                <IntegrationCard>
                  <GitHubLogo />
                </IntegrationCard>
                <IntegrationCard>
                  <SlackLogo />
                </IntegrationCard>
              </div>
              <div className="mx-auto my-2 flex w-fit justify-center gap-2">
                <IntegrationCard>
                  <NotionLogo />
                </IntegrationCard>

                <IntegrationCard
                  borderClassName="shadow-black-950/10 shadow-xl border-black/25 dark:border-white/25"
                  className="dark:bg-white/10"
                >
                  <NotionLogo />
                </IntegrationCard>
                <IntegrationCard>
                  <FigmaLogo />
                </IntegrationCard>
              </div>

              <div className="mx-auto flex w-fit justify-center gap-2">
                <IntegrationCard>
                  <DiscordLogo />
                </IntegrationCard>

                <IntegrationCard>
                  <VSCodeLogo />
                </IntegrationCard>
              </div>
            </div>
            <div className="mx-auto mt-6 max-w-lg space-y-6 text-center">
              <h2 className="text-balance text-3xl font-semibold md:text-4xl">
                Integrate with your favorite tools
              </h2>
              <p className="text-muted-foreground">
                Connect seamlessly with popular platforms and services to
                enhance your workflow.
              </p>

              <Button variant="outline" size="sm" asChild>
                <Link href="#">Get Started</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    );
  }

  const IntegrationCard = ({
    children,
    className,
    borderClassName,
  }: {
    children: React.ReactNode;
    className?: string;
    borderClassName?: string;
  }) => {
    return (
      <div
        className={cn(
          "bg-background relative flex size-20 rounded-xl dark:bg-transparent",
          className,
        )}
      >
        <div
          role="presentation"
          className={cn(
            "absolute inset-0 rounded-xl border border-black/20 dark:border-white/25",
            borderClassName,
          )}
        />
        <div className="relative z-20 m-auto size-fit *:size-8">{children}</div>
      </div>
    );
  };

  const GitHubLogo = () => (
    <svg viewBox="0 0 24 24" fill="currentColor" className="text-black">
      <path
        d="M12 0C5.37 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.6.11.793-.26.793-.577 
          0-.285-.01-1.04-.016-2.04-3.338.726-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.757-1.333-1.757-1.09-.745.083-.73.083-.73 
          1.204.085 1.838 1.237 1.838 1.237 1.07 1.835 2.807 1.304 3.492.997.108-.775.42-1.304.763-1.604-2.665-.3-5.466-1.333-5.466-5.93 
          0-1.31.47-2.38 1.236-3.22-.124-.303-.536-1.52.117-3.167 0 0 1.008-.322 3.3 1.23a11.52 11.52 0 0 1 3-.404c1.02.004 2.045.137 
          3 .404 2.29-1.552 3.297-1.23 3.297-1.23.655 1.647.243 2.864.12 3.167.77.84 1.235 1.91 1.235 3.22 
          0 4.61-2.803 5.625-5.475 5.92.431.372.816 1.102.816 2.222 0 1.606-.015 2.9-.015 3.293 
          0 .32.19.694.8.576C20.565 21.796 24 17.3 24 12c0-6.627-5.373-12-12-12z"
      />
    </svg>
  );

  const SlackLogo = () => (
    <svg viewBox="0 0 24 24" fill="currentColor" className="text-purple-600">
      <path d="M5.2 15.7a2.6 2.6 0 1 1 0 5.2H2.6a2.6 2.6 0 1 1 0-5.2H5.2zm1.3-1.3a2.6 2.6 0 1 1 0-5.2h2.6v5.2H6.5zm6.5-6.5a2.6 2.6 0 1 1 5.2 0v2.6h-5.2V7.9zm-1.3 1.3a2.6 2.6 0 1 1 0 5.2H9.1V9.2h2.6zm8.4 0a2.6 2.6 0 1 1 0 5.2h-2.6V9.2h2.6zM15.7 5.2a2.6 2.6 0 1 1 0 5.2h-2.6V5.2h2.6zM9.2 2.6a2.6 2.6 0 1 1 0 5.2H6.6V2.6h2.6z" />
    </svg>
  );

  const NotionLogo = () => (
    <svg viewBox="0 0 24 24" fill="currentColor" className="text-gray-900">
      <path d="M4 3.5l16-1.5 0 19-16 1.5V3.5zm2 3.7v9.6l8 .6v-9.6l-8-.6z" />
    </svg>
  );

  const FigmaLogo = () => (
    <svg viewBox="0 0 24 24" fill="currentColor" className="text-pink-500">
      <path d="M12 4a4 4 0 100 8 4 4 0 000-8zM12 12a4 4 0 100 8 4 4 0 000-8zM4 4a4 4 0 100 8 4 4 0 000-8zM20 4a4 4 0 100 8 4 4 0 000-8zM12 20a4 4 0 100 8 4 4 0 000-8z" />
    </svg>
  );

  const DiscordLogo = () => (
    <svg viewBox="0 0 24 24" fill="currentColor" className="text-indigo-500">
      <path d="M20 0H4C1.79 0 0 1.79 0 4v16c0 2.21 1.79 4 4 4h12l-1-3h5l1 3c2.21 0 4-1.79 4-4V4c0-2.21-1.79-4-4-4z" />
    </svg>
  );

  const VSCodeLogo = () => (
    <svg viewBox="0 0 24 24" fill="currentColor" className="text-blue-600">
      <path d="M4 3l16 9-16 9V3zm4 5v8l6-4-6-4z" />
    </svg>
  );
  return IntegrationsSection;
})();

export default IntegrationsSection;

export { IntegrationsSection as IntegrationsGrid };
