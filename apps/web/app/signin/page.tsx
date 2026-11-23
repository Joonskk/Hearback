import { signIn } from "@/auth";

export default function SignInPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6">
      <h1 className="text-3xl font-semibold">Hearback</h1>
      <form
        action={async () => {
          "use server";
          await signIn("google", { redirectTo: "/" });
        }}
      >
        <button
          type="submit"
          className="rounded-full bg-black px-5 py-3 text-white dark:bg-white dark:text-black"
        >
          Sign in with Google
        </button>
      </form>
    </main>
  );
}
