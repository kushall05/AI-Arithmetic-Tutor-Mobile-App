/* ==========================================================================
   AI ARITHMETIC TUTOR - VOICE MODULE (TTS & SPEECH RECOGNITION)
   ========================================================================== */

const VoiceModule = {
    synth: window.speechSynthesis,
    recognition: null,
    isListening: false,

    init() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';

            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                console.log('Voice recognized:', transcript);
                this.handleRecognizedVoice(transcript);
            };

            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.stopListening();
            };

            this.recognition.onend = () => {
                this.stopListening();
            };
        } else {
            console.warn('Web Speech Recognition is not supported in this browser.');
        }
    },

    speak(text) {
        if (!this.synth) return;
        this.synth.cancel(); // Stop any active speech

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.95; // Slightly slower for clarity
        utterance.pitch = 1.1; // Friendly pitch
        
        // Select an English voice if available
        const voices = this.synth.getVoices();
        const enVoice = voices.find(v => v.lang.includes('en') && v.name.includes('Google') || v.name.includes('Natural'));
        if (enVoice) utterance.voice = enVoice;

        this.synth.speak(utterance);
    },

    listen(callback) {
        if (!this.recognition) {
            alert('Voice input is not supported on this browser. Try Google Chrome!');
            return;
        }

        this.onVoiceCallback = callback;
        try {
            this.isListening = true;
            this.recognition.start();
            this.updateVoiceButtonState(true);
        } catch (e) {
            console.error('Recognition start error:', e);
        }
    },

    stopListening() {
        this.isListening = false;
        this.updateVoiceButtonState(false);
    },

    handleRecognizedVoice(transcript) {
        // Extract numbers from recognized text (e.g. "twenty five" -> 25)
        const text = transcript.toLowerCase();
        let numberFound = null;

        // Extract digits first
        const digitMatch = text.match(/\d+/);
        if (digitMatch) {
            numberFound = parseInt(digitMatch[0]);
        } else {
            // Word to number basic map
            const wordMap = {
                'zero': 0, 'one': 1, 'two': 2, 'to': 2, 'too': 2, 'three': 3, 'four': 4, 'for': 4,
                'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'ate': 8, 'nine': 9, 'ten': 10,
                'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
                'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
            };
            for (let word in wordMap) {
                if (text.includes(word)) {
                    numberFound = wordMap[word];
                    break;
                }
            }
        }

        if (this.onVoiceCallback && numberFound !== null) {
            this.onVoiceCallback(numberFound, transcript);
        } else {
            this.speak(`I heard "${transcript}". Please say a clear number!`);
        }
    },

    updateVoiceButtonState(active) {
        const btn = document.getElementById('voiceInputBtn');
        if (btn) {
            if (active) {
                btn.innerHTML = '🔴 Listening...';
                btn.classList.add('listening');
            } else {
                btn.innerHTML = '🎙️ Speak Answer';
                btn.classList.remove('listening');
            }
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    VoiceModule.init();
});
