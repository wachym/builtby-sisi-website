(function () {
  var header = document.querySelector("[data-header]");
  var nav = document.querySelector(".nav");
  var toggle = document.querySelector("[data-nav-toggle]");
  var menu = document.querySelector("[data-nav-menu]");
  var yearEl = document.querySelector("[data-year]");
  var reveals = document.querySelectorAll("[data-reveal]");
  var contactForm = document.querySelector("[data-contact-form]");
  var navLinks = menu ? Array.from(menu.querySelectorAll('a[href^="#"]')) : [];
  var themeToggle = document.querySelector("[data-theme-toggle]");
  var services = document.querySelector("[data-services]");
  var serviceOutput = document.querySelector("[data-service-output]");
  var modal = document.querySelector("[data-project-modal]");
  var modalClose = document.querySelector("[data-project-close]");
  var tiltItems = Array.from(document.querySelectorAll("[data-tilt]"));
  var parallaxRoot = document.querySelector("[data-parallax-root]");
  var revealSections = Array.from(document.querySelectorAll("main section"));

  var projectDetails = {
    platform: {
      tag: "Platform",
      title: "API-first modernization",
      summary:
        "A staged modernization plan that replaced fragile legacy components while keeping existing operations stable.",
      points: [
        "Progressive migration with zero-downtime cutover strategy.",
        "Contract tests around critical APIs to reduce regressions.",
        "Release metrics dashboard for product and engineering visibility."
      ]
    },
    integrations: {
      tag: "Integrations",
      title: "Observable cross-system integrations",
      summary:
        "An integration architecture designed for resilience, transparency, and easier ownership across teams.",
      points: [
        "Idempotent sync jobs and dead-letter handling for failed events.",
        "Distributed tracing added to key data paths.",
        "Operational runbooks for faster incident response."
      ]
    },
    mvp: {
      tag: "Product",
      title: "MVP delivered with production discipline",
      summary:
        "A launch-ready product foundation balancing speed, product clarity, and long-term maintainability.",
      points: [
        "Component system with accessibility built in from day one.",
        "Performance budget applied to keep interfaces fast.",
        "Developer onboarding docs and handover for internal teams."
      ]
    }
  };

  var serviceDetails = {
    engineering: {
      title: "Product & platform engineering",
      text: "We design and build scalable product foundations with maintainable code, clear boundaries, and reliable release workflows so teams can ship without fear."
    },
    cloud: {
      title: "Cloud & infrastructure",
      text: "From CI/CD to secure environment strategy, we shape infrastructure that is cost-aware, observable, and stable under growth."
    },
    integrations: {
      title: "Integrations & data",
      text: "We connect systems with robust event and data pipelines, giving you retry safety, auditability, and confidence in cross-tool automation."
    },
    direction: {
      title: "Technical direction",
      text: "When priorities are unclear, we bring senior decision support: architecture audits, pragmatic roadmaps, and clear trade-off guidance."
    }
  };

  if (yearEl) {
    yearEl.textContent = String(new Date().getFullYear());
  }

  function setupTheme() {
    var stored = localStorage.getItem("bbs-theme");
    var systemDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    var theme = stored || (systemDark ? "dark" : "light");
    document.body.setAttribute("data-theme", theme);
    if (themeToggle) {
      themeToggle.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
      themeToggle.title = theme === "dark" ? "Switch to light mode" : "Switch to dark mode";
    }
  }

  setupTheme();

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var current = document.body.getAttribute("data-theme") === "dark" ? "dark" : "light";
      var next = current === "dark" ? "light" : "dark";
      document.body.setAttribute("data-theme", next);
      localStorage.setItem("bbs-theme", next);
      themeToggle.setAttribute("aria-pressed", next === "dark" ? "true" : "false");
      themeToggle.title = next === "dark" ? "Switch to light mode" : "Switch to dark mode";
    });
  }

  function getHeaderOffset() {
    if (!header) return 0;
    return header.getBoundingClientRect().height || 0;
  }

  function onScroll() {
    if (!header) return;
    header.classList.toggle("is-scrolled", window.scrollY > 24);
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  if (toggle && menu && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });

    menu.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });

    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      if (!nav.classList.contains("is-open")) return;
      nav.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
      toggle.focus();
    });

    document.addEventListener("click", function (e) {
      if (!nav.classList.contains("is-open")) return;
      if (nav.contains(e.target)) return;
      nav.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    });
  }

  function setActiveNav(hash) {
    if (!navLinks.length) return;
    navLinks.forEach(function (a) {
      if (a.getAttribute("href") === hash) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
  }

  function setupSectionObserver() {
    if (!navLinks.length) return;
    if (!("IntersectionObserver" in window)) return;

    var sections = navLinks
      .map(function (a) {
        var id = (a.getAttribute("href") || "").slice(1);
        return id ? document.getElementById(id) : null;
      })
      .filter(Boolean);

    if (!sections.length) return;

    var current = "";
    var ioNav = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var next = "#" + entry.target.id;
          if (next !== current) {
            current = next;
            setActiveNav(current);
          }
        });
      },
      { rootMargin: "-" + Math.round(getHeaderOffset() + 24) + "px 0px -65% 0px", threshold: 0.01 }
    );

    sections.forEach(function (s) {
      ioNav.observe(s);
    });
  }

  function setupAnchorScrolling() {
    if (!navLinks.length) return;
    navLinks.forEach(function (a) {
      a.addEventListener("click", function (e) {
        var href = a.getAttribute("href");
        if (!href || href.charAt(0) !== "#") return;
        var id = href.slice(1);
        var el = document.getElementById(id);
        if (!el) return;
        e.preventDefault();

        var top = el.getBoundingClientRect().top + window.pageYOffset - getHeaderOffset() - 14;
        window.scrollTo({ top: top, behavior: "smooth" });
        history.pushState(null, "", href);
        setActiveNav(href);
      });
    });
  }

  setupAnchorScrolling();
  setupSectionObserver();

  function setupTilt() {
    if (!tiltItems.length) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    tiltItems.forEach(function (item) {
      function onMove(e) {
        var rect = item.getBoundingClientRect();
        var px = (e.clientX - rect.left) / rect.width;
        var py = (e.clientY - rect.top) / rect.height;
        var rx = (0.5 - py) * 10;
        var ry = (px - 0.5) * 12;
        item.style.transform = "rotateX(" + rx.toFixed(2) + "deg) rotateY(" + ry.toFixed(2) + "deg) translateY(-4px)";
      }

      function reset() {
        item.style.transform = "";
      }

      item.addEventListener("mousemove", onMove);
      item.addEventListener("mouseleave", reset);
      item.addEventListener("blur", reset, true);
    });
  }

  function setupParallaxRoot() {
    if (!parallaxRoot) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    parallaxRoot.addEventListener("mousemove", function (e) {
      var rect = parallaxRoot.getBoundingClientRect();
      var x = (e.clientX - rect.left) / rect.width - 0.5;
      var y = (e.clientY - rect.top) / rect.height - 0.5;
      var images = parallaxRoot.querySelectorAll(".showcase__item img");
      images.forEach(function (img, i) {
        var depth = 8 + i * 2;
        img.style.transform =
          "translate3d(" +
          (x * depth).toFixed(2) +
          "px," +
          (y * depth).toFixed(2) +
          "px,30px)";
      });
    });

    parallaxRoot.addEventListener("mouseleave", function () {
      var images = parallaxRoot.querySelectorAll(".showcase__item img");
      images.forEach(function (img) {
        img.style.transform = "";
      });
    });
  }

  setupTilt();
  setupParallaxRoot();

  function setupRevealChoreography() {
    if (!revealSections.length) return;
    revealSections.forEach(function (section) {
      var items = Array.from(section.querySelectorAll("[data-reveal]"));
      items.forEach(function (el, idx) {
        el.style.setProperty("--reveal-delay", idx * 90 + "ms");
      });
    });
  }

  setupRevealChoreography();

  if (services && serviceOutput) {
    var serviceCards = Array.from(services.querySelectorAll("[data-service]"));
    var outTitle = serviceOutput.querySelector(".service-spotlight__title");
    var outText = serviceOutput.querySelector(".service-spotlight__text");

    function activateService(key) {
      var data = serviceDetails[key];
      if (!data || !outTitle || !outText) return;
      serviceCards.forEach(function (card) {
        card.classList.toggle("is-active", card.getAttribute("data-service") === key);
      });
      outTitle.textContent = data.title;
      outText.textContent = data.text;
    }

    serviceCards.forEach(function (card) {
      card.addEventListener("mouseenter", function () {
        activateService(card.getAttribute("data-service"));
      });
      card.addEventListener("focus", function () {
        activateService(card.getAttribute("data-service"));
      });
      card.addEventListener("click", function () {
        activateService(card.getAttribute("data-service"));
      });
    });
  }

  if (modal) {
    var modalTag = modal.querySelector("[data-project-tag]");
    var modalTitle = modal.querySelector("[data-project-title]");
    var modalSummary = modal.querySelector("[data-project-summary]");
    var modalPoints = modal.querySelector("[data-project-points]");
    var openers = Array.from(document.querySelectorAll("[data-project]"));

    function renderProject(key) {
      var data = projectDetails[key];
      if (!data || !modalTag || !modalTitle || !modalSummary || !modalPoints) return;
      modalTag.textContent = data.tag;
      modalTitle.textContent = data.title;
      modalSummary.textContent = data.summary;
      modalPoints.innerHTML = "";
      data.points.forEach(function (point) {
        var li = document.createElement("li");
        li.textContent = point;
        modalPoints.appendChild(li);
      });
    }

    openers.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var key = btn.getAttribute("data-project");
        renderProject(key);
        if (typeof modal.showModal === "function") modal.showModal();
      });
    });

    if (modalClose) {
      modalClose.addEventListener("click", function () {
        modal.close();
      });
    }

    modal.addEventListener("click", function (e) {
      var rect = modal.getBoundingClientRect();
      var inside =
        e.clientX >= rect.left && e.clientX <= rect.right && e.clientY >= rect.top && e.clientY <= rect.bottom;
      if (!inside) modal.close();
    });
  }

  if (contactForm) {
    contactForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var form = e.currentTarget;
      var name = (form.querySelector('[name="name"]') || {}).value || "";
      var email = (form.querySelector('[name="email"]') || {}).value || "";
      var message = (form.querySelector('[name="message"]') || {}).value || "";

      var to = "builtbysisi@gmail.com";
      var subject = "Project inquiry — " + (name ? name : "Built By Sisi");
      var body =
        "Name: " +
        name +
        "\nEmail: " +
        email +
        "\n\nMessage:\n" +
        message +
        "\n\n— Sent from builtbysisi.com";

      var mailto =
        "mailto:" +
        encodeURIComponent(to) +
        "?subject=" +
        encodeURIComponent(subject) +
        "&body=" +
        encodeURIComponent(body);

      window.location.href = mailto;
    });
  }

  if (!reveals.length || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    reveals.forEach(function (el) {
      el.classList.add("is-visible");
    });
    return;
  }

  var io = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    },
    { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
  );

  reveals.forEach(function (el) {
    io.observe(el);
  });
})();
