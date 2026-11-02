---
layout: page
permalink: /publications/
title: publications
nav: true
nav_order: 1
---

<!-- _pages/publications.md -->

<style>
  /* Hide Bib and toggle buttons */
  a.bibtex, .bibtex.btn, a.btn.bibtex, a.abstract.btn {
    display: none !important;
  }
  /* Show abstract directly under publication with elegant styling */
  .publications .abstract.hidden,
  .publications .abstract {
    display: block !important;
    margin-top: 0.5rem;
    margin-bottom: 0.8rem;
    padding: 0.5rem 0.85rem;
    border-left: 3px solid var(--global-theme-color, #2563eb);
    background: var(--global-card-bg-color, rgba(0, 0, 0, 0.02));
    border-radius: 0 6px 6px 0;
    font-size: 0.86rem;
    line-height: 1.55;
    color: var(--global-text-color, #374151);
  }
</style>

<div class="publications">

{% bibliography %}

</div>
