#!/usr/bin/env python3
"""
Local Live Previewer for Danho Kim's Homepage
Generates a standalone, zero-dependency local preview of the site in `_preview/`
and serves it on localhost so you can verify changes before pushing to GitHub!
"""

import argparse
import csv
import http.server
import json
import os
import re
import shutil
import socketserver
import sys
import webbrowser
from pathlib import Path

# Force UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent
CSV_DIR = ROOT_DIR / "_csv"
DATA_DIR = ROOT_DIR / "_data"
ASSETS_DIR = ROOT_DIR / "assets"
PREVIEW_DIR = ROOT_DIR / "_preview"

def run_sync():
    sync_script = ROOT_DIR / "bin" / "sync_site_data.py"
    if sync_script.exists():
        import subprocess
        subprocess.run([sys.executable, str(sync_script)], check=True)

def slugify(text, prefix=""):
    text = text.strip().lower()
    slug = re.sub(r'[^a-z0-9]+', '_', text).strip('_')
    if not slug:
        slug = "item"
    return f"{prefix}{slug}" if prefix else slug

def clean_list(cell):
    if not cell:
        return []
    normalized = cell.replace(';', ',')
    items = [item.strip() for item in normalized.split(',')]
    return [item for item in items if item]

def read_ego_data():
    csv_path = CSV_DIR / "ego_network.csv"
    if not csv_path.exists():
        csv_path = DATA_DIR / "ego_network.csv"
        
    ego = {
        "name": "Danho, Kim",
        "label": "Master's Student",
        "affiliation": "Library & Information Science"
    }
    keywords = []
    methods = []
    papers = []
    
    if csv_path.exists():
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row or not any(row):
                    continue
                row_type = row[0].strip().lower()
                title = row[1].strip() if len(row) > 1 else ""
                desc = row[2].strip() if len(row) > 2 else ""
                
                if row_type == "ego":
                    if title: ego["name"] = title
                    if desc: ego["label"] = desc
                    if len(row) > 3 and row[3].strip(): ego["affiliation"] = row[3].strip()
                elif row_type == "keyword":
                    cat = row[3].strip().lower() if len(row) > 3 and row[3].strip() else "sub"
                    if cat not in ("core", "sub"): cat = "sub"
                    k_id = slugify(title, "kw_")
                    keywords.append({
                        "id": k_id,
                        "label": title,
                        "category": cat,
                        "description": desc,
                        "linked_papers": []
                    })
                elif row_type == "method":
                    full_name = row[4].strip() if len(row) > 4 and row[4].strip() else title
                    m_id = slugify(title, "m_")
                    methods.append({
                        "id": m_id,
                        "label": title,
                        "full_name": full_name,
                        "desc": desc,
                        "description": desc,
                        "linked_papers": []
                    })
                elif row_type == "paper":
                    status = row[3].strip().lower() if len(row) > 3 and row[3].strip() else "published"
                    core_kws = clean_list(row[4]) if len(row) > 4 else []
                    sub_kws = clean_list(row[5]) if len(row) > 5 else []
                    paper_methods = clean_list(row[6]) if len(row) > 6 else []
                    venue = row[7].strip() if len(row) > 7 else ""
                    year = row[8].strip() if len(row) > 8 else "2026"
                    short_title = row[9].strip() if len(row) > 9 and row[9].strip() else title
                    badge = "Published" if "publish" in status else ("Under Review" if "review" in status else "In Preparation")
                    
                    paper_obj = {
                        "id": slugify(short_title, "p_"),
                        "title": title,
                        "short_title": short_title,
                        "year": year,
                        "venue": venue,
                        "status": "published" if "publish" in status else "ongoing",
                        "badge": badge,
                        "description": desc,
                        "keywords": [slugify(k, "kw_") for k in (core_kws + sub_kws)],
                        "methods": [slugify(m, "m_") for m in paper_methods]
                    }
                    papers.append(paper_obj)
                    
                    # Backlink to keywords and methods
                    for kw_name in (core_kws + sub_kws):
                        kw_id = slugify(kw_name, "kw_")
                        for kw in keywords:
                            if kw["id"] == kw_id and short_title not in kw["linked_papers"]:
                                kw["linked_papers"].append(short_title)
                    for m_name in paper_methods:
                        m_id = slugify(m_name, "m_")
                        for m in methods:
                            if m["id"] == m_id and short_title not in m["linked_papers"]:
                                m["linked_papers"].append(short_title)

    return {
        "ego": ego,
        "keywords": keywords,
        "methods": methods,
        "papers": papers
    }

def read_about_data():
    csv_path = CSV_DIR / "about.csv"
    data = {
        "subtitle": "Master's Student",
        "paragraphs": [],
        "footer_note": "Feel free to interact with my <em>Research Ego-Network</em> on the left to navigate across my core topics, methods, and ongoing publications!"
    }
    if csv_path.exists():
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sec = row.get("section", "").strip().lower()
                content = row.get("content", "").strip()
                if sec == "subtitle" and content:
                    data["subtitle"] = content
                elif sec == "paragraph" and content:
                    data["paragraphs"].append(content)
                elif sec == "footer_note" and content:
                    data["footer_note"] = content
    if not data["paragraphs"]:
        data["paragraphs"] = [
            'I am a master’s student advised by Professor <a href="https://snis.yonsei.ac.kr/" target="_blank" rel="noopener noreferrer">Ji-Hong Park</a>.',
            'I study social networks, scholarly communication, bibliometrics, and the science of science.',
            'Network theory moves beyond the dualism of individual attributes and social institutions and norms, explaining human interaction at the meso level. From this perspective, I examine scholarly communication as a relational phenomenon.'
        ]
    return data

def read_publications():
    pub_csv = CSV_DIR / "publications.csv"
    papers = []
    if pub_csv.exists():
        with open(pub_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                papers.append(r)
    return papers

def read_cv_data():
    csv_path = CSV_DIR / "cv.csv"
    data = {
        "name": "Danho Kim",
        "label": "Master's Student in Library and Information Science",
        "email": "danhokim@yonsei.ac.kr",
        "location": "Seoul, Republic of Korea",
        "social": {"network": "GitHub", "username": "danhokim020"},
        "education": [],
        "skills": []
    }
    if csv_path.exists():
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sec = row.get("section", "").strip().lower()
                title = row.get("title", "").strip()
                subtitle = row.get("subtitle", "").strip()
                inst = row.get("institution", "").strip()
                sdate = row.get("start_date", "").strip()
                edate = row.get("end_date", "").strip()
                loc = row.get("location", "").strip()
                details = row.get("details", "").strip()
                
                if sec == "profile":
                    if title: data["name"] = title
                    if subtitle: data["label"] = subtitle
                    if inst and "@" in inst: data["email"] = inst
                    if loc: data["location"] = loc
                elif sec == "social":
                    data["social"] = {"network": title, "username": subtitle or inst}
                elif sec == "education":
                    highlights = [h.strip() for h in details.split(";") if h.strip()] if details else []
                    data["education"].append({
                        "institution": inst or title,
                        "location": loc,
                        "area": subtitle,
                        "studyType": title,
                        "start_date": sdate,
                        "end_date": edate,
                        "highlights": highlights
                    })
                elif sec == "skills":
                    kws = [k.strip() for k in details.split(";") if k.strip()] if details else []
                    data["skills"].append({
                        "name": title,
                        "keywords": kws
                    })
    return data

def get_common_head(title="Danho Kim"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | Danho Kim (Local Preview)</title>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto:300,400,500,700|Roboto+Slab:100,300,400,500,700&display=swap">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@7.2.0/css/all.min.css">
  <link rel="stylesheet" href="assets/css/al-folio-cv.css">
  <link rel="stylesheet" href="assets/css/ego_network.css">
  <style>
    :root {{
      --global-bg-color: #ffffff;
      --global-code-bg-color: #f7f7f7;
      --global-text-color: #333333;
      --global-text-color-light: #666666;
      --global-theme-color: #2563eb;
      --global-hover-color: #1d4ed8;
      --global-card-bg-color: #ffffff;
      --global-divider-color: rgba(0, 0, 0, 0.1);
    }}
    body {{
      font-family: "Roboto", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 0;
      color: var(--global-text-color);
      background-color: var(--global-bg-color);
      line-height: 1.6;
    }}
    /* Preview Bar on Top */
    .preview-banner {{
      background: #1e293b;
      color: #f8fafc;
      padding: 10px 18px;
      font-size: 0.84rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 99999;
      box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }}
    .preview-banner a {{
      color: #38bdf8;
      text-decoration: none;
      font-weight: 600;
      margin: 0 6px;
    }}
    .preview-banner a:hover {{
      text-decoration: underline;
    }}
    .preview-badge {{
      background: #f59e0b;
      color: #000;
      padding: 3px 7px;
      border-radius: 4px;
      font-weight: 700;
      font-size: 0.72rem;
      margin-right: 8px;
    }}
    .navbar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      max-width: 930px;
      margin: 0 auto;
      padding: 1.2rem 1rem;
    }}
    .navbar-brand {{
      font-size: 1.35rem;
      font-weight: 300;
      text-decoration: none;
      color: var(--global-text-color);
    }}
    .navbar-brand strong {{
      font-weight: 700;
    }}
    .navbar-nav {{
      display: flex;
      list-style: none;
      margin: 0;
      padding: 0;
      gap: 1.5rem;
    }}
    .nav-link {{
      text-decoration: none;
      color: var(--global-text-color);
      font-weight: 500;
      font-size: 0.95rem;
      text-transform: capitalize !important;
      transition: color 0.2s;
    }}
    .nav-link:hover, .nav-link.active {{
      color: var(--global-theme-color);
    }}
    .main-container {{
      max-width: 930px;
      margin: 0 auto 3rem auto;
      padding: 0 1rem;
    }}
    .post-header {{
      margin-bottom: 1.5rem;
    }}
    .post-title {{
      font-size: 2.2rem;
      font-weight: 300;
      margin: 0;
    }}
    .post-title strong {{
      font-weight: 700;
    }}
    .post-subtitle {{
      color: var(--global-text-color-light);
      margin-top: 0.4rem;
      font-size: 1.1rem;
    }}
    h2.section-heading {{
      font-size: 1.5rem;
      font-weight: 500;
      margin-top: 2.5rem;
      margin-bottom: 1rem;
      border-bottom: 1px solid var(--global-divider-color);
      padding-bottom: 0.5rem;
      text-transform: capitalize !important;
    }}
    .pub-entry {{
      margin-bottom: 1.4rem;
      padding-bottom: 1.2rem;
      border-bottom: 1px solid rgba(0,0,0,0.06);
    }}
    .pub-title {{
      font-weight: 600;
      font-size: 1.05rem;
      color: var(--global-text-color);
    }}
    .pub-author {{
      color: var(--global-text-color-light);
      font-size: 0.92rem;
      margin: 0.25rem 0;
    }}
    .pub-venue {{
      font-style: italic;
      color: var(--global-text-color-light);
      font-size: 0.88rem;
    }}
    .badge-status {{
      display: inline-block;
      padding: 2px 7px;
      border-radius: 4px;
      font-size: 0.72rem;
      font-weight: 600;
      margin-left: 6px;
      background: #e0f2fe;
      color: #0369a1;
    }}
    .btn-abs {{
      display: inline-block;
      margin-top: 0.4rem;
      padding: 2px 8px;
      font-size: 0.76rem;
      font-weight: 600;
      border: 1px solid #cbd5e1;
      border-radius: 4px;
      background: #f8fafc;
      color: #334155;
      cursor: pointer;
    }}
    .btn-abs:hover {{
      background: #e2e8f0;
      color: #0f172a;
    }}
    .abstract-box {{
      display: none;
      margin-top: 0.5rem;
      padding: 0.6rem 0.85rem;
      background: #f8fafc;
      border-left: 3px solid var(--global-theme-color);
      font-size: 0.88rem;
      color: #475569;
      border-radius: 0 4px 4px 0;
    }}
  </style>
</head>
<body>
  <div class="preview-banner">
    <div>
      <span class="preview-badge">LOCAL PREVIEW</span>
      <span>현재 화면은 <strong>로컬 미리보기</strong> 상태입니다 (GitHub 미반영)</span>
    </div>
    <div>
      <span>페이지 바로가기:</span>
      <a href="index.html">About</a> |
      <a href="publications.html">Publications</a> |
      <a href="cv.html">CV</a>
    </div>
  </div>

  <header>
    <nav class="navbar">
      <a class="navbar-brand" href="index.html"><strong>Danho</strong> Kim</a>
      <ul class="navbar-nav">
        <li><a class="nav-link {'active' if title == 'About' else ''}" href="index.html">About</a></li>
        <li><a class="nav-link {'active' if title == 'Publications' else ''}" href="publications.html">Publications</a></li>
        <li><a class="nav-link {'active' if title == 'CV' else ''}" href="cv.html">CV</a></li>
      </ul>
    </nav>
  </header>
  <main class="main-container">
"""

def get_common_footer():
    return """
  </main>
  <footer style="text-align: center; padding: 2rem 0; font-size: 0.82rem; color: #888; border-top: 1px solid rgba(0,0,0,0.06);">
    &copy; 2026 Danho Kim. Local Preview Environment.
  </footer>
</body>
</html>
"""

def build_about_page(ego_data, about_data, papers):
    html = get_common_head("About")
    html += f"""
    <div class="post-header">
      <h1 class="post-title"><strong>Danho</strong> Kim</h1>
      <div class="post-subtitle">{about_data.get('subtitle', "Master's Student")}</div>
    </div>
    
    <div class="ego-layout-row">
      <!-- Left Column: Ego-Network Card -->
      <div class="ego-layout-left">
        <div id="ego-network-container" class="ego-card">
          <div class="ego-header">
            <div class="ego-title-row">
              <span class="ego-card-title">
                <span class="ego-live-badge"></span> Research Network
              </span>
              <span style="font-size: 0.68rem; color: #888; font-weight: 500;">3-Lens View</span>
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
      
      <!-- Right Column: Biography -->
      <div class="ego-layout-right">
    """
    for p in about_data.get("paragraphs", []):
        html += f"        <p>{p}</p>\n"
        
    footer_note = about_data.get("footer_note", "Feel free to interact with my <em>Research Ego-Network</em> on the left!")
    html += f"""
        <p style="font-size: 0.88rem; color: #666;">{footer_note}</p>
      </div>
    </div>
    
    <!-- News Announcements -->
    <h2 class="section-heading"><a href="#" style="text-decoration:none; color:inherit;">News</a></h2>
    <div style="font-size: 0.92rem; margin-bottom: 2rem;">
      <table style="width: 100%; border-collapse: collapse;">
        <tr>
          <td style="width: 120px; font-weight: 600; color: #666; vertical-align: top; padding: 6px 0;">Nov 02, 2026</td>
          <td style="padding: 6px 0;">🚀 Launched my research website!</td>
        </tr>
      </table>
    </div>

    <!-- Selected Publications -->
    <h2 class="section-heading"><a href="publications.html" style="text-decoration:none; color:inherit;">Selected Publications</a></h2>
    <div class="publications">
    """
    
    for paper in papers:
        is_selected = str(paper.get("selected", "")).strip().lower() in ("true", "1")
        if not is_selected and len(papers) > 1:
            continue
        p_id = paper.get("id", "p")
        title = paper.get("title", "")
        author = paper.get("author", "Danho Kim")
        journal = paper.get("journal", "")
        year = paper.get("year", "2026")
        abbr = paper.get("abbr", "")
        abstract = paper.get("abstract", "")
        
        badge_html = f'<span class="badge-status">{abbr}</span>' if abbr else ''
        abstract_btn = f'<button class="btn-abs" onclick="toggleAbs(\'{p_id}\')">Abs</button>' if abstract else ''
        abstract_div = f'<div id="abs-{p_id}" class="abstract-box">{abstract}</div>' if abstract else ''
        
        html += f"""
      <div class="pub-entry">
        <div class="pub-title">{title} {badge_html}</div>
        <div class="pub-author">{author} ({year})</div>
        <div class="pub-venue">{journal}</div>
        {abstract_btn}
        {abstract_div}
      </div>
        """
        
    html += f"""
    </div>
    
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
      window.__EGO_DATA__ = {json.dumps(ego_data, ensure_ascii=False)};
      function toggleAbs(id) {{
        var el = document.getElementById('abs-' + id);
        if (el) {{
          el.style.display = (el.style.display === 'block') ? 'none' : 'block';
        }}
      }}
    </script>
    <script src="assets/js/ego_network.js"></script>
    """
    html += get_common_footer()
    return html

def build_publications_page(papers):
    html = get_common_head("Publications")
    html += """
    <div class="post-header">
      <h1 class="post-title">Publications</h1>
    </div>
    <div class="publications">
    """
    for paper in papers:
        p_id = paper.get("id", "p")
        title = paper.get("title", "")
        author = paper.get("author", "Danho Kim")
        journal = paper.get("journal", "")
        year = paper.get("year", "2026")
        abbr = paper.get("abbr", "")
        abstract = paper.get("abstract", "")
        
        badge_html = f'<span class="badge-status">{abbr}</span>' if abbr else ''
        abstract_btn = f'<button class="btn-abs" onclick="toggleAbs(\'{p_id}\')">Abs</button>' if abstract else ''
        abstract_div = f'<div id="abs-{p_id}" class="abstract-box">{abstract}</div>' if abstract else ''
        
        html += f"""
      <div class="pub-entry">
        <div class="pub-title">{title} {badge_html}</div>
        <div class="pub-author">{author} ({year})</div>
        <div class="pub-venue">{journal}</div>
        {abstract_btn}
        {abstract_div}
      </div>
        """
    html += """
    </div>
    <script>
      function toggleAbs(id) {
        var el = document.getElementById('abs-' + id);
        if (el) {
          el.style.display = (el.style.display === 'block') ? 'none' : 'block';
        }
      }
    </script>
    """
    html += get_common_footer()
    return html

def build_cv_page(cv_data):
    html = get_common_head("CV")
    profile_name = cv_data.get("name", "Danho Kim")
    email = cv_data.get("email", "danhokim@yonsei.ac.kr")
    location = cv_data.get("location", "Seoul, Republic of Korea")
    education = cv_data.get("education", [])
    skills = cv_data.get("skills", [])
    
    html += f"""
    <div class="post-header">
      <h1 class="post-title">CV</h1>
    </div>
    
    <div class="row" style="display: flex; gap: 2rem; align-items: flex-start;">
      <!-- Sidebar TOC (Simulated Tocbot with bar removed) -->
      <div style="flex: 0 0 160px;">
        <nav id="toc-sidebar" class="toc toc-sidebar" style="position: sticky; top: 70px;">
          <ul class="toc-list" style="list-style: none; padding-left: 0; margin: 0;">
            <li class="toc-list-item" style="margin-bottom: 0.6rem;"><a href="#education" class="toc-link" style="text-decoration:none; color:inherit; font-weight:500;">Education</a></li>
            <li class="toc-list-item" style="margin-bottom: 0.6rem;"><a href="#skills" class="toc-link" style="text-decoration:none; color:inherit; font-weight:500;">Skills</a></li>
          </ul>
        </nav>
      </div>

      <!-- Main CV Content -->
      <div class="cv" style="flex: 1 1 0; min-width: 0;">
        <!-- Profile Card -->
        <div class="card p-3 mb-4" style="background:#f8fafc; border:1px solid rgba(0,0,0,0.08); border-radius:10px; padding:1.2rem; margin-bottom:1.5rem;">
          <h2 style="margin:0 0 0.5rem 0; font-size:1.4rem; font-weight:600;">{profile_name}</h2>
          <div style="font-size:0.92rem; color:#475569; display:flex; flex-wrap:wrap; gap:1.2rem;">
            <span><i class="fa-solid fa-envelope"></i> {email}</span>
            <span><i class="fa-solid fa-location-dot"></i> {location}</span>
            <span><i class="fa-brands fa-github"></i> danhokim020</span>
          </div>
        </div>

        <!-- Education Card -->
        <a class="anchor" id="education"></a>
        <div class="card mt-3 p-3" style="background:#fff; border:1px solid rgba(0,0,0,0.1); border-radius:10px; padding:1.4rem; margin-bottom:1.5rem;">
          <h3 class="card-title font-weight-medium" style="margin:0 0 1rem 0; font-size:1.25rem;">Education</h3>
          <ul class="list-group list-group-flush" style="list-style:none; padding:0; margin:0;">
    """
    
    for edu in education:
        inst = edu.get("institution", "")
        loc = edu.get("location", "")
        area = edu.get("area", "")
        stype = edu.get("studyType", "")
        sdate = edu.get("start_date", "")
        edate = edu.get("end_date", "")
        date_badge = f"{sdate} - {edate}" if sdate and edate else (sdate or edate)
        highlights = edu.get("highlights", [])
        
        cleaned_highlights = []
        for h in highlights:
            if "<style>" in h:
                h = h[:h.find("<style>")]
            cleaned_highlights.append(h)
            
        hl_html = ""
        if cleaned_highlights:
            hl_html = '<ul class="items" style="margin-top:0.5rem; padding-left:1.25rem;">'
            for h in cleaned_highlights:
                hl_html += f'<li><span class="item">{h}</span></li>'
            hl_html += '</ul>'
            
        html += f"""
            <li class="list-group-item" style="border-bottom:1px solid rgba(0,0,0,0.06); padding:1rem 0;">
              <div class="row">
                <div class="date-column">
                  <table class="table-cv">
                    <tbody>
                      <tr>
                        <td>
                          <span class="badge" style="display:inline-block; background:#dc2626; color:#fff; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:4px;">{date_badge}</span>
                        </td>
                      </tr>
                      <tr>
                        <td>
                          <p class="location"><i class="fa-solid fa-location-dot iconlocation"></i> {loc}</p>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div>
                  <h6 class="title" style="margin:0 0 0.2rem 0; font-size:1.05rem; font-weight:700;">{stype}</h6>
                  <h6 style="margin:0 0 0.2rem 0; font-size:0.95rem; font-weight:500;">{inst}</h6>
                  <h6 style="margin:0; font-size:0.92rem; font-style:italic; color:#555;">{area}</h6>
                  {hl_html}
                </div>
              </div>
            </li>
        """
        
    html += """
          </ul>
        </div>

        <!-- Skills Card -->
        <a class="anchor" id="skills"></a>
        <div class="card mt-3 p-3" style="background:#fff; border:1px solid rgba(0,0,0,0.1); border-radius:10px; padding:1.4rem;">
          <h3 class="card-title font-weight-medium" style="margin:0 0 1rem 0; font-size:1.25rem;">Skills</h3>
          <div class="card-text">
    """
    for sk in skills:
        sname = sk.get("name", "")
        kw_list = ", ".join(sk.get("keywords", []))
        html += f"""
            <div style="padding:0.4rem 0; font-size:0.95rem;">
              <strong>{sname}:</strong> {kw_list}
            </div>
        """
        
    html += """
          </div>
        </div>
      </div>
    </div>
    """
    html += get_common_footer()
    return html

def build_preview_site():
    print("[Preview] Building local preview bundle in `_preview/`...")
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Sync data first
    run_sync()
    
    # 2. Copy assets (excluding heavy video / typst)
    preview_assets = PREVIEW_DIR / "assets"
    if preview_assets.exists():
        shutil.rmtree(preview_assets)
    shutil.copytree(ASSETS_DIR, preview_assets, ignore=shutil.ignore_patterns("video", "*.mp4", "*.typ"))
    
    # 3. Read data from CSV
    ego_data = read_ego_data()
    about_data = read_about_data()
    papers = read_publications()
    cv_data = read_cv_data()
    
    # 4. Generate HTML pages
    index_html = build_about_page(ego_data, about_data, papers)
    pubs_html = build_publications_page(papers)
    cv_html = build_cv_page(cv_data)
    
    with open(PREVIEW_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    with open(PREVIEW_DIR / "publications.html", "w", encoding="utf-8") as f:
        f.write(pubs_html)
    with open(PREVIEW_DIR / "cv.html", "w", encoding="utf-8") as f:
        f.write(cv_html)
        
    print(f"[Preview Success] Generated index.html, publications.html, cv.html in {PREVIEW_DIR}")

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PREVIEW_DIR), **kwargs)
    def log_message(self, format, *args):
        pass # suppress request noise

def serve_preview(port=8000, open_browser=True):
    build_preview_site()
    
    actual_port = port
    max_tries = 10
    httpd = None
    for attempt in range(max_tries):
        try:
            httpd = socketserver.TCPServer(("", actual_port), QuietHandler)
            break
        except OSError:
            actual_port += 1
            
    if not httpd:
        print(f"[Error] Could not find an open port starting from {port}.")
        return

    preview_url = f"http://localhost:{actual_port}/"
    print("\n" + "="*65)
    print(f"🚀 [Local Preview Server Running] ➔ {preview_url}")
    print("="*65)
    print("• 브라우저에서 화면을 직접 확인하고 인터랙션을 테스트하세요.")
    print("• 마음에 드시면 에이전트에게 '푸시해줘'라고 말씀해주세요.")
    print("• 마음에 들지 않으시면 에이전트에게 '롤백해줘'라고 말씀해주세요.")
    print("• 프리뷰 서버를 종료하려면 터미널에서 Ctrl + C를 누르세요.\n")
    
    if open_browser:
        webbrowser.open(preview_url)
        
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Preview Server Stopped]")
        httpd.server_close()

def main():
    parser = argparse.ArgumentParser(description="Danho Kim Homepage Local Previewer")
    parser.add_argument("--build-only", action="store_true", help="Build static preview HTML files without starting the server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run local server on (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open the web browser")
    
    args = parser.parse_args()
    if args.build_only:
        build_preview_site()
    else:
        serve_preview(port=args.port, open_browser=not args.no_browser)

if __name__ == "__main__":
    main()
