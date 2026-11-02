/**
 * Ego-Network 3-Lens Interactive Visualization (D3.js v7)
 * Tailored for Danho Kim's Research Homepage
 * Fully supports CSV auto-sync, dynamic co-occurrence links, and On-going status
 */

(function () {
  'use strict';

  // 1. Built-in Fallback Data (reflecting user's latest CSV updates)
  var DEFAULT_EGO_DATA = {
    ego: {
      name: "Danho, Kim",
      label: "Bibliometrics & SNA Researcher",
      affiliation: "Library & Information Science"
    },
    keywords: [
      { id: "kw_bibliometrics", label: "Bibliometrics", category: "core", linked_papers: ["Authors Embeddedness Project"] },
      { id: "kw_science_of_science", label: "Science of Science", category: "core", linked_papers: ["Structural Holes Project"] },
      { id: "kw_social_network_analysis", label: "Social Network Analysis", category: "core", linked_papers: ["Structural Holes Project", "Authors Embeddedness Project"] },
      { id: "kw_library_as_place", label: "Library as Place", category: "sub", linked_papers: ["Library Place-Shaping (2026)"] },
      { id: "kw_academic_library", label: "Academic Library", category: "sub", linked_papers: ["Library Place-Shaping (2026)"] },
      { id: "kw_perception_of_libraries", label: "Perception of Libraries", category: "sub", linked_papers: ["Library Place-Shaping (2026)"] },
      { id: "kw_structural_holes", label: "Structural Holes", category: "sub", linked_papers: ["Structural Holes Project"] },
      { id: "kw_collaboration", label: "Collaboration", category: "sub", linked_papers: ["Structural Holes Project"] },
      { id: "kw_interdisciplinary_research", label: "Interdisciplinary Research", category: "sub", linked_papers: ["Structural Holes Project"] },
      { id: "kw_field_maturation", label: "Field Maturation", category: "sub", linked_papers: ["Structural Holes Project"] },
      { id: "kw_research_performance", label: "Research Performance", category: "sub", linked_papers: ["Structural Holes Project", "Authors Embeddedness Project"] },
      { id: "kw_network_embeddedness", label: "Network Embeddedness", category: "sub", linked_papers: ["Authors Embeddedness Project"] },
      { id: "kw_bibliographic_coupling", label: "Bibliographic Coupling", category: "sub", linked_papers: ["Authors Embeddedness Project"] },
      { id: "kw_collaboration_dynamics", label: "Collaboration Dynamics", category: "sub", linked_papers: ["Authors Embeddedness Project"] }
    ],
    methods: [
      { id: "m_in_depth_interview", label: "In-depth Interview", full_name: "In-depth Interview", desc: "Qualitative Phenomenological Inquiry", linked_papers: ["Library Place-Shaping (2026)"] },
      { id: "m_ipa", label: "IPA", full_name: "Interpretative Phenomenological Analysis", desc: "Phenomenological Analysis", linked_papers: ["Library Place-Shaping (2026)"] },
      { id: "m_sna", label: "SNA", full_name: "Social Network Analysis", desc: "Network metrics, structural holes, centralities", linked_papers: ["Structural Holes Project", "Authors Embeddedness Project"] },
      { id: "m_classical_statistics", label: "Classical statistics", full_name: "Classical statistics", desc: "Descriptive & inferential statistics, regression", linked_papers: ["Structural Holes Project", "Authors Embeddedness Project"] }
    ],
    papers: [
      {
        id: "p1",
        title: "An Interpretive Phenomenological Approach to Library Place-Shaping and Perception of Libraries: Focusing on Student Users of Academic Libraries",
        short_title: "Library Place-Shaping (2026)",
        year: 2026,
        venue: "한국문헌정보학회지, 60(2), 315-336",
        status: "published",
        badge: "Published",
        keywords: ["kw_library_as_place", "kw_academic_library", "kw_perception_of_libraries"],
        methods: ["m_in_depth_interview", "m_ipa"]
      },
      {
        id: "p2",
        title: "Structural Holes Project (26.04.~)",
        short_title: "Structural Holes Project",
        year: 2026,
        venue: "Under Review",
        status: "ongoing",
        badge: "Under Review",
        keywords: ["kw_science_of_science", "kw_social_network_analysis", "kw_structural_holes", "kw_collaboration", "kw_interdisciplinary_research", "kw_field_maturation", "kw_research_performance"],
        methods: ["m_sna", "m_classical_statistics"]
      },
      {
        id: "p3",
        title: "Authors Subject Embeddedness Project (26.07.~)",
        short_title: "Authors Embeddedness Project",
        year: 2026,
        venue: "In Preparation",
        status: "ongoing",
        badge: "In Preparation",
        keywords: ["kw_bibliometrics", "kw_social_network_analysis", "kw_network_embeddedness", "kw_bibliographic_coupling", "kw_collaboration_dynamics", "kw_research_performance"],
        methods: ["m_sna", "m_classical_statistics"]
      }
    ]
  };

  // 2. Ensure D3 v7 is loaded
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

    var rawData = (window.__EGO_DATA__ && window.__EGO_DATA__.keywords && window.__EGO_DATA__.keywords.length > 0)
      ? window.__EGO_DATA__
      : DEFAULT_EGO_DATA;

    var currentLens = 'keywords'; // Default lens: keywords | methods | papers
    var svg = d3.select('#ego-network-svg');
    var tooltip = d3.select('#ego-tooltip');

    var width = container.clientWidth || 340;
    var height = 330;
    var centerX = width / 2;
    var centerY = height / 2;

    svg.attr('viewBox', [0, 0, width, height]).attr('width', '100%').attr('height', '100%');
    svg.selectAll('*').remove(); // Clear any previous elements

    var gRoot = svg.append('g').attr('class', 'ego-root-group');
    var gLinks = gRoot.append('g').attr('class', 'links-group');
    var gNodes = gRoot.append('g').attr('class', 'nodes-group');

    // Distinct, vibrant colors
    var colors = {
      ego: '#2563eb',             // Vibrant Royal Blue
      keywordCore: '#3b82f6',     // Bright Blue
      keywordSub: '#60a5fa',      // Soft Blue
      method: '#10b981',          // Emerald Green
      paperPublished: '#f59e0b',  // Warm Amber / Gold
      paperOngoing: '#ec4899',    // Pink / Rose (On-going / Under Review)
      edgeDefault: 'rgba(156, 163, 175, 0.55)',
      edgeHighlight: '#2563eb'
    };

    // Physics Simulation Setup
    var simulation = d3.forceSimulation()
      .force('link', d3.forceLink().id(function (d) { return d.id; }))
      .force('charge', d3.forceManyBody().strength(function (d) {
        if (d.isEgo) return -280;
        if (d.isPrimary) return -130;
        return -45;
      }))
      .force('center', d3.forceCenter(centerX, centerY).strength(0.08))
      .force('collision', d3.forceCollide().radius(function (d) {
        return (d.radius || 12) + 6;
      }).iterations(2));

    // Project graph data based on selected lens
    function projectGraph(lens) {
      var nodes = [];
      var links = [];
      var nodeMap = {};

      // Helper to initialize node with safe coordinates
      function addNode(n) {
        if (typeof n.x !== 'number' || isNaN(n.x)) {
          n.x = centerX + (Math.random() - 0.5) * 80;
        }
        if (typeof n.y !== 'number' || isNaN(n.y)) {
          n.y = centerY + (Math.random() - 0.5) * 80;
        }
        nodes.push(n);
        nodeMap[n.id] = n;
      }

      // 1. Center Ego Node
      var egoNode = {
        id: 'ego',
        label: (rawData.ego && rawData.ego.name) ? rawData.ego.name : 'Danho, Kim',
        subLabel: (rawData.ego && rawData.ego.label) ? rawData.ego.label : 'Researcher',
        type: 'ego',
        isEgo: true,
        isPrimary: false,
        radius: 26,
        color: colors.ego,
        x: centerX,
        y: centerY,
        fx: centerX,
        fy: centerY
      };
      addNode(egoNode);

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
            radius: isCore ? 19 : 14,
            color: isCore ? colors.keywordCore : colors.keywordSub,
            stroke: isCore ? '#1d4ed8' : '#3b82f6',
            linked_papers: kw.linked_papers || []
          };
          addNode(kwNode);

          links.push({
            source: 'ego',
            target: kw.id,
            type: 'ego-primary',
            distance: isCore ? 75 : 95
          });
        });

        // Papers as satellite dots orbiting their keywords
        rawData.papers.forEach(function (p) {
          var isPub = p.status === 'published';
          var pNode = {
            id: p.id + '_sat',
            realId: p.id,
            label: p.short_title || p.title,
            title: p.title,
            venue: p.venue,
            year: p.year,
            status: p.status,
            badge: p.badge,
            type: 'paper',
            isSatellite: true,
            radius: isPub ? 9 : 8,
            color: isPub ? colors.paperPublished : colors.paperOngoing,
            stroke: isPub ? '#d97706' : colors.paperOngoing
          };
          addNode(pNode);

          if (p.keywords && p.keywords.length > 0) {
            p.keywords.forEach(function (kwId) {
              if (nodeMap[kwId]) {
                links.push({
                  source: kwId,
                  target: pNode.id,
                  type: 'primary-satellite',
                  distance: 36
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
            color: colors.method,
            stroke: '#047857',
            linked_papers: m.linked_papers || []
          };
          addNode(mNode);

          links.push({
            source: 'ego',
            target: m.id,
            type: 'ego-primary',
            distance: 80
          });
        });

        // Dynamic inter-method connections for co-occurring methods in the same paper
        var methodPairs = {};
        rawData.papers.forEach(function (p) {
          if (p.methods && p.methods.length > 1) {
            for (var i = 0; i < p.methods.length; i++) {
              for (var j = i + 1; j < p.methods.length; j++) {
                var m1 = p.methods[i], m2 = p.methods[j];
                var pairKey = [m1, m2].sort().join('--');
                if (!methodPairs[pairKey] && nodeMap[m1] && nodeMap[m2]) {
                  methodPairs[pairKey] = true;
                  links.push({
                    source: m1,
                    target: m2,
                    type: 'inter-primary',
                    distance: 65
                  });
                }
              }
            }
          }
        });

        // Papers as satellite dots orbiting methods
        rawData.papers.forEach(function (p) {
          var isPub = p.status === 'published';
          var pNode = {
            id: p.id + '_sat',
            realId: p.id,
            label: p.short_title || p.title,
            title: p.title,
            venue: p.venue,
            year: p.year,
            status: p.status,
            badge: p.badge,
            type: 'paper',
            isSatellite: true,
            radius: isPub ? 9 : 8,
            color: isPub ? colors.paperPublished : colors.paperOngoing,
            stroke: isPub ? '#d97706' : colors.paperOngoing
          };
          addNode(pNode);

          if (p.methods && p.methods.length > 0) {
            p.methods.forEach(function (mId) {
              if (nodeMap[mId]) {
                links.push({
                  source: mId,
                  target: pNode.id,
                  type: 'primary-satellite',
                  distance: 38
                });
              }
            });
          }
        });

      } else if (lens === 'papers') {
        // Papers are Primary nodes; Keywords & Methods are Satellites
        rawData.papers.forEach(function (p) {
          var isPub = p.status === 'published';
          var pNode = {
            id: p.id,
            label: p.short_title || p.title,
            title: p.title,
            venue: p.venue,
            year: p.year,
            status: p.status,
            badge: p.badge,
            type: 'paper',
            isPrimary: true,
            radius: isPub ? 21 : 18,
            color: isPub ? colors.paperPublished : colors.paperOngoing,
            stroke: isPub ? '#b45309' : colors.paperOngoing
          };
          addNode(pNode);

          links.push({
            source: 'ego',
            target: p.id,
            type: 'ego-primary',
            distance: 85
          });
        });

        // Dynamically connect papers that share keywords
        var paperPairs = {};
        for (var pi = 0; pi < rawData.papers.length; pi++) {
          for (var pj = pi + 1; pj < rawData.papers.length; pj++) {
            var pa = rawData.papers[pi];
            var pb = rawData.papers[pj];
            if (pa.keywords && pb.keywords) {
              var sharedKws = pa.keywords.filter(function (k) {
                return pb.keywords.indexOf(k) !== -1;
              });
              if (sharedKws.length > 0 && nodeMap[pa.id] && nodeMap[pb.id]) {
                var pPairKey = [pa.id, pb.id].sort().join('--');
                if (!paperPairs[pPairKey]) {
                  paperPairs[pPairKey] = true;
                  links.push({
                    source: pa.id,
                    target: pb.id,
                    type: 'inter-primary',
                    distance: 75
                  });
                }
              }
            }
          }
        }

        // Add method & keyword satellites around each paper
        rawData.papers.forEach(function (p) {
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
                color: colors.method,
                stroke: '#047857',
                linked_papers: [p.short_title || p.title]
              };
              addNode(mSat);
              links.push({ source: p.id, target: mSat.id, type: 'primary-satellite', distance: 35 });
            }
          }

          if (p.keywords && p.keywords.length > 0) {
            var lastKwId = p.keywords[p.keywords.length - 1];
            var kwObj = rawData.keywords.find(function (k) { return k.id === lastKwId; });
            if (kwObj) {
              var kwSat = {
                id: p.id + '_' + kwObj.id,
                label: kwObj.label,
                type: 'keyword',
                isSatellite: true,
                radius: 7,
                color: colors.keywordSub,
                stroke: '#3b82f6',
                linked_papers: [p.short_title || p.title]
              };
              addNode(kwSat);
              links.push({ source: p.id, target: kwSat.id, type: 'primary-satellite', distance: 35 });
            }
          }
        });
      }

      // CRITICAL: Filter links strictly to ensure source & target exist in nodes
      var safeLinks = links.filter(function (l) {
        return nodeMap[l.source] && nodeMap[l.target];
      });

      return { nodes: nodes, links: safeLinks, egoNode: egoNode };
    }

    // Render & Update Function
    function update(lens) {
      currentLens = lens;
      var graph = projectGraph(lens);

      // 1. Update Links
      var link = gLinks.selectAll('.ego-link')
        .data(graph.links, function (d) {
          var s = typeof d.source === 'object' ? d.source.id : d.source;
          var t = typeof d.target === 'object' ? d.target.id : d.target;
          return s + '--' + t;
        });

      link.exit().remove();

      var linkEnter = link.enter().append('line')
        .attr('class', function (d) {
          var cls = 'ego-link';
          if (d.type === 'primary-satellite') cls += ' is-satellite';
          return cls;
        })
        .attr('stroke', colors.edgeDefault)
        .attr('stroke-width', function (d) {
          return d.type === 'primary-satellite' ? 1.2 : 1.8;
        })
        .attr('stroke-dasharray', function (d) {
          return d.type === 'primary-satellite' ? '3, 2' : 'none';
        });

      link = linkEnter.merge(link);

      // 2. Update Nodes
      var node = gNodes.selectAll('.ego-node')
        .data(graph.nodes, function (d) { return d.id; });

      node.exit().remove();

      var nodeEnter = node.enter().append('g')
        .attr('class', function (d) {
          var cls = 'ego-node node-' + d.type;
          var isOngoing = (d.status === 'ongoing' || d.status === 'ghost');
          if (isOngoing) cls += ' is-ongoing is-ghost';
          return cls;
        })
        .call(d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended)
        );

      // Pulse ring for Ego
      nodeEnter.filter(function (d) { return d.isEgo; })
        .append('circle')
        .attr('class', 'pulse-ring')
        .attr('r', 26)
        .attr('fill', 'none')
        .attr('stroke', colors.ego)
        .attr('stroke-width', 1.8);

      // Main Node Circle with explicit colors & radius
      nodeEnter.append('circle')
        .attr('class', function (d) { return d.isEgo ? 'center-node' : 'orbit-node'; })
        .attr('r', function (d) { return d.radius || 14; })
        .attr('fill', function (d) { return d.color || colors.ego; })
        .attr('stroke', function (d) { return d.stroke || '#ffffff'; })
        .attr('stroke-width', function (d) { return d.isEgo ? 3 : 2; })
        .attr('stroke-dasharray', function (d) {
          return (d.status === 'ongoing' || d.status === 'ghost') ? '4, 3' : 'none';
        })
        .style('fill-opacity', function (d) {
          return (d.status === 'ongoing' || d.status === 'ghost') ? 0.35 : 1;
        });

      // Node Text Label
      nodeEnter.append('text')
        .attr('class', function (d) {
          return 'ego-label' + (d.isEgo ? ' ego-center-label' : '');
        })
        .attr('dy', function (d) {
          if (d.isEgo) return '0.35em';
          if (d.isSatellite) return '-1.2em';
          return '0.35em';
        })
        .attr('text-anchor', 'middle')
        .attr('fill', function (d) {
          return d.isEgo ? '#ffffff' : 'currentColor';
        })
        .attr('font-size', function (d) {
          return d.isEgo ? '10.5px' : '9px';
        })
        .attr('font-weight', function (d) {
          return d.isEgo ? '700' : '600';
        })
        .text(function (d) {
          if (d.isEgo) return d.label;
          if (d.isSatellite) return '';
          return d.label;
        });

      node = nodeEnter.merge(node);

      // Re-apply attributes on update
      node.select('circle.orbit-node')
        .attr('r', function (d) { return d.radius || 14; })
        .attr('fill', function (d) { return d.color || colors.ego; })
        .attr('stroke', function (d) { return d.stroke || '#ffffff'; })
        .attr('stroke-dasharray', function (d) {
          return (d.status === 'ongoing' || d.status === 'ghost') ? '4, 3' : 'none';
        })
        .style('fill-opacity', function (d) {
          return (d.status === 'ongoing' || d.status === 'ghost') ? 0.35 : 1;
        });

      node.select('text')
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

      // 3. Configure and Restart Simulation
      simulation.nodes(graph.nodes);
      simulation.force('link').links(graph.links).distance(function (d) {
        return d.distance || 60;
      });
      simulation.alpha(0.7).restart();

      simulation.on('tick', function () {
        // Keep Ego strictly centered
        graph.egoNode.x = centerX;
        graph.egoNode.y = centerY;

        link
          .attr('x1', function (d) { return d.source.x; })
          .attr('y1', function (d) { return d.source.y; })
          .attr('x2', function (d) { return d.target.x; })
          .attr('y2', function (d) { return d.target.y; });

        node.attr('transform', function (d) {
          var r = d.radius || 12;
          if (isNaN(d.x)) d.x = centerX;
          if (isNaN(d.y)) d.y = centerY;
          d.x = Math.max(r + 4, Math.min(width - r - 4, d.x));
          d.y = Math.max(r + 4, Math.min(height - r - 4, d.y));
          return 'translate(' + d.x + ',' + d.y + ')';
        });
      });
    }

    // Highlighting on hover
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
        .attr('stroke', function (l) {
          var sId = l.source.id;
          var tId = l.target.id;
          return (sId === activeNode.id || tId === activeNode.id) ? colors.edgeHighlight : 'rgba(156, 163, 175, 0.2)';
        })
        .attr('stroke-width', function (l) {
          var sId = l.source.id;
          var tId = l.target.id;
          return (sId === activeNode.id || tId === activeNode.id) ? 2.5 : 1;
        });

      gNodes.selectAll('.ego-node')
        .style('opacity', function (n) {
          return connectedNodeIds[n.id] ? 1 : 0.25;
        });
    }

    function resetHighlight() {
      gLinks.selectAll('.ego-link')
        .classed('highlighted', false)
        .attr('stroke', colors.edgeDefault)
        .attr('stroke-width', function (d) {
          return d.type === 'primary-satellite' ? 1.2 : 1.8;
        });

      gNodes.selectAll('.ego-node')
        .style('opacity', 1);
    }

    // Enhanced Human-Friendly Tooltip formatting
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
          bodyHtml = d.venue ? '🏛️ ' + d.venue : 'Published paper';
        } else {
          var badgeText = d.badge || 'On-going';
          badgeHtml = '<span class="ego-tooltip-badge badge-ongoing">On-going &bull; ' + badgeText + '</span>';
          bodyHtml = d.venue ? '⏳ ' + d.venue : 'On-going research project';
        }
      } else if (d.type === 'method') {
        titleHtml = d.full_name || d.label;
        badgeHtml = '<span class="ego-tooltip-badge badge-published">METHOD</span>';
        var paperList = (d.linked_papers && d.linked_papers.length > 0) ? d.linked_papers.join(', ') : '';
        bodyHtml = paperList ? '🛠️ 적용 연구: ' + paperList : (d.desc || '분석 프레임워크');
      } else if (d.type === 'keyword') {
        titleHtml = d.label;
        var badgeText = d.isCore ? 'CORE TOPIC' : 'TOPIC';
        badgeHtml = '<span class="ego-tooltip-badge badge-published">' + badgeText + '</span>';
        var paperList = (d.linked_papers && d.linked_papers.length > 0) ? d.linked_papers.join(', ') : '';
        bodyHtml = paperList ? '📌 연계 연구: ' + paperList : (d.isCore ? '주요 연구 분야' : '세부 탐구 주제');
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

    // Initial render: start with 'keywords'
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
