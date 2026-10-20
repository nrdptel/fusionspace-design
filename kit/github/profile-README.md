<picture>
  <source media="(prefers-color-scheme: dark)" srcset="readme-banner@2x-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="readme-banner@2x-light.png">
  <img alt="FusionSpace · Tolerances tight. Ambitions loose." src="readme-banner@2x-dark.png" width="100%">
</picture>

### Hi, I'm Neer.

I'm a software engineer in Auburn, Alabama. Under the name [FusionSpace](https://fusionspace.co) I make free, open-source
software for hobby and high-power rockets: [HPR Sim](https://hpr.fusionspace.co/the-simulator.html), a flight simulator,
and the suite I'm building around it.

#### FusionSpace HPR

It's one suite for hobby and high-power rockets, written in Rust and licensed MIT or Apache-2.0. Every product's source
and releases live in [fusionspace-eridanus](https://github.com/nrdptel/fusionspace-eridanus).

HPR Sim is released: version [0.1.0](https://github.com/nrdptel/fusionspace-eridanus/releases/tag/v0.1.0), from 2026-10-08. It's a 6-DOF
flight simulator: a Rust library, the `hpr` command and a Python package. It reads OpenRocket designs, flies Monte Carlo
dispersions, and publishes [how far to trust it](https://hpr.fusionspace.co/trusting-a-simulation.html).
[Guide](https://hpr.fusionspace.co/the-simulator.html) · [Docs](https://hpr.fusionspace.co/) ·
[PyPI](https://pypi.org/project/fusionspace-hpr/) · [crates.io](https://crates.io/crates/fusionspace-hpr)

To try it, run `pip install fusionspace-hpr` for Python, or `cargo install fusionspace-hpr-cli --locked` for the `hpr`
command. The rest of the suite is in preparation:

- the Analyzer, for 0.2, reads a flight computer's log and sets the flight beside its simulation;
- the Competition Kit, for 0.4, holds challenge rules, presets and submission packs for student rocketry competitions;
- the app, with a preview in 0.5 and then 1.0, does design, simulation and flight replay on the desktop, the web and
  phones;
- after 1.0 come the Motor Designer, the Recovery Designer and Avionics.

#### Web tools

These four browser tools came before FusionSpace HPR. Each keeps working at its own address until its rebuild inside HPR
ships.

- [HPR Motor Finder](https://motor.fusionspace.co) shows AeroTech, Cesaroni and Loki motor stock and prices across U.S.
  vendors, matched to ThrustCurve. [Source](https://github.com/nrdptel/Hobby-Rocket-Motor-Finder)
- [Charge](https://charge.fusionspace.co) sizes black-powder ejection charges, every constant shown, with a log of your
  ground tests. [Source](https://github.com/nrdptel/fusionspace-charge)
- [Window](https://window.fusionspace.co) gives launch weather at any U.S. field: surface wind, winds aloft, storms, cloud
  ceiling and a few days ahead. [Source](https://github.com/nrdptel/fusionspace-window)
- [Muster](https://muster.fusionspace.co) shows which reloads, closures and spacers fit each reloadable motor case, and
  the parts to buy. [Source](https://github.com/nrdptel/fusionspace-muster)

#### How they're built

- Show the working. Formulas, constants and sources are there to read, not hidden.
- Say how far to trust it. An estimate says it's an estimate and shows its spread. You never get a go/no-go verdict.
- Work at the field. Screens read well in sun and have big targets for cold hands. HPR Sim's core needs no network.
- No accounts, no tracking.

Every FusionSpace site, tool and app follows one brand and product system,
[fusionspace-design](https://github.com/nrdptel/fusionspace-design). The front page's source is
[fusionspace-site](https://github.com/nrdptel/fusionspace-site).
