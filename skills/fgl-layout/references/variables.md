# `<VAn>` Runtime Variables

Boca firmware substitutes `<VAn>` tokens at print time with values from the printer's runtime state. **No client-side data is needed** — the printer fills in the value from its own EEPROM / NVRAM / config. This makes `<VAn>` ideal for printer self-diagnostic tickets and field-service health checks.

The most useful indices, sourced from the BOCA cheat sheet's `CFG.html` template:

| Token | Value |
|---|---|
| `<VA1>` | Serial number |
| `<VA2>` | Font file |
| `<VA7>` | Firmware / PROM version |
| `<VA10>` | Serial port baud rate |
| `<VA11>` | Printer type |
| `<VA12>` | Print speed |
| `<VA13>` | Ticket type |
| `<VA14>` | Status return mode |
| `<VA17>` | DPI |
| `<VA18>` | Special head |
| `<VA19>` | Path type |
| `<VA32>` | Bidir parallel |
| `<VA34>` | USB enabled |
| `<VA50>` | Expansion memory |
| `<VA58>` | Font encoding |
| `<VA81>` | Ethernet enabled |
| `<VA82>` | IP address |
| `<VA83>` | MAC address |
| `<VA89>` | Shuffle mode |
| `<VA111>` | USB device type |
| `<VA112>` | Bluetooth enabled |
| `<VA113>` | WiFi enabled |

The validator does not constrain the variable index — `<VA1>` and `<VA999>` both pass — so it's safe to use any token your firmware supports without tripping `FGL001`.

## Canonical diagnostic-ticket idiom

```
<F3>
<RC10,10>Serial Number = <VA1>
<RC60,10>Firmware = <VA7>
<RC110,10>DPI = <VA17>
<RC160,10>IP Address = <VA82>
<RC210,10>MAC Address = <VA83>
<p>
```

This is the simplest "is the printer alive?" payload — everything is firmware-side, so it works without any host-side ticket database. The full `cfg_dump.fgl` fixture (`tests/fixtures/valid/cfg_dump.fgl`) shows the two-column layout with all 22 useful indices.

## When to use `<VAn>`

- After `<rte>` / `<rtd>` provisioning, to confirm the printer survived the reset.
- As a one-line health check from a fleet-management tool.
- During hardware iteration, to capture firmware/DPI/IP into a printable diagnostic so a remote operator can read the ticket and report numbers without console access.

Don't use `<VAn>` in customer-facing tickets — the values are noisy and can leak operational details.
