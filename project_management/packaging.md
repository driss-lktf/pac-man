# Packaging & Deployment (Itch.io)

The game ships as a standalone executable built with **PyInstaller**, then
published on **Itch.io** as a free, **unlisted/private** build.

## 1. Build the executable

From the repository root:

```bash
./build.sh
```

This produces `dist/pac-man`, a self-contained binary that bundles the code,
`config.json` and the assigned `mazegenerator` package. Test it:

```bash
./dist/pac-man config.json
```

> The packaging spec is `pacman.spec` at the repository root. You may be asked
> to regenerate the package during the peer review — `./build.sh` does exactly
> that.

## 2. The release folder

`build.sh` also assembles the folder a player unzips, and zips it:

```
dist/pac-man-release/
├── pac-man            # the executable
├── config.json        # default configuration (editable)
├── play.sh            # launcher: runs ./pac-man config.json
└── README.txt         # minimal in-package instructions

dist/pac-man-linux.zip # the archive to upload
```

`play.sh` matters: the game takes **exactly one argument**, so a player who
just runs the bare executable would only get the usage line. The launcher
`cd`s next to itself and passes `config.json`, which also keeps
`highscores.json` next to the game.

`README.txt` carries the in-package instructions the subject asks for:
how to run, the controls, the rules, the cheat keys and the configurable
options.

## 3. Publish on Itch.io

1. Create a free account on <https://itch.io>, then **Dashboard >
   Create new project**.
2. **Kind of project = Downloadable**.
3. **Pricing = No payments** (free).
4. Upload `dist/pac-man-linux.zip`, then tick the platform it was built for
   (**Linux**) on the uploaded file.
5. **Visibility & access = Restricted** with a password, so the build stays
   private while remaining reachable during the peer review (Draft is
   owner-only).
6. **Save**, then use **View page** to get the URL, and record it in the
   README's *Packaging & Deployment* section.

### Optional: upload with `butler` (Itch.io CLI)

```bash
# install butler, then:
butler login
butler push dist/pac-man-release <user>/<game>:linux
```

`butler` is the better option for re-uploads: it only sends what changed and
versions each push as a channel build.

## Notes

- Build on the OS you target (Linux/macOS/Windows); PyInstaller is not a
  cross-compiler. The published Linux build only runs on Linux x86_64.
- Some GUI unzip tools drop the executable bit; `chmod +x pac-man play.sh`
  fixes it. The itch.io app preserves it.
- Keep the build **free** and **unlisted/private** as required by the subject.
