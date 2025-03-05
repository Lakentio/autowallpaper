# AutoWallpaper

AutoWallpaper is a Python script that automatically changes your desktop environment (DE) wallpapers based on the time of day (morning, afternoon, and evening). It is compatible with various desktop environments such as XFCE, KDE, GNOME, MATE, and Budgie.

## Features
- Automatically changes wallpapers based on the time of day.
- Configuration via terminal or GUI.
- Saves user preferences.
- Compatible with multiple desktop environments.
- Can be started automatically at system startup.

## Requirements
- Python 3.13 or higher
- `setuptools` and `pip` installed
- A compatible desktop environment (XFCE, KDE, GNOME, MATE, Budgie, etc.)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Lakentio/autowallpaper.git
   cd autowallpaper
   ```

2. Install the script globally:
   ```bash
   sudo python3.13 -m pip install .
   ```

3. Verify the installation:
   ```bash
   autowallpaper --help
   ```

## Configuration
```bash
autowallpaper --morning /path/to/morning_wallpaper.jpg --afternoon /path/to/afternoon_wallpaper.jpg --evening /path/to/evening_wallpaper.jpg --interval 10
```

## Removal
To remove AutoWallpaper from your system:
```bash
sudo python3.13 -m pip uninstall autowallpaper
```

## Contribution
Anyone can take the code and improve it, after all, even I didn't think it was well structured.
