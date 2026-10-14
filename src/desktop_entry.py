"""Frozen entry: multiprocessing dispatch MUST precede GUI/heavy imports."""
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    import sys
    if "--system-audio-check" in sys.argv:
        from system_audio_check import main
        main()
    elif "--packaged-check" in sys.argv:
        from packaged_check import main
        main()
    else:
        from gui import main
        main()
