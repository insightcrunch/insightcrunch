#!/usr/bin/env python3
"""
fix_wwii_medicine_links.py

Repoints the WWII series medical links at the ReportMedic reference page.

The problem:
    24 posts in the WWII Decisions series contain 53 links written as
    ](/reportmedic/some-medical-slug). That is a relative path on
    insightcrunch.com pointing at a section of this site that was never built,
    so every one of them is a 404. The target articles were never written and
    never will be.

The fix:
    A single reference page, tools/wwii-battlefield-medicine.html on
    reportmedic.org, covers all 49 distinct subjects across 20 anchored
    sections. Each old slug maps to the section that answers it, so the reader
    lands on the right subject rather than at the top of a long page.

    ](/reportmedic/frostbite-cold-weather-injury)
        becomes
    ](https://reportmedic.org/tools/wwii-battlefield-medicine.html#cold-injury)

Anchor text and surrounding prose are never touched. Only the link target moves.

The ALIASES table below is generated from the WW.aliases map inside the page
itself. If a section id is renamed on the page, update both together or the
links will resolve to the top of the page instead of the section.

Safe to run repeatedly. A clean repo produces no diff.

Usage:
    python _scripts/fix_wwii_medicine_links.py --dry-run
    python _scripts/fix_wwii_medicine_links.py
"""

import argparse
import glob
import os
import re
import sys

PAGE = 'https://reportmedic.org/tools/wwii-battlefield-medicine.html'

# old slug -> anchor id on the reference page
ALIASES = {
    'frostbite-cold-weather-injury': 'cold-injury',
    'frostbite-cold-weather-injury-treatment': 'cold-injury',
    'frostbite-cold-weather-injury-mountain-warfare': 'cold-injury',
    'frostbite-treatment-long-term-recovery': 'cold-injury',
    'frostbite-hypothermia-eastern-front-winter': 'cold-injury',
    'cold-weather-injury-and-frostbite': 'cold-injury',
    'hypothermia-symptoms-treatment': 'cold-injury',
    'hypothermia-cold-weather-injury-field-treatment': 'cold-injury',
    'hypothermia-cold-water-immersion': 'cold-injury',
    'cold-water-immersion-survival-times': 'naval-and-immersion',
    'seasickness-exposure-combat-effectiveness': 'naval-and-immersion',
    'casualty-evacuation-and-triage-at-sea': 'naval-and-immersion',
    'heat-exhaustion-dehydration-treatment': 'heat-and-dehydration',
    'dehydration-heat-exhaustion-field-treatment': 'heat-and-dehydration',
    'burn-injury-treatment-severity-classification': 'burns-and-blast',
    'burn-injury-treatment-history': 'burns-and-blast',
    'thermal-burn-treatment': 'burns-and-blast',
    'aviation-burns-reconstructive-surgery': 'burns-and-blast',
    'smoke-inhalation-respiratory-injury': 'burns-and-blast',
    'blast-injury-concussion-mechanics': 'burns-and-blast',
    'blast-and-crush-injuries-battlefield': 'burns-and-blast',
    'prisoner-of-war-nutrition-recovery': 'starvation-and-nutrition',
    'siege-starvation-physiology-world-war-two': 'starvation-and-nutrition',
    'wartime-rationing-nutrition-britain': 'starvation-and-nutrition',
    'combat-stress-and-operational-fatigue': 'combat-stress',
    'combat-fatigue-aircrew-1940': 'combat-stress',
    'wartime-psychiatric-assessment-prisoners': 'combat-stress',
    'mountain-warfare-medical-evacuation-cold-casualties': 'evacuation-and-triage',
    'combat-trauma-medicine-pacific-theater': 'evacuation-and-triage',
    'pearl-harbor-casualty-treatment-december-1941': 'evacuation-and-triage',
    'battlefield-casualties-1939-poland': 'evacuation-and-triage',
    'atlantic-theater-casualty-protocols-1941-1942': 'medical-logistics',
    'allied-supply-chain-architecture-western-europe': 'medical-logistics',
    'wartime-blood-plasma-medical-logistics': 'transfusion-and-plasma',
    'quinine-malaria-wartime-supply': 'epidemic-disease',
    'bubonic-plague-symptoms-and-treatment': 'epidemic-disease',
    'cholera-causes-symptoms-treatment': 'epidemic-disease',
    'warsaw-1939-siege-medical-response': 'epidemic-disease',
    'civilian-medical-collapse-poland-1939': 'civilian-and-forensic',
    'occupied-europe-civilian-mortality-1940-1944': 'civilian-and-forensic',
    'vichy-occupation-deportation-health-records': 'civilian-and-forensic',
    'mass-deportation-health-consequences-1940': 'civilian-and-forensic',
    'soviet-deportation-mortality-health': 'civilian-and-forensic',
    'soviet-deportation-transport-mortality': 'civilian-and-forensic',
    'wartime-mass-grave-forensic-identification': 'civilian-and-forensic',
    'forensic-identification-contested-deaths': 'civilian-and-forensic',
    '1938-british-air-raid-casualty-projections': 'civilian-and-forensic',
    'september-1938-civil-defense-gas-mask-mobilization': 'chemical-and-gas',
    'acute-radiation-syndrome': 'radiation-injury',}

LINK = re.compile(r'\]\(/reportmedic/([a-z0-9][a-z0-9-]*)/?\)')


def process(path, dry_run):
    """Rewrite one file. Returns (rewritten, unmapped list)."""
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            original = handle.read()
    except (UnicodeDecodeError, OSError) as exc:
        print(f"  SKIP {path}: {exc}")
        return 0, []

    unmapped = []
    counts = {'n': 0}

    def replace(match):
        slug = match.group(1)
        anchor = ALIASES.get(slug)
        if not anchor:
            unmapped.append(slug)
            return match.group(0)
        counts['n'] += 1
        return f']({PAGE}#{anchor})'

    updated = LINK.sub(replace, original)

    if counts['n'] and not dry_run:
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(updated)

    return counts['n'], unmapped


def main():
    parser = argparse.ArgumentParser(
        description='Repoint WWII series medical links at the ReportMedic reference page.'
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Report what would change without writing any file.')
    args = parser.parse_args()

    if not os.path.isdir('_posts'):
        print('ERROR: run this from the repository root, _posts not found.')
        return 1

    files = sorted(glob.glob('_posts/*.md'))
    print(f"Scanning {len(files)} posts for /reportmedic/ links.")
    print(f"Alias table covers {len(ALIASES)} slugs across "
          f"{len(set(ALIASES.values()))} anchored sections.")
    print()

    total = 0
    changed = 0
    all_unmapped = []

    for path in files:
        n, unmapped = process(path, args.dry_run)
        all_unmapped.extend(unmapped)
        if n:
            changed += 1
            total += n
            print(f"  {os.path.basename(path)}: {n}")

    print()
    verb = 'Would repoint' if args.dry_run else 'Repointed'
    print(f"{verb} {total} link(s) across {changed} post(s) to "
          f"wwii-battlefield-medicine.html")

    if all_unmapped:
        unique = sorted(set(all_unmapped))
        print()
        print(f"UNMAPPED: {len(all_unmapped)} link(s) using "
              f"{len(unique)} slug(s) not in the alias table:")
        for slug in unique:
            print(f"  {slug}")
        print("  Add each to ALIASES here and to WW.aliases on the page, then re-run.")

    if args.dry_run:
        print('\nDry run, no files written.')

    return 0


if __name__ == '__main__':
    sys.exit(main())
