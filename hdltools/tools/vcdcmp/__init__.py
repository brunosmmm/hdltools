"""VCD file comparison tool."""

import argparse
import sys
from pathlib import Path
from hdltools.vcd.compare import compare_vcd_files


def main():
    """Main entry point for VCD comparison tool."""
    parser = argparse.ArgumentParser(
        description="Compare two VCD files for functional equivalence",
        prog="vcdcmp"
    )
    
    parser.add_argument('file1', help='First VCD file to compare')
    parser.add_argument('file2', help='Second VCD file to compare')
    parser.add_argument(
        '--tolerance', '-t', 
        type=float, 
        default=1e-9,
        help='Time tolerance for comparison (default: 1e-9)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Only show summary result'
    )
    parser.add_argument(
        '--max-mismatches', '-m',
        type=int,
        default=10,
        help='Maximum number of mismatches to display (default: 10)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed comparison information'
    )
    parser.add_argument(
        '--streaming',
        action='store_true',
        help='Force streaming mode for large files'
    )
    parser.add_argument(
        '--no-streaming',
        action='store_true',
        help='Disable streaming mode (load entire files into memory)'
    )
    parser.add_argument(
        '--max-memory',
        type=int,
        default=100,
        help='Maximum memory to use for buffering in MB (default: 100)'
    )
    
    args = parser.parse_args()
    
    # Check if files exist
    file1_path = Path(args.file1)
    file2_path = Path(args.file2)
    
    if not file1_path.exists():
        print(f"Error: File '{args.file1}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not file2_path.exists():
        print(f"Error: File '{args.file2}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    # Determine streaming mode
    use_streaming = None
    if args.streaming and args.no_streaming:
        print("Error: Cannot specify both --streaming and --no-streaming", file=sys.stderr)
        sys.exit(1)
    elif args.streaming:
        use_streaming = True
    elif args.no_streaming:
        use_streaming = False
    
    # Show file sizes for information
    size1_mb = file1_path.stat().st_size / (1024 * 1024)
    size2_mb = file2_path.stat().st_size / (1024 * 1024)
    total_size_mb = size1_mb + size2_mb
    
    if not args.quiet:
        print(f"File sizes: {size1_mb:.1f}MB + {size2_mb:.1f}MB = {total_size_mb:.1f}MB total")
        if use_streaming is None:
            mode = "streaming" if total_size_mb > args.max_memory else "regular"
            print(f"Using {mode} mode (auto-detected)")
        elif use_streaming:
            print("Using streaming mode (forced)")
        else:
            print("Using regular mode (forced)")
    
    # Perform comparison
    try:
        result = compare_vcd_files(
            str(file1_path), 
            str(file2_path), 
            time_tolerance=args.tolerance,
            use_streaming=use_streaming,
            max_memory_mb=args.max_memory
        )
    except Exception as e:
        print(f"Error comparing VCD files: {e}", file=sys.stderr)
        sys.exit(2)
    
    # Display results
    if args.quiet:
        if result.equivalent:
            print("EQUIVALENT")
        else:
            print("DIFFERENT")
    else:
        if args.verbose or not result.equivalent:
            result.print_summary(max_mismatches=args.max_mismatches)
        else:
            print(f"✓ VCD files are functionally equivalent")
            print(f"  Compared {len(result.file1_signals)} signals")
    
    # Exit with appropriate code
    sys.exit(0 if result.equivalent else 1)


if __name__ == '__main__':
    main()