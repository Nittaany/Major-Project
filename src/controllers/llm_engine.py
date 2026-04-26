"""
═══════════════════════════════════════════════════════════════════════════════
LLM_ENGINE.PY - PHASE 3.2 HYBRID LLM INTEGRATION
Dual-Backend Natural Language Generation for ISL Translation
═══════════════════════════════════════════════════════════════════════════════

ARCHITECTURE:
    Primary:  MLX (Local, Offline, Fast)
    Fallback: Groq API (Cloud, Reliable)
    Final:    Raw gloss output (Always works)

AUTHOR: Jarvis-EcoSign Team
DATE: April 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
from typing import List, Tuple, Optional
from dotenv import load_dotenv

# ═══════════════════════════════════════════════════════════════════════════
# 1. ENVIRONMENT & SECURITY
# ═══════════════════════════════════════════════════════════════════════════
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ═══════════════════════════════════════════════════════════════════════════
# 2. CONDITIONAL IMPORTS (Graceful Degradation)
# ═══════════════════════════════════════════════════════════════════════════
MLX_AVAILABLE = False
GROQ_AVAILABLE = False

try:
    import mlx.core as mx
    from mlx_lm import load, generate
    MLX_AVAILABLE = True
    print("[LLM] ✓ MLX backend loaded successfully")
except Exception as e:
    print(f"[LLM] ⚠ MLX unavailable: {e}")

try:
    from groq import Groq
    if GROQ_API_KEY and GROQ_API_KEY != "gsk_your_actual_key_here":
        GROQ_AVAILABLE = True
        print("[LLM] ✓ Groq API backend loaded successfully")
    else:
        print("[LLM] ⚠ Groq API key not configured")
except Exception as e:
    print(f"[LLM] ⚠ Groq unavailable: {e}")

# ═══════════════════════════════════════════════════════════════════════════
# 3. SYSTEM PROMPT (CRITICAL FOR QUALITY)
# ═══════════════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """You are an expert Indian Sign Language (ISL) to English translator.
You will receive a sequence of normalized gloss tokens representing a signed sentence.

STRICT RULES:
1. Convert them into ONE simple, natural English sentence.
2. Use proper grammar, word order, and capitalization.
3. the sentence should be gramatically correct and fluent.
4. STRICTLY preserve the core meaning. Do NOT invent new context.
5. DO NOT change the subject (e.g., if it says "I", keep it as "I").
6. Output ONLY the final translated sentence. No explanations, no pleasantries.

EXAMPLES:
Glosses: ['TIME', 'TEACHER']
Translation: Teacher, what is the time?

Glosses: ['BOOK', 'RED', 'WHERE']
Translation: Where is the red book?

Glosses: ['YOU_PLURAL', 'COME', 'TOMORROW']
Translation: You all are coming tomorrow.

Glosses: ['I', 'HAPPY', 'TODAY']
Translation: I am feeling happy today."""

# ═══════════════════════════════════════════════════════════════════════════
# 4. HYBRID LLM ENGINE CLASS
# ═══════════════════════════════════════════════════════════════════════════
class HybridLLM:
    """
    Dual-backend LLM with automatic fallback chain.
    
    Execution Order:
        1. MLX Local (if available)
        2. Groq API (if MLX fails or unavailable)
        3. Raw output (if both fail)
    """
    
    def __init__(self):
        self.mlx_model = None
        self.mlx_tokenizer = None
        self.groq_client = None
        self.cache = {}  # Result cache for repeated phrases
        
        # MLX Setup
        if MLX_AVAILABLE:
            self._initialize_mlx()
        
        # Groq Setup
        if GROQ_AVAILABLE:
            self._initialize_groq()
    
    # ═══════════════════════════════════════════════════════════════════════
    # MLX INITIALIZATION
    # ═══════════════════════════════════════════════════════════════════════
    def _initialize_mlx(self):
        """
        Load MLX model (Qwen1.5-1.8B-Chat-4bit).
        This happens ONCE at startup, then cached.
        """
        try:
            print("[LLM] 🔄 Loading MLX model (this may take 30-60 seconds)...")
            
            model_name = "mlx-community/Qwen1.5-1.8B-Chat-4bit"
            self.mlx_model, self.mlx_tokenizer = load(model_name)
            
            print("[LLM] ✅ MLX model ready")
            
        except Exception as e:
            print(f"[LLM] ❌ MLX initialization failed: {e}")
            self.mlx_model = None
            self.mlx_tokenizer = None
    
    # ═══════════════════════════════════════════════════════════════════════
    # GROQ INITIALIZATION
    # ═══════════════════════════════════════════════════════════════════════
    def _initialize_groq(self):
        """Setup Groq API client."""
        try:
            self.groq_client = Groq(api_key=GROQ_API_KEY)
            print("[LLM] ✅ Groq API client ready")
        except Exception as e:
            print(f"[LLM] ❌ Groq initialization failed: {e}")
            self.groq_client = None
    
    # ═══════════════════════════════════════════════════════════════════════
    # TOKEN NORMALIZATION (CRITICAL FOR QUALITY)
    # ═══════════════════════════════════════════════════════════════════════
    @staticmethod
    def normalize_tokens(words: List[str]) -> List[str]:
        """
        Convert to uppercase and replace spaces with underscores.
        
        Examples:
            ["hello", "you (plural)"] → ["HELLO", "YOU_PLURAL"]
        """
        normalized = []
        for word in words:
            # Uppercase
            word = word.upper()
            # Replace spaces with underscores
            word = word.replace(" ", "_").replace("(", "").replace(")", "")
            normalized.append(word)
        return normalized
    
    # ═══════════════════════════════════════════════════════════════════════
    # OUTPUT CLEANING (CRITICAL FOR QUALITY)
    # ═══════════════════════════════════════════════════════════════════════
    @staticmethod
    def _clean_output(text: str) -> str:
        """
        Clean LLM output to extract only the sentence.
        
        Fixes:
            - Removes system tokens
            - Keeps only first sentence
            - Capitalizes properly
            - Removes extra whitespace
        """
        text = text.strip()
        
        # Remove system tokens
        unwanted_tokens = ["<|im_end|>", "<|im_start|>", "<|assistant|>", "<|user|>"]
        for token in unwanted_tokens:
            text = text.replace(token, "")
        
        # Remove multiple sentences (keep first)
        if "." in text:
            text = text.split(".")[0] + "."
        
        # Capitalize first letter
        if text and not text[0].isupper():
            text = text[0].upper() + text[1:]
        
        # Clean extra whitespace
        text = " ".join(text.split())
        
        return text
    
    # ═══════════════════════════════════════════════════════════════════════
    # MLX INFERENCE
    # ═══════════════════════════════════════════════════════════════════════
    def _mlx_generate(self, gloss_tokens: List[str]) -> Optional[str]:
        """
        Generate sentence using local MLX model.
        
        Returns:
            str if successful, None if failed
        """
        if not self.mlx_model or not self.mlx_tokenizer:
            return None
        
        try:
            # Format prompt using tokenizer's chat template (PROPER METHOD)
            gloss_str = " ".join(gloss_tokens)
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": gloss_str}
            ]
            
            # Use tokenizer's built-in chat template
            prompt = self.mlx_tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # Generate
            output = generate(
                self.mlx_model,
                self.mlx_tokenizer,
                prompt=prompt,
                max_tokens=50,
                verbose=False
            )
            
            # Clean output (CRITICAL)
            sentence = self._clean_output(output)
            
            # Quality check
            if len(sentence) > 5 and not sentence.startswith("<"):
                return sentence
            else:
                return None
                
        except Exception as e:
            print(f"[LLM] ⚠ MLX generation failed: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════════════
    # GROQ API INFERENCE
    # ═══════════════════════════════════════════════════════════════════════
    def _groq_generate(self, gloss_tokens: List[str]) -> Optional[str]:
        """
        Generate sentence using Groq API (llama3-8b-8192).
        
        Returns:
            str if successful, None if failed
        """
        if not self.groq_client:
            return None
        
        try:
            gloss_str = " ".join(gloss_tokens)
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Updated to current model
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": gloss_str}
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            sentence = response.choices[0].message.content.strip()
            
            # Clean output (CRITICAL)
            sentence = self._clean_output(sentence)
            
            # Quality check
            if len(sentence) > 5:
                return sentence
            else:
                return None
                
        except Exception as e:
            print(f"[LLM] ⚠ Groq API failed: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════════════
    # MAIN GENERATION METHOD (PUBLIC API)
    # ═══════════════════════════════════════════════════════════════════════
    def generate_sentence(self, gloss_tokens: List[str]) -> Tuple[str, str]:
        """
        Generate natural sentence from ISL gloss tokens.
        
        Fallback Chain:
            1. Try MLX (local, fast)
            2. Try Groq (cloud, reliable)
            3. Return raw gloss (always works)
        
        Args:
            gloss_tokens: List of ISL words (e.g., ["HELLO", "YOU", "GOOD"])
        
        Returns:
            Tuple of (sentence, source)
            - sentence: Generated natural language
            - source: "mlx", "groq", or "raw"
        """
        # Normalize tokens
        normalized = self.normalize_tokens(gloss_tokens)
        
        # ─────────────────────────────────────────────────────────────────
        # OPTIMIZATION 1: Length Guard (avoid LLM for simple cases)
        # ─────────────────────────────────────────────────────────────────
        if len(normalized) <= 1:
            raw = " ".join(normalized)
            return raw.capitalize() + ".", "raw"
        
        # ─────────────────────────────────────────────────────────────────
        # OPTIMIZATION 2: Cache Check (instant for repeated phrases)
        # ─────────────────────────────────────────────────────────────────
        cache_key = tuple(normalized)
        if cache_key in self.cache:
            print(f"[LLM] ⚡ Cache hit: {self.cache[cache_key]}")
            return self.cache[cache_key], "cache"
        
        print(f"[LLM] 🔄 Generating sentence from: {normalized}")
        
        # ─────────────────────────────────────────────────────────────────
        # ATTEMPT 1: MLX LOCAL
        # ─────────────────────────────────────────────────────────────────
        if MLX_AVAILABLE and self.mlx_model:
            result = self._mlx_generate(normalized)
            if result:
                print(f"[LLM] ✅ MLX: {result}")
                self.cache[cache_key] = result  # Cache successful result
                return result, "mlx"
            else:
                print("[LLM] ⚠ MLX failed, trying Groq...")
        
        # ─────────────────────────────────────────────────────────────────
        # ATTEMPT 2: GROQ API
        # ─────────────────────────────────────────────────────────────────
        if GROQ_AVAILABLE and self.groq_client:
            result = self._groq_generate(normalized)
            if result:
                print(f"[LLM] ✅ Groq: {result}")
                self.cache[cache_key] = result  # Cache successful result
                return result, "groq"
            else:
                print("[LLM] ⚠ Groq failed, using raw output...")
        
        # ─────────────────────────────────────────────────────────────────
        # ATTEMPT 3: RAW FALLBACK (ALWAYS WORKS)
        # ─────────────────────────────────────────────────────────────────
        raw_sentence = " ".join(normalized).capitalize() + "."
        print(f"[LLM] ⚠ Fallback to raw: {raw_sentence}")
        return raw_sentence, "raw"


# ═══════════════════════════════════════════════════════════════════════════
# 5. STANDALONE TEST MODE
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("═" * 70)
    print("   LLM ENGINE - COMPREHENSIVE TEST")
    print("═" * 70)
    
    # Initialize engine
    engine = HybridLLM()
    
    # Test cases
    test_cases = [
        ["HELLO", "YOU", "GOOD"],
        ["TIME", "TEACHER"],
        ["I", "HAPPY", "TODAY"],
        ["YOU (PLURAL)", "COME", "TOMORROW"],
    ]
    
    print("\n" + "─" * 70)
    print("RUNNING TEST QUERIES...")
    print("─" * 70 + "\n")
    
    for i, gloss in enumerate(test_cases, 1):
        print(f"\n🔹 Test {i}: {gloss}")
        print("─" * 50)
        
        sentence, source = engine.generate_sentence(gloss)
        
        print(f"📝 Output:  {sentence}")
        print(f"🔧 Source:  {source.upper()}")
        print()
    
    print("═" * 70)
    print("   TEST COMPLETE")
    print("═" * 70)