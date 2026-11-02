#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync Ego-Network from CSV (_data/ego_network.csv -> _data/ego_network.yml)
Designed for Danho Kim's Research Homepage
"""

import csv
import os
import re
import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def slugify(text, prefix=""):
    """Generate safe, clean alphanumeric ID for YAML/HTML/D3 usage."""
    text = text.strip().lower()
    slug = re.sub(r'[^a-z0-9]+', '_', text).strip('_')
    if not slug:
        slug = "item"
    return f"{prefix}{slug}" if prefix else slug

def clean_list(cell):
    """Split string by semicolon or comma, stripping whitespace."""
    if not cell:
        return []
    # If cell contains semicolon, prefer semicolon split; otherwise comma
    delimiters = ';' if ';' in cell else ','
    items = [item.strip() for item in cell.split(delimiters)]
    return [item for item in items if item]

def format_yaml_str(val):
    """Safely format string for YAML output."""
    if not val:
        return '""'
    val_str = str(val).strip()
    escaped = val_str.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'

def sync_network():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))
    
    csv_path = os.path.join(root_dir, "_data", "ego_network.csv")
    yml_path = os.path.join(root_dir, "_data", "ego_network.yml")
    
    if not os.path.exists(csv_path):
        print(f"[Sync Error] CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)
        
    print(f"[Sync] Reading data from {csv_path}...")
    
    papers = []
    keyword_map = {}  # id -> {id, label, category, papers: []}
    method_map = {}   # id -> {id, label, full_name, desc, papers: []}
    
    # Read CSV
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                paper_id = row.get('id', '').strip() or f"p{idx+1}"
                title = row.get('title', '').strip()
                short_title = row.get('short_title', '').strip() or title
                raw_status = row.get('status', '').strip().lower()
                year = row.get('year', '').strip() or '2026'
                venue = row.get('venue', '').strip()
                
                # Check status: published vs on-going (ghost)
                is_ongoing = any(k in raw_status for k in ["on-going", "ongoing", "ghost", "under_review", "in_prep", "draft", "working"])
                status = "ongoing" if is_ongoing else "published"
                
                # Human-friendly badge
                if "under_review" in raw_status or "under review" in venue.lower():
                    badge = "Under Review"
                elif "in_prep" in raw_status or "in preparation" in venue.lower():
                    badge = "In Preparation"
                elif is_ongoing:
                    badge = "On-going"
                else:
                    badge = "Published"
                
                # Parse Core and Sub Keywords
                core_kws = clean_list(row.get('core_keywords', ''))
                sub_kws = clean_list(row.get('sub_keywords', ''))
                methods = clean_list(row.get('methods', ''))
                
                paper_kw_ids = []
                paper_m_ids = []
                
                # Register Core Keywords
                for kw in core_kws:
                    kw_id = slugify(kw, prefix="kw_")
                    if kw_id not in keyword_map:
                        keyword_map[kw_id] = {"id": kw_id, "label": kw, "category": "core", "papers": []}
                    keyword_map[kw_id]["papers"].append(short_title)
                    paper_kw_ids.append(kw_id)
                    
                # Register Sub Keywords
                for kw in sub_kws:
                    kw_id = slugify(kw, prefix="kw_")
                    if kw_id not in keyword_map:
                        keyword_map[kw_id] = {"id": kw_id, "label": kw, "category": "sub", "papers": []}
                    keyword_map[kw_id]["papers"].append(short_title)
                    paper_kw_ids.append(kw_id)
                    
                # Register Methods
                for m in methods:
                    m_id = slugify(m, prefix="m_")
                    if m_id not in method_map:
                        method_map[m_id] = {
                            "id": m_id,
                            "label": m,
                            "full_name": m,
                            "desc": f"Methodology: {m}",
                            "papers": []
                        }
                    method_map[m_id]["papers"].append(short_title)
                    paper_m_ids.append(m_id)
                    
                papers.append({
                    "id": paper_id,
                    "title": title,
                    "short_title": short_title,
                    "status": status,
                    "badge": badge,
                    "year": year,
                    "venue": venue,
                    "keywords": paper_kw_ids,
                    "methods": paper_m_ids
                })
    except Exception as e:
        print(f"[Sync Error] Failed to read CSV: {e}", file=sys.stderr)
        sys.exit(1)
        
    print(f"[Sync] Parsed {len(papers)} papers/projects, {len(keyword_map)} unique keywords, {len(method_map)} methods.")
    
    # Generate YAML content
    lines = [
        "# -----------------------------------------------------------------------------",
        "# AUTO-GENERATED from _data/ego_network.csv by bin/sync_ego_network.py",
        "# DO NOT EDIT THIS FILE DIRECTLY - Edit _data/ego_network.csv instead!",
        "# -----------------------------------------------------------------------------",
        "",
        "ego:",
        '  name: "Danho, Kim"',
        '  label: "Bibliometrics & SNA Researcher"',
        '  affiliation: "Library & Information Science"',
        "",
        "keywords:"
    ]
    
    # Sort keywords (core first, then alphabetical)
    sorted_kws = sorted(keyword_map.values(), key=lambda x: (0 if x["category"] == "core" else 1, x["label"]))
    for kw in sorted_kws:
        lines.append(f"  - id: {kw['id']}")
        lines.append(f"    label: {format_yaml_str(kw['label'])}")
        lines.append(f"    category: {kw['category']}")
        unique_papers = list(dict.fromkeys(kw['papers']))
        p_str = ", ".join([format_yaml_str(p) for p in unique_papers])
        lines.append(f"    linked_papers: [{p_str}]")
        
    lines.append("")
    lines.append("methods:")
    for m in method_map.values():
        lines.append(f"  - id: {m['id']}")
        lines.append(f"    label: {format_yaml_str(m['label'])}")
        lines.append(f"    full_name: {format_yaml_str(m['full_name'])}")
        lines.append(f"    desc: {format_yaml_str(m['desc'])}")
        unique_papers = list(dict.fromkeys(m['papers']))
        p_str = ", ".join([format_yaml_str(p) for p in unique_papers])
        lines.append(f"    linked_papers: [{p_str}]")
        
    lines.append("")
    lines.append("papers:")
    for p in papers:
        lines.append(f"  - id: {p['id']}")
        lines.append(f"    title: {format_yaml_str(p['title'])}")
        lines.append(f"    short_title: {format_yaml_str(p['short_title'])}")
        lines.append(f"    year: {p['year']}")
        lines.append(f"    venue: {format_yaml_str(p['venue'])}")
        lines.append(f"    status: {p['status']}")
        lines.append(f"    badge: {format_yaml_str(p['badge'])}")
        
        # Keywords array
        kw_formatted = ", ".join([f'"{k}"' for k in p['keywords']])
        lines.append(f"    keywords: [{kw_formatted}]")
        
        # Methods array
        m_formatted = ", ".join([f'"{m}"' for m in p['methods']])
        lines.append(f"    methods: [{m_formatted}]")
        lines.append("")
        
    yaml_content = "\n".join(lines) + "\n"
    
    # Write to _data/ego_network.yml
    try:
        with open(yml_path, mode='w', encoding='utf-8') as f:
            f.write(yaml_content)
        print(f"[Sync Success] Successfully synchronized to {yml_path}!")
    except Exception as e:
        print(f"[Sync Error] Failed to write YAML: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    sync_network()
