import type { Metadata } from "next";
import { Crest } from "@/components/Crest";
import { LoginForm } from "./LoginForm";

export const metadata: Metadata = {
  title: "Sign In",
  robots: { index: false, follow: false },
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-forest-950 px-5 py-16">
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0"
        style={{
          backgroundImage:
            "radial-gradient(110% 70% at 50% 0%, rgba(43,115,88,0.35), transparent 60%)",
        }}
      />

      <div className="relative w-full max-w-sm">
        <div className="flex flex-col items-center text-center">
          <Crest size={56} priority className="h-14 w-14" />
          <h1 className="font-display mt-6 text-[1.5rem] leading-tight text-paper">
            Anchor Real Estate Group
          </h1>
          <p className="label-sm mt-2 text-gold-400/80">
            Secretariat Administration
          </p>
        </div>

        <div className="mt-10 bg-paper px-6 py-8 sm:px-8">
          <LoginForm next={next} />
        </div>

        <p className="label-sm mt-8 text-center text-paper/55">
          Authorised officers only
        </p>
      </div>
    </div>
  );
}
