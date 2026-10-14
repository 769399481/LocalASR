# Clean Windows validation — NOT yet executed

Use a fresh Windows 10/11 x64 VM or separate Windows computer, with no Python, Conda, project checkout, developer PATH, CUDA toolkit or Hugging Face cache. A normal vendor display driver is allowed and should be recorded. Keep a separate CPU-only run and a supported NVIDIA run.

1. Record Windows edition/build, RAM, CPU/GPU, display scaling, network/proxy conditions and EXE SHA256.
2. Copy the complete standalone directory as a standard user. Double-click LocalASR.exe with no terminal activation.
3. Verify the GUI, first-run checking state, recommendation and Diagnostics version. Confirm no writes to Program Files/application resources.
4. Initially disconnect network: app should still open, missing models should offer a concise download prompt. Cancel/skip setup should leave app usable for recovery and export.
5. Reconnect; download Fast/Balanced. Record progress, cancel mid-transfer, restart and retry. Confirm a partial directory is not installed. Reconnect after an interruption and complete download.
6. Verify insufficient-space check using a test user-data volume. Do not fill the OS disk or delete real data.
7. Verify download integrity rejection with test fixtures, not by modifying user's models. Confirm incomplete downloads do not become selectable.
8. With model complete, disconnect network. Transcribe a short test file and verify all five formats. Test microphone Start/Stop twice; verify original English remains independent of translation.
9. Enable Translation: verify optional language model prompt, then download and test English→Chinese. Verify offline bilingual operation and spawned worker shutdown.
10. Save preferences, close, reopen, recover a synthetic session; verify diagnostics contains no audio text, username paths or private filenames.
11. Copy a second build into a separate application directory. Confirm preferences, models, recovery and output remain reusable.
12. Installer, shortcuts, uninstall and automatic updates are explicitly deferred until the main features stabilize.
13. Test 100%, 125%, 150% display scaling and a smaller window; keyboard navigation, partial and status labels remain visible.
14. Archive results, screenshots, sanitized diagnostics and failures. Do not label the release clean-Windows verified until this checklist has actually passed.

Public release gate: select the project's license, review bundled binary notices/source obligations, test the checklist, sign release artifacts if available, publish checksum and real download link. No automatic update/account service is required.
