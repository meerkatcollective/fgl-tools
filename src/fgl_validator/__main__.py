import sys
from pathlib import Path
from . import validate
from .profile import PROFILES, DEFAULT


def main():
    args = sys.argv[1:]
    profile = DEFAULT

    # Parse optional --profile NAME flag
    if "--profile" in args:
        idx = args.index("--profile")
        if idx + 1 >= len(args):
            print("fgl_validator: --profile requires a NAME argument", file=sys.stderr)
            sys.exit(2)
        profile_name = args[idx + 1]
        if profile_name not in PROFILES:
            known = ", ".join(sorted(PROFILES))
            print(
                f"fgl_validator: unknown profile '{profile_name}'. "
                f"Known profiles: {known}",
                file=sys.stderr,
            )
            sys.exit(2)
        profile = PROFILES[profile_name]
        args = args[:idx] + args[idx + 2:]

    if not args:
        print("usage: python -m fgl_validator [--profile NAME] <file>", file=sys.stderr)
        sys.exit(2)

    path = Path(args[0])
    diags = validate(path.read_text(), profile=profile)
    for d in diags:
        print(f"{path}:{d.line}:{d.col}: {d.severity}: [{d.code}] {d.message}")
    sys.exit(1 if any(d.severity == "error" for d in diags) else 0)


if __name__ == "__main__":
    main()
