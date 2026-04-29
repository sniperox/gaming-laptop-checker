# Release Guide

## Build Locally

```powershell
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1 -Clean
```

Verify:

```powershell
.\dist\GamingLaptopChecker.exe --version
.\dist\GamingLaptopChecker.exe --smoke-report
```

## Publish Manually

1. Create a GitHub release, for example `v1.0.0`.
2. Upload `dist\GamingLaptopChecker.exe`.
3. Confirm this URL downloads the asset:

```text
https://github.com/sniperox/gaming-laptop-checker/releases/latest/download/GamingLaptopChecker.exe
```

## Publish With GitHub Actions

Push a tag:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

The workflow builds the EXE on Windows and attaches it to the release.
