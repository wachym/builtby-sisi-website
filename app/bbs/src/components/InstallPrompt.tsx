"use client";

import { useCallback, useEffect, useState } from "react";

const DISMISS_KEY = "bbs-install-dismissed";

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

export function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(
    null,
  );
  const [visible, setVisible] = useState(false);
  const [isIos, setIsIos] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (localStorage.getItem(DISMISS_KEY) === "1") return;
    if (window.matchMedia("(display-mode: standalone)").matches) return;

    const onBeforeInstall = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
    };

    window.addEventListener("beforeinstallprompt", onBeforeInstall);

    const showTimer = window.setTimeout(() => {
      // Platform detection happens here rather than in the effect body: the
      // value is only needed once the prompt is shown, and setting it up front
      // would cascade a render before anything is visible.
      const ua = window.navigator.userAgent;
      setIsIos(
        /iPad|iPhone|iPod/.test(ua) ||
          (ua.includes("Mac") && "ontouchend" in document),
      );
      setVisible(true);
    }, 4500);

    return () => {
      window.removeEventListener("beforeinstallprompt", onBeforeInstall);
      window.clearTimeout(showTimer);
    };
  }, []);

  const dismiss = useCallback(() => {
    localStorage.setItem(DISMISS_KEY, "1");
    setVisible(false);
    setDeferredPrompt(null);
  }, []);

  const install = useCallback(async () => {
    if (!deferredPrompt) return;
    await deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    dismiss();
  }, [deferredPrompt, dismiss]);

  if (!visible) return null;

  return (
    <aside className="install-prompt" role="dialog" aria-labelledby="install-prompt-title">
      <div className="install-prompt__inner">
        <p id="install-prompt-title" className="install-prompt__title">
          Install Built By Sisi
        </p>
        <p className="install-prompt__text">
          {isIos && !deferredPrompt
            ? "Tap Share, then “Add to Home Screen” for quick access."
            : "Add this app to your home screen or desktop for faster access."}
        </p>
        <div className="install-prompt__actions">
          {deferredPrompt && (
            <button type="button" className="btn btn--primary" onClick={install}>
              Install
            </button>
          )}
          <button type="button" className="btn btn--ghost" onClick={dismiss}>
            Not now
          </button>
        </div>
      </div>
    </aside>
  );
}
