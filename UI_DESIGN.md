# Android Toolbox / Midnight UI

Kind: software — native Windows utility, Python + CustomTkinter.

## Direction

Deep navy with cyan actions; amber, mint, blue, coral, and rose identify tools
and device states. Rounded 18px panels, 10px controls, subtle borders, aligned
content edges, Segoe UI for native readability, and Consolas for command output.
Lucide interface icons are local, high-resolution PNGs generated from the
skill's pinned SVG source. No runtime icon download is needed.

The design-taste-frontend skill is adapted to an operating desktop tool.
Website hero/layout dealers, marketing sections, scroll scenes, photographs,
share metadata, and browser gates do not apply to native Tk widgets.
The user's requested rounded, colourful dark UI supplies the design direction.

Voice: direct, task-oriented, sentence-case headings; device data and operation
results remain real. There are no invented product claims or customer assets.
Verification fixtures are confined to `utils/check_ui.py`.

## Interface

- Floating sidebar, colour-coded navigation, persistent device picker and tool status.
- Device overview with connection state, system details, battery meter, reboot
  controls, and working shortcuts into the four common workflows.
- Local Gaussian-blurred cyan/blue accent lighting in the overview banner.
  It is a static decorative material, not desktop backdrop transparency.
  Compact windows hide it to
  prioritise device information. There are no looping decorative animations.
- Shared controls, keyboard focus rings and Enter/Space button activation,
  pointer hover and press feedback.
- Rounded panels across packages, files, flashing, terminal, logs, and wireless
  tools; readable terminal surfaces and visible file selection.
- Dense screens scroll vertically at the minimum 1024×720 window size.

## Verification

The HTML-only skill gate, browser layout checker, and web performance checker
are not applicable to this application and were not run. Native verification:

```powershell
python -m compileall -q ui utils
python -m utils.check_ui --shots "$env:TEMP\android-toolbox-review"
```

The native check renders all seven views at 1240×860 and 1024×720, checks control
bounds, populated lists, search and file selection, keyboard navigation, device
state transitions and the battery reset. It also checks
all seven views at 125% scaling. It never starts ADB monitoring or executes
device commands. Screenshots contain explicitly synthetic fixtures where named.

Physical-device operations still need a connected Android device for end-to-end
verification. No website waivers, stock photography, client slots, assumed
business facts, forms or canonical domain are applicable.

## Assets and maintenance

- Theme tokens: `utils/constants.py`
- CustomTkinter theme: `ui/components/style.py`
- Shared native widgets: `ui/components/widgets.py`
- Icon loader: `ui/components/icons.py`
- Icon attribution: `assets/icons/icons-credits.json` and `LICENSE.txt`
- Optional development-only rasterizer: `python utils/render_ui_icons.py`
  (requires `resvg-py`; the running app does not).

The existing PyInstaller command bundles the full `assets` directory, including
all icon PNGs and licence notices.
