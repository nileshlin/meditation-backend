import httpx
import subprocess
import os
import asyncio
from pathlib import Path
from app.config.settings import settings
from app.config.logger import logger
from typing import List, Dict, Optional


class AudioBlockService:
    def __init__(self):
        self.settings = settings
        self.voice_id = self.settings.ELEVENLABS_VOICE_ID
        logger.info(f"AudioBlockService initialized with voice_id: Reigo Vilbiks voice ({self.voice_id})")
        self.base_storage = Path(self.settings.STORAGE_PATH) / "audio_blocks"
        self.base_storage.mkdir(parents=True, exist_ok=True)

    async def generate_audio_blocks(
        self,
        scripts: List[str],
        meditation_id: int,
        music_path: Optional[Path] = None
    ) -> List[Dict]:
    
        med_dir = self.base_storage / f"meditation_{meditation_id}"
        med_dir.mkdir(parents=True, exist_ok=True)

        blocks_to_generate = [
            {"number": 1, "duration": 90, "text": scripts[0]},
            {"number": 2, "duration": 150, "text": scripts[1]},
            {"number": 3, "duration": 90,  "text": scripts[2]},
            {"number": 4, "duration": 120, "text": scripts[3]},
            {"number": 5, "duration": 120, "text": scripts[4]},
        ]
    
        results = []
        for block in blocks_to_generate:
            logger.info(f"Generating block {block['number']} (meditation {meditation_id})")

            base_audio_path = await self._generate_base_clip(
                block['text'],
                block['number'],
                med_dir
            )

            final_filename = f"block_{block['number']}.mp3"
            final_path = med_dir / final_filename

            await self._loop_audio(
                base_audio_path,
                final_path,
                block['duration'],
                music_path
            )

            public_url = f"/storage/audio_blocks/meditation_{meditation_id}/{final_filename}"

            results.append({
                "block": block['number'],
                "duration": block['duration'],
                "url": public_url,
                "background_audio": music_path.name if music_path else None
            })

        return results

    async def _generate_base_clip(self, text: str, block_number: int, med_dir: Path) -> Path:
        headers = {
            "xi-api-key": self.settings.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        payload = {
            "text": text,
            "model_id": self.settings.ELEVENLABS_MODEL,
            "voice_settings": {
                "stability": 0.6,
                "similarity_boost": 0.75,
                "style": 0.5,
                "use_speaker_boost": True,
            },
        }

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}?output_format=mp3_44100_128"

        base_path = med_dir / f"base_clip_{block_number}.mp3"

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            with open(base_path, "wb") as f:
                f.write(response.content)

        return base_path

    async def _loop_audio(self, input_path: Path, output_path: Path, duration_seconds: int, music_path: Path = None):
        duration_f = float(duration_seconds)
        wav_path = output_path.with_suffix(".temp.wav")
        
        VOICE_VOLUME_DB = "+6.0"
        
        wav_cmd = [
            self.settings.FFMPEG_PATH, "-y",
            "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={duration_f}",
            "-stream_loop", "-1",
            "-i", str(input_path),
        ]

        if music_path:
            wav_cmd.extend([
                "-stream_loop", "-1",
                "-i", str(music_path)
            ])
            filter_complex = (
                f"[1:a]atrim=0:{duration_f},volume={VOICE_VOLUME_DB},loudnorm=I=-16:TP=-1.5:LRA=11[v]; "
                f"[2:a]atrim=0:{duration_f},volume=0.35[m]; "
                f"[0:a][v][m]amix=inputs=3:duration=first:dropout_transition=0"
            )
        else:
            filter_complex = (
                f"[1:a]atrim=0:{duration_f},volume={VOICE_VOLUME_DB},loudnorm=I=-16:TP=-1.5:LRA=11[v]; "
                f"[0:a][v]amix=inputs=2:duration=first"
            )

        wav_cmd.extend([
            "-filter_complex", filter_complex,
            "-t", f"{duration_f}",
            "-ar", "44100",
            str(wav_path)
        ])
        
        mp3_cmd = [
            self.settings.FFMPEG_PATH, "-y",
            "-i", str(wav_path),
            "-c:a", "libmp3lame", "-b:a", "128k",
            "-ar", "44100",
            str(output_path)
        ]
        
        def _execute(cmd, label):
            logger.info(f"[{label}] Running: {' '.join(cmd)}")
            return subprocess.run(cmd, capture_output=True, text=True)

        res1 = await asyncio.to_thread(_execute, wav_cmd, "WAV_MIX")
        if res1.returncode != 0:
            logger.error(f"WAV Mix failed: {res1.stderr}")
            raise RuntimeError(f"WAV Mix failed for {wav_path}")

        res2 = await asyncio.to_thread(_execute, mp3_cmd, "MP3_ENCODE")
        if res2.returncode != 0:
            logger.error(f"MP3 Encode failed: {res2.stderr}")
            raise RuntimeError(f"MP3 Encode failed for {output_path}")
        
        logger.info(f"Generated high-precision audio (Exact): {output_path} ({duration_f}s)")
        
        if wav_path.exists():
            os.remove(wav_path)
        if input_path.exists():
            os.remove(input_path)
