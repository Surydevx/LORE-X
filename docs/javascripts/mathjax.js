window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  }
};

// Re-render math when navigating between pages via instant navigation
if (typeof document$ !== "undefined") {
  document$.subscribe(() => {
    MathJax.typesetPromise();
  });
}