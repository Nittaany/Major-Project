"""
═══════════════════════════════════════════════════════════════════════════════
LLM_ENGINE.PY - PHASE 3.2 HYBRID LLM INTEGRATION
Dual-Backend Natural Language Generation for ISL Translation
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import time
import concurrent.futures
from typing import List, Tuple, Optional
from dotenv import load_dotenv

# ═══════════════════════════════════════════════════════════════════════════
# ENVIRONMENT & SECURITY
# ═══════════════════════════════════════════════════════════════════════════
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MLX_AVAILABLE = False
GROQ_AVAILABLE = False

try:
    import mlx.core as mx
    from mlx_lm import load, generate
    MLX_AVAILABLE = True
except Exception: pass

try:
    from groq import Groq
    if GROQ_API_KEY and GROQ_API_KEY != "gsk_your_actual_key_here":
        GROQ_AVAILABLE = True
except Exception: pass

SYSTEM_PROMPT = """You are an expert Indian Sign Language (ISL) to English translator.
You will receive a sequence of normalized gloss tokens representing a signed sentence.

STRICT RULES:
1. Convert them into ONE simple, natural English sentence.
2. Use proper grammar, word order, and capitalization.
3. The sentence should be grammatically correct and fluent.
4. STRICTLY preserve the core meaning. Do NOT invent new context.
5. DO NOT change the subject (e.g., if it says "I", keep it as "I").
6. Output ONLY the final translated sentence. No explanations, no pleasantries.

EXAMPLES:
Glosses: ['GOOD MORNING', 'FATHER', 'TIME']
Translation: Good morning father, what is the time?

Glosses: ['GOOD MORNING', 'I', 'HAPPY']
Translation: Good morning, I am happy today.

Glosses: ['BOOK', 'RED', 'WHERE']
Translation: Where is the red book?

Glosses: ['YOU', 'COME', 'TOMORROW']
Translation: You are coming tomorrow."""

# ═══════════════════════════════════════════════════════════════════════════
# HYBRID LLM ENGINE CLASS
# ═══════════════════════════════════════════════════════════════════════════
class HybridLLM:
    
    def __init__(self):
        self.mlx_model = None
        self.mlx_tokenizer = None
        self.groq_client = None
        self.cache = {}
        
        if MLX_AVAILABLE: self._initialize_mlx()
        if GROQ_AVAILABLE: self._initialize_groq()
    
    def _initialize_mlx(self):
        try:
            print("[LLM] 🔄 Loading MLX model (this may take 30-60 seconds)...")
            self.mlx_model, self.mlx_tokenizer = load("mlx-community/Qwen1.5-1.8B-Chat-4bit")
            print("[LLM] ✅ MLX model ready")
        except Exception as e:
            print(f"[LLM] ❌ MLX initialization failed: {e}")
    
    def _initialize_groq(self):
        try:
            self.groq_client = Groq(api_key=GROQ_API_KEY)
            print("[LLM] ✅ Groq API client ready")
        except Exception as e:
            print(f"[LLM] ❌ Groq initialization failed: {e}")
    
    @staticmethod
    def normalize_tokens(words: List[str]) -> List[str]:
        normalized = []
        for word in words:
            word = word.upper().replace(" ", "_").replace("(", "").replace(")", "")
            normalized.append(word)
        return normalized
    
    @staticmethod
    def _clean_output(text: str) -> str:
        text = text.strip()
        unwanted_tokens = ["<|im_end|>", "<|im_start|>", "<|assistant|>", "<|user|>"]
        for token in unwanted_tokens:
            text = text.replace(token, "")
        if "." in text:
            text = text.split(".")[0] + "."
        if text and not text[0].isupper():
            text = text[0].upper() + text[1:]
        return " ".join(text.split())
    
    def _mlx_generate(self, gloss_tokens: List[str]) -> Optional[str]:
        if not self.mlx_model or not self.mlx_tokenizer: return None
        try:
            # Add commas between words for better model parsing
            gloss_str = ", ".join(gloss_tokens) 
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                # Force the exact pattern from the examples!
                {"role": "user", "content": f"Input: [ {gloss_str} ]\nOutput:"} 
            ]
            
            prompt = self.mlx_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            output = generate(self.mlx_model, self.mlx_tokenizer, prompt=prompt, max_tokens=50, verbose=False)
            sentence = self._clean_output(output)
            
            # Clean up any accidental "Output:" text the model might spit back
            if sentence.startswith("Output:"):
                sentence = sentence.replace("Output:", "").strip()
                
            if len(sentence) > 5 and not sentence.startswith("<"): return sentence
            return None
        except Exception as e:
            print(f"[LLM] ⚠ MLX generation failed: {e}")
            return None
    
    def _groq_generate(self, gloss_tokens: List[str]) -> Optional[str]:
        if not self.groq_client: return None
        gloss_str = " ".join(gloss_tokens)
        
        # 2-Attempt Retry Loop for network stability
        for attempt in range(2):
            try:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": gloss_str}
                    ],
                    max_tokens=50,
                    temperature=0.3
                )
                sentence = self._clean_output(response.choices[0].message.content.strip())
                if len(sentence) > 5: return sentence
                return None
            except Exception as e:
                if attempt == 0:
                    print(f"\033[93m[LLM] ⚠ Groq network blip. Retrying...\033[0m")
                    time.sleep(0.5)
                else:
                    print(f"\033[91m[LLM] ⚠ Groq API failed after retry: {e}\033[0m")
                    return None

    # ═══════════════════════════════════════════════════════════════════════════
    # THE MAIN GENERATION PIPELINE
    # ═══════════════════════════════════════════════════════════════════════════
    def generate_sentence(self, gloss_tokens: List[str]) -> Tuple[str, str]:
        # 1. Default to Groq
        active_mode = "GROQ" 
        
        # 2. Try to read the live UI toggle state from the file
        try:
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            mode_file = os.path.join(project_root, "data", "llm_mode.txt")
            if os.path.exists(mode_file):
                with open(mode_file, "r") as f:
                    content = f.read().strip()
                    if content: active_mode = content
        except Exception: pass

        normalized = self.normalize_tokens(gloss_tokens)
        if len(normalized) <= 1:
            return " ".join(normalized).capitalize() + ".", "raw"
            
        cache_key = tuple(normalized)
        if cache_key in self.cache:
            return self.cache[cache_key], "cache"
            
        print(f"\n[LLM] 🔄 Translating: {normalized} (via {active_mode})")

        def _run_engine():
            if active_mode in ["MLX", "AUTO"] and MLX_AVAILABLE and self.mlx_model:
                res = self._mlx_generate(normalized)
                if res: return res, "mlx"
                
            if active_mode in ["GROQ", "AUTO"] and GROQ_AVAILABLE and self.groq_client:
                res = self._groq_generate(normalized)
                if res: return res, "groq"
                
            return " ".join(normalized).capitalize() + ".", "raw"

        # 3. Execute with 5-second timeout protection
# 3. Execute with 5-second timeout protection
        start_time = time.time() # <--- START LATENCY TIMER
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_run_engine)
                result, source = future.result(timeout=5.0) 
                
                end_time = time.time() # <--- END LATENCY TIMER
                latency_ms = (end_time - start_time) * 1000
                
                self.cache[cache_key] = result
                print(f"\033[96m║  [Metric] Latency: {latency_ms:.0f} ms{'':<22} ║\033[0m") # <--- LOG IT
                return result, source
                
        except concurrent.futures.TimeoutError:
            print("\033[91m[LLM] ⏱️ TIMEOUT: Generation exceeded 5 seconds. Bailing out!\033[0m")
            return " ".join(normalized).capitalize() + ".", "raw_timeout"
        except Exception as e:
            print(f"\033[91m[LLM] ❌ Error: {e}\033[0m")
            return " ".join(normalized).capitalize() + ".", "raw_error"

# ═══════════════════════════════════════════════════════════════════════════
# STANDALONE TEST MODE
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("═" * 70)
    print("   LLM ENGINE - COMPREHENSIVE TEST")
    print("═" * 70)
    engine = HybridLLM()
    test_cases = [["HELLO", "YOU", "GOOD"], ["TIME", "TEACHER"]]
    for i, gloss in enumerate(test_cases, 1):
        print(f"\n🔹 Test {i}: {gloss}")
        sentence, source = engine.generate_sentence(gloss)
        print(f"📝 Output:  {sentence}")
        print(f"🔧 Source:  {source.upper()}")