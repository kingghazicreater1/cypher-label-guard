import unittest
from core.modality import derive_modality

class TestDeriveModality(unittest.TestCase):
    """
    Unit test for State-Independent Modality Derivation (core.modality.derive_modality).
    Root-cause test preventing lingering state from mutating video jobs into image jobs.
    """

    def test_video_extensions(self):
        video_files = [
            "WIN_20260830_21_50_59_Pro.mp4",
            "security_cam_1080p.MOV",
            "drone_flight_log.avi",
            "factory_floor.mkv",
            "stream_sample.webm",
            "clip.m4v",
            "mobile_capture.3gp",
            "flash_legacy.flv",
            "surveillance.wmv",
        ]
        for f in video_files:
            mod = derive_modality(f)
            self.assertEqual(mod, "VIDEO", f"File '{f}' failed to derive as VIDEO")

    def test_audio_extensions(self):
        audio_files = [
            "engine_hum.mp3",
            "acoustic_vibration.wav",
            "voice_memo.ogg",
            "speech_sample.m4a",
            "codec_test.aac",
            "lossless_specimen.flac",
        ]
        for f in audio_files:
            mod = derive_modality(f)
            self.assertEqual(mod, "AUDIO", f"File '{f}' failed to derive as AUDIO")

    def test_image_extensions(self):
        image_files = [
            "surface_bearing.png",
            "defect_macro.jpg",
            "sample_highres.jpeg",
            "optical_scan.webp",
            "animation.gif",
            "schematic.svg",
            "raw_frame.bmp",
            "microscope.tiff",
        ]
        for f in image_files:
            mod = derive_modality(f)
            self.assertEqual(mod, "IMAGE", f"File '{f}' failed to derive as IMAGE")

    def test_text_and_fallbacks(self):
        text_files = [
            "dataset.csv",
            "readme.txt",
            "specifications.json",
            "manifest.yaml",
            "plain_text_prompt",
            "",
            None,
        ]
        for f in text_files:
            mod = derive_modality(f)
            self.assertEqual(mod, "TEXT", f"Input '{f}' failed to derive as default TEXT")

    def test_state_independence_across_sequences(self):
        """
        Guarantees derive_modality is purely functional and holds zero lingering state.
        Rapidly interleave Video -> Image -> Audio -> Text -> Video.
        """
        sequence = [
            ("WIN_20260830_21_50_59_Pro.mp4", "VIDEO"),
            ("surface_bearing.png", "IMAGE"),
            ("engine_hum.mp3", "AUDIO"),
            ("notes.txt", "TEXT"),
            ("WIN_20260830_21_50_59_Pro.mp4", "VIDEO"),
            ("defect_macro.jpg", "IMAGE"),
        ]
        for filename, expected in sequence:
            mod = derive_modality(filename)
            self.assertEqual(mod, expected, f"Sequence call on '{filename}' expected {expected} but got {mod}")

    def test_payload_prefixes_and_mime(self):
        self.assertEqual(derive_modality("video container payload: WIN_2026.mp4"), "VIDEO")
        self.assertEqual(derive_modality("audio track payload: hum.wav"), "AUDIO")
        self.assertEqual(derive_modality("visual payload: frame.png"), "IMAGE")
        self.assertEqual(derive_modality("unnamed_stream", mime_type="video/mp4"), "VIDEO")
        self.assertEqual(derive_modality("unnamed_stream", mime_type="audio/ogg"), "AUDIO")
        self.assertEqual(derive_modality("unnamed_stream", mime_type="image/jpeg"), "IMAGE")

    def test_multi_dot_and_path_names(self):
        self.assertEqual(derive_modality(r"C:\Recordings\2026\sample.backup.v1.MP4"), "VIDEO")
        self.assertEqual(derive_modality(r"/var/data/my.audio.file.flac"), "AUDIO")
        self.assertEqual(derive_modality(r"archive.tar.gz"), "TEXT")

if __name__ == "__main__":
    unittest.main()
