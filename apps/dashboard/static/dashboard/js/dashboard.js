document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;
    const nav = document.getElementById("landingNav");
    const navLinks = document.querySelectorAll(".landing-nav-link");
    const sections = document.querySelectorAll("section[id]");
    const revealItems = document.querySelectorAll("[data-reveal]");
    const counters = document.querySelectorAll("[data-counter]");
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const updateNavShadow = () => {
        if (!nav) return;
        if (window.scrollY > 8) {
            nav.classList.add("is-scrolled");
        } else {
            nav.classList.remove("is-scrolled");
        }
    };

    const setActiveLink = (id) => {
        navLinks.forEach((link) => {
            link.classList.toggle("active", link.getAttribute("href") === `#${id}`);
        });
    };

    const animateCounter = (el) => {
        const target = Number(el.dataset.target || 0);
        const suffix = el.dataset.suffix || "";
        const duration = 1200;
        let start = null;

        const frame = (timestamp) => {
            if (!start) start = timestamp;
            const progress = Math.min((timestamp - start) / duration, 1);
            const currentValue = Math.floor(progress * target);
            el.textContent = `${currentValue.toLocaleString("id-ID")}${suffix}`;
            if (progress < 1) {
                window.requestAnimationFrame(frame);
            }
        };

        window.requestAnimationFrame(frame);
    };

    if (prefersReducedMotion) {
        revealItems.forEach((item) => item.classList.add("is-visible"));
        counters.forEach((counter) => {
            const target = Number(counter.dataset.target || 0);
            const suffix = counter.dataset.suffix || "";
            counter.textContent = `${target.toLocaleString("id-ID")}${suffix}`;
        });
    } else {
        const revealObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        revealObserver.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.2 }
        );

        revealItems.forEach((item) => revealObserver.observe(item));

        const counterObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        animateCounter(entry.target);
                        counterObserver.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.4 }
        );

        counters.forEach((counter) => counterObserver.observe(counter));
    }

    if ("bootstrap" in window && body && nav) {
        new bootstrap.ScrollSpy(body, {
            target: "#landingNav",
            offset: 120,
        });
    }

    const sectionObserver = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    setActiveLink(entry.target.id);
                }
            });
        },
        { rootMargin: "-45% 0px -45% 0px", threshold: 0.01 }
    );

    sections.forEach((section) => sectionObserver.observe(section));

    updateNavShadow();
    window.addEventListener("scroll", updateNavShadow, { passive: true });
});
