# Datasheet assets moved

The datasheet application (Typst sources, PDF output, build scripts, and bundled
assets) lives in the **`datasheet`** repo:

```
D:\XDrive\datasheet\examples\solar-lora-sensor\
```

Edit and build there:

```powershell
cd D:\XDrive\datasheet
.\tools\sync-from-source.ps1          # refresh assets from this hardware repo
.\tools\build.ps1 -Example solar-lora-sensor -SkipBlender
```

Open `examples/solar-lora-sensor/out/datasheet.pdf`.

This folder is not the canonical home for datasheet files.
