---
layout: about
title: about
permalink: /
subtitle: Researcher in Bibliometrics, Science of Science & Social Network Analysis

profile: false # replaced with interactive 3-lens ego-network widget below

selected_papers: true # includes a list of papers marked as "selected={true}"
social: true # includes social icons at the bottom of the page

announcements:
  enabled: true # includes a list of news items
  scrollable: true # adds a vertical scroll bar if there are more than 3 news items
  limit: 5 # leave blank to include all the news in the `_news` folder

latest_posts:
  enabled: false # set to true if you write blog posts
---

<link rel="stylesheet" href="{{ '/assets/css/ego_network.css' | relative_url }}">

<div class="row align-items-start mt-2 mb-4">
  <!-- Right column: Interactive Ego-Network Card (Desktop right, Mobile top) -->
  <div class="col-12 col-md-5 order-md-2 mb-4 mb-md-0">
    <div id="ego-network-container" class="ego-card">
      <div class="ego-header">
        <div class="ego-title-row">
          <span class="ego-card-title">
            <span class="ego-live-badge"></span> Research Network
          </span>
          <span style="font-size: 0.68rem; color: var(--global-text-color-light, #888); font-weight: 500;">3-Lens View</span>
        </div>
        <div class="ego-lens-controls">
          <button class="ego-lens-btn active" data-lens="keywords">Keywords</button>
          <button class="ego-lens-btn" data-lens="methods">Methods</button>
          <button class="ego-lens-btn" data-lens="papers">Papers</button>
        </div>
      </div>
      <div class="ego-canvas-wrap">
        <svg id="ego-network-svg"></svg>
        <div id="ego-tooltip" class="ego-tooltip"></div>
      </div>
      <div class="ego-footer-hint">
        💡 Drag nodes to explore &bull; Switch lenses above
      </div>
    </div>
  </div>

  <!-- Left column: Biography & Research Profile -->
  <div class="col-12 col-md-7 order-md-1">
    <p>
      Hello! I am <strong>Danho Kim</strong>, an academic researcher specializing in 
      <strong>Bibliometrics</strong>, <strong>Science of Science</strong>, and <strong>Social Network Analysis (SNA)</strong>.
    </p>

    <p>
      My research investigates the structural and social dynamics of knowledge production, scholarly collaboration networks, and institutional spaces. Specifically, my work focuses on:
    </p>
    <ul>
      <li><strong>Structural Holes & Collaboration Networks</strong>: Exploring how brokering positions across disciplinary boundaries influence research performance and field maturation.</li>
      <li><strong>Author Embeddedness & Bibliographic Coupling</strong>: Analyzing author-level subject embeddedness and thematic evolution in scientific communities.</li>
      <li><strong>Library Place-Shaping & User Perception</strong>: Phenomenological and empirical investigations into how academic libraries function as socially constructed spaces.</li>
    </ul>

    <p>
      I combine <strong>Social Network Analysis (SNA)</strong>, <strong>Classical Statistics</strong>, and <strong>In-depth Qualitative Inquiry</strong> to bridge quantitative graph metrics with rich contextual interpretations.
    </p>
    <p style="font-size: 0.88rem; color: var(--global-text-color-light, #666);">
      Feel free to interact with my <em>Research Ego-Network</em> on the right to navigate across my core topics, methods, and ongoing publications!
    </p>
  </div>
</div>

<script>
  window.__EGO_DATA__ = {{ site.data.ego_network | jsonify }};
</script>
<script src="{{ '/assets/js/ego_network.js' | relative_url }}"></script>
