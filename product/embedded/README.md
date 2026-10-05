# Device screens

| File | What |
|---|---|
| `oled-128x64-*.png` | 1:1 frame buffers (and `@4x` previews): SAFE, ARMED with a fault, in flight, landed |
| `tft-240x240-recovery.*` | A color ground-station screen in the dark roles |
| `fs_lvgl_styles.c/.h` | LVGL styles (checked against LVGL 9.3) |

Text on the OLED screens is Spleen (BSD-2, `LICENSE-Spleen.txt`), which u8g2 includes. Rules in `product/embedded.md`.
