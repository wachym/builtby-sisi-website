"use client";

import Image from "next/image";
import { useRef } from "react";
import {
  projectDetails,
  serviceCards,
  serviceDetails,
  workItems,
} from "@/lib/bbs-data";
import { useBbsSite } from "@/hooks/use-bbs-site";

const NAV_LINKS = [
  { hash: "#services", label: "Services" },
  { hash: "#work", label: "Work" },
  { hash: "#process", label: "Process" },
  { hash: "#about", label: "About" },
  { hash: "#contact", label: "Contact", cta: true },
] as const;

export function BbsSite() {
  const headerRef = useRef<HTMLElement>(null);
  const navRef = useRef<HTMLElement>(null);
  const menuRef = useRef<HTMLUListElement>(null);
  const parallaxRef = useRef<HTMLDivElement>(null);
  const modalRef = useRef<HTMLDialogElement>(null);

  const {
    navOpen,
    headerScrolled,
    activeNav,
    activeService,
    activeProject,
    theme,
    toggleRef,
    year,
    toggleTheme,
    toggleNav,
    setActiveService,
    openProject,
    closeProject,
    handleModalClick,
    handleNavClick,
    handleContactSubmit,
  } = useBbsSite({ headerRef, navRef, menuRef, parallaxRef, modalRef });

  const spotlight = serviceDetails[activeService];
  const project = activeProject ? projectDetails[activeProject] : null;

  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>

      <header
        ref={headerRef}
        className={`site-header${headerScrolled ? " is-scrolled" : ""}`}
      >
        <div className="container header__inner">
          <a className="logo" href="#top" aria-label="Built By Sisi home">
            <Image
              className="logo__image"
              src="/BBS.png"
              alt=""
              width={150}
              height={150}
              priority
              sizes="96px"
            />
          </a>
          <nav
            ref={navRef}
            className={`nav${navOpen ? " is-open" : ""}`}
            aria-label="Primary"
          >
            <button
              type="button"
              className="theme-toggle"
              aria-label="Toggle dark mode"
              title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
              aria-pressed={theme === "dark"}
              onClick={toggleTheme}
            >
              <span className="theme-toggle__icon" aria-hidden="true">
                ◐
              </span>
            </button>
            <button
              ref={toggleRef}
              type="button"
              className="nav__toggle"
              aria-expanded={navOpen}
              aria-controls="nav-menu"
              onClick={toggleNav}
            >
              <span className="nav__toggle-bar" />
              <span className="visually-hidden">Menu</span>
            </button>
            <ul id="nav-menu" ref={menuRef} className="nav__list">
              {NAV_LINKS.map((link) => (
                <li key={link.hash}>
                  <a
                    href={link.hash}
                    className={"cta" in link && link.cta ? "nav__cta" : undefined}
                    aria-current={activeNav === link.hash ? "page" : undefined}
                    onClick={(e) => handleNavClick(e, link.hash)}
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>

      <main id="main">
        <section id="top" className="hero">
          <div className="hero__glow" aria-hidden="true" />
          <div className="container hero__grid">
            <div className="hero__copy">
              <p className="eyebrow reveal" data-reveal>
                Software studio
              </p>
              <h1 className="hero__title reveal" data-reveal>
                Thoughtful engineering
                <br />
                <em>for serious products.</em>
              </h1>
              <p className="hero__lead reveal" data-reveal>
                We partner with founders and teams to design, build, and evolve
                software that stays fast, maintainable, and aligned with your
                business—without the noise.
              </p>
              <div className="hero__actions reveal" data-reveal>
                <a className="btn btn--primary" href="#contact" onClick={(e) => handleNavClick(e, "#contact")}>
                  Start a conversation
                </a>
                <a className="btn btn--ghost" href="#services" onClick={(e) => handleNavClick(e, "#services")}>
                  Explore services
                </a>
              </div>

              <div className="trust reveal" data-reveal aria-label="Trusted by">
                <p className="trust__label">Trusted by teams shipping real software</p>
                <div className="trust__row" role="list">
                  {["Fintech", "SaaS", "E-commerce", "Healthcare"].map((label) => (
                    <span key={label} className="trust__logo" role="listitem">
                      {label}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            <aside className="hero__panel reveal" data-reveal aria-label="Highlights">
              <ul className="hero__stats">
                <li>
                  <span className="hero__stat-value">End-to-end</span>
                  <span className="hero__stat-label">From discovery to production</span>
                </li>
                <li>
                  <span className="hero__stat-value">Quality-first</span>
                  <span className="hero__stat-label">Tests, reviews, observability</span>
                </li>
                <li>
                  <span className="hero__stat-value">Clear comms</span>
                  <span className="hero__stat-label">Predictable delivery you can trust</span>
                </li>
              </ul>
            </aside>
          </div>
        </section>

        <section id="services" className="section section--services">
          <div className="container">
            <header className="section__head reveal" data-reveal>
              <p className="eyebrow">What we do</p>
              <h2 className="section__title">Capabilities built around your roadmap.</h2>
              <p className="section__intro">
                Whether you are launching something new or hardening what you
                already run, we embed as an extension of your team.
              </p>
            </header>
            <div className="cards">
              {serviceCards.map((card) => (
                <article
                  key={card.key}
                  className={`card reveal${activeService === card.key ? " is-active" : ""}`}
                  data-reveal
                  data-service={card.key}
                  tabIndex={0}
                  onMouseEnter={() => setActiveService(card.key)}
                  onFocus={() => setActiveService(card.key)}
                  onClick={() => setActiveService(card.key)}
                >
                  <span className="card__index">{card.index}</span>
                  <h3 className="card__title">{card.title}</h3>
                  <p className="card__text">{card.text}</p>
                </article>
              ))}
            </div>
            <aside className="service-spotlight reveal" data-reveal aria-live="polite">
              <p className="service-spotlight__eyebrow">Service spotlight</p>
              <h3 className="service-spotlight__title">{spotlight.title}</h3>
              <p className="service-spotlight__text">{spotlight.text}</p>
            </aside>
          </div>
        </section>

        <section id="work" className="section section--work">
          <div className="container">
            <header className="section__head reveal" data-reveal>
              <p className="eyebrow">Selected work</p>
              <h2 className="section__title">Elegant builds. Measurable outcomes.</h2>
              <p className="section__intro">
                A few example engagements to show how we think. Replace these with
                your real case studies as you grow.
              </p>
            </header>

            <div className="work">
              {workItems.map((item) => (
                <article key={item.key} className="work__item reveal" data-reveal>
                  <p className="work__tag">{item.tag}</p>
                  <h3 className="work__title">{item.title}</h3>
                  <ul className="work__bullets">
                    {item.bullets.map((bullet) => (
                      <li key={bullet}>{bullet}</li>
                    ))}
                  </ul>
                  <button
                    className="work__link"
                    type="button"
                    data-project={item.key}
                    aria-label={item.ariaLabel}
                    onClick={() => openProject(item.key)}
                  >
                    View project details
                  </button>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="section section--showcase" aria-label="Software capability showcase">
          <div className="container">
            <header className="section__head reveal" data-reveal>
              <p className="eyebrow">Capability showcase</p>
              <h2 className="section__title">We design real product surfaces, not just slides.</h2>
              <p className="section__intro">
                Example visual directions we build for clients: product dashboards, platform architecture, and
                mobile-ready execution views.
              </p>
            </header>

            <div className="showcase" ref={parallaxRef} data-parallax-root>
              <ShowcaseItem
                src="/assets/engineering-3d.svg"
                alt="3D software product engineering visualization"
                title="Product Engineering Systems"
                description="We design connected product surfaces across frontend, services, and deployment layers."
              />
              <ShowcaseItem
                src="/assets/automation-3d.svg"
                alt="3D automation and workflow orchestration visualization"
                title="Automation & AI Workflows"
                description="From business events to actions, we automate repeatable operations with resilient flow control."
              />
              <ShowcaseItem
                src="/assets/platform-3d.svg"
                alt="3D cloud platform and observability visualization"
                title="Cloud Platform Capability"
                description="Scalable cloud architecture, observability, and release confidence designed into the platform."
              />
            </div>
          </div>
        </section>

        <section className="section section--capability-wall" aria-label="Capability gallery">
          <div className="container">
            <header className="section__head reveal" data-reveal>
              <p className="eyebrow">Inside the build</p>
              <h2 className="section__title">From concept to production architecture.</h2>
            </header>
            <div className="capability-wall">
              <article className="cap-card cap-card--wide reveal" data-reveal>
                <img src="/assets/engineering-3d.svg" alt="3D software systems composition" loading="lazy" />
                <div className="cap-card__overlay">
                  <h3>Full-stack Product Delivery</h3>
                  <p>UX, frontend, backend, data, and release systems built as one coherent product engine.</p>
                </div>
              </article>
              <article className="cap-card reveal" data-reveal>
                <img src="/assets/automation-3d.svg" alt="3D automation orchestration concept" loading="lazy" />
                <div className="cap-card__overlay">
                  <h3>Automation Pipelines</h3>
                </div>
              </article>
              <article className="cap-card reveal" data-reveal>
                <img src="/assets/platform-3d.svg" alt="3D cloud platform concept" loading="lazy" />
                <div className="cap-card__overlay">
                  <h3>Cloud Reliability Architecture</h3>
                </div>
              </article>
            </div>
          </div>
        </section>

        <section id="process" className="section section--process">
          <div className="container process">
            <header className="section__head reveal" data-reveal>
              <p className="eyebrow">How we work</p>
              <h2 className="section__title">A calm, deliberate delivery rhythm.</h2>
            </header>
            <ol className="process__steps">
              {[
                {
                  num: "1",
                  title: "Align",
                  text: "We clarify outcomes, constraints, and success metrics so scope matches reality—not slides.",
                },
                {
                  num: "2",
                  title: "Shape",
                  text: "Thin slices of design and engineering de-risk the unknown early, with visible increments you can react to.",
                },
                {
                  num: "3",
                  title: "Ship",
                  text: "Production releases with monitoring, docs, and handover so your team owns the result with confidence.",
                },
              ].map((step) => (
                <li key={step.num} className="process__step reveal" data-reveal>
                  <span className="process__num">{step.num}</span>
                  <div>
                    <h3>{step.title}</h3>
                    <p>{step.text}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section id="about" className="section section--about">
          <div className="container about">
            <div className="about__copy reveal" data-reveal>
              <p className="eyebrow">About</p>
              <h2 className="section__title">Built By Sisi</h2>
              <p>
                We are a software company focused on craft: readable code, honest
                timelines, and interfaces that respect the people who use them.
                Our clients range from early-stage startups to established teams
                modernizing critical systems.
              </p>
              <p>
                If you value precision over hype, we would love to hear what you
                are building.
              </p>
            </div>
            <blockquote className="about__quote reveal" data-reveal>
              <p>
                &ldquo;Software should feel inevitable—simple surfaces hiding careful
                work.&rdquo;
              </p>
              <footer>— Built By Sisi</footer>
            </blockquote>
          </div>
        </section>

        <section className="section section--testimonials" aria-label="Testimonials">
          <div className="container">
            <header className="section__head reveal" data-reveal>
              <p className="eyebrow">What teams say</p>
              <h2 className="section__title">Trusted for clarity and follow-through.</h2>
            </header>

            <div className="testimonials">
              <figure className="quote reveal" data-reveal>
                <blockquote>
                  &ldquo;A calm, senior partner—clear decisions, clean delivery, and no surprises.&rdquo;
                </blockquote>
                <figcaption>Founder, product studio</figcaption>
              </figure>
              <figure className="quote reveal" data-reveal>
                <blockquote>
                  &ldquo;The codebase got simpler, our releases got safer, and the team leveled up.&rdquo;
                </blockquote>
                <figcaption>Engineering lead, SaaS</figcaption>
              </figure>
            </div>
          </div>
        </section>

        <section id="contact" className="section section--contact">
          <div className="container contact">
            <div className="contact__inner reveal" data-reveal>
              <p className="eyebrow">Contact</p>
              <h2 className="section__title">Tell us about your next release.</h2>
              <p className="contact__lead">
                Share a few details and we will reply with next steps. (This is a
                no-backend form that opens your email client.)
              </p>
              <form className="contact__form" onSubmit={handleContactSubmit}>
                <div className="field">
                  <label htmlFor="name">Name</label>
                  <input id="name" name="name" type="text" autoComplete="name" required />
                </div>
                <div className="field">
                  <label htmlFor="email">Email</label>
                  <input id="email" name="email" type="email" autoComplete="email" required />
                </div>
                <div className="field">
                  <label htmlFor="message">What are you building?</label>
                  <textarea id="message" name="message" rows={5} required />
                </div>
                <div className="contact__actions">
                  <button className="btn btn--primary btn--large" type="submit">
                    Send message
                  </button>
                  <a className="btn btn--ghost btn--large" href="mailto:builtbysisi@gmail.com">
                    Email instead
                  </a>
                </div>
                <p className="contact__fineprint">
                  Prefer email? Reach us at{" "}
                  <a href="mailto:builtbysisi@gmail.com">builtbysisi@gmail.com</a>.
                </p>
              </form>
            </div>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="container footer__inner">
          <p className="footer__brand">Built By Sisi</p>
          <p className="footer__meta">© {year} Built By Sisi. All rights reserved.</p>
        </div>
      </footer>

      <dialog
        ref={modalRef}
        className="project-modal"
        onClick={handleModalClick}
        onClose={closeProject}
      >
        {project && (
          <article className="project-modal__card" role="document">
            <button
              type="button"
              className="project-modal__close"
              aria-label="Close project details"
              onClick={closeProject}
            >
              ×
            </button>
            <p className="project-modal__tag">{project.tag}</p>
            <h3 className="project-modal__title">{project.title}</h3>
            <p className="project-modal__summary">{project.summary}</p>
            <ul className="project-modal__points">
              {project.points.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </article>
        )}
      </dialog>
    </>
  );
}

function ShowcaseItem({
  src,
  alt,
  title,
  description,
}: {
  src: string;
  alt: string;
  title: string;
  description: string;
}) {
  return (
    <article className="showcase__item reveal" data-reveal data-tilt>
      <span className="showcase__shine" aria-hidden="true" />
      <img src={src} alt={alt} loading="lazy" width={960} height={600} />
      <div className="showcase__meta">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </article>
  );
}

