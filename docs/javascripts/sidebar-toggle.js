document.addEventListener("DOMContentLoaded", () => {
  // 1. Navigation Configuration
  const navLinks = [
    { id: "index", name: "Get started", path: "/", color: "rgba(74, 222, 128, 0.85)" },
    { id: "architecture", name: "Architecture", path: "/architecture/", color: "rgba(56, 189, 248, 0.85)" },
    { id: "cli", name: "CLI Guide", path: "/cli/", color: "rgba(192, 132, 252, 0.85)" },
    { id: "api", name: "API Reference", path: "/api/", color: "rgba(250, 204, 21, 0.85)" },
    { id: "configuration", name: "Configuration", path: "/configuration/", color: "rgba(251, 146, 60, 0.85)" },
    { id: "development", name: "Development", path: "/development/", color: "rgba(244, 114, 182, 0.85)" }
  ];

  // 2. Build the DOM nodes
  const navContainer = document.createElement("div");
  navContainer.id = "lorex-dynamic-nav";

  navLinks.forEach(link => {
    const a = document.createElement("a");
    a.href = link.path;
    a.className = "nav-item";
    a.style.backgroundColor = link.color;
    
    a.dataset.id = link.id;
    a.dataset.path = link.path;

    const textSpan = document.createElement("span");
    textSpan.className = "nav-text";
    textSpan.innerText = link.name;
    
    a.appendChild(textSpan);
    navContainer.appendChild(a);
  });

  const headerInner = document.querySelector(".md-header__inner");
  const navWrapper = document.createElement("div");
  navWrapper.className = "lorex-nav-wrapper";

  // 3. Responsive DOM Placement (Moves dock based on viewport)
  function placeDock() {
    if (window.innerWidth <= 768) {
      // Mobile: Escape the header trap, attach directly to body
      document.body.appendChild(navContainer);
    } else {
      // Desktop: Place neatly inside the header
      if (headerInner) {
        const title = headerInner.querySelector(".md-header__title");
        if (title) title.parentNode.insertBefore(navWrapper, title.nextSibling);
        else headerInner.appendChild(navWrapper);
        navWrapper.appendChild(navContainer);
      } else {
        document.body.appendChild(navContainer);
      }
    }
  }

  // Run on initial load and whenever the user resizes the window
  placeDock();
  window.addEventListener("resize", placeDock);

  // 4. SPA Routing Updates (Handles Instant Navigation)
  function updateActiveState() {
    let currentPath = window.location.pathname.toLowerCase();
    currentPath = currentPath.replace(/\/index\.html$/, "").replace(/\/$/, "") || "/";

    document.querySelectorAll("#lorex-dynamic-nav .nav-item").forEach(a => {
      const linkId = a.dataset.id;
      let targetPath = a.dataset.path.toLowerCase().replace(/\/$/, "") || "/";
      const isHome = (linkId === "index" && currentPath === "/");
      const isExactMatch = (linkId !== "index" && currentPath === targetPath);

      if (isHome || isExactMatch) a.classList.add("active");
      else a.classList.remove("active");
    });
  }

  updateActiveState();
  
  // Watch for MkDocs Instant Loading URL changes without full page reload
  let lastUrl = location.href;
  new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      updateActiveState();
    }
  }).observe(document, { subtree: true, childList: true });
});