import sys

if __name__ == "__main__":
    try:
        from toolkit.app import main
        main()
    except ImportError as exc:
        print(f"Desktop dependency missing: {exc}\nInstall Python 3.11+ with Tcl/Tk support.", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        import tkinter
        if not isinstance(exc, tkinter.TclError):
            raise
        print(f"Desktop runtime could not start: {exc}\n"
              "Run python -m tkinter to check your Python installation.\n"
              "See README.md for the project-local runtime setup option.", file=sys.stderr)
        sys.exit(1)
