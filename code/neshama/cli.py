#!/usr/bin/env python3
"""
Neshama CLI - Command Line Interface

Usage:
    neshama init <name>              Create new personality
    neshama validate <file>          Validate SKILL.md
    neshama export <name> [options]  Export to SKILL.md
    neshama preset <name>           Show preset details
"""

import argparse
import sys
from typing import Optional

from neshama.core.ocean import OceanManager
from neshama.core.personality import Personality
from neshama.core.validator import Validator
from neshama import __version__


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new personality."""
    import os
    try:
        # Create directory
        os.makedirs(args.name, exist_ok=True)
        
        # Get OCEAN parameters
        if args.preset:
            manager = OceanManager()
            if not manager.apply_preset(args.preset):
                print(f"Error: Unknown preset '{args.preset}'")
                return 1
            ocean = manager.params
        else:
            ocean = OceanManager().params
        
        # Create personality
        p = Personality(args.name, ocean)
        
        # Add default desires
        for d in Personality.DEFAULT_DESIRES:
            p.add_desire(d['name'], d['description'], d['priority'])
        
        # Save SKILL.md
        output_path = f"{args.name}/SKILL.md"
        p.save_skill_md(output_path)
        
        print(f"✓ Created personality: {args.name}")
        print(f"  Output: {output_path}")
        print(f"  Preset: {args.preset or 'default'}")
        print()
        print("Next steps:")
        print(f"  neshama validate {output_path}")
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a SKILL.md file."""
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        validator = Validator()
        result = validator.validate_skill_md(content)
        
        print(result.summary())
        
        if result.warnings:
            print()
            for warning in result.warnings:
                print(f"  ⚠ {warning}")
        
        if args.verbose and result.infos:
            print()
            for info in result.infos:
                print(f"  ℹ {info}")
        
        return 0 if result.valid else 1
    except FileNotFoundError:
        print(f"Error: File not found: {args.file}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_export(args: argparse.Namespace) -> int:
    """Export personality to file."""
    try:
        # Get OCEAN from preset or arguments
        if args.preset:
            manager = OceanManager()
            if not manager.apply_preset(args.preset):
                print(f"Error: Unknown preset '{args.preset}'")
                return 1
            ocean = manager.params
        else:
            ocean = OceanManager().params
        
        # Create and configure personality
        p = Personality(args.name, ocean)
        
        for d in Personality.DEFAULT_DESIRES:
            p.add_desire(d['name'], d['description'], d['priority'])
        
        # Set style
        if args.style:
            p.set_response_style(
                directness=args.style.get('directness', 0.7),
                humor=args.style.get('humor', 0.5),
                empathy=args.style.get('empathy', 0.6)
            )
        
        # Export
        if args.output:
            p.save_skill_md(args.output)
            print(f"✓ Exported to: {args.output}")
        else:
            print(p.generate_skill_md())
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_preset(args: argparse.Namespace) -> int:
    """Show preset details."""
    manager = OceanManager()
    preset = manager.get_preset(args.name)
    
    if not preset:
        print(f"Error: Unknown preset '{args.name}'")
        print()
        print("Available presets:")
        for name in manager.PRESETS.keys():
            print(f"  - {name}")
        return 1
    
    print(f"Preset: {args.name}")
    print()
    print(preset.get_summary())
    print()
    for trait in ['openness', 'conscientiousness', 'extraversion', 
                  'agreeableness', 'neuroticism']:
        print(preset.get_trait_description(trait))
    
    return 0


def cmd_list_presets(args: argparse.Namespace) -> int:
    """List all available presets."""
    manager = OceanManager()
    
    print("Available presets:")
    for name, params in manager.PRESETS.items():
        print(f"  {name:15} O:{params.openness:.2f} C:{params.conscientiousness:.2f} "
              f"E:{params.extraversion:.2f} A:{params.agreeableness:.2f} N:{params.neuroticism:.2f}")
    
    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='neshama',
        description='Neshama - AI Personality Operating System'
    )
    parser.add_argument('--version', action='version', version=f'neshama {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # init command
    init_parser = subparsers.add_parser('init', help='Create new personality')
    init_parser.add_argument('name', help='Personality name')
    init_parser.add_argument('--preset', '-p', help='Use a preset (analyst, helper, etc.)')
    
    # validate command
    validate_parser = subparsers.add_parser('validate', help='Validate SKILL.md')
    validate_parser.add_argument('file', help='Path to SKILL.md file')
    validate_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    # export command
    export_parser = subparsers.add_parser('export', help='Export personality')
    export_parser.add_argument('name', help='Personality name')
    export_parser.add_argument('--preset', '-p', help='Use a preset')
    export_parser.add_argument('--output', '-o', help='Output file path')
    
    # preset command
    preset_parser = subparsers.add_parser('preset', help='Show preset details')
    preset_parser.add_argument('name', help='Preset name')
    
    # list-presets command
    subparsers.add_parser('list', help='List all presets')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    commands = {
        'init': cmd_init,
        'validate': cmd_validate,
        'export': cmd_export,
        'preset': cmd_preset,
        'list': cmd_list_presets,
    }
    
    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
