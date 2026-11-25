"use client";

export default function ApplicationsError({ retry }: { retry: () => void }) {
  return (
    <main className="mx-auto flex max-w-4xl flex-col items-start gap-4 p-8">
      <p>Couldn&apos;t load your applications. Is the API running?</p>
      <button type="button" onClick={retry} className="underline">
        Try again
      </button>
    </main>
  );
}
