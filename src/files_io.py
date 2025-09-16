# files_io.py
# File parsing and directory helpers.

import os, re, csv
from datetime import datetime
from config import LETTERS, OUTPUT_ROOT

def parse_answer_key(path):
    """Return (exam_name, key_dict). First non-empty line is exam name. Lines like "12: B"."""
    mapping = {c:i for i,c in enumerate(LETTERS)}
    key, exam_name = {}, None
    if not os.path.exists(path):
        return exam_name, key
    with open(path, 'r', encoding='utf-8') as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    if not lines:
        return exam_name, key
    exam_name = lines[0]
    for ln in lines[1:]:
        m = re.match(r"(\d+)\s*:\s*([A-Ea-e])", ln)
        if m:
            q = int(m.group(1))
            a = mapping[m.group(2).upper()]
            key[q] = a
    return exam_name, key


def parse_class_section(path):
    """Return (section_name, dict_id_to_name). First non-empty line = section; then "Full Name, 00001"."""
    id2name = {}
    section_name = None
    if not os.path.exists(path):
        return section_name, id2name
    with open(path, 'r', encoding='utf-8') as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    if not lines:
        return section_name, id2name
    section_name = lines[0]
    for ln in lines[1:]:
        parts = [p.strip() for p in ln.split(',')]
        if len(parts) >= 2:
            name = ','.join(parts[:-1]).strip()
            sid = parts[-1].replace(' ', '')
            if re.fullmatch(r"\d{5}", sid):
                id2name[sid] = name
    return section_name, id2name


def ensure_outdir(path):
    os.makedirs(path, exist_ok=True)
