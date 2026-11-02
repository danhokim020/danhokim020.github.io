/**
 * Ego-Network 3-Lens Interactive Visualization (D3.js v7)
 * Designed for Danho Kim's Research Homepage
 * Implements: Keywords | Methods | Papers 3-Lens Perspective Toggle
 */

(function () {
  'use strict';

  // Ensure D3 v7 is loaded
  if (typeof d3 === 'undefined') {
    var script = document.createElement('script');
    script.src = 'https://d3js.org/d3.v7.min.js';
    script.onload = function () {
      initEgoNetwork();
    };
    document.head.appendChild(script);
  } else {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initEgoNetwork);
    } else {
      initEgoNetwork();
    }
  }

  function initEgoNetwork() {
    var container = document.getElementById('ego-network-container');
    if (!container) return;

    var rawData = window.__EGO_DATA__;
    if (!rawData) {
      console.warn('[Ego-Network] No data found in window.__EGO_DATA__');
      return;
    }

    var currentLens = 'keywords'; // Default lens: keywords | methods | papers
    var svg = d3.select('#ego-network-svg');
    var tooltip = d3.select('#ego-tooltip');

    var width = container.clientWidth || 340;
    var height = 330;
    var centerX = width / 2;
    var centerY = height / 2;

    svg.attr('viewBox', [0, 0, width, height]).attr('width', '100%').attr('height', '100%');

    var gRoot = svg.append('g').attr('class', 'ego-root-group');
    var gLinks = gRoot.append('g').attr('class', 'links-group');
    var gNodes = gRoot.append('g').attr('class', 'nodes-group');

    // Color definitions
    var colors = {
      ego: 'var(--global-theme-color, #2563eb)',
      keyword: '#3b82f6', // vibrant blue
      method: '#059669',  // emerald green
      paperPublished: '#d97706', // warm amber
      paperGhost: '#e11d48'      // rose
    };

    // Physics Simulation Setup
    var simulation = d3.forceSimulation()
      .force('link', d3.forceLink().id(function (d) { return d.id; }).distance(function (d) {
        if (d.type === 'ego-primary') return 80;
        if (d.type === 'primary-satellite') return 36;
        return 65;
      }).strength(function (d) {
        if (d.type === 'ego-primary') return 0.8;
        if (d.type === 'primary-satellite') return 0.6;
        return 0.3;
      }))
      .force('charge', d3.forceManyBody().strength(function (d) {
        if (d.isEgo) return -260;
        if (d.isPrimary) return -120;
        return -45;
      }))
      .force('center', d3.forceCenter(centerX, centerY).strength(0.1))
      .force('collision', d3.forceCollide().radius(function (d) {
        return (d.radius || 12) + 6;
      }).iterations(2));

    // Project data based on lens
    function projectGraph(lens) {
      var nodes = [];
      var links = [];
      var nodeMap = {};

      // 1. Center Ego Node
      var egoNode = {
        id: 'ego',
        label: rawData.ego.name || 'Danho, Kim',
        subLabel: rawData.ego.label || 'Researcher',
        type: 'ego',
        isEgo: true,
        isPrimary: false,
        radius: 25,
        fx: centerX,
        fy: centerY
      };
      nodes.push(egoNode);
      nodeMap['ego'] = egoNode;

      if (lens === 'keywords') {
        // Keywords are Primary nodes; Papers are Satellites
        rawData.keywords.forEach(function (kw) {
          var isCore = kw.category === 'core';
          var kwNode = {
            id: kw.id,
            label: kw.label,
            type: 'keyword',
            isPrimary: true,
            isCore: isCore,
            radius: isCore ? 18 : 14,
            color: colors.keyword
          };
          nodes.push(kwNode);
          nodeMap[kw.id] = kwNode;

          links.push({
            source: 'ego',
            target: kw.id,
            type: 'ego-primary',
            weight: isCore ? 2 : 1
          });
        });

        // Papers as satellite dots orbiting keywords
        rawData.papers.forEach(function (p) {
          var pNode = {
            id: p.id + '_sat',
            realId: p.id,
            label: p.short_title || p.title,
            title: p.title,
            venue: p.venue,
            year: p.year,
            status: p.status,
            type: 'paper',
            isSatellite: true,
            radius: p.status === 'published' ? 8 : 7,
            color: p.status === 'published' ? colors.paperPublished : colors.paperGhost
          };
          nodes.push(pNode);

          if (p.keywords && p.keywords.length > 0) {
            p.keywords.forEach(function (kwId) {
              if (nodeMap[kwId]) {
                links.push({
                  source: kwId,
                  target: pNode.id,
                  type: 'primary-satellite'
                });
              }
            });
          }
        });

      } else if (lens === 'methods') {
        // Methods are Primary nodes; Papers are Satellites
        rawData.methods.forEach(function (m) {
          var mNode = {
            id: m.id,
            label: m.label,
            full_name: m.full_name,
            desc: m.desc,
            type: 'method',
            isPrimary: true,
            radius: 20,
            color: colors.method
          };
          nodes.push(mNode);
          nodeMap[m.id] = mNode;

          links.push({
            source: 'ego',
            target: m.id,
            type: 'ego-primary',
            weight: 2
          });
        });

        // Link shared methods between papers
        links.push({
          source: 'm_sna',
          target: 'm_stat',
          type: 'inter-primary',
          weight: 1
        });

        // Papers as satellite dots orbiting methods
        rawData.papers.forEach(function (p) {
          var pNode = {
            id: p.id + '_sat',
            realId: p.id,
            label: p.short_title || p.title,
            title: p.title,
            venue: p.venue,
            year: p.year,
            status: p.status,
            type: 'paper',
            isSatellite: true,
            radius: p.status === 'published' ? 8 : 7,
            color: p.status === 'published' ? colors.paperPublished : colors.paperGhost
          };
          nodes.push(pNode);

          if (p.methods && p.methods.length > 0) {
            p.methods.forEach(function (mId) {
              if (nodeMap[mId]) {
                links.push({
                  source: mId,
                  target: pNode.id,
                  type: 'primary-satellite'
                });
              }
            });
          }
        });

      } else if (lens === 'papers') {
        // Papers (3 projects) are Primary nodes; Keywords & Methods are Satellites
        rawData.papers.forEach(function (p) {
          var isPub = p.status === 'published';
          var pNode = {
            id: p.id,
            label: p.short_title || p.title,
            title: p.title,
            venue: p.venue,
            year: p.year,
            status: p.status,
            type: 'paper',
            isPrimary: true,
            radius: isPub ? 21 : 18,
            color: isPub ? colors.paperPublished : colors.paperGhost
          };
          nodes.push(pNode);
          nodeMap[p.id] = pNode;

          links.push({
            source: 'ego',
            target: p.id,
            type: 'ego-primary',
            weight: isPub ? 2 : 1
          });
        });

        // Connect p2 and p3 (shared SNA/Bibliometrics interest)
        links.push({
          source: 'p2',
          target: 'p3',
          type: 'inter-primary'
        });

        // Add key methods & keywords as satellites around each paper
        rawData.papers.forEach(function (p) {
          // Add primary method satellite
          if (p.methods && p.methods.length > 0) {
            var firstMethodId = p.methods[0];
            var mObj = rawData.methods.find(function (m) { return m.id === firstMethodId; });
            if (mObj) {
              var mSat = {
                id: p.id + '_' + mObj.id,
                label: mObj.label,
                type: 'method',
                isSatellite: true,
                radius: 7,
                color: colors.method
              };
              nodes.push(mSat);
              links.push({ source: p.id, target: mSat.id, type: 'primary-satellite' });
            }
          }

          // Add primary keyword satellite
          if (p.keywords && p.keywords.length > 0) {
            var firstKwId = p.keywords[p.keywords.length - 1]; // take specific sub-keyword
            var kwObj = rawData.keywords.find(function (k) { return k.id === firstKwId; });
            if (kwObj) {
              var kwSat = {
                id: p.id + '_' + kwObj.id,
                label: kwObj.label,
                type: 'keyword',
                isSatellite: true,
                radius: 7,
                color: colors.keyword
              };
              nodes.push(kwSat);
              links.push({ source: p.id, target: kwSat.id, type: 'primary-satellite' });
            }
          }
        });
      }

      return { nodes: nodes, links: links };
    }

    // Render / Update function
    function update(lens) {
      currentLens = lens;
      var graph = projectGraph(lens);

      // Links Join
      var link = gLinks.selectAll('.ego-link')
        .data(graph.links, function (d) {
          var s = typeof d.source === 'object' ? d.source.id : d.source;
          var t = typeof d.target === 'object' ? d.target.id : d.target;
          return s + '-' + t;
        });

      link.exit()
        .transition().duration(400)
        .style('opacity', 0)
        .remove();

      var linkEnter = link.enter().append('line')
        .attr('class', function (d) {
          var cls = 'ego-link';
          if (d.type === 'primary-satellite') cls += ' is-satellite';
          return cls;
        })
        .style('opacity', 0);

      link = linkEnter.merge(link);
      link.transition().duration(500).style('opacity', function (d) {
        return d.type === 'primary-satellite' ? 0.45 : 0.8;
      });

      // Nodes Join
      var node = gNodes.selectAll('.ego-node')
        .data(graph.nodes, function (d) { return d.id; });

      node.exit()
        .transition().duration(400)
        .attr('transform', function () {
          return 'translate(' + centerX + ',' + centerY + ') scale(0.1)';
        })
        .style('opacity', 0)
        .remove();

      var nodeEnter = node.enter().append('g')
        .attr('class', function (d) {
          var cls = 'ego-node node-' + d.type;
          if (d.status === 'ghost') cls += ' is-ghost';
          return cls;
        })
        .attr('transform', function (d) {
          return 'translate(' + (d.x || centerX) + ',' + (d.y || centerY) + ')';
        })
        .call(d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended)
        );

      // Ego Pulse Effect
      nodeEnter.filter(function (d) { return d.isEgo; })
        .append('circle')
        .attr('class', 'pulse-ring')
        .attr('r', 24);

      // Node Circle
      nodeEnter.append('circle')
        .attr('class', function (d) { return d.isEgo ? 'center-node' : 'orbit-node'; })
        .attr('r', 0)
        .style('fill', function (d) { return d.color || colors.ego; })
        .style('stroke', function (d) {
          return d.status === 'ghost' ? colors.paperGhost : '#ffffff';
        });

      // Node Label
      nodeEnter.append('text')
        .attr('class', function (d) {
          return 'ego-label' + (d.isEgo ? ' ego-center-label' : '');
        })
        .attr('dy', function (d) {
          if (d.isEgo) return '0.35em';
          if (d.isSatellite) return '-1.2em';
          return '0.35em';
        })
        .text(function (d) {
          if (d.isEgo) return d.label;
          if (d.isSatellite) return '';
          return d.label;
        })
        .style('opacity', 0);

      node = nodeEnter.merge(node);

      // Transition node radii and labels
      node.select('circle.orbit-node')
        .transition().duration(500)
        .attr('r', function (d) { return d.radius; })
        .style('fill', function (d) { return d.color || colors.ego; });

      node.select('circle.center-node')
        .transition().duration(500)
        .attr('r', function (d) { return d.radius; });

      node.select('text')
        .transition().duration(500)
        .style('opacity', 1)
        .text(function (d) {
          if (d.isEgo) return d.label;
          if (d.isSatellite) return '';
          return d.label;
        });

      // Hover / Tooltip Interaction
      node
        .on('mouseenter', function (event, d) {
          highlightConnections(d);
          showTooltip(event, d);
        })
        .on('mouseleave', function () {
          resetHighlight();
          hideTooltip();
        });

      // Restart Simulation
      simulation.nodes(graph.nodes);
      simulation.force('link').links(graph.links);
      simulation.alpha(0.6).restart();

      simulation.on('tick', function () {
        // Keep Ego strictly centered
        egoNode.x = centerX;
        egoNode.y = centerY;

        link
          .attr('x1', function (d) { return d.source.x; })
          .attr('y1', function (d) { return d.source.y; })
          .attr('x2', function (d) { return d.target.x; })
          .attr('y2', function (d) { return d.target.y; });

        node.attr('transform', function (d) {
          // Constrain within SVG boundary
          var r = d.radius || 12;
          d.x = Math.max(r, Math.min(width - r, d.x));
          d.y = Math.max(r, Math.min(height - r, d.y));
          return 'translate(' + d.x + ',' + d.y + ')';
        });
      });
    }

    // Highlighting
    function highlightConnections(activeNode) {
      var connectedNodeIds = {};
      connectedNodeIds[activeNode.id] = true;

      gLinks.selectAll('.ego-link')
        .classed('highlighted', function (l) {
          var sId = l.source.id;
          var tId = l.target.id;
          var isConnected = sId === activeNode.id || tId === activeNode.id;
          if (isConnected) {
            connectedNodeIds[sId] = true;
            connectedNodeIds[tId] = true;
          }
          return isConnected;
        })
        .style('opacity', function (l) {
          var sId = l.source.id;
          var tId = l.target.id;
          return (sId === activeNode.id || tId === activeNode.id) ? 1 : 0.15;
        });

      gNodes.selectAll('.ego-node')
        .style('opacity', function (n) {
          return connectedNodeIds[n.id] ? 1 : 0.25;
        });
    }

    function resetHighlight() {
      gLinks.selectAll('.ego-link')
        .classed('highlighted', false)
        .style('opacity', function (d) {
          return d.type === 'primary-satellite' ? 0.45 : 0.8;
        });

      gNodes.selectAll('.ego-node')
        .style('opacity', 1);
    }

    // Tooltip formatting
    function showTooltip(event, d) {
      var titleHtml = '';
      var badgeHtml = '';
      var bodyHtml = '';

      if (d.isEgo) {
        titleHtml = d.label;
        badgeHtml = '<span class="ego-tooltip-badge badge-published">EGO</span>';
        bodyHtml = 'Danho Kim &bull; ' + (rawData.ego.affiliation || 'LIS & SNA Researcher');
      } else if (d.type === 'paper') {
        titleHtml = d.title || d.label;
        if (d.status === 'published') {
          badgeHtml = '<span class="ego-tooltip-badge badge-published">Published (' + d.year + ')</span>';
          bodyHtml = d.venue || '';
        } else {
          badgeHtml = '<span class="ego-tooltip-badge badge-ghost">Ghost &bull; ' + (d.venue || 'Under Review') + '</span>';
          bodyHtml = 'Working project / In review';
        }
      } else if (d.type === 'method') {
        titleHtml = d.full_name || d.label;
        badgeHtml = '<span class="ego-tooltip-badge badge-published">METHOD</span>';
        bodyHtml = d.desc || 'Core Analytical Framework';
      } else if (d.type === 'keyword') {
        titleHtml = d.label;
        badgeHtml = '<span class="ego-tooltip-badge badge-published">TOPIC</span>';
        bodyHtml = d.isCore ? 'Core Research Domain' : 'Investigated Sub-field';
      }

      var html = '<div class="ego-tooltip-header">' +
        '<span class="ego-tooltip-title">' + titleHtml + '</span>' +
        badgeHtml +
        '</div>' +
        '<div class="ego-tooltip-body">' + bodyHtml + '</div>';

      tooltip.html(html).classed('visible', true);
    }

    function hideTooltip() {
      tooltip.classed('visible', false);
    }

    // Drag handlers
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      if (d.isEgo) return; // Keep Ego fixed at center
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      if (!d.isEgo) {
        d.fx = null;
        d.fy = null;
      }
    }

    // Button event listeners
    var buttons = document.querySelectorAll('.ego-lens-btn');
    buttons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        buttons.forEach(function (b) { b.classList.remove('active'); });
        this.classList.add('active');
        var lens = this.getAttribute('data-lens');
        update(lens);
      });
    });

    // Initial render
    update('keywords');

    // Handle Window Resize
    window.addEventListener('resize', function () {
      var newWidth = container.clientWidth || 340;
      if (Math.abs(newWidth - width) > 10) {
        width = newWidth;
        centerX = width / 2;
        svg.attr('viewBox', [0, 0, width, height]);
        simulation.force('center', d3.forceCenter(centerX, centerY));
        simulation.alpha(0.3).restart();
      }
    });
  }
})();
