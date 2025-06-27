# src/crawler/run.py
import sys, pathlib, requests, hashlib, shutil

def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def download(url: str, dest: pathlib.Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            shutil.copyfileobj(r.raw, f)

def main(state_code: str):
    state = state_code.lower()
    urlfile = pathlib.Path(__file__).with_name(f"urls_{state}.txt")
    raw_root = pathlib.Path("data/raw") / state.upper()
    if not urlfile.exists():
        print(f"[!] {urlfile} not found")
        sys.exit(1)

    for line in urlfile.read_text().splitlines():
        url = line.strip()
        if not url or url.startswith("#"):
            continue
        fname = raw_root / url.split("/")[-1]
        if fname.exists():
            # re-download only if remote differs by SHA256 (cheap HEAD fallback skipped for simplicity)
            try:
                tmp = fname.with_suffix(".tmp")
                download(url, tmp)
                if sha256(tmp) != sha256(fname):
                    tmp.replace(fname)
                    print("⇣  updated", fname.name)
                else:
                    tmp.unlink()
                    print("✓  up-to-date", fname.name)
            except Exception as e:
                print("!  failed refresh:", fname.name, e)
        else:
            try:
                download(url, fname)
                print("⇣  new", fname.name)
            except Exception as e:
                print("!  failed:", fname.name, e)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run.py OR")
        sys.exit(1)
    main(sys.argv[1])
