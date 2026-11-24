import Link from "next/link";

export default function NotFound() {
  return (
    <main className="grid min-h-screen place-items-center bg-paper px-6 text-ink">
      <div className="text-center">
        <p className="font-serif text-4xl">That page is not on the map</p>
        <Link className="mt-4 inline-block text-sm underline" href="/">
          Back to the map
        </Link>
      </div>
    </main>
  );
}
