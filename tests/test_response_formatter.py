# Tests for ResponseFormatter
"""
Tests for cleaning and converting LLM stage direction formats.
"""

import pytest

from neshama.soul.response_formatter import ResponseFormatter, FormatMode


class TestResponseFormatterClean:
    """Tests for CLEAN mode (remove stage directions)."""
    
    def setup_method(self):
        self.formatter = ResponseFormatter()
    
    def test_clean_asterisk_stage_direction(self):
        """Asterisk stage directions should be removed."""
        text = "*微笑* 你好啊，旅人。"
        result = self.formatter.format(text, FormatMode.CLEAN)
        assert result == "你好啊，旅人。"
    
    def test_clean_fullwidth_parentheses(self):
        """Full-width parentheses should be removed."""
        text = "（轻叹）这条路还很长。"
        result = self.formatter.format(text, FormatMode.CLEAN)
        assert result == "这条路还很长。"
    
    def test_clean_halfwidth_parentheses(self):
        """Half-width parentheses should be removed."""
        text = "(smiles) Welcome, traveler."
        result = self.formatter.format(text, FormatMode.CLEAN)
        assert result == "Welcome, traveler."
    
    def test_clean_multiple_stage_directions(self):
        """Multiple stage directions should all be removed."""
        text = "*微笑* 你好。*转身* *挥手* 再见！"
        result = self.formatter.format(text, FormatMode.CLEAN)
        # After removing stage directions, extra whitespace is cleaned to single space
        assert "你好" in result
        assert "再见" in result
        assert "微笑" not in result
        assert "转身" not in result
        assert "挥手" not in result
    
    def test_clean_mixed_formats(self):
        """Mixed format stage directions should all be removed."""
        text = "*点头* 好的。（思考）让我想想... (pauses) Hmm."
        result = self.formatter.format(text, FormatMode.CLEAN)
        assert "点头" not in result
        assert "思考" not in result
        assert "pauses" not in result
        assert "好的" in result
        assert "让我想想" in result
        assert "Hmm" in result
    
    def test_clean_no_stage_directions(self):
        """Text without stage directions should be unchanged."""
        text = "你好，欢迎来到旅店。"
        result = self.formatter.format(text, FormatMode.CLEAN)
        assert result == text
    
    def test_clean_empty_string(self):
        """Empty string should return empty string."""
        result = self.formatter.format("", FormatMode.CLEAN)
        assert result == ""
    
    def test_clean_only_stage_direction(self):
        """Text that is only stage directions should return empty."""
        text = "*沉默*"
        result = self.formatter.format(text, FormatMode.CLEAN)
        assert result == ""


class TestResponseFormatterConvert:
    """Tests for CONVERT mode (convert to bracket format)."""
    
    def setup_method(self):
        self.formatter = ResponseFormatter()
    
    def test_convert_asterisk_stage_direction(self):
        """Asterisk stage directions should be converted to brackets."""
        text = "*微笑* 你好啊，旅人。"
        result = self.formatter.format(text, FormatMode.CONVERT)
        assert result == "[微笑] 你好啊，旅人。"
    
    def test_convert_fullwidth_parentheses(self):
        """Full-width parentheses should be converted to brackets."""
        text = "（轻叹）这条路还很长。"
        result = self.formatter.format(text, FormatMode.CONVERT)
        assert result == "[轻叹]这条路还很长。"
    
    def test_convert_halfwidth_parentheses(self):
        """Half-width parentheses should be converted to brackets."""
        text = "(smiles) Welcome, traveler."
        result = self.formatter.format(text, FormatMode.CONVERT)
        assert result == "[smiles] Welcome, traveler."
    
    def test_convert_multiple_stage_directions(self):
        """Multiple stage directions should all be converted."""
        text = "*微笑* 你好。*转身* 再见！"
        result = self.formatter.format(text, FormatMode.CONVERT)
        assert "[微笑]" in result
        assert "[转身]" in result
        assert "你好" in result
        assert "再见" in result
    
    def test_convert_no_stage_directions(self):
        """Text without stage directions should be unchanged."""
        text = "你好，欢迎来到旅店。"
        result = self.formatter.format(text, FormatMode.CONVERT)
        assert result == text


class TestResponseFormatterFormatAll:
    """Tests for format_all (returns both modes)."""
    
    def setup_method(self):
        self.formatter = ResponseFormatter()
    
    def test_format_all_returns_both(self):
        """format_all should return both clean and convert versions."""
        text = "*微笑* 你好。"
        result = self.formatter.format_all(text)
        assert "clean" in result
        assert "convert" in result
        assert result["clean"] == "你好。"
        assert result["convert"] == "[微笑] 你好。"
    
    def test_format_all_empty(self):
        """format_all with empty string should return empty strings."""
        result = self.formatter.format_all("")
        assert result["clean"] == ""
        assert result["convert"] == ""


class TestResponseFormatterEdgeCases:
    """Edge case tests."""
    
    def setup_method(self):
        self.formatter = ResponseFormatter()
    
    def test_nested_asterisks_not_matched(self):
        """Nested asterisks should be handled gracefully."""
        # This is an edge case - the regex uses non-greedy match
        text = "*a*b* c"
        result = self.formatter.format(text, FormatMode.CONVERT)
        # Should convert *a* and *b* separately or handle gracefully
        assert "c" in result
    
    def test_whitespace_cleanup(self):
        """Extra whitespace from removal should be cleaned up."""
        text = "*a*     *b* text"
        result = self.formatter.format(text, FormatMode.CLEAN)
        assert "  " not in result
    
    def test_none_input(self):
        """None input should be handled gracefully."""
        result = self.formatter.format(None, FormatMode.CLEAN)
        assert result is None
