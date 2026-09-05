document.addEventListener("DOMContentLoaded", () => {
  const navLinks = [
    { id: "index", name: "Get started", path: "/", color: "rgba(74, 222, 128, 0.85)", icon: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"></path><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"></path><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"></path><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"></path></svg>` },
    { id: "architecture", name: "Architecture", path: "/architecture/", color: "rgba(56, 189, 248, 0.85)", icon: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 12 12 17 22 12"></polyline><polyline points="2 17 12 22 22 17"></polyline></svg>` },
    { id: "cli", name: "CLI Guide", path: "/cli/", color: "rgba(192, 132, 252, 0.85)", icon: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>` },
    { id: "api", name: "API Reference", path: "/api/", color: "rgba(250, 204, 21, 0.85)", icon: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>` },
    { id: "configuration", name: "Configuration", path: "/configuration/", color: "rgba(251, 146, 60, 0.85)", icon: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>` },
    { id: "development", name: "Development", path: "/development/", color: "rgba(244, 114, 182, 0.85)", icon: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 12-8.5 8.5c-.83.83-2.17.83-3 0 0 0 0 0 0 0a2.12 2.12 0 0 1 0-3L12 9"></path><path d="M17.64 15 22 10.64"></path><path d="m20.91 11.7-1.25-1.25c-.6-.6-.93-1.4-.93-2.25v-.86L16.01 4.6a5.56 5.56 0 0 0-3.94-1.64H11L8.67 5"></path></svg>` }
  ];

  const navContainer = document.createElement("div");
  navContainer.id = "lorex-dynamic-nav";

  navLinks.forEach(link => {
    const a = document.createElement("a");
    a.href = link.path;
    a.className = "nav-item";
    a.style.backgroundColor = link.color;
    a.dataset.id = link.id;

    const iconSpan = document.createElement("span");
    iconSpan.className = "nav-icon";
    iconSpan.innerHTML = link.icon;

    const textSpan = document.createElement("span");
    textSpan.className = "nav-text";
    textSpan.innerText = link.name;
    
    a.appendChild(iconSpan);
    a.appendChild(textSpan);

    // Dynamic Island Tap Logic
    a.addEventListener("click", (e) => {
      if (window.innerWidth <= 768) {
        // If they click the ACTIVE pill while closed, intercept it and expand the menu
        if (a.classList.contains("active") && !navContainer.classList.contains("expanded")) {
          e.preventDefault();
          navContainer.classList.add("expanded");
          return;
        }
      }
      // Otherwise, close the menu and let it navigate naturally
      navContainer.classList.remove("expanded");
    });
    navContainer.appendChild(a);
  });

  // Tap anywhere else on the screen to collapse
  document.addEventListener("click", (e) => {
    if (!navContainer.contains(e.target)) navContainer.classList.remove("expanded");
  });

  document.body.appendChild(navContainer);

  function updateActiveState() {
    const currentPath = window.location.pathname.toLowerCase();
    let hasActive = false;

    document.querySelectorAll("#lorex-dynamic-nav .nav-item").forEach(a => {
      a.classList.remove("active");
      const linkId = a.dataset.id;
      
      if (linkId === "index") {
        if (currentPath === "/" || currentPath === "" || currentPath === "/index.html" || currentPath === "/lore-x/" || currentPath === "/lore-x/index.html") {
          a.classList.add("active");
          hasActive = true;
        }
      } else if (currentPath.includes(`/${linkId}`)) {
        a.classList.add("active");
        hasActive = true;
      }
    });

    if (!hasActive) {
      const fallback = document.querySelector("#lorex-dynamic-nav .nav-item[data-id='index']");
      if (fallback) fallback.classList.add("active");
    }
  }

  function triggerPageTransition() {
    const content = document.querySelector(".md-content") || document.querySelector("main");
    if (content) {
      content.classList.remove("page-transition");
      void content.offsetWidth;
      content.classList.add("page-transition");
    }
  }

  updateActiveState();
  triggerPageTransition();
  
  let lastUrl = location.href;
  new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      updateActiveState();
      triggerPageTransition();
    }
  }).observe(document, { subtree: true, childList: true });
});