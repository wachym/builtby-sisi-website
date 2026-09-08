"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type MouseEvent as ReactMouseEvent,
  type RefObject,
} from "react";
import type { ProjectKey, ServiceKey } from "@/lib/bbs-data";

const NAV_HASHES = ["#services", "#work", "#process", "#about", "#contact"] as const;

type UseBbsSiteOptions = {
  headerRef: RefObject<HTMLElement | null>;
  navRef: RefObject<HTMLElement | null>;
  menuRef: RefObject<HTMLUListElement | null>;
  parallaxRef: RefObject<HTMLDivElement | null>;
  modalRef: RefObject<HTMLDialogElement | null>;
};

export function useBbsSite({
  headerRef,
  navRef,
  menuRef,
  parallaxRef,
  modalRef,
}: UseBbsSiteOptions) {
  const [navOpen, setNavOpen] = useState(false);
  const [headerScrolled, setHeaderScrolled] = useState(false);
  const [activeNav, setActiveNav] = useState<string>("");
  const [activeService, setActiveService] = useState<ServiceKey>("engineering");
  const [activeProject, setActiveProject] = useState<ProjectKey | null>(null);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [themeReady, setThemeReady] = useState(false);

  const toggleRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const stored = localStorage.getItem("bbs-theme");
    const systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initial = (stored === "dark" || stored === "light" ? stored : systemDark ? "dark" : "light") as
      | "light"
      | "dark";
    // The stored and system preferences only exist in the browser, so they
    // cannot seed useState without diverging from the server-rendered HTML.
    // Reading them once on mount is the intended trade: one extra render in
    // exchange for no hydration mismatch.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTheme(initial);
    setThemeReady(true);
  }, []);

  useEffect(() => {
    if (!themeReady) return;
    document.body.setAttribute("data-theme", theme);
    localStorage.setItem("bbs-theme", theme);
  }, [theme, themeReady]);

  const toggleTheme = useCallback(() => {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  }, []);

  const getHeaderOffset = useCallback(() => {
    return headerRef.current?.getBoundingClientRect().height ?? 0;
  }, [headerRef]);

  useEffect(() => {
    const onScroll = () => setHeaderScrolled(window.scrollY > 24);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const closeNav = useCallback(() => {
    setNavOpen(false);
    toggleRef.current?.setAttribute("aria-expanded", "false");
  }, []);

  const toggleNav = useCallback(() => {
    setNavOpen((open) => {
      const next = !open;
      toggleRef.current?.setAttribute("aria-expanded", next ? "true" : "false");
      return next;
    });
  }, []);

  useEffect(() => {
    if (!navOpen) return;

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      closeNav();
      toggleRef.current?.focus();
    };

    const onClick = (e: MouseEvent) => {
      const nav = navRef.current;
      if (!nav?.contains(e.target as Node)) closeNav();
    };

    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("click", onClick);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("click", onClick);
    };
  }, [navOpen, closeNav, navRef]);

  const scrollToSection = useCallback(
    (hash: string) => {
      const id = hash.slice(1);
      const el = document.getElementById(id);
      if (!el) return;
      const top = el.getBoundingClientRect().top + window.pageYOffset - getHeaderOffset() - 14;
      window.scrollTo({ top, behavior: "smooth" });
      history.pushState(null, "", hash);
      setActiveNav(hash);
    },
    [getHeaderOffset],
  );

  const handleNavClick = useCallback(
    (e: ReactMouseEvent<HTMLAnchorElement>, hash: string) => {
      e.preventDefault();
      closeNav();
      scrollToSection(hash);
    },
    [closeNav, scrollToSection],
  );

  useEffect(() => {
    if (!menuRef.current || !("IntersectionObserver" in window)) return;

    const sections = NAV_HASHES.map((hash) => {
      const id = hash.slice(1);
      return document.getElementById(id);
    }).filter(Boolean) as HTMLElement[];

    if (!sections.length) return;

    let current = "";
    const offset = Math.round(getHeaderOffset() + 24);

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const next = "#" + entry.target.id;
          if (next !== current) {
            current = next;
            setActiveNav(current);
          }
        });
      },
      { rootMargin: `-${offset}px 0px -65% 0px`, threshold: 0.01 },
    );

    sections.forEach((s) => io.observe(s));
    return () => io.disconnect();
  }, [menuRef, getHeaderOffset]);

  useEffect(() => {
    const sections = Array.from(document.querySelectorAll("main section"));
    sections.forEach((section) => {
      const items = Array.from(section.querySelectorAll("[data-reveal]"));
      items.forEach((el, idx) => {
        (el as HTMLElement).style.setProperty("--reveal-delay", idx * 90 + "ms");
      });
    });
  }, []);

  useEffect(() => {
    const reveals = document.querySelectorAll("[data-reveal]");
    if (!reveals.length) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      reveals.forEach((el) => el.classList.add("is-visible"));
      return;
    }

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 },
    );

    reveals.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const tiltItems = Array.from(document.querySelectorAll<HTMLElement>("[data-tilt]"));
    const cleanups: (() => void)[] = [];

    tiltItems.forEach((item) => {
      const onMove = (e: MouseEvent) => {
        const rect = item.getBoundingClientRect();
        const px = (e.clientX - rect.left) / rect.width;
        const py = (e.clientY - rect.top) / rect.height;
        const rx = (0.5 - py) * 10;
        const ry = (px - 0.5) * 12;
        item.style.transform = `rotateX(${rx.toFixed(2)}deg) rotateY(${ry.toFixed(2)}deg) translateY(-4px)`;
      };
      const reset = () => {
        item.style.transform = "";
      };
      item.addEventListener("mousemove", onMove);
      item.addEventListener("mouseleave", reset);
      item.addEventListener("blur", reset, true);
      cleanups.push(() => {
        item.removeEventListener("mousemove", onMove);
        item.removeEventListener("mouseleave", reset);
        item.removeEventListener("blur", reset, true);
      });
    });

    return () => cleanups.forEach((fn) => fn());
  }, []);

  useEffect(() => {
    const root = parallaxRef.current;
    if (!root || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const onMove = (e: MouseEvent) => {
      const rect = root.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      const images = root.querySelectorAll<HTMLImageElement>(".showcase__item img");
      images.forEach((img, i) => {
        const depth = 8 + i * 2;
        img.style.transform = `translate3d(${(x * depth).toFixed(2)}px,${(y * depth).toFixed(2)}px,30px)`;
      });
    };

    const onLeave = () => {
      root.querySelectorAll<HTMLImageElement>(".showcase__item img").forEach((img) => {
        img.style.transform = "";
      });
    };

    root.addEventListener("mousemove", onMove);
    root.addEventListener("mouseleave", onLeave);
    return () => {
      root.removeEventListener("mousemove", onMove);
      root.removeEventListener("mouseleave", onLeave);
    };
  }, [parallaxRef]);

  useEffect(() => {
    if (!activeProject || !modalRef.current) return;
    if (typeof modalRef.current.showModal === "function") {
      modalRef.current.showModal();
    }
  }, [activeProject, modalRef]);

  const openProject = useCallback((key: ProjectKey) => {
    setActiveProject(key);
  }, []);

  const closeProject = useCallback(() => {
    modalRef.current?.close();
    setActiveProject(null);
  }, [modalRef]);

  const handleModalClick = useCallback(
    (e: ReactMouseEvent<HTMLDialogElement>) => {
      const modal = modalRef.current;
      if (!modal) return;
      const rect = modal.getBoundingClientRect();
      const inside =
        e.clientX >= rect.left &&
        e.clientX <= rect.right &&
        e.clientY >= rect.top &&
        e.clientY <= rect.bottom;
      if (!inside) closeProject();
    },
    [closeProject, modalRef],
  );

  const handleContactSubmit = useCallback((e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const name = (form.elements.namedItem("name") as HTMLInputElement)?.value ?? "";
    const email = (form.elements.namedItem("email") as HTMLInputElement)?.value ?? "";
    const message = (form.elements.namedItem("message") as HTMLTextAreaElement)?.value ?? "";

    const to = "builtbysisi@gmail.com";
    const subject = "Project inquiry — " + (name || "Built By Sisi");
    const body = `Name: ${name}\nEmail: ${email}\n\nMessage:\n${message}\n\n— Sent from builtbysisi.com`;

    window.location.href =
      "mailto:" +
      encodeURIComponent(to) +
      "?subject=" +
      encodeURIComponent(subject) +
      "&body=" +
      encodeURIComponent(body);
  }, []);

  const year = new Date().getFullYear();

  return {
    navOpen,
    headerScrolled,
    activeNav,
    activeService,
    activeProject,
    theme,
    themeReady,
    toggleRef,
    year,
    toggleTheme,
    toggleNav,
    closeNav,
    setActiveService,
    openProject,
    closeProject,
    handleModalClick,
    handleNavClick,
    handleContactSubmit,
  };
}
