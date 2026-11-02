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
    # If cell contains semicolon, prefer semicolon split
    delimiters = ';' if ';' in cell else ','
    items = [item.strip() for item in cell.split(delimiters)]
    return [item for item in items if item]

def format_yaml_str(val):
    """Safely format string for YAML output."""
    if not val:
        return '""'
    val_str = str(val).strip()
    # Check if quotes are needed
    if any(c in val_str for c in [':', '#', '[', ']', '{', '}', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '\\']) or '\n' in val_str or '"' in val_str:
        escaped = val_str.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    return f'"{val_str}"'

def sync_network():
    # Resolve project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))
    
    csv_path = os.path.join(root_dir, "_data", "ego_network.csv")
    yml_path = os.path.join(root_dir, "_data", "ego_network.yml")
    
    if not os.path.exists(csv_path):
        print(f"[Sync Error] CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)
        
    print(f"[Sync] Reading data from {csv_path}...")
    
    papers = []
    keyword_map = {}  # id -> {label, category}
    method_map = {}   # id -> {label, full_name, desc}
    
    # Read CSV
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                paper_id = row.get('id', '').strip() or f"p{idx+1}"
                title = row.get('title', '').strip()
                short_title = row.get('short_title', '').strip() or title
                status = row.get('status', '').strip().lower() or 'published'
                year = row.get('year', '').strip() or '2026'
                venue = row.get('venue', '').strip()
                
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
                        keyword_map[kw_id] = {"id": kw_id, "label": kw, "category": "core"}
                    paper_kw_ids.append(kw_id)
                    
                # Register Sub Keywords
                for kw in sub_kws:
                    kw_id = slugify(kw, prefix="kw_")
                    if kw_id not in keyword_map:
                        keyword_map[kw_id] = {"id": kw_id, "label": kw, "category": "sub"}
                    paper_kw_ids.append(kw_id)
                    
                # Register Methods
                for m in methods:
                    m_id = slugify(m, prefix="m_")
                    if m_id not in method_map:
                        method_map[m_id] = {
                            "id": m_id,
                            "label": m,
                            "full_name": m,
                            "desc": f"Methodology: {m}"
                        }
                    paper_m_ids.append(m_id)
                    
                papers.append({
                    "id": paper_id,
                    "title": title,
                    "short_title": short_title,
                    "status": "ghost" if status in ["ghost", "under_review", "in_prep", "draft"] else "published",
                    "badge": "Under Review" if status in ["ghost", "under_review"] else ("In Prep" if status == "in_prep" else "Published"),
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
    
    # Sort keywords (core first, then sub)
    sorted_kws = sorted(keyword_map.values(), key=lambda x: (0 if x["category"] == "core" else 1, x["label"]))
    for kw in sorted_kws:
        lines.append(f"  - id: {kw['id']}")
        lines.append(f"    label: {format_yaml_str(kw['label'])}")
        lines.append(f"    category: {kw['category']}")
        
    lines.append("")
    lines.append("methods:")
    for m in method_map.values():
        lines.append(f"  - id: {m['id']}")
        lines.append(f"    label: {format_yaml_str(m['label'])}")
        lines.append(f"    full_name: {format_yaml_str(m['full_name'])}")
        lines.append(f"    desc: {format_yaml_str(m['desc'])}")
        
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
