# Soul Layer - Response Formatter
"""
ResponseFormatter - Cleans and converts LLM stage direction formats.

LLMs sometimes output stage directions in formats like *动作描写* or
（动作描写）. This module provides two modes:
- clean: Remove stage directions, keep dialogue text only
- convert: Convert stage directions to bracket format [动作描写] for UI rendering

Features:
- Handles *asterisk* stage directions
- Handles （全角括号）and (half-width) stage directions
- Preserves dialogue text
- No external dependencies
"""

import re
from typing import Dict, Any
from enum import Enum


class FormatMode(Enum):
    """Formatting mode for stage directions."""
    CLEAN = "clean"      # Remove stage directions entirely
    CONVERT = "convert"  # Convert to [bracket] format


class ResponseFormatter:
    """
    Format LLM responses by cleaning or converting stage directions.
    
    Example:
        >>> formatter = ResponseFormatter()
        >>> formatter.format("*微笑* 你好啊，旅人。")
        {'clean': '你好啊，旅人。', 'convert': '[微笑] 你好啊，旅人。'}
        >>> formatter.format("*微笑* 你好啊，旅人。", mode=FormatMode.CLEAN)
        '你好啊，旅人。'
    """
    
    # Pattern for asterisk-wrapped stage directions: *动作描写*
    _ASTERISK_PATTERN = re.compile(r'\*([^*]+?)\*')
    
    # Pattern for full-width parentheses: （动作描写）
    _FULLWIDTH_PAREN_PATTERN = re.compile(r'（([^）]+?)）')
    
    # Pattern for half-width parentheses with Chinese or action content
    # Only match when content looks like a stage direction (short, no sentence-ending punctuation)
    _HALFWIDTH_PAREN_PATTERN = re.compile(r'\(([^)]+?)\)')
    
    def format(self, text: str, mode: FormatMode = FormatMode.CONVERT) -> str:
        """
        Format a response text by handling stage directions.
        
        Args:
            text: The raw LLM response text
            mode: FormatMode.CLEAN to remove, FormatMode.CONVERT to bracket format
            
        Returns:
            Formatted text string
        """
        if not text:
            return text
        
        if mode == FormatMode.CLEAN:
            return self._clean(text)
        elif mode == FormatMode.CONVERT:
            return self._convert(text)
        else:
            raise ValueError(f"Unknown format mode: {mode}")
    
    def format_all(self, text: str) -> Dict[str, str]:
        """
        Return both clean and convert formatted versions.
        
        Args:
            text: The raw LLM response text
            
        Returns:
            Dict with 'clean' and 'convert' keys
        """
        return {
            "clean": self._clean(text),
            "convert": self._convert(text),
        }
    
    def _clean(self, text: str) -> str:
        """Remove all stage directions from text."""
        # Remove *asterisk* stage directions
        result = self._ASTERISK_PATTERN.sub('', text)
        
        # Remove （全角括号）stage directions
        result = self._FULLWIDTH_PAREN_PATTERN.sub('', result)
        
        # Remove (half-width) stage directions
        result = self._HALFWIDTH_PAREN_PATTERN.sub('', result)
        
        # Clean up extra whitespace left by removal
        result = re.sub(r'\s{2,}', ' ', result).strip()
        
        return result
    
    def _convert(self, text: str) -> str:
        """Convert stage directions to [bracket] format."""
        # Convert *asterisk* to [bracket]
        result = self._ASTERISK_PATTERN.sub(r'[\1]', text)
        
        # Convert （全角括号）to [bracket]
        result = self._FULLWIDTH_PAREN_PATTERN.sub(r'[\1]', result)
        
        # Convert (half-width) to [bracket]
        result = self._HALFWIDTH_PAREN_PATTERN.sub(r'[\1]', result)
        
        # Clean up extra whitespace
        result = re.sub(r'\s{2,}', ' ', result).strip()
        
        return result
