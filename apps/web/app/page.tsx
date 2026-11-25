import Link from "next/link";
import { Suspense } from "react";

import { signOut } from "@/auth";
import { apiFetch } from "@/lib/api";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6">
      <h1 className="text-3xl font-semibold">Hearback</h1>
      <Suspense fallback={<p>Loading…</p>}>
        <CurrentUser />
      </Suspense>
    </main>
  );
}

type Me = {
  id: string;
  email: string;
  name: string | null;
};

async function CurrentUser() {
  const me = await apiFetch<Me>("/me");

  return (
    <div className="flex flex-col items-center gap-4">
      <p>Signed in as {me.email}</p>
      <Link href="/applications" className="underline">
        My applications
      </Link>
      <form
        action={async () => {
          "use server";
          await signOut({ redirectTo: "/signin" });
        }}
      >
        <button type="submit" className="underline">
          Sign out
        </button>
      </form>
    </div>
  );
}
