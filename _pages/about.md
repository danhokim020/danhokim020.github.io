---
layout: about
title: about
permalink: /
subtitle: Master's Student

profile: false # replaced with interactive 3-lens ego-network widget below

selected_papers: true # includes a list of papers marked as "selected={true}"
social: false # includes social icons at the bottom of the page

announcements:
  enabled: true # includes a list of news items
  scrollable: true # adds a vertical scroll bar if there are more than 3 news items
  limit: 5 # leave blank to include all the news in the `_news` folder

latest_posts:
  enabled: false # set to true if you write blog posts
---

<link rel="stylesheet" href="{{ '/assets/css/ego_network.css' | relative_url }}">

<div class="ego-layout-row">
  <!-- Left column: Interactive Ego-Network Card -->
  <div class="ego-layout-left">
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

  <!-- Right column: Biography & Research Profile (managed via _csv/about.csv) -->
  <div class="ego-layout-right">
    {% if site.data.about.paragraphs and site.data.about.paragraphs.size > 0 %}
      {% for p in site.data.about.paragraphs %}
        <p>{{ p }}</p>
      {% endfor %}
    {% else %}
      <p>
        I am a master’s student advised by Professor <a href="https://snis.yonsei.ac.kr/" target="_blank" rel="noopener noreferrer">Ji-Hong Park</a>.
      </p>

      <p>
        I study social networks, scholarly communication, bibliometrics, and the science of science.
      </p>

      <p>
        Network theory moves beyond the dualism of individual attributes and social institutions and norms, explaining human interaction at the meso level. From this perspective, I examine scholarly communication as a relational phenomenon.
      </p>
    {% endif %}

    <p style="font-size: 0.88rem; color: var(--global-text-color-light, #666);">
      {{ site.data.about.footer_note | default: "Feel free to interact with my <em>Research Ego-Network</em> on the left to navigate across my core topics, methods, and ongoing publications!" }}
    </p>
  </div>
</div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
  window.__EGO_DATA__ = {{ site.data.ego_network | jsonify }};
</script>
<script src="{{ '/assets/js/ego_network.js' | relative_url }}"></script>
