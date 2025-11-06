#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Test pentru generarea Markdown"""

import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from hybrid_parser import HybridLegislativeParser

# Citește fișier test
with open('LEGE 121 30_04_2024.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Parsează
parser = HybridLegislativeParser()
df, metrics = parser.parse(content, 'html')

print(f"✅ Parsed {len(df)} articole")
print(f"✅ Confidence: {metrics['confidence']:.2f}")

# Salvează
saved = parser.save_to_rezultate(df, 'test')

print(f"\n📁 Fișiere salvate:")
for fmt, path in saved.items():
    print(f"  - {fmt}: {path}")

# Afișează primele linii din MD
if 'markdown' in saved:
    with open(saved['markdown'], 'r', encoding='utf-8') as f:
        lines = f.readlines()[:50]
    print(f"\n📄 Preview Markdown (primele 50 linii):")
    print("".join(lines))
