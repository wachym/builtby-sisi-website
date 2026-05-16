import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Offline — Built By Sisi",
  robots: { index: false, follow: false },
};

export default function OfflinePage() {
  return (
    <div className="offline-page">
      <div className="offline-page__card">
        <Image
          src="/icons/icon-192.png"
          alt=""
          width={80}
          height={80}
          className="offline-page__logo"
          priority
        />
        <p className="offline-page__eyebrow">You&apos;re offline</p>
        <h1 className="offline-page__title">Connection unavailable</h1>
        <p className="offline-page__text">
          Built By Sisi needs a network connection to load the latest content. Check your
          connection, then try again.
        </p>
        <Link href="/" className="btn btn--primary offline-page__btn">
          Try again
        </Link>
        <p className="offline-page__hint">
          Previously visited pages may still be available from cache.
        </p>
      </div>
    </div>
  );
}
