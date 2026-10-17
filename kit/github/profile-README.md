<picture>
  <source media="(prefers-color-scheme: dark)" srcset="readme-banner@2x-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="readme-banner@2x-light.png">
  <img alt="FusionSpace · Tolerances tight. Ambitions loose." src="readme-banner@2x-dark.png" width="100%">
</picture>

### Hi, I'm Neer.

I'm a software engineer in Auburn, Alabama. Under the name [FusionSpace](https://fusionspace.co) I make free, open-source
software for hobby and high-power rockets: [HPR Sim](https://hpr.fusionspace.co/the-simulator.html), a flight simulator,
and the suite being built around it.

#### FusionSpace HPR

One suite for hobby and high-power rockets, written in Rust, MIT or Apache-2.0. Every product's source and releases live in
[fusionspace-eridanus](https://github.com/nrdptel/fusionspace-eridanus).

- **HPR Sim** · released, [0.1.0](https://github.com/nrdptel/fusionspace-eridanus/releases/tag/v0.1.0) (2026-10-08)<br>
  A 6-DOF flight simulator: a Rust library, the `hpr` command and a Python package. Reads OpenRocket designs, flies
  Monte Carlo dispersions, and publishes [how far to trust it](https://hpr.fusionspace.co/trusting-a-simulation.html).<br>
  [Guide](https://hpr.fusionspace.co/the-simulator.html) · [Docs](https://hpr.fusionspace.co/) ·
  [PyPI](https://pypi.org/project/fusionspace-hpr/) · [crates.io](https://crates.io/crates/fusionspace-hpr)
- **Analyzer** · in preparation, for 0.2<br>
  Reads a flight computer's log and sets the flight beside its simulation.
- **Competition Kit** · in preparation, for 0.4<br>
  Challenge rules, presets and submission packs for student rocketry competitions.
- **The app** · in preparation, a preview in 0.5, then 1.0<br>
  Design, simulation and flight replay on the desktop, the web and phones.
- After 1.0: **Motor Designer**, **Recovery Designer** and **Avionics**.

Try it: `pip install fusionspace-hpr` for Python, or `cargo install fusionspace-hpr-cli --locked` for the `hpr` command.

#### Web tools

Four tools for the browser that came before FusionSpace HPR. Each keeps working at its own address until its rebuild
inside HPR ships.

- **[HPR Motor Finder](https://motor.fusionspace.co)** · AeroTech, Cesaroni and Loki motor stock and prices across U.S.
  vendors, matched to ThrustCurve. [Source](https://github.com/nrdptel/Hobby-Rocket-Motor-Finder)
- **[Charge](https://charge.fusionspace.co)** · Sizes black-powder ejection charges, every constant shown, with a log of
  your ground tests. [Source](https://github.com/nrdptel/fusionspace-charge)
- **[Window](https://window.fusionspace.co)** · Launch weather at any U.S. field: surface wind, winds aloft, storms, cloud
  ceiling and a few days ahead. [Source](https://github.com/nrdptel/fusionspace-window)
- **[Muster](https://muster.fusionspace.co)** · Which reloads, closures and spacers fit each reloadable motor case, and the
  parts to buy. [Source](https://github.com/nrdptel/fusionspace-muster)

#### How they're built

- **Show the working.** Formulas, constants and sources are there to read, not hidden.
- **Say how far to trust it.** Estimates are labeled as estimates, with their spread. Never a go/no-go verdict.
- **Work at the field.** Readable in sun, with big targets for cold hands. HPR Sim's core needs no network.
- **No accounts, no tracking.**

Every FusionSpace site, tool and app follows one brand and product system,
[fusionspace-design](https://github.com/nrdptel/fusionspace-design). The front page is
[fusionspace-site](https://github.com/nrdptel/fusionspace-site).
