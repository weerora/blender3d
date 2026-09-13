/** Small local soundscape. No autoplay, external media, or microphone access. */
export class AmbientAudio {
  private context?: AudioContext;
  private gain?: GainNode;
  private oscillators: OscillatorNode[] = [];
  public playing = false;
  public volume = .22;
  async toggle() {
    if (!this.context) {
      this.context = new AudioContext();
      this.gain = this.context.createGain();
      this.gain.gain.value = 0;
      this.gain.connect(this.context.destination);
      for (const frequency of [130.81, 196, 261.63, 329.63]) {
        const oscillator = this.context.createOscillator();
        oscillator.type = 'sine';
        oscillator.frequency.value = frequency;
        oscillator.detune.value = (this.oscillators.length - 1.5) * 2;
        oscillator.connect(this.gain);
        oscillator.start();
        this.oscillators.push(oscillator);
      }
    }
    await this.context.resume();
    this.playing = !this.playing;
    this.updateVolume();
    return this.playing;
  }
  setVolume(value: number) { this.volume = value; this.updateVolume(); }
  private updateVolume() {
    if (this.gain && this.context) this.gain.gain.setTargetAtTime(this.playing ? this.volume * .10 : 0, this.context.currentTime, .3);
  }
  async stop() { this.playing = false; this.updateVolume(); }
  dispose() { this.oscillators.forEach(o => o.stop()); void this.context?.close(); }
}
