#!/usr/bin/env python3
"""Independently sample infographic types with replacement."""
import argparse
import json
import secrets

TYPES = (
    'single-brand-infographic',
    'multi-brand-infographic',
    'recommendation-list-infographic',
    'concise-recommendation-list-infographic',
    'regional-brand-comparison-infographic',
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=1)
    parser.add_argument('--exclude', action='append', choices=TYPES, default=[])
    args = parser.parse_args()
    eligible = [item for item in TYPES if item not in args.exclude]
    if args.count < 1 or not eligible:
        parser.error('count must be positive and at least one type must remain')
    print(json.dumps([secrets.choice(eligible) for _ in range(args.count)], ensure_ascii=False))


if __name__ == '__main__':
    main()
